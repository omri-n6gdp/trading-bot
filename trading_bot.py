# --- IMPORTS ---

import yfinance as yf           # Pulls real stock data
import pandas as pd             # Data manipulation
import numpy as np              # Maths and calculations
import matplotlib.pyplot as plt # Plotting
import warnings
warnings.filterwarnings("ignore")

# --- CONFIGURATION ---

start_date = "2000-01-01"   # Start date of backtest data
end_date = "2026-01-01"     # End date of backtest data
initial_capital = 10000     # Starting capital

indicies = [
    '^FTSE',    # UK FTSE 100
    '^NDX',     # NASDAQ 100
    '^GSPC',    # S&P 500
    '^DJI',     # Dow Jones Industrial
    'VWRL.L',   # FTSE All-World
]

plot_results = True     # Show charts
save_plots = False      # Save charts as files

# --- STRATEGY PARAMETERS ---

sma_short = 20          # SMA short window (days)
sma_long = 50           # SMA long window (days)

rsi_period = 14         # RSI lookback period
rsi_overbought = 70     # RSI sell threshold
rsi_oversold = 30       # RSI buy threshold

macd_fast = 12          # MACD fast EMA (days)
macd_slow = 26          # MACD slow EMA (days)
macd_signal = 9         # MACD signal line (days)

momentum_period = 10    # Momentum lookback (days)

bb_period = 20          # Bollinger Bands MA period
bb_std = 2              # Bollinger Bands standard deviations

# --- SCORING WEIGHTS ---

metric_weights = {
    'total_return': 0.25,       # Total profit %
    'sharpe_ratio': 0.25,       # Risk-adjusted return
    'win_rate': 0.20,           # % of winning trades
    'max_drawdown': 0.20,       # Worst peak-to-trough
    'avg_trade_return': 0.10    # Average profit per trade
}

# --- DATA FETCHING ---

def fetch_data(ticker, start, end):

    print(f"  Fetching {ticker}...")

    try:
        data = yf.download(ticker, start=start, end=end, progress=False)
        data.columns = data.columns.get_level_values(0)

        if data.empty:
            print(f"  No data found for {ticker}. Skipping...")
            return None

        missing_count = data.isnull().sum().sum()
        if missing_count > 0:
            data = data.ffill()

        if data.index.duplicated().any():
            data = data[~data.index.duplicated(keep='first')]

        data = data.sort_index()
        print(f"  {len(data)} data points fetched")
        return data

    except Exception as e:
        print(f"  Error fetching {ticker}: {e}")
        return None

# --- BASE STRATEGY ---

class Strategy:

    def __init__(self, name, data):
        self.name = name
        self.data = data.copy()
        self.signals = None
        self.trades = []
        self.metrics = {}

    def generate_signals(self):
        raise NotImplementedError("Subclasses must implement generate_signals()")

    def backtest(self):

        self.generate_signals()

        position = None
        self.trades = []

        for date, row in self.data.iterrows():
            signal = self.signals.loc[date] if date in self.signals.index else 0
            close_price = row['Close']

            if signal == 1 and position is None:
                position = close_price

            elif signal == -1 and position is not None:
                pnl = close_price - position
                pnl_pct = (pnl / position) * 100
                self.trades.append({
                    'entry_price': position,
                    'exit_price': close_price,
                    'pnl': pnl,
                    'pnl_pct': pnl_pct,
                    'exit_date': date
                })
                position = None

    def calculate_metrics(self):

        if len(self.trades) == 0:
            self.metrics = {
                'total_return': 0, 'win_rate': 0, 'num_trades': 0,
                'avg_trade_return': 0, 'max_drawdown': 0, 'sharpe_ratio': 0
            }
            return self.metrics

        trades_df = pd.DataFrame(self.trades)

        total_return = trades_df['pnl_pct'].sum()
        win_rate = (trades_df['pnl_pct'] > 0).sum() / len(trades_df) * 100
        avg_trade_return = trades_df['pnl_pct'].mean()

        cumulative_pnl = trades_df['pnl_pct'].cumsum()
        running_max = cumulative_pnl.expanding().max()
        max_drawdown = (cumulative_pnl - running_max).min()

        if trades_df['pnl_pct'].std() > 0:
            sharpe_ratio = (trades_df['pnl_pct'].mean() / trades_df['pnl_pct'].std()) * np.sqrt(252)
        else:
            sharpe_ratio = 0

        self.metrics = {
            'total_return': total_return,
            'win_rate': win_rate,
            'num_trades': len(trades_df),
            'avg_trade_return': avg_trade_return,
            'max_drawdown': max_drawdown,
            'sharpe_ratio': sharpe_ratio
        }
        return self.metrics

    def run(self):
        self.backtest()
        self.calculate_metrics()
        return self.metrics

