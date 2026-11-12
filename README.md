# Trading bot

Two small stock-trading experiments.

## `trading_bot.py`: strategy backtest

Downloads price history with yfinance (2000 to 2026) and backtests five strategies on £10,000 starting capital: SMA crossover, RSI, MACD, momentum and Bollinger Bands. Each strategy is scored and the results are plotted.

```bash
pip install yfinance pandas numpy matplotlib
python3 trading_bot.py
```

## `ai_bot/`: multi-AI stock picker

1. Give several AIs the prompt in `ai_bot/AI_PROMPT_TEMPLATE.md` (pick the 5 best stocks for a Monday-to-Friday swing trade).
2. Paste each AI's answer into `ai_bot/aggregator.py`.
3. Run `python3 ai_bot/aggregator.py`. It keeps only stocks picked by at least 2 AIs, ranks them by average score, and splits capital across the top 5.

`ai_bot.zip` is a zipped copy of the same folder.

Not investment advice.
