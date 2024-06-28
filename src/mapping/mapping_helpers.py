import pandas as pd
import re
import numpy as np
import logging
from typing import Callable
import os
import toml

from src.utils.wrappers import time_logger_wrap, exception_wrap

MappingLogger = logging.getLogger(__name__)


@time_logger_wrap
@exception_wrap
def validate_ultfoc_df(df: pd.DataFrame) -> pd.DataFrame:
    """
    Validates ultfoc df:
    1. Checks if the DataFrame has exactly two columns.
    2. Checks if the column headers are 'ruref' and 'ultfoc'.
    3. Checks the validity of values in the 'ultfoc' column.
    Args:
        df (pd.DataFrame): The input DataFrame containing 'ruref'
        and 'ultfoc' columns.
    """
    try:
        # Check DataFrame shape
        if df.shape[1] != 2:
            raise ValueError("Dataframe file must have exactly two columns")

        # Check column headers
        if list(df.columns) != ["ruref", "ultfoc"]:
            raise ValueError("Column headers should be 'ruref' and 'ultfoc'")

        # Check 'ultfoc' values are either 2 characters or 'nan'
        def check_ultfoc(value):
            if pd.isna(value):
                return True
            else:
                return isinstance(value, str) and (len(value) == 2)

        df["contents_check"] = df.apply(lambda row: check_ultfoc(row["ultfoc"]), axis=1)

        # check any unexpected contents
        if not df["contents_check"].all():
            raise ValueError("Unexpected format within 'ultfoc' column contents")

        df.drop(columns=["contents_check"], inplace=True)

    except ValueError as ve:
        raise ValueError("Foreign ownership mapper validation failed: " + str(ve))


def update_ref_list(full_df: pd.DataFrame, ref_list_df: pd.DataFrame) -> pd.DataFrame:
    """
    Update long form references that should be on the reference list.

    For the first year (processing 2022 data) only, several references
    should have been designated on the "reference list", ie, should have been
    assigned cellnumber = 817, but were wrongly assigned a different cellnumber.

    Args:
        full_df (pd.DataFrame): The full_responses dataframe
        ref_list_df (pd.DataFrame): The mapper containing updates for the cellnumber
    Returns:
        df (pd.DataFrame): with cellnumber and selectiontype cols updated.
    """
    ref_list_filtered = ref_list_df.loc[
        (ref_list_df.formtype == "1") & (ref_list_df.cellnumber != 817)
    ]
    df = pd.merge(
        full_df,
        ref_list_filtered[["reference", "cellnumber"]],
        how="outer",
        on="reference",
        suffixes=("", "_new"),
        indicator=True,
    )
    # check no items in the reference list mapper are missing from the full responses
    missing_refs = df.loc[df["_merge"] == "right_only"]
    if not missing_refs.empty:
        msg = (
            "The following references in the reference list mapper are not in the data:"
        )
        raise ValueError(msg + str(missing_refs.reference.unique()))

    # update cellnumber and selectiontype where there is a match
    match_cond = df["_merge"] == "both"
    df = df.copy()
    df.loc[match_cond, "cellnumber"] = 817
    df.loc[match_cond, "selectiontype"] = "L"

    df = df.drop(["_merge", "cellnumber_new"], axis=1)

    return df
