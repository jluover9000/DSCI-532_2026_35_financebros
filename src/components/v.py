"""
v.py — Core Shiny test: Metrics table + ticker dropdown + sort controls
Testing individual fash card before putting all together

- Keep numeric formatting (MarketCap as 1234.56B, % columns, PE rounded)
- Add sort controls (metric + asc/desc) to reorder rows
- No extra "Selected" column. Cannot do selective highlight for now. 
- Row highlight happens when you click rows (native DataGrid selection)
Run:
  shiny run --reload src/components/v.py
"""

from pathlib import Path
import sys

import pandas as pd
from shiny import App, ui, render

# --- make src/ importable so `from stocks import stocks` works ---
SRC_DIR = Path(__file__).parent.parent  # .../src
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from stocks import stocks  # noqa: E402

# --- load metric.csv ---
DATA_DIR = Path(__file__).parent.parent.parent / "data"
metric_df = pd.read_csv(DATA_DIR / "metric.csv")

TICKER_COL = "Ticker"
if TICKER_COL not in metric_df.columns:
    raise ValueError("metric.csv must include a 'Ticker' column.")


# ---------------- UI ----------------
SORT_CHOICES = {
    "Market Cap": "MarketCap",
    "P/E Ratio": "P/E Ratio",
    "Dividend Yield": "DividendYield",
    "Revenue Growth": "Revenue Growth",
}

app_ui = ui.page_fluid(
    ui.card(
        ui.card_header("Stock Metrics Table"),
        ui.layout_columns(
            ui.input_select("ticker", "Select Stock", choices=stocks, selected="NVDA"),
            ui.input_select("sort_by", "Sort by", choices=list(SORT_CHOICES.keys()), selected="Market Cap"),
            ui.input_radio_buttons(
                "sort_dir",
                "Order",
                choices={"desc": "Descending", "asc": "Ascending"},
                selected="desc",
                inline=True,
            ),
            col_widths=[4, 4, 4],
        ),
        ui.output_data_frame("tbl"),
    ),
)


# ---------------- Server ----------------
def server(input, output, session):
    @render.data_frame
    def tbl():
        df = metric_df.copy()

        # drop ugly index col if present
        if "Unnamed: 0" in df.columns:
            df = df.drop(columns=["Unnamed: 0"])

        # --------- Build a numeric copy for sorting (before formatting to strings) ---------
        sort_df = df.copy()

        # MarketCap: ensure numeric
        if "MarketCap" in sort_df.columns:
            sort_df["MarketCap"] = pd.to_numeric(sort_df["MarketCap"], errors="coerce")

        # P/E Ratio numeric
        if "P/E Ratio" in sort_df.columns:
            sort_df["P/E Ratio"] = pd.to_numeric(sort_df["P/E Ratio"], errors="coerce")

        # DividendYield numeric
        if "DividendYield" in sort_df.columns:
            sort_df["DividendYield"] = pd.to_numeric(sort_df["DividendYield"], errors="coerce")

        # Revenue Growth numeric
        if "Revenue Growth" in sort_df.columns:
            sort_df["Revenue Growth"] = pd.to_numeric(sort_df["Revenue Growth"], errors="coerce")

        # --------- Sort by chosen metric ---------
        sort_key = SORT_CHOICES.get(input.sort_by(), "MarketCap")
        ascending = (input.sort_dir() == "asc")

        if sort_key in sort_df.columns:
            # Put NaNs at bottom regardless of direction
            df["_sort_key_"] = sort_df[sort_key]
            df = df.sort_values(by="_sort_key_", ascending=ascending, na_position="last")
            df = df.drop(columns=["_sort_key_"])

        df = df.reset_index(drop=True)

        # --------- Formatting for display ---------
        if "MarketCap" in df.columns:
            mc = pd.to_numeric(df["MarketCap"], errors="coerce") / 1_000_000_000
            df["MarketCap"] = mc.map(lambda x: "" if pd.isna(x) else f"{x:,.2f}B")

        if "P/E Ratio" in df.columns:
            pe = pd.to_numeric(df["P/E Ratio"], errors="coerce")
            df["P/E Ratio"] = pe.map(lambda x: "" if pd.isna(x) else f"{x:.2f}")

        if "DividendYield" in df.columns:
            dy = pd.to_numeric(df["DividendYield"], errors="coerce") * 100
            df["DividendYield"] = dy.map(lambda x: "" if pd.isna(x) else f"{x:.2f}%")

        if "Revenue Growth" in df.columns:
            rg = pd.to_numeric(df["Revenue Growth"], errors="coerce") * 100
            df["Revenue Growth"] = rg.map(lambda x: "" if pd.isna(x) else f"{x:.2f}%")

        # --------- Render table (click rows to highlight) ---------
        return render.DataGrid(
            df,
            width="100%",
            height="420px",
            selection_mode="rows",
        )


app = App(app_ui, server)