# --- STRATEGY 1: SMA CROSSOVER ---

class SMACrossover(Strategy):

    def __init__(self, name, data, short_window, long_window):
        super().__init__(name, data)
        self.short_window = short_window
        self.long_window = long_window

    def generate_signals(self):

        self.data['SMA_short'] = self.data['Close'].rolling(window=self.short_window).mean()
        self.data['SMA_long'] = self.data['Close'].rolling(window=self.long_window).mean()
        self.signals = pd.Series(0, index=self.data.index)

        for i in range(1, len(self.data)):
            curr_s = self.data['SMA_short'].iloc[i]
            curr_l = self.data['SMA_long'].iloc[i]
            prev_s = self.data['SMA_short'].iloc[i-1]
            prev_l = self.data['SMA_long'].iloc[i-1]

            if pd.isna(curr_s) or pd.isna(curr_l):
                continue

            if prev_s <= prev_l and curr_s > curr_l:
                self.signals.iloc[i] = 1
            elif prev_s >= prev_l and curr_s < curr_l:
                self.signals.iloc[i] = -1

# --- STRATEGY 2: RSI ---

class RSIStrategy(Strategy):

    def __init__(self, name, data, period, overbought, oversold):
        super().__init__(name, data)
        self.period = period
        self.overbought = overbought
        self.oversold = oversold

    def generate_signals(self):

        delta = self.data['Close'].diff()
        gains = delta.clip(lower=0)
        losses = -delta.clip(upper=0)
        avg_gain = gains.rolling(window=self.period).mean()
        avg_loss = losses.rolling(window=self.period).mean()
        rs = avg_gain / avg_loss
        self.data['RSI'] = 100 - (100 / (1 + rs))
        self.signals = pd.Series(0, index=self.data.index)

        for i in range(1, len(self.data)):
            curr_rsi = self.data['RSI'].iloc[i]
            prev_rsi = self.data['RSI'].iloc[i-1]

            if pd.isna(curr_rsi):
                continue

            if prev_rsi <= self.oversold and curr_rsi > self.oversold:
                self.signals.iloc[i] = 1
            elif prev_rsi <= self.overbought and curr_rsi > self.overbought:
                self.signals.iloc[i] = -1

# --- STRATEGY 3: MACD ---

class MACDStrategy(Strategy):

    def __init__(self, name, data, fast, slow, signal):
        super().__init__(name, data)
        self.fast = fast
        self.slow = slow
        self.signal = signal

    def generate_signals(self):

        ema_fast = self.data['Close'].ewm(span=self.fast).mean()
        ema_slow = self.data['Close'].ewm(span=self.slow).mean()
        self.data['MACD'] = ema_fast - ema_slow
        self.data['Signal_Line'] = self.data['MACD'].ewm(span=self.signal).mean()
        self.signals = pd.Series(0, index=self.data.index)

        for i in range(1, len(self.data)):
            curr_macd = self.data['MACD'].iloc[i]
            curr_sig = self.data['Signal_Line'].iloc[i]
            prev_macd = self.data['MACD'].iloc[i-1]
            prev_sig = self.data['Signal_Line'].iloc[i-1]

            if pd.isna(curr_macd) or pd.isna(curr_sig):
                continue

            if prev_macd <= prev_sig and curr_macd > curr_sig:
                self.signals.iloc[i] = 1
            elif prev_macd >= prev_sig and curr_macd < curr_sig:
                self.signals.iloc[i] = -1

# --- STRATEGY 4: MOMENTUM ---

class MomentumStrategy(Strategy):

    def __init__(self, name, data, period):
        super().__init__(name, data)
        self.period = period

    def generate_signals(self):

        self.data['Momentum'] = self.data['Close'].diff(self.period)
        self.signals = pd.Series(0, index=self.data.index)

        for i in range(1, len(self.data)):
            curr_mom = self.data['Momentum'].iloc[i]
            prev_mom = self.data['Momentum'].iloc[i-1]

            if pd.isna(curr_mom) or pd.isna(prev_mom):
                continue

            if prev_mom <= 0 and curr_mom > 0:
                self.signals.iloc[i] = 1
            elif prev_mom >= 0 and curr_mom < 0:
                self.signals.iloc[i] = -1

# --- STRATEGY 5: BOLLINGER BANDS ---

