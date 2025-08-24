import pandas as pd
from app.utils.helper_functions import  df_to_html_table

def generate_expense_table(exp_df: pd.DataFrame) -> str:
    print(f'Generating Expense Table')
    exp_df_for_table = exp_df.copy()
    fiscal_exp_df = (
        exp_df_for_table.groupby(["FISCAL_YEAR", "TYPE"])["COST"]
        .sum()
        .reset_index()
        .sort_values(["FISCAL_YEAR", "COST"], ascending=[True, False])
    )
    return df_to_html_table(fiscal_exp_df, index=False)


def generate_savings_table(s_df: pd.DataFrame) -> str:
    print(f'Generating Savings Table')
    s_df_for_table = s_df.copy()
    if "return_percentage" in s_df_for_table:
        s_df_for_table["return_percentage"] = s_df_for_table["return_percentage"].map(lambda v: f"{v:.2f}%")

    ordered_cols = [c for c in [
            "TYPE", "NAME", "T_BUY", "T_SELL", "PROFIT_BOOKED",
            "CURRENT_INVESTED", "CURRENT_VALUE", "PROFIT_LOSS", "RETURN_PERCENTAGE"
        ] if c in s_df_for_table.columns]

    s_df_for_table = s_df_for_table[ordered_cols]
    return df_to_html_table(s_df_for_table, index=False)

def generate_yearly_distribution_table(yearly_df: pd.DataFrame):
    print(f'Generating Yearly Distribution Table')
    return df_to_html_table(yearly_df, index=False)
