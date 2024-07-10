"""Useful utilities for the construction module."""
import pathlib
import logging
from typing import Union, Callable

import pandas as pd

def read_construction_file(
        path: Union[str, pathlib.Path],
        logger: logging.Logger,
        read_csv_func: Callable,
        file_exists_func: Callable
    ) -> pd.DataFrame:
    """_summary_

    Args:
        path (Union[str, pathlib.Path]): _description_
        logger (logging.Logger): _description_
        read_csv_func (Callable): _description_
        file_exists_func (Callable): _description_

    Returns:
        pd.DataFrame: _description_
    """
    logger.info(f"Attempting to read construction file from {path}...")
    construction_file_exists = file_exists_func(path)
    if construction_file_exists:
        try:
            construction_df = read_csv_func(path)
            logger.info(f"Successfully read construction file from {path}.")
            return construction_df
        except pd.errors.EmptyDataError:
            logger.warning(
                f"Construction file {path} is empty, skipping..."
            )
            return None
    logger.warning(
        "Construction file not found, skipping construction..."
    )
    return None


def convert_formtype(formtype_value):
    if pd.notnull(formtype_value):
        if formtype_value == "1" or formtype_value == "1.0" or formtype_value == "0001":
            return "0001"
        elif (
            formtype_value == "6" or formtype_value == "6.0" or formtype_value == "0006"
        ):
            return "0006"
        else:
            return None
    else:
        return None