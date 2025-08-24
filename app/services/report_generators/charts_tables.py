# # app/services/report_generators/charts_tables.py
# import base64
# from io import BytesIO
# from datetime import datetime
# import pandas as pd
# import matplotlib.pyplot as plt
# from jinja2 import Template

# # -- Helpers -----------------------------------------------------------------
# def _fig_to_base64(fig) -> str:
#     """Convert Matplotlib figure to base64 PNG string."""
#     buf = BytesIO()
#     fig.savefig(buf, format="png", bbox_inches="tight")
#     plt.close(fig)
#     buf.seek(0)
#     return base64.b64encode(buf.read()).decode("utf-8")


# def _safe_number(x):
#     try:
#         return float(x)
#     except Exception:
#         return 0.0


# # -- Table helpers -----------------------------------------------------------
# def df_to_html_table(df: pd.DataFrame, title: str = "", index: bool = False) -> str:
#     if df is None or df.empty:
#         return f"<h3>{title}</h3><p>No data</p>"

#     html_table = df.copy()
#     for col in html_table.select_dtypes(include=["float", "int"]).columns:
#         html_table[col] = html_table[col].map(lambda v: f"{v:,.2f}" if pd.notna(v) else "")

#     table_html = html_table.to_html(
#         index=index,
#         classes="table table-sm table-bordered",
#         border=0,
#         justify="left",
#         escape=False  # ✅ Render HTML badges
#     )
#     return f"<h3>{title}</h3>\n{table_html}"


# def create_html_table(df: pd.DataFrame, title: str = "", index: bool = False) -> str:
#     """Alias for df_to_html_table to match earlier naming."""
#     return df_to_html_table(df, title=title, index=index)


# # -- Chart generators (base64) ----------------------------------------------
# def generate_pie_chart_base64(series: pd.Series, title: str = "") -> str:
#     """Generate a pie chart from a Series (index = labels, values) -> base64 PNG."""
#     if series is None or series.empty:
#         return None
#     fig, ax = plt.subplots(figsize=(6, 6))
#     series.plot.pie(autopct="%1.1f%%", startangle=90, ax=ax)
#     ax.set_ylabel("")
#     ax.set_title(title)
#     plt.tight_layout()
#     return _fig_to_base64(fig)


# def generate_bar_chart_base64(df: pd.DataFrame, x_col: str, y_col: str, title: str = "") -> str:
#     """Generate a bar chart (base64 PNG)"""
#     if df is None or df.empty:
#         return None
#     fig, ax = plt.subplots(figsize=(8, 4))
#     df.plot.bar(x=x_col, y=y_col, ax=ax, legend=False)
#     ax.set_title(title)
#     ax.set_ylabel("")
#     plt.tight_layout()
#     return _fig_to_base64(fig)


# def generate_line_chart_base64(x, y, title: str = "") -> str:
#     """Small helper to create a line chart from x, y lists -> base64"""
#     fig, ax = plt.subplots(figsize=(8, 3.5))
#     ax.plot(x, y, marker="o")
#     ax.set_title(title)
#     plt.xticks(rotation=45, ha="right")
#     plt.tight_layout()
#     return _fig_to_base64(fig)

# def generate_stacked_bar_chart_base64(df: pd.DataFrame, x_col: str, stack_col: str, value_col: str, title: str = "") -> str:
#     """Generate stacked bar chart (fiscal year bars, stacked by type)."""
#     if df.empty:
#         return None
#     pivot_df = df.pivot_table(index=x_col, columns=stack_col, values=value_col, aggfunc="sum").fillna(0)
#     fig, ax = plt.subplots(figsize=(8, 4))
#     pivot_df.plot(kind="bar", stacked=True, ax=ax)
#     ax.set_ylabel("Expense")
#     ax.set_xlabel(x_col.replace("_", " "))
#     ax.set_title(title)
#     plt.xticks(rotation=45)
#     plt.tight_layout()
#     return _fig_to_base64(fig)



# # -- Expense-specific helpers -----------------------------------------------
# def generate_expense_monthly_trend_base64(df: pd.DataFrame, date_col: str = "DATE", value_col: str = "COST") -> str:
#     """
#     Input: df with a date column (datetime or parseable) and a cost column.
#     Output: base64 line-chart of month-year vs total cost.
#     """
#     if df is None or df.empty:
#         return None

