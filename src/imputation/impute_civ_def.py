"""This code could eventually be added to tmi_imputation.py this 
doesn't impact on the readability of the existing code. """

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple

from src.imputation import tmi_imputation as tmi


def calc_cd_proportions(df: pd.DataFrame): # -> Tuple[float, float]:
    """Calc the proportion of civil and defence entries in a df"""
    num_civ = len(df.loc[df["200"] == 'C', "200"])
    num_def = len(df.loc[df["200"] == 'D', "200"])

    proportion_civ = num_civ/(num_civ + num_def)
    proportion_def = num_def/(num_civ + num_def)

    return proportion_civ, proportion_def


def create_civdef_dict(
    df: pd.DataFrame
) -> Tuple[Dict[str, float], pd.DataFrame]:
    """Create dictionary with values to use for civil and defence imputation.

    Args:
        df (pd.DataFrame): The dataframe of 'clear' responses for the given 
            imputation class

    Returns:
        Dict[str, Tuple(float, float)]
    """
    # create dictionary to hold civil or defence ratios for each class
    civdef_dict = {}

    # Filter out imputation classes that are missing either "201" or "rusic"
    # and exclude empty pg_sic classes
    cond1 = ~(df["pg_sic_class"].str.contains("nan")) & (df["empty_pgsic_group"] == False)
    filtered_df = df[cond1]

    # Group by the pg_sic imputation class 
    pg_sic_grp = filtered_df.loc[filtered_df["instance"] != 0].groupby("pg_sic_class")

    # loop through the pg_sic imputation class groups
    for pg_sic_class, class_group_df in pg_sic_grp:
        civdef_dict[pg_sic_class] = calc_cd_proportions(class_group_df)

    # create a second dictionary to hold civil or defence ratios 
    # for the "empty_pgsic_group" cases
    civdef_empty_group_dict = {}

    # filter out invalid pg classes and empty pg groups from the original dataframe
    cond2 = ~(df["pg_class"].str.contains("nan")) & (df["empty_pg_group"] == False)
    filtered_df2 = df[cond2]

    # evaluate which pg classes are needed for empty pg_sic groups
    num_empty = filtered_df2.groupby("pg_class")["empty_pgsic_group"].transform(sum)

    filtered_df2 = filtered_df2.loc[num_empty > 0]

    # Group by the pg-only imputation class the loop through the groups
    pg_grp = filtered_df2.loc[filtered_df2["instance"] != 0].groupby("pg_class")

    for pg_class, class_group_df in pg_grp:
        civdef_empty_group_dict[pg_class] = calc_cd_proportions(class_group_df)

    return civdef_dict, civdef_empty_group_dict


def calc_empty_group(
        df: pd.DataFrame, 
        class_name: str, 
        new_col_name: str
) -> pd.DataFrame:
    """Add a new bool column flagging empty groups."""

    clear_status_cond = df["statusencoded"].isin(["210", "211"])
    df["valid_civdef_val"] = ~df["200"].isnull() & clear_status_cond

    # calculate the number of valid entries in the class for column 200 
    num_valid = df.groupby(class_name)["valid_civdef_val"].transform(sum)

    # exclude classes that are not valid
    valid_class_cond = ~(df[class_name].str.contains("nan"))

    # create new bool column to flag empty classes
    df[new_col_name] = valid_class_cond &  (num_valid == 0) 

    df = df.drop("valid_civdef_val", axis=1)

    return df


def prep_cd_imp_classes(df: pd.DataFrame) -> pd.DataFrame:
    # create imputation classes based on product group and rusic
    df = tmi.create_imp_class_col(df, "201", "rusic", "pg_sic_class")

    # flag empty pg_sic_classes in new bool col "empty_pgsic_class"
    df = calc_empty_group(df, "pg_sic_class", "empty_pgsic_group")

    # create a new imputation class called "pg_class" to be used only when
    # "empty_pgsic_group" is true (ie, no avaible R&D type entries)
    # this imputation class will include product group (col 201) only.
    df = tmi.create_imp_class_col(df, "201", None, "pg_class")

    # flag empty pg_classes in new bool col "empty_pg_class"
    df = calc_empty_group(df, "pg_class", "empty_pg_group")

    return df


def random_assign_civdef(df: pd.DataFrame, proportions: Tuple[float, float]) -> pd.DataFrame:
    """Assign "C" for civil or "D" for defence randomly based on
        the proportions supplied.
    """
    df["200_imputed"] = np.random.choice(
        ["C", "D"], 
        size = len(df), 
        p = proportions
    )
    return df