class BollingerBands(Strategy):

    def __init__(self, name, data, period, std_dev):
        super().__init__(name, data)
        self.period = period
        self.std_dev = std_dev

    def generate_signals(self):

        self.data['BB_mid'] = self.data['Close'].rolling(window=self.period).mean()
        self.data['BB_std'] = self.data['Close'].rolling(window=self.period).std()
        self.data['BB_upper'] = self.data['BB_mid'] + (self.std_dev * self.data['BB_std'])
        self.data['BB_lower'] = self.data['BB_mid'] - (self.std_dev * self.data['BB_std'])
        self.signals = pd.Series(0, index=self.data.index)

        for i in range(1, len(self.data)):
            curr_close = self.data['Close'].iloc[i]
            prev_close = self.data['Close'].iloc[i-1]
            curr_upper = self.data['BB_upper'].iloc[i]
            curr_lower = self.data['BB_lower'].iloc[i]
            prev_upper = self.data['BB_upper'].iloc[i-1]
            prev_lower = self.data['BB_lower'].iloc[i-1]

            if pd.isna(curr_upper) or pd.isna(curr_lower):
                continue

            if prev_close >= prev_lower and curr_close < curr_lower:
                self.signals.iloc[i] = 1
            elif prev_close <= prev_upper and curr_close > curr_upper:
                self.signals.iloc[i] = -1

# --- BACKTESTING ENGINE ---

def run_all_strategies(indicies, start_date, end_date):

    all_results = {}

    for ticker in indicies:
        print(f"\n[{ticker}]")
        data = fetch_data(ticker, start_date, end_date)
        if data is None:
            continue

        all_results[ticker] = {}

        strategies = [
            SMACrossover("SMA Crossover", data, sma_short, sma_long),
            RSIStrategy("RSI", data, rsi_period, rsi_overbought, rsi_oversold),
            MACDStrategy("MACD", data, macd_fast, macd_slow, macd_signal),
            MomentumStrategy("Momentum", data, momentum_period),
            BollingerBands("Bollinger Bands", data, bb_period, bb_std)
        ]

        for strategy in strategies:
            metrics = strategy.run()
            all_results[ticker][strategy.name] = metrics
            print(f"  {strategy.name}: {metrics['num_trades']} trades | return={metrics['total_return']:.1f}% | sharpe={metrics['sharpe_ratio']:.2f}")

    return all_results

# --- SCORING & RANKING ---

def score_and_rank(results):

    rows = []
    for ticker, strategies in results.items():
        for strat_name, metrics in strategies.items():
            rows.append({'ticker': ticker, 'strategy': strat_name, **metrics})

    df = pd.DataFrame(rows)

    def normalise(series, invert=False):
        min_val, max_val = series.min(), series.max()
        if max_val == min_val:
            return pd.Series(0.5, index=series.index)
        normalised = (series - min_val) / (max_val - min_val)
        return 1 - normalised if invert else normalised

    df['n_total_return']     = normalise(df['total_return'])
    df['n_sharpe_ratio']     = normalise(df['sharpe_ratio'])
    df['n_win_rate']         = normalise(df['win_rate'])
    df['n_max_drawdown']     = normalise(df['max_drawdown'], invert=True)
    df['n_avg_trade_return'] = normalise(df['avg_trade_return'])

    df['score'] = (
        df['n_total_return']     * metric_weights['total_return']     +
        df['n_sharpe_ratio']     * metric_weights['sharpe_ratio']     +
        df['n_win_rate']         * metric_weights['win_rate']         +
        df['n_max_drawdown']     * metric_weights['max_drawdown']     +
        df['n_avg_trade_return'] * metric_weights['avg_trade_return']
    )

    df = df.sort_values('score', ascending=False).reset_index(drop=True)
    df['rank'] = df.index + 1
    return df

# --- VISUALISATIONS ---

def plot_heatmap(ranked_df):

    pivot = ranked_df.pivot(index='strategy', columns='ticker', values='score')
    fig, ax = plt.subplots(figsize=(10, 5))
    im = ax.imshow(pivot.values, cmap='RdYlGn', aspect='auto')

    ax.set_xticks(range(len(pivot.columns)))
    ax.set_yticks(range(len(pivot.index)))
    ax.set_xticklabels(pivot.columns)
    ax.set_yticklabels(pivot.index)

    for i in range(len(pivot.index)):
        for j in range(len(pivot.columns)):
            ax.text(j, i, f"{pivot.values[i,j]:.2f}", ha='center', va='center', fontsize=9)

    plt.colorbar(im, ax=ax, label='Score')
    ax.set_title('Strategy Scores by Index (Green = Better)')
    plt.tight_layout()
    plt.show()


def plot_metrics(ranked_df):

    metrics_to_plot = ['total_return', 'sharpe_ratio', 'win_rate', 'max_drawdown']
    fig, axes = plt.subplots(2, 2, figsize=(12, 8))
    axes = axes.flatten()

    for idx, metric in enumerate(metrics_to_plot):
        avg = ranked_df.groupby('strategy')[metric].mean().sort_values(ascending=False)
        axes[idx].bar(avg.index, avg.values, color='steelblue')
        axes[idx].set_title(f'Avg {metric} by Strategy')
        axes[idx].set_xticklabels(avg.index, rotation=15, ha='right')
        axes[idx].grid(axis='y', alpha=0.3)

    plt.tight_layout()
    plt.show()

