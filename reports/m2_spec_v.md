# Phase 2: App Specification (M2)

This document is a specification for our Shiny dashboard. It will be updated in M3 and M4 as the implementation evolves.

## 2.1 Updated Job Stories

| # | Job Story | Status | Notes |
|---:|---|:---:|---|
| 1 | When I want to compare Magnificent 7 companies, I want to view their key valuation and growth metrics side-by-side so I can quickly rank and evaluate them. | ⏳ Pending M3 | Focus: sortable table with selected ticker highlighted. |
| 2 | When I analyze investment tradeoffs, I want to see a risk vs return scatter plot so I can understand how volatility relates to performance across companies. | ⏳ Pending M3 | Hover tooltip should display ticker, return, and volatility. |

---

## 2.2 Component Inventory

This inventory is our implementation checklist for Phase 3+ (inputs → reactive calcs → outputs).

| ID | Type | Shiny widget / renderer | Depends on | Job story |
|---|---|---|---|---|
| `input_ticker` | Input | `ui.input_select()` | — | #1, #2 |
| `input_dates` | Input | `ui.input_date_range()` | — | #2 |
| `input_rr_period` | Input | `ui.input_select()` (Full, 1Y, 5Y, 10Y) | — | #2 |
| `analysis_close` | Reactive calc | `@reactive.calc` | `input_dates`, `input_rr_period` | #2 |
| `risk_return_df` | Reactive calc | `@reactive.calc` | `analysis_close` | #2 |
| `metrics_table_df` | Reactive calc | `@reactive.calc` | — | #1 |
| `tbl_stock_metrics` | Output | `@render.data_frame` / `render.DataGrid` | `metrics_table_df`, `input_ticker` | #1 |
| `plot_risk_return` | Output | `@render_plotly` → `go.Figure()` | `risk_return_df`, `input_ticker` | #2 |

---

## 2.3 Reactivity Diagram

```mermaidS
flowchart TD
  D[/input_dates/] --> A{{analysis_close}}
  P[/input_rr_period/] --> A{{analysis_close}}

  A --> R{{risk_return_df}}
  R --> S([plot_risk_return])

  T[/input_ticker/] --> S
  M{{metrics_table_df}} --> G([tbl_stock_metrics])
  T --> G
```
---

## 2.4 Calculation Details

### `analysis_close`

**Inputs:** `input_dates`, `input_rr_period`  

**Transformation:**  
This reactive calculation first filters the historical closing price dataset to the selected date range (`input_dates`). It then applies the selected risk/return analysis window (`input_rr_period`), which can be Full, 1Y, 5Y, or 10Y.  

If **Full** is selected, the entire filtered date range is used.  
If 1Y, 5Y, or 10Y is selected, the calculation uses the most recent 1, 5, or 10 years within the selected date range (if sufficient data is available).  

The resulting dataset represents the final price window used for return and volatility calculations.

**Used by:** `risk_return_df`

---

### `risk_return_df`

**Input:** `analysis_close`  

**Transformation:**  
Using the dataset returned by `analysis_close`, this reactive calculation computes daily percentage returns for each ticker. It then calculates:

- Annualized return  
- Annualized volatility  

The output is a summary dataframe containing one row per stock with its corresponding risk and return values, based on the selected analysis window.

**Used by:** `plot_risk_return`

---

### `metrics_table_df`

**Inputs:** `input_ticker` (for row highlighting), table sorting controls

**Transformation:**  
Prepares the snapshot valuation dataset from `metric.csv`, including Ticker, Date, Market Cap, P/E Ratio, Dividend Yield, and Revenue Growth.  

The full 7-row dataset is displayed at all times. The row matching `input_ticker` is visually highlighted. If column sorting is enabled, the table can be reordered based on the selected metric while maintaining the highlighted row.

Fundamental metrics remain constant because only the latest snapshot values are available.

**Used by:** `tbl_stock_metrics`