def apply_civdev_imputation(
    df: pd.DataFrame, 
    pgsic_dict: Dict[str, Tuple[float, float]],
    pg_dict: Dict[str, Tuple[float, float]]
) -> pd.DataFrame:
    """Apply imputation for R&D type for non-responders and 'No R&D'.

    Values in column 200 (R&D type) are imputed with either "C" for civl or
    "D" for defence, based on ratios in the same imputation class in 
    clear responders.
    
    Args:
        df (pd.DataFrame): The dataframe of all responses
        cd_dict (Dict[str, Tuple(float, float)]): Dictionary with values to 
            use for imputation.

    Returns:
        pd.DataFrame: An updated dataframe with new col "200_imputed".
    '"""
    df["200_imputed"] = "N/A"
    df["200_imp_marker"] = "N/A"

    # Create logic conditions for filtering
    clear_status_cond = df["statusencoded"].isin(["210", "211"])
    to_impute_cond = (
        ((df["status"] == "Form sent out") | (df["604"] == "No"))
        & df["instance"] != 0
    )


    # find civil and defence proportions for the whole clear dataframe
    clear_df = df.loc[clear_status_cond].copy()
    proportions = calc_cd_proportions(clear_df)

    # randomly assign civil or defence based on proportions in whole clear df
    to_impute_df = df.loc[to_impute_cond].copy()
    to_impute_df = random_assign_civdef(to_impute_df, proportions)
    to_impute_df["200_imp_marker"] = "fall_back_imputed"

    # next refine the civil and defence based on product group imputation class
    # filter out empty and invalid imputation classes
    cond1 = to_impute_df["empty_pg_group"] == False
    cond2 = ~to_impute_df["pg_class"].str.contains("nan")

    filtered_df = to_impute_df.loc[cond1 & cond2].copy()

    # loop through the pg imputation classes to apply imputation
    pg_grp = filtered_df.loc[filtered_df["instance"] != 0].groupby("pg_class")

    for pg_class, class_group_df in pg_grp:
        if pg_class in pg_dict.keys():
            class_group_df = random_assign_civdef(
                class_group_df, 
                pg_dict[pg_class]
            )
            class_group_df["200_imp_marker"] = "pg_group_imputed"
        else:
            class_group_df["200_imp_marker"] = "no pg value available"

        tmi.apply_to_original(class_group_df, filtered_df)

    tmi.apply_to_original(filtered_df, to_impute_df)

    # first impute the pg_sic 
    # filter out empty and invalid imputation classes
    cond3 = to_impute_df["empty_pgsic_group"] == False
    cond4 = ~to_impute_df["pg_sic_class"].str.contains("nan")

    filtered_df2 = to_impute_df.loc[cond3 & cond4].copy()

    # loop through the pg_sic imputation classes to apply imputation
    pg_sic_grp = filtered_df2.loc[filtered_df2["instance"] != 0].groupby("pg_sic_class")

    for pg_sic_class, class_group_df in pg_sic_grp:
        if pg_sic_class in pgsic_dict.keys():
            class_group_df = random_assign_civdef(
                class_group_df, 
                pgsic_dict[pg_sic_class]
            )
            class_group_df["200_imp_marker"] = "pg_sic group imputed"
        else:
            #TODO could put empty_group flag in here
            class_group_df["200_imp_marker"] = "no pgsic value available"

        tmi.apply_to_original(class_group_df, filtered_df2)
    tmi.apply_to_original(filtered_df2, to_impute_df)

    updated_df = tmi.apply_to_original(to_impute_df, df)
    return updated_df


def impute_civil_defence(df: pd.DataFrame) -> pd.DataFrame:
    """Impute the R&D type for non-responders and 'No R&D'.

    Args:
        df (pd.DataFrame): SPP dataframe afer PG imputation.

    Returns:
        pd.DataFrame: The original dataframe with imputed values for 
            R&D type (civil or defence)
    """

    df = prep_cd_imp_classes(df)

    # Filter for clear statuses
    clear_df = tmi.filter_by_column_content(df, "statusencoded", ["210", "211"])

    # create a dict mapping each class to either 'C' (civil) or 'D'(defence)
    pgsic_dict, pg_dict = create_civdef_dict(clear_df)

    df = apply_civdev_imputation(df, pgsic_dict, pg_dict)

    return df