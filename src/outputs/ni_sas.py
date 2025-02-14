"""The NI SAS for the Outputs module."""
import logging
import pandas as pd
from datetime import datetime
from typing import Callable, Dict, Any
import src.outputs.map_output_cols as map_o
from src.staging.validation import load_schema
from src.outputs.outputs_helpers import create_output_df

OutputMainLogger = logging.getLogger(__name__)


def output_ni_sas(
    df: pd.DataFrame,
    config: Dict[str, Any],
    write_csv: Callable,
    run_id: int,
):
    """Run the outputs module.

    Args:
        df (pd.DataFrame): The Northern Ireland dataset of responses
        config (dict): The configuration settings.
        write_csv (Callable): Function to write to a csv file.
            This will be the hdfs or network version depending on settings.
        run_id (int): The current run id
    """
    output_path = config["outputs_paths"]["outputs_master"]

    # Map the sizebands based on frozen employment
    df = map_o.map_sizebands(df)

    # Create C_lnd_bl
    df["C_lnd_bl"] = df[["219", "220"]].fillna(0).sum(axis=1)

    # Create ovss_oth
    df["ovss_oth"] = (
        df[["243", "244", "245", "246", "247", "249"]].fillna(0).sum(axis=1)
    )

    # Create oth_sc
    df["oth_sc"] = df[["242", "248", "250"]].fillna(0).sum(axis=1)

    # Create NI SAS output dataframe with required columns from schema
    schema_path = config["schema_paths"]["ni_sas_schema"]
    schema_dict = load_schema(schema_path)
    output = create_output_df(df, schema_dict)

    # Outputting the CSV file with timestamp and run_id
    tdate = datetime.now().strftime("%y-%m-%d")
    survey_year = config["survey"]["survey_year"]
    filename = f"{survey_year}_output_ni_sas_{tdate}_v{run_id}.csv"
    write_csv(f"{output_path}/output_ni_sas/{filename}", output)