# --- FINAL RANKINGS ---

def print_recommendations(ranked_df):

    print("\n" + "="*60)
    print("FINAL RANKINGS & RECOMMENDATIONS")
    print("="*60)

    print("\n--- OVERALL TOP 5 ---")
    for _, row in ranked_df.head(5).iterrows():
        print(f"  #{int(row['rank'])}: {row['strategy']} on {row['ticker']}"
              f" | Score: {row['score']:.3f}"
              f" | Return: {row['total_return']:.1f}%"
              f" | Sharpe: {row['sharpe_ratio']:.2f}"
              f" | Win Rate: {row['win_rate']:.1f}%")

    print("\n--- BEST STRATEGY PER INDEX ---")
    for ticker in indicies:
        if ticker not in ranked_df['ticker'].values:
            continue
        best = ranked_df[ranked_df['ticker'] == ticker].iloc[0]
        print(f"  {ticker}: {best['strategy']}"
              f" | Score: {best['score']:.3f}"
              f" | Return: {best['total_return']:.1f}%")

    print("\n--- BEST STRATEGY OVERALL (avg score across all indices) ---")
    avg_scores = ranked_df.groupby('strategy')['score'].mean().sort_values(ascending=False)
    for strat, score in avg_scores.items():
        print(f"  {strat}: {score:.3f}")

    print(f"\n  WINNER: {avg_scores.index[0]} (avg score: {avg_scores.iloc[0]:.3f})")
    print("="*60)

# --- MAIN ---

if __name__ == "__main__":

    print("=" * 60)
    print("TRADING STRATEGY BACKTESTER")
    print(f"Period: {start_date} to {end_date}")
    print("=" * 60)

    results = run_all_strategies(indicies, start_date, end_date)

    ranked_df = score_and_rank(results)
    print_recommendations(ranked_df)

    if plot_results:
        plot_heatmap(ranked_df)
        plot_metrics(ranked_df)

# --- VISUALISE WINNING STRATEGIES VS MARKET ---

def plot_winners_vs_market(results, ranked_df, indicies, start_date, end_date):

    avg_scores = ranked_df.groupby('strategy')['score'].mean().sort_values(ascending=False)
    winning_strategy = avg_scores.index[0]

    # Best strategy per ticker
    best_per_ticker = {}
    for ticker in indicies:
        subset = ranked_df[ranked_df['ticker'] == ticker]
        if not subset.empty:
            best_per_ticker[ticker] = subset.iloc[0]['strategy']

    fig, axes = plt.subplots(len(indicies), 1, figsize=(14, 4 * len(indicies)))
    if len(indicies) == 1:
        axes = [axes]

    for ax, ticker in zip(axes, indicies):
        if ticker not in results:
            continue

        data = fetch_data(ticker, start_date, end_date)
        if data is None:
            continue

        # Buy-and-hold baseline
        bh = (data['Close'] / data['Close'].iloc[0]) * 100
        ax.plot(data.index, bh, label='Buy & Hold', color='gray', linewidth=1.2, linestyle='--')

        strat_name = best_per_ticker.get(ticker)
        if not strat_name:
            continue

        # Rebuild strategy to get trade list
        strategies = {
            'SMA Crossover':  SMACrossover("SMA Crossover", data, sma_short, sma_long),
            'RSI':            RSIStrategy("RSI", data, rsi_period, rsi_overbought, rsi_oversold),
            'MACD':           MACDStrategy("MACD", data, macd_fast, macd_slow, macd_signal),
            'Momentum':       MomentumStrategy("Momentum", data, momentum_period),
            'Bollinger Bands': BollingerBands("Bollinger Bands", data, bb_period, bb_std),
        }

        s = strategies[strat_name]
        s.backtest()

        # Reconstruct equity curve from trades
        equity = [100]
        dates = [data.index[0]]
        running = 100

        for trade in s.trades:
            running *= (1 + trade['pnl_pct'] / 100)
            equity.append(running)
            dates.append(trade['exit_date'])

        ax.plot(dates, equity, label=f'{strat_name} (best)', color='steelblue', linewidth=1.5)
        ax.set_title(ticker)
        ax.set_ylabel('Indexed (start=100)')
        ax.legend(fontsize=8)
        ax.grid(axis='y', alpha=0.3)

    plt.suptitle(f'Best Strategy vs Buy & Hold | Overall winner: {winning_strategy}', fontsize=13)
    plt.tight_layout()
    plt.show()

plot_winners_vs_market(results, ranked_df, indicies, start_date, end_date)