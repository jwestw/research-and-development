"""The main file for the UK Intram by ITL 1 and 2 output."""

# Standard Library Imports
import logging
import pathlib
import os
import re
from datetime import datetime
from typing import Callable, Dict, Any, Union, Tuple

# Third Party Imports
import pandas as pd


OutputMainLogger = logging.getLogger(__name__)


def save_detailed_csv(
    df: pd.DataFrame,
    output_dir: Union[pathlib.Path, str],
    survey_year: str,
    title: str,
    run_id: int,
    write_csv: Callable,
    overwrite: bool = True,
) -> Dict[str, int]:
    """Save a df as a csv with a detailed filename.

    Args:
        df (pd.DataFrame): The dataframe to save
        output_dir (Union[pathlib.Path, str]): The directory to save the dataframe to.
        survey_year (str): The year that the data is from (from config).
        title (str): The filename to save the df as (excluding date, run id).
        run_id (int): The current run ID.
        write_csv (Callable): A function to write to a csv file.
        overwrite (bool, optional): Whether or not to overwrite any current
            files saved under the same name. Defaults to True.

    Raises:
        FileExistsError: An error raised if overwrite is false and the file
            already exists.

    Returns:
        Dict[str, int]: A dictionary of intramural totals.
    """
    date = datetime.now().strftime("%y-%m-%d")
    save_name = f"{survey_year}_{title}_{date}_v{run_id}.csv"
    save_path = os.path.join(output_dir, save_name)
    if not overwrite and os.path.exists(save_path):
        raise FileExistsError(
            f"File '{save_path}' already exists. Pass overwrite=True if you "
            "want to overwrite this file."
        )
    write_csv(save_path, df)


def rename_itl(df: pd.DataFrame, itl: int, year) -> pd.DataFrame:
    """Renames ITL columns in a dataframe. Puts current year in total column name.


    Args:
        df (pd.DataFrame): The dataframe containing the ITL columns.
        itl (int): The ITL level.
        year (int): The current year from config.


    Returns:
        pd.DataFrame: A df with the renamed ITL columns.
    """
    renamer = {"211": f"Year {year} Total q211"}
    for col in df.columns:
        cd = re.search(rf"^ITL{itl}[0-9]*CD$", col)
        if cd:
            renamer[cd.group()] = f"Area Code (ITL{itl})"
            continue
        nm = re.search(rf"^ITL{itl}[0-9]*NM$", col)
        if nm:
            renamer[nm.group()] = f"Region (ITL{itl})"
        df = df.rename(mapper=renamer, axis=1)
    return df


def aggregate_itl(
    gb_df: pd.DataFrame,
    ni_df: pd.DataFrame,
    config,
    uk_output: bool = False,
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """Aggregates a dataframe to an ITL level.

    Args:
        gb_df (pd.DataFrame): The GB microdata with weights applied.
        ni_df (pd.DataFrame): The NI microdata (weights are 1).
        config (Dict[str, Any]): Pipeline configuation settings.
        uk_output (bool, optional): Whether to output UK or GB data. Defaults to False.

    Returns:
        Tuple[pd.DataFrame, pd.DataFrame]: The ITL1 and ITL2 dataframes.
    """
    CURRENT_YEAR = config["survey"]["survey_year"]
    GEO_COLS = config["mappers"]["geo_cols"]
    BASE_COLS = ["postcodes_harmonised", "formtype", "211"]
    df = gb_df[GEO_COLS + BASE_COLS]

    # conditionally include NI responses to produce UK
    if uk_output:
        ni_df = ni_df.copy()[["formtype", "211"]]
        for col in GEO_COLS + ["postcodes_harmonised"]:
            ni_df[col] = pd.NA
        df = df.append(ni_df, ignore_index=True).copy()

    # Aggregate to ITL2 and ITL1 (Keep 3 and 4 letter codes)
    itl2 = df.groupby(GEO_COLS).agg({"211": "sum"}).reset_index()
    itl1 = itl2.drop(GEO_COLS[:2], axis=1).copy()
    itl1 = itl1.groupby(GEO_COLS[2:]).agg({"211": "sum"}).copy().reset_index()

    # # Clean data rady for export
    itl2 = itl2.drop(GEO_COLS[2:], axis=1)
    itl1 = rename_itl(itl1, 1, CURRENT_YEAR)
    itl2 = rename_itl(itl2, 2, CURRENT_YEAR)

    return itl1, itl2


def output_intram_by_itl(
    gb_df: pd.DataFrame,
    ni_df: pd.DataFrame,
    config: Dict[str, Any],
    intram_tot_dict: Dict[str, int],
    write_csv: Callable,
    run_id: int,
    uk_output: bool = False,
):
    """Generate outputs aggregated to ITL levels 1 and 2.

    Args:
        gb_df (pd.DataFrame): GB microdata with weights applied.
        ni_df (pd.DataFrame): NI microdata (weights are 1),
        config (Dict[str, Any]): Project config.
        intram_tot_dict (Dict[str, int]): Dictionary with the intramural totals.
        write_csv (Callable): A function to write to a csv file.
        run_id (int): The current run ID.
        uk_output (bool, optional): Whether to output UK or GB data. Defaults to False.
    """
    # Declare Config Values
    OUTPUT_PATH = config["outputs_paths"]["outputs_master"]

    # Aggregate to ITL2 and ITL1 (Keep 3 and 4 letter codes)
    itl1, itl2 = aggregate_itl(gb_df, ni_df, config, uk_output)

    # Export UK outputs
    area = "gb" if not uk_output else "uk"
    itl_dfs = [itl1, itl2]
    for i, itl_df in enumerate(itl_dfs, start=1):
        # update the dictionary of intramural totals
        # get the name of the column which contains the string "211"
        col_name = itl_df.columns[itl_df.columns.str.contains("211")][0]
        intram_tot_dict[f"{area}_itl{i}"] = round(itl_df[col_name].sum(), 0)

        # Save the ITL data
        output_dir = f"{OUTPUT_PATH}/output_intram_{area}_itl{i}/"
        save_detailed_csv(
            itl_df,
            output_dir,
            config["survey"]["survey_year"],
            f"output_intram_{area}_itl{i}",
            run_id,
            write_csv,
            overwrite=True,
        )

    return intram_tot_dict
