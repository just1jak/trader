# Futures Analytica-Inspired Order Flow Spread

This is a mechanical research implementation inspired by public Futures Analytica material. It is not a copy of their proprietary tools, not a transcript, and not trading advice.

## Source Notes

I checked Futures Analytica's YouTube channel, public video descriptions, and first-party product pages. YouTube advertised auto-generated captions, but the timed-text endpoints returned empty bodies in this environment, so this note is based on available metadata, descriptions, chapters, and first-party page copy.

Primary sources reviewed:

- [Learn Order Flow Scalping in 20 Minutes | Trade Like a Hedge Fund](https://www.youtube.com/watch?v=wGuo8XPe2zQ) - chapters highlight footprint charts, delta sum, delta divergences, imbalances, unusual order saturation, prior points of interest, trade thesis, unfinished auctions, high win-rate prioritization, and exits.
- [AUTOMATED ORDER FLOW TRADING | Tutorial and Live Trading Recap](https://www.youtube.com/watch?v=LrcrKSKKaiE) - description names Polarity ATI as an assisted interface that automates an "Imbalance Price Shift" strategy.
- [Livestream Trading Recap: Exploiting Order Flow Imbalances to Semi-Automatically Trade NQ Futures](https://www.youtube.com/watch?v=C--5asfxboY) - description links order-flow imbalance research and Polarity ATI examples.
- [L2Azimuth](https://futuresanalytica.com/products/l2azimuth) - first-party page says it uses Level 2 market data to detect market manipulation such as spoofing and trade those insights.
- [Dex Array](https://futuresanalytica.com/products/dex-array) - first-party page describes detecting high-contract limit orders placed within the bid/ask spread, then validating with spoofing, directional forecast, and volatility/omega gates.
- [Trespass](https://futuresanalytica.com/products/trespass-individual-product-1) - first-party page describes bid/ask depth aggregation across 3-5 levels and an imbalance ratio with spoofing and microprobability gates.
- [AnalyticaChart4 Base](https://futuresanalytica.com/products/analyticachart4) - first-party page describes footprint features: bid/ask volume per price/bar, delta, imbalance detection, and unfinished auction detection.

## Highlights Converted To Rules

- Treat the strategy as order-book/footprint driven, not simple price-action.
- Aggregate bid and ask depth over several levels to calculate directional pressure.
- Detect large in-spread orders where `best_bid < order_price < best_ask`; this approximates the DEX Array idea of aggressive intent inside the spread.
- Confirm with footprint pressure such as delta, volume saturation, or an unfinished-auction proxy.
- Filter out likely spoofing when a `spoofing_score` column is available.
- Require directional forecast confirmation when `microprobability` and `microprobability_direction` are available.
- Keep execution short: use max-hold exits, ATR stops, and modest risk/reward targets.

## Backtest Implementation

Strategy file: `backend/api/strategies/futures_analytica_orderflow_spread.py`

Strategy name for API/UI: `futures_analytica_orderflow_spread`

Best data columns:

- `best_bid`, `best_ask`
- `bid_size_1` ... `bid_size_N`, `ask_size_1` ... `ask_size_N` or aggregate `bid_depth`, `ask_depth`
- `order_price`, `order_size`, `order_side`
- `delta`
- Optional gates: `spoofing_score`, `microprobability`, `microprobability_direction`, `hf_omega`

Fallback behavior:

- If L2 columns are missing and `allow_ohlcv_proxy` is true, the strategy approximates book pressure from candle direction, volume, and delta-style price/volume movement.
- If `require_in_spread_order` is true, the strategy only enters when real in-spread order columns are present and aligned.

Important defaults:

- `depth_levels`: `5`
- `imbalance_threshold`: `0.5`
- `microprob_threshold`: `0.8`
- `spoofing_max`: `0.4`
- `spread_max_ticks`: `4`
- `tick_size`: `0.25`
- `large_order_mult`: `2.0`
- `saturation_z`: `1.2`
- `delta_threshold`: `0.35`
- `risk_reward`: `1.5`
- `max_hold_bars`: `12`

## Notes

This implementation is intentionally transparent and approximate. The real Futures Analytica products appear to use proprietary scanners and models, so this backtest only captures public concepts in a reproducible way. For serious validation, use tick/Level 2 data, realistic futures fees, queue position assumptions, slippage, and session-specific contract settings.
