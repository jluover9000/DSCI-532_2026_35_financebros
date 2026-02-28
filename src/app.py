"""
Stock Visualization Dashboard - Magnificent 7 Portfolio
Finviz-inspired design with 8 visualization components.
"""

from pathlib import Path

import pandas as pd
import plotly.graph_objects as go
from shiny import reactive
from shiny.express import input, render, ui
from shinywidgets import render_plotly

from stocks import stocks, wishlist as wishlist_dict

# -----------------------------------------------------------------------------
# Data Loading - Load CSV files once at startup
# -----------------------------------------------------------------------------
DATA_DIR = Path(__file__).parent.parent / "data"

close_df = pd.read_csv(DATA_DIR / "close.csv", parse_dates=["Date"])
metric_df = pd.read_csv(DATA_DIR / "metric.csv")
spy_df = pd.read_csv(DATA_DIR / "spy.csv", parse_dates=["Date"])
wishlist_df = pd.read_csv(DATA_DIR / "wishlist.csv", parse_dates=["Date"])

# Date range from close.csv
DATE_MIN = close_df["Date"].min().date()
DATE_MAX = close_df["Date"].max().date()

# -----------------------------------------------------------------------------
# Page Setup
# -----------------------------------------------------------------------------
ui.page_opts(title="Magnificent 7 Stock Explorer", fillable=True)

ui.tags.style("""
/* Finviz-style strip */
.tickerstrip {
  display: flex;
  align-items: stretch;
  border: 1px solid #2a2e39;
  border-radius: 10px;
  overflow: hidden;             /* makes separators look clean */
  background: #1e222d;
}

/* Each tile */
.tickerbox {
  flex: 1;
  padding: 10px 10px 8px 10px;
  min-width: 0;
  text-align: left;
}

/* Thin vertical separators between boxes */
.tickerbox + .tickerbox {
  border-left: 1px solid #2a2e39;
}

.tickerbox-ticker {
  font-weight: 700;
  font-size: 12px;
  letter-spacing: 0.04em;
  color: #d1d4dc;
  text-transform: uppercase;
  margin-bottom: 4px;
}

/* Price row */
.tickerbox-price {
  font-weight: 700;
  font-size: 16px;
  color: #ffffff;
  line-height: 1.1;
}

/* Return row */
.tickerbox-ret {
  margin-top: 4px;
  font-weight: 600;
  font-size: 12px;
  line-height: 1.1;
  display: inline-flex;
  gap: 6px;
  align-items: center;
}

.ret-pos { color: #44bb70; }
.ret-neg { color: #d62728; }
.ret-flat { color: #9aa0a6; }

/* Arrow style */
.ret-arrow {
  font-size: 12px;
  opacity: 0.95;
}

/* Subtle hover like finviz */
.tickerbox:hover {
  background: #232a37;
}

/* Small screens: allow horizontal scroll instead of wrapping */
@media (max-width: 900px) {
  .tickerstrip {
    overflow-x: auto;
  }
  .tickerbox {
    flex: 0 0 140px;
  }
}
""")

# -----------------------------------------------------------------------------
# Sidebar - Stock dropdown and date range
# -----------------------------------------------------------------------------
with ui.sidebar():
    ui.input_selectize(
        "ticker",
        "Select Stock",
        choices=stocks,
        selected="AAPL",
    )
    ui.input_date_range(
        "dates",
        "Select Date Range",
        start=DATE_MIN,
        end=DATE_MAX,
        min=DATE_MIN,
        max=DATE_MAX,
        format="yyyy-mm-dd",
        separator=" - ",
    )

# -----------------------------------------------------------------------------
# Reactive Data Calculations
# -----------------------------------------------------------------------------


@reactive.calc
def get_filtered_close():
    """Filter close.csv by selected date range."""
    dates = input.dates()
    mask = (close_df["Date"] >= pd.Timestamp(dates[0])) & (
        close_df["Date"] <= pd.Timestamp(dates[1])
    )
    return close_df.loc[mask].copy()


@reactive.calc
def get_current_price():
    """Get most recent price for selected stock (from full close.csv, not date range)."""
    ticker = input.ticker()
    if ticker not in close_df.columns:
        return None
    return float(close_df[ticker].iloc[-1])


@reactive.calc
def get_selected_stock_series():
    """Get price series for selected stock within date range."""
    ticker = input.ticker()
    df = get_filtered_close()
    if ticker not in df.columns:
        return pd.Series(dtype=float)
    return df.set_index("Date")[ticker]


