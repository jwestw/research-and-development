"""Module containing all functions relating to short form expansion."""
from typing import List, Union
import pandas as pd
import logging

from src.imputation.expansion_imputation import split_df_on_trim
from src.imputation.tmi_imputation import create_imp_class_col, apply_to_original
from src.utils.wrappers import df_change_func_wrap

SFExpansionLogger = logging.getLogger(__name__)

formtype_long = "0001"
formtype_short = "0006"


def expansion_impute(
    group: pd.core.groupby.DataFrameGroupBy,
    master_col: str,
    trim_col: str,
    break_down_cols: List[Union[str, int]],
) -> pd.DataFrame:
    """Calculate the expansion imputated values for short forms using long form data"""

    # Create a copy of the group dataframe
    group_copy = group.copy()

    imp_class = group_copy["imp_class"].values[0]
    SFExpansionLogger.debug(f"Imputation class: {imp_class}.")

    # Make cols into str just in case coming through as ints
    bd_cols = [str(col) for col in break_down_cols]

    # Make long and short masks
    long_mask = group_copy["formtype"] == formtype_long
    short_mask = group_copy["formtype"] == formtype_short

    # Create mask for clear responders
    clear_statuses = ["Clear", "Clear - overridden"]
    clear_mask = group_copy["status"].isin(clear_statuses)

    # Create a mask to exclude trimmed values
    exclude_trim_mask = group_copy[trim_col].isin([False])

    # Combination masks to select correct records for summing
    # NOTE: we only use long form clear responders in calculations
    # but we calculate breakdown values for imputed short form rows
    long_responder_mask = clear_mask & long_mask & exclude_trim_mask
    to_expand_mask = short_mask

    # Get long forms only for summing the master_col (scalar value)
    sum_master_q_lng = group_copy.loc[long_responder_mask, master_col].sum()

    # Get the master (e.g. 211) value for all short forms (will be a vector)
    returned_master_vals = group_copy.loc[to_expand_mask, master_col]

    # Calculate the imputation columns for the breakdown questions
    for bd_col in bd_cols:
        # Sum the breakdown q for the (clear) responders
        sum_breakdown_q = group_copy.loc[long_responder_mask, bd_col].sum()

        # Calculate the values of the imputation column
        if sum_master_q_lng > 0:
            scale_factor = sum_breakdown_q / sum_master_q_lng
        else:
            scale_factor = 0

        imputed_sf_vals = scale_factor * returned_master_vals
        
        # Write imputed value to all records
        group_copy.loc[short_mask, f"{bd_col}_imputed"] = imputed_sf_vals

    # Returning updated group and updated QA dict
    return group_copy


@df_change_func_wrap
def apply_expansion(df: pd.DataFrame, master_values: List, breakdown_dict: dict):

    # Renaming this df to use in the for loop
    expanded_df = df.copy()

    # Cast nulls in the boolean trim columns to False
    expanded_df[["211_trim", "305_trim"]] = expanded_df[
        ["211_trim", "305_trim"]
    ].fillna(False)

    for master_value in master_values:
        # exclude the "305" case which will be based on different trimming
        if master_value == "305":
            trim_col = "305_trim"
        else:
            trim_col = "211_trim"

        SFExpansionLogger.debug(f"Processing exansion imputation for {master_value}")

        # Create group_by obj of the trimmed df
        groupby_obj = expanded_df.groupby("imp_class")  

        # Calculate the imputation values for master question
        expanded_df = groupby_obj.apply(
            expansion_impute,
            master_value,
            trim_col,
            break_down_cols=breakdown_dict[master_value],
        )  # returns a dataframe


    # Calculate the headcount_m and headcount_f imputed values by summing
    short_mask = expanded_df["formtype"] == formtype_short

    expanded_df.loc[short_mask, "headcount_tot_m_imputed"] = (
        expanded_df["headcount_res_m_imputed"]
        + expanded_df["headcount_tec_m_imputed"]
        + expanded_df["headcount_oth_m_imputed"]
    )

    expanded_df.loc[short_mask, "headcount_tot_f_imputed"] = (
        expanded_df["headcount_res_f_imputed"]
        + expanded_df["headcount_tec_f_imputed"]
        + expanded_df["headcount_oth_f_imputed"]
    )

    return expanded_df


def split_df_on_imp_class(df: pd.DataFrame, exclusion_list: List = ["817", "nan"]):

    # Exclude the records from the reference list
    exclusion_str = "|".join(exclusion_list)

    # Create the filter
    exclusion_filter = df["imp_class"].str.contains(exclusion_str)
    # Where imputation class is null, `NaN` is returned by the
    # .str.contains(exclusion_str) so we need to swap out the
    # returned `NaN`s with True, so it gets filtered out
    exclusion_filter = exclusion_filter.fillna(True)

    # Filter out imputation classes that include "817" or "nan"
    filtered_df = df[~exclusion_filter]  # df has 817 and nan filtered out
    excluded_df = df[exclusion_filter]  # df only has 817 and nan records

    return filtered_df, excluded_df


@df_change_func_wrap
def run_sf_expansion(df: pd.DataFrame, config: dict) -> pd.DataFrame:
    # Remove records that have the reference list variables
    # and those that have "nan" in the imp class
    filtered_df, excluded_df = split_df_on_imp_class(df)

    # Get dictionary of short form master keys (or target variables)
    # and breakdown variables
    breakdown_dict = config["breakdowns"]
    master_values = list(breakdown_dict)

    # Run the `expansion_impute` function in a for-loop via `apply_expansion`
    expanded_df = apply_expansion(filtered_df, master_values, breakdown_dict)

    # Re-include those records from the reference list before returning df
    result_df = pd.concat([expanded_df, excluded_df], axis=0)

    result_df = result_df.sort_values(
        ["reference", "instance"], ascending=[True, True]
    ).reset_index(drop=True)

    SFExpansionLogger.info("Short-form expansion imputation completed.")

    return result_df
