"""The main file for the BERD Intram by PG output."""
import logging
import pandas as pd
from datetime import datetime
from typing import Callable, Dict, Any

OutputMainLogger = logging.getLogger(__name__)


def output_intram_by_pg(
    gb_df: pd.DataFrame,
    pg_detailed: pd.DataFrame,
    config: Dict[str, Any],
    write_csv: Callable,
    run_id: int,
    ni_df: pd.DataFrame = None,
):
    """Run the outputs module.

    Args:
        gb_df (pd.DataFrame): The dataset main with weights not applied
        pg_detailed (pd.DataFrame): Detailed info for the product groups.
        config (dict): The configuration settings.
        write_csv (Callable): Function to write to a csv file.
            This will be the hdfs or network version depending on settings.
        run_id (int): The current run id
        ni_df (pd.DataFrame): The NI datasets without weights applied.

    """
    NETWORK_OR_HDFS = config["global"]["network_or_hdfs"]
    paths = config[f"{NETWORK_OR_HDFS}_paths"]
    output_path = paths["output_path"]
    # assign columns for easier use
    key_col = "201"
    value_col = "211"
    # evaluate if NI data is included and clean
    if not isinstance(ni_df, (pd.DataFrame, type(None))):
        raise TypeError(f"'ni_df' expected type pd.DataFrame. Got {type(ni_df)}")
    if ni_df is not None:
        if not ni_df.empty:
            # defence
            # work out cols to select
            cols_to_keep = [col for col in gb_df.columns if col in ni_df.columns]
            gb_df = gb_df[cols_to_keep]
            ni_df = ni_df[cols_to_keep]
            gb_df = gb_df.append(ni_df)

    # Group by PG and aggregate intram
    df_agg = gb_df.groupby([key_col]).agg({value_col: "sum"}).reset_index()

    # Create Total and concatinate it to df_agg
    value_tot = df_agg[value_col].sum()
    df_tot = pd.DataFrame({key_col: ["total"], value_col: value_tot})
    df_agg = pd.concat([df_agg, df_tot])

    # Merge with labels and ranks
    df_merge = pg_detailed.merge(
        df_agg, how="left", left_on="pg_alpha", right_on=key_col
    )
    df_merge[value_col] = df_merge[value_col].fillna(0)

    # Sort by rank
    df_merge.sort_values("ranking", axis=0, ascending=True)

    # Select and rename the correct columns
    detail = "Detailed product groups (Alphabetical product groups A-AH)"
    notes = "Notes"
    value_title = "2023 (Current period)"
    df_merge = df_merge[[detail, value_col, notes]].rename(
        columns={value_col: value_title}
    )

    # Outputting the CSV file with timestamp and run_id
    tdate = datetime.now().strftime("%y-%m-%d")
    survey_year = config["years"]["survey_year"]
    filename = (
        f"{survey_year}_output_intram_by_pg_{'uk' if ni_df is not None else 'gb'}_{tdate}_v{run_id}.csv"
    )
    write_csv(
        f"{output_path}/output_intram_by_pg_{'uk' if ni_df is not None else 'gb'}/{filename}",
        df_merge,
    )