# -----------------------------------------------------------------------------
# Layout - 3-column grid matching sketch.png
# Row 1: 1 (Current Price), 2 (Stock Chart), 6 (Risk-Return)
# Row 2: 3 (Performance), 4 (S&P 500), 7 (Treemap)
# Row 3: 5 (Metrics Table), 8 (Watchlist)
# -----------------------------------------------------------------------------
with ui.layout_columns(col_widths={"sm": (5, 5, 2)}, row_heights="auto"):

    # 1. Current Price Display
    with ui.card():
        ui.card_header("1. Current Price")

        @render.ui
        def render_current_price():
            """
            1. Current Price Display.
            Display current stock price. Reacts to dropdown only (not date range).
            Uses the most recent price from close.csv regardless of selected date range.
            Data: Last row from close.csv for selected stock.
            """
            cur = close_df.iloc[-1]
            prev = close_df.iloc[-2]

            boxes = []
            for ticker in close_df.columns[1:]:  
                if ticker not in close_df.columns:
                    boxes.append(
                        ui.tags.div(
                            {"class": "tickerbox"},
                            ui.tags.div(ticker, class_="tickerbox-ticker"),
                            ui.tags.div("—", class_="tickerbox-price"),
                            ui.tags.div("—", class_="tickerbox-ret ret-flat"),
                        )
                    )
                    continue

                current = float(cur[ticker])
                previous = float(prev[ticker])

                pct = 0.0 if previous == 0 else (current / previous - 1.0) * 100

                if pct > 0.05:
                    cls = "ret-pos"
                    arrow = "▲"
                elif pct < -0.05:
                    cls = "ret-neg"
                    arrow = "▼"
                else:
                    cls = "ret-flat"
                    arrow = "•"

                pct_txt = f"{arrow}{pct:.2f}%"

                boxes.append(
                    ui.tags.div(
                        {"class": "tickerbox"},
                        ui.tags.div(ticker, class_="tickerbox-ticker"),
                        ui.tags.div(f"${current:,.2f}", class_="tickerbox-price"),
                        ui.tags.div(pct_txt, class_=f"tickerbox-ret {cls}"),
                    )
                )

            return ui.tags.div({"class": "tickerstrip"}, *boxes)
            

    # 2. Stock Price Chart
    with ui.card(full_screen=True):
        ui.card_header("2. Stock Price Chart")

        @render_plotly
        def render_stock_price_chart():
            """
            2. Stock Price Chart.
            Line graph of stock price from start to end of selected date range.
            Reacts to: dropdown + date range.
            Data: Filtered close.csv for selected stock and date range.
            """
            ticker = input.ticker()
            df = get_filtered_close().copy()

            if df.empty or ticker not in df.columns:
                fig = go.Figure()
                fig.update_layout(
                    template="plotly_dark",
                    paper_bgcolor="#131722",
                    plot_bgcolor="#1e222d",
                    margin=dict(l=10, r=10, t=10, b=10),
                    annotations=[
                        dict(
                            text="No data available for the selected range/ticker.",
                            x=0.5, y=0.5, xref="paper", yref="paper",
                            showarrow=False, font=dict(color="#d1d4dc", size=14)
                        )
                    ],
                )
                return fig
            
            df = df.sort_values("Date")
            x = df["Date"]
            y = df[ticker].astype(float)

            start_price = float(y.iloc[0])
            end_price = float(y.iloc[-1])
            pct_change = (end_price / start_price - 1) * 100 if start_price != 0 else 0.0
            pct_color = "#44bb70" if pct_change >= 0 else "#d62728"

            fig = go.Figure()
            fig.add_trace(
                go.Scatter(
                    x=x,
                    y=y,
                    mode="lines",
                    name=ticker,
                    line=dict(color="#2962ff", width=2.5),
                    hovertemplate="<b>%{x|%Y-%m-%d}</b><br>"
                                f"{ticker}: $%{{y:.2f}}<extra></extra>",
                )
            )

            fig.update_layout(
                template="plotly_dark",
                paper_bgcolor="#131722",
                plot_bgcolor="#1e222d",
                margin=dict(l=10, r=10, t=30, b=10),
                hovermode="x unified",
                xaxis=dict(
                    title="Date",
                    showgrid=True,
                    gridcolor="rgba(255,255,255,0.06)",
                    rangeslider=dict(visible=True),
                    rangeselector=None,
                ),
                yaxis=dict(
                    title="Close Price ($)",
                    showgrid=True,
                    gridcolor="rgba(255,255,255,0.06)",
                    tickprefix="$",
                ),
                title=dict(
                    text=f"{ticker} Close Price  <span style='color:{pct_color}; font-size:12px;'>({pct_change:+.2f}%)</span>",
                    x=0.01,
                    xanchor="left",
                    font=dict(size=16, color="#d1d4dc"),
                ),
                showlegend=False,
            )

            return fig
            

    # 6. Risk-Return Scatter Plot
    with ui.card(full_screen=True):
        ui.card_header("6. Risk-Return Scatter")

        @render_plotly
        def render_risk_return_scatter():
            """
            6. Risk-Return Scatter Plot.
            Scatter plot of risk (volatility) vs return for all portfolio stocks.
            Selected stock highlighted. Reacts to: dropdown only (uses selected date range).
            Data: Calculate from close.csv; highlight selected stock.
            """
            pass
            return go.Figure()


