# Phase 2: App Specification (M2)

This document is a living specification for our Shiny dashboard. It will be updated in M3 and M4 as the implementation evolves.

## 2.1 Updated Job Stories

| # | Job Story | Status | Notes |
|---:|---|:---:|---|
| 1 | When I want to evaluate a stock, I want to select a time window (1Y, 2Y, Annualized, or Quarterly) so I can see the stock’s risk & valuation metrics for that period. | ⏳ Pending M3 | Focus: dropdown controls how metrics are summarized in the table. |
| 2 | When I compare Magnificent 7 stocks, I want a risk vs return scatter plot so I can quickly see which stocks have higher return for a given level of risk. | ⏳ Pending M3 | Hover should show a “tooltip card” with ticker + risk + return. |

### 2.2 Component Inventory

This inventory is our implementation checklist for Phase 3+ (inputs → reactive calcs → outputs).

| ID | Type | Shiny widget / renderer | Depends on | Job story |
|---|---|---|---|---|
| `input_ticker` | Input | `ui.input_select()` | — | #1 |
| `metrics_table_df` | Reactive calc | `@reactive.calc` | — | #1 |
| `tbl_stock_metrics` | Output | `@render.data_frame` / `render.DataGrid` | `metrics_table_df`, `input_ticker` | #1 |
| `filtered_close` | Reactive calc | `@reactive.calc` | `input_dates` | #2 |
| `risk_return_df` | Reactive calc | `@reactive.calc` | `filtered_close` | #2 |
| `plot_risk_return` | Output | `@render_plotly` → `go.Figure()` | `risk_return_df`, `input_ticker` | #2 |

#### Notes: (what each output should show)

**Risk & Valuation Metrics Table (Bottom-Left)**

- Displays all 7 Magnificent 7 stocks as rows.
- Columns include:
  - Ticker
  - Date (latest available per ticker)
  - Market Cap
  - P/E Ratio
  - Dividend Yield
  - Revenue Growth

Behavior:
- Table always shows the full 7-row dataset.
- The row matching `input_ticker` is visually highlighted.
- Table supports column sorting so user can choose the metrics and the table sort based on that metrics while keeping the highlighted stock.
- No time-window dropdown is used, since only latest snapshot fundamentals are available.

---

**Risk vs Return Scatter Plot (Top-Right)**

- Displays all 7 stocks as points.
- X-axis: Volatility (risk)
- Y-axis: Annualized Return
- Legend
- Values are computed from historical closing price data.

**Behavior:**
- Hover tooltip displays:
  - Ticker
  - Annualized Return (%)
  - Volatility (%)
- The selected ticker may be visually emphasized (larger marker or different color).