#     df_local = df.copy()
#     # Ensure datetime
#     df_local[date_col] = pd.to_datetime(df_local[date_col], errors="coerce")
#     df_local = df_local.dropna(subset=[date_col, value_col])
#     df_local[value_col] = df_local[value_col].apply(_safe_number)

#     # Group by month-year
#     df_local["year_month"] = df_local[date_col].dt.to_period("M").astype(str)
#     monthly = df_local.groupby("year_month")[value_col].sum().reset_index()
#     if monthly.empty:
#         return None

#     return generate_line_chart_base64(monthly["year_month"].tolist(), monthly[value_col].tolist(), title="Monthly Expense Trend")


# def generate_expense_charts(df: pd.DataFrame):
#     """
#     Convenience: returns dict with keys 'pie' and 'trend' base64 images.
#     Expects df with columns: CATEGORY, DATE, COST (or compatible names).
#     """
#     if df is None or df.empty:
#         return {"pie": None, "trend": None}

#     df_local = df.copy()
#     # normalize column names
#     cols = {c.upper(): c for c in df_local.columns}
#     # Try to coerce common column names
#     if "CATEGORY" not in cols and "TYPE" in cols:
#         df_local.rename(columns={cols["TYPE"]: "CATEGORY"}, inplace=True)
#     if "COST" not in cols:
#         # try lowercase
#         for k, v in cols.items():
#             if k.lower() == "cost":
#                 df_local.rename(columns={v: "COST"}, inplace=True)

#     # Pie by category
#     try:
#         pie_series = df_local.groupby("CATEGORY")["COST"].sum()
#     except Exception:
#         pie_series = None

#     pie_b64 = generate_pie_chart_base64(pie_series, title="Expense Breakdown by Category") if pie_series is not None else None
#     trend_b64 = generate_expense_monthly_trend_base64(df_local, date_col="DATE", value_col="COST")

#     return {"pie": pie_b64, "trend": trend_b64}


# # -- Portfolio / Investment helpers -----------------------------------------
# def generate_portfolio_chart(savings_df: pd.DataFrame, value_col: str = "CURRENT_VALUE", type_col: str = "TYPE") -> str:
#     """
#     Given savings_df which contains a TYPE and CURRENT_VALUE columns, return pie chart base64.
#     """
#     if savings_df is None or savings_df.empty:
#         return None

#     df_local = savings_df.copy()
#     # try to normalize columns
#     if type_col not in df_local.columns:
#         # attempt uppercase/lowercase matches
#         for c in df_local.columns:
#             if c.lower() == type_col.lower():
#                 type_col = c
#                 break
#     if value_col not in df_local.columns:
#         for c in df_local.columns:
#             if c.lower().startswith(value_col.lower()):
#                 value_col = c
#                 break

#     df_local[value_col] = df_local[value_col].apply(_safe_number)
#     grouped = df_local.groupby(type_col)[value_col].sum().sort_values(ascending=False)
#     if grouped.empty:
#         return None
#     return generate_pie_chart_base64(grouped, title="Portfolio Breakdown")


# def create_portfolio_pie_chart(savings_df: pd.DataFrame, value_col: str = "CURRENT_VALUE", type_col: str = "TYPE"):
#     """
#     Return a matplotlib Figure (not base64). Useful when caller wants to manage conversion themselves.
#     """
#     if savings_df is None or savings_df.empty:
#         fig = plt.figure(figsize=(6, 6))
#         return fig

#     df_local = savings_df.copy()
#     df_local[value_col] = df_local[value_col].apply(_safe_number)
#     grouped = df_local.groupby(type_col)[value_col].sum()
#     fig, ax = plt.subplots(figsize=(6, 6))
#     grouped.plot.pie(autopct="%1.1f%%", startangle=90, ax=ax)
#     ax.set_ylabel("")
#     ax.set_title("Portfolio Breakdown")
#     plt.tight_layout()
#     return fig


# def create_investment_summary_table(savings_df: pd.DataFrame) -> str:
#     """
#     Creates a compact summary table (HTML) with totals and returns breakdown by TYPE.
#     """
#     if savings_df is None or savings_df.empty:
#         return "<p>No investment summary available</p>"

#     df_local = savings_df.copy()
#     # normalize column names - common variants
#     for col in df_local.columns:
#         if col.lower().startswith("current"):
#             current_col = col
#             break
#     else:
#         current_col = next((c for c in df_local.columns if "current" in c.lower()), None)

#     for col in df_local.columns:
#         if col.lower().startswith("current_invest"):
#             invested_col = col
#             break
#     else:
#         invested_col = next((c for c in df_local.columns if "invest" in c.lower()), None)

#     # fallback names
#     invested_col = invested_col if invested_col in df_local.columns else next((c for c in df_local.columns if "t_buy" in c.lower() or "buy" in c.lower()), None)
#     current_col = current_col if current_col in df_local.columns else next((c for c in df_local.columns if "current" in c.lower()), None)

#     # Ensure numeric
#     if invested_col:
#         df_local[invested_col] = df_local[invested_col].apply(_safe_number)
#     if current_col:
#         df_local[current_col] = df_local[current_col].apply(_safe_number)

#     total_invested = df_local[invested_col].sum() if invested_col else 0.0
#     total_value = df_local[current_col].sum() if current_col else 0.0
#     profit_loss = total_value - total_invested
#     avg_return = (profit_loss / total_invested * 100) if total_invested else 0.0

#     # Breakdown by type
#     breakdown = df_local.groupby(df_local.columns[df_local.columns.str.lower().str.contains("type")][0] if any(df_local.columns.str.lower().str.contains("type")) else "TYPE")
#     breakdown_df = pd.DataFrame({
#         "TOTAL_VALUE": breakdown[current_col].sum() if current_col else pd.Series(),
#         "TOTAL_INVESTED": breakdown[invested_col].sum() if invested_col else pd.Series()
#     }).reset_index().fillna(0.0)

#     summary_df = pd.DataFrame([{
#         "METRIC": "TOTAL_INVESTED",
#         "VALUE": total_invested
#     }, {
#         "METRIC": "CURRENT_VALUE",
#         "VALUE": total_value
#     }, {
#         "METRIC": "PROFIT_LOSS",
#         "VALUE": profit_loss
#     }, {
#         "METRIC": "AVERAGE_RETURN_PERCENT",
#         "VALUE": avg_return
#     }])

#     # Render small HTML combining both tables
#     tpl = """
#     <div class="investment-summary">
#         <h3>Investment Summary</h3>
#         {{ summary_table | safe }}
#         <h4>Breakdown by Type</h4>
#         {{ breakdown_table | safe }}
#     </div>
#     """
#     template = Template(tpl)
#     rendered = template.render(
#         summary_table=summary_df.to_html(index=False, classes="table table-sm table-bordered", float_format="%.2f"),
#         breakdown_table=breakdown_df.to_html(index=False, classes="table table-sm table-bordered", float_format="%.2f")
#     )
#     return rendered

# def generate_financial_monthly_trend_base64(df: pd.DataFrame) -> str:
#     """
#     df: columns = ['year_month', 'expense', 'buy', 'sell', 'income', 'bank', 'loan']
#     Generates a multi-line chart with fixed color mapping.
#     """
#     if df.empty:
#         return None

#     fig, ax = plt.subplots(figsize=(10, 5))
#     colors = {
#         'expense': '#e74a3b',
#         'buy': '#27ae60',
#         'sell': '#f39c12',
#         'income': '#2980b9',
#         'bank': '#16a085',
#         'loan': '#7f8c8d'
#     }

#     for col in ['expense', 'buy', 'sell', 'income', 'bank', 'loan']:
#         if col in df.columns and df[col].notna().any():
#             ax.plot(df['year_month'], df[col], marker='o', label=col.capitalize(), color=colors[col])

#     ax.set_ylabel("Amount (₹)")
#     ax.set_xlabel("Month")
#     ax.set_title("Monthly Financial Trends")
#     ax.legend()
#     plt.xticks(rotation=45)
#     plt.tight_layout()
#     return _fig_to_base64(fig)