with ui.layout_columns(col_widths={"sm": (5, 5, 2)}, row_heights="auto"):

    # 3. Performance Comparison
    with ui.card(full_screen=True):
        ui.card_header("3. Performance Comparison")

        @render_plotly
        def render_performance_comparison():
            """
            3. Performance Comparison.
            Multi-line chart comparing all portfolio stocks. Selected stock highlighted,
            others greyed out. Hovering over a point in the line will show the date, actual price at the date, and normalized value (tooltip).
            Reacts to: dropdown + date range.
            Data: All portfolio stocks from close.csv.
            """

            df = get_filtered_close().copy()
            ticker = input.ticker()

            if df.empty:
                return go.Figure()

            df = df.set_index("Date")

            raw_prices = df.copy()  # for the price/ tooltip

            # normalize to 100 at start since the raw prices arent comparable in the same graph, prices are too differentr
            normalized = df / df.iloc[0] * 100
            fig = go.Figure()

            for col in normalized.columns:

                fig.add_trace(
                    go.Scatter(
                        x=normalized.index,
                        y=normalized[col],
                        mode="lines",
                        name=col,
                        line=dict(
                            width=3 if col == ticker else 1,
                            color="green" if col == ticker else "lightgray",
                        ),
                        opacity=1 if col == ticker else 0.6,
                        # tooltip hover. I had help from chatgpt to generate the hovertemplate
                        customdata=raw_prices[col],
                        hovertemplate="<b>%{fullData.name}</b><br>"
                        + "Date: %{x|%Y-%m-%d}<br>"
                        + "Price: $%{customdata:.2f}<br>"
                        + "Performance: %{y:.2f}<extra></extra>",
                    )
                )

            # for col in normalized.columns:
            #     if col == ticker:
            #         fig.add_trace(
            #             go.Scatter(
            #                 x=normalized.index, y=normalized[col], mode="lines",
            #                 name=col, line=dict(color="green", width=3)))
            #     else:
            #         fig.add_trace(
            #             go.Scatter(
            #                 x=normalized.index, y=normalized[col], mode="lines",
            #                 name=col, line=dict(color="lightgray", width=2),
            #                 opacity=0.6))

            fig.update_layout(
                template="plotly_dark",
                yaxis_title="Normalized Performance (Base = 100)",
                xaxis_title="Date",
                showlegend=True,
                margin=dict(l=10, r=10, t=10, b=10),
            )

            return fig
            # pass
            # return go.Figure()

    # 4. S&P 500 Comparison
    with ui.card(full_screen=True):
        ui.card_header("4. S&P 500 Comparison")

        @render_plotly
        def render_sp500_comparison():
            """
            4. S&P 500 Comparison.
            Chart comparing selected stock vs SPY (S&P 500). Reacts to: dropdown + date range.
            Data: Selected stock from close.csv + SPY from spy.csv.
            """
            ticker = input.ticker()

            stock_df = get_filtered_close().copy()
            dates = input.dates()

            if stock_df.empty:
                return go.Figure()

            # filter SPY by same date range
            spy_filtered = spy_df[
                (spy_df["Date"] >= pd.Timestamp(dates[0]))
                & (spy_df["Date"] <= pd.Timestamp(dates[1]))
            ].copy()

            stock_df = stock_df.set_index("Date")
            spy_filtered = spy_filtered.set_index("Date")

            if ticker not in stock_df.columns:
                return go.Figure()

            stock_series = stock_df[ticker]
            spy_series = spy_filtered["SPY"]

            # like 3 above, normalize both to 100
            stock_norm = stock_series / stock_series.iloc[0] * 100
            spy_norm = spy_series / spy_series.iloc[0] * 100

            fig = go.Figure()

            fig.add_trace(
                go.Scatter(
                    x=stock_norm.index,
                    y=stock_norm,
                    mode="lines",
                    name=ticker,
                    line=dict(width=3),
                )
            )

            fig.add_trace(
                go.Scatter(
                    x=spy_norm.index,
                    y=spy_norm,
                    mode="lines",
                    name="S&P 500 (SPY)",
                    line=dict(color="orange", width=2),
                )
            )

            fig.update_layout(
                template="plotly_dark",
                yaxis_title="Normalized Performance (Base = 100)",
                xaxis_title="Date",
                margin=dict(l=10, r=10, t=10, b=10),
            )

            return fig

            # pass
            # return go.Figure()

    # 7. Portfolio Treemap
    with ui.card(full_screen=True):
        ui.card_header("7. Portfolio Treemap")

        @render_plotly
        def render_portfolio_treemap():
            """
            7. Portfolio Treemap.
            Treemap of portfolio sized by market cap. Selected stock highlighted.
            Reacts to: dropdown only. Data: MarketCap from metric.csv.
            """
            selected_ticker = input.ticker()

            labels = []
            values = []
            text_info = []
            colors = []

            for _, row in metric_df.iterrows():
                ticker = str(row["Ticker"])
                company_name = stocks.get(ticker, ticker)
                labels.append(f"{ticker}")
                values.append(row["MarketCap"])
                text_info.append(f"{company_name}")

                if ticker == selected_ticker:
                    colors.append("#2962ff")
                else:
                    colors.append("#787b86")

            fig = go.Figure(
                go.Treemap(
                    labels=labels,
                    parents=[""] * len(labels),
                    values=values,
                    text=text_info,
                    textposition="middle center",
                    marker=dict(colors=colors, line=dict(color="#2a2e39", width=2)),
                    hovertemplate="<b>%{label}</b><br>%{text}<br>Market Cap: $%{value:,.0f}<extra></extra>",
                )
            )

            fig.update_layout(
                paper_bgcolor="#131722",
                plot_bgcolor="#1e222d",
                font=dict(color="#d1d4dc", size=14),
                margin=dict(l=10, r=10, t=10, b=10),
            )

            return fig


with ui.layout_columns(col_widths={"sm": (10, 2)}, row_heights="auto"):

    # 5. Stock Metrics Table
    with ui.card():
        ui.card_header("5. Stock Metrics Table")

        @render.data_frame
        def render_stock_metrics_table():
            """
            5. Stock Metrics Table.
            Table with Stock name, P/E ratio, Revenue growth, Annual return (placeholder),
            Volatility (placeholder). Reacts to: dropdown only.
            Data: metric.csv for P/E and Revenue Growth.
            """
            pass
            return pd.DataFrame()

    # 8. Watchlist Display
    with ui.card():
        ui.card_header("8. Watchlist")
        ui.input_switch("watchlist_toggle", "Show as $ or %", value=False)

        @render.data_frame
        def render_watchlist():
            """
            8. Watchlist Display.
            Table of watchlist stocks (from wishlist.csv) with Symbol, Company,
            and Change (colored red/green). Global toggle for percentage vs dollar.
            Reacts to: neither dropdown nor date range.
            """
            current_prices = wishlist_df.iloc[-1]
            previous_prices = wishlist_df.iloc[-2]

            watchlist_data = []
            for ticker in wishlist_dict.keys():
                current = current_prices[ticker]
                previous = previous_prices[ticker]
                dollar_change = current - previous
                percent_change = (dollar_change / previous) * 100

                if input.watchlist_toggle():
                    change_value = f"{percent_change:+.2f}%"
                else:
                    change_value = f"${dollar_change:+.2f}"

                watchlist_data.append(
                    {
                        "Symbol": ticker,
                        "Change": change_value,
                    }
                )

            df = pd.DataFrame(watchlist_data)

            return render.DataTable(
                df,
                styles=[
                    {
                        "rows": [
                            i
                            for i, row in enumerate(watchlist_data)
                            if "-" not in row["Change"]
                        ],
                        "cols": [0, 1],
                        "style": {
                            "color": "#44bb70",
                            "font-weight": "600",
                            "background-color": "transparent",
                        },
                    },
                    {
                        "rows": [
                            i
                            for i, row in enumerate(watchlist_data)
                            if "-" in row["Change"]
                        ],
                        "cols": [0, 1],
                        "style": {
                            "color": "#d62728",
                            "font-weight": "600",
                            "background-color": "transparent",
                        },
                    },
                ],
                filters=False,
                selection_mode="none",
            )


# -----------------------------------------------------------------------------
# Apply finviz-inspired styles
# -----------------------------------------------------------------------------
ui.include_css(Path(__file__).parent / "styles.css")
