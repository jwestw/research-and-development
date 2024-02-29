"""The main file for the UK Intram by ITL 1 and 2 output."""
import logging
from xmlrpc.client import Boolean
import pandas as pd
from datetime import datetime
from typing import Callable, Dict, Any

from src.outputs.outputs_helpers import aggregate_output
import src.outputs.map_output_cols as map_o

OutputMainLogger = logging.getLogger(__name__)


def output_frozen_group(
    df_gb: pd.DataFrame,
    df_ni: pd.DataFrame,
    ultfoc_mapper: pd.DataFrame,
    config: Dict[str, Any],
    write_csv: Callable,
    run_id: int,
    deduplicate: bool = True
):
    """Creates a "frozen group" output  for the
    entire UK. Combines BERD and NI data. Selects the columns we need for this
    type of output. De-duplicates the dataframe, combining the values of 
    multiple sites in one record. Adds blank columns and zero columns -
    they need to be in the output for back-compatibility, but we don't have any
    data. output CSV files.

    Args:
        df_gb (pd.DataFrame): The GB microdata with weights applied
        df_ ni (pd.DataFrame): The NI microdata; weights are 1
        ultfoc_mappe (pd.DataFrame): Ultimate foreign owner mappper.
        config (dict): The configuration settings.
        write_csv (Callable): Function to write to a csv file.
         This will be the hdfs or network version depending on settings.
        run_id (int): The current run id
        deduplicate (Boolean): If true, the results are deduplicated.

    """

    NETWORK_OR_HDFS = config["global"]["network_or_hdfs"]
    paths = config[f"{NETWORK_OR_HDFS}_paths"]
    output_path = paths["output_path"]

    # Categorical columns that we have in BERD and NI data
    category_columns = [
        "period_year", "reference", "employment", "ultfoc", 
        "formtype", "form_status", "wowenterprisereference", "rusic",
    ]
    
    # Numerical value columns that we have in BERD and NI data
    value_columns = [
        "emp_researcher", "emp_technician", "emp_other", 
        "emp_total", "202", "203", "204", "205", "206", "207", "209", "210", 
        "211", "212", "214", "216", "218", "219", "220", "221", "222",
        "223", "225", "226", "227", "228", "229", "237", "242", "243", "244",
        "245", "246", "247", "248", "249", "302", "303", "304", "305",
        "headcount_res_m", "headcount_res_f", "headcount_tec_m", 
        "headcount_tec_f", "headcount_oth_m", "headcount_oth_f",
        "headcount_oth_f",
        "250", "251", "307", "308", "309", 
    ]


    # Columns that we don't have that should have pd.NA values
    blank_columns = [
        "freeze_id", "period", "cell_id", "period_contributor_id",
    ]

    # Columns that we don't have that should have zero values
    # The numerical questions starting with q, like q208, are needed for the 
    # output. If it's without q, then we have it in our data.
    zero_columns = [
        "data_source", "q208", "q213", "q215", "q224", "q230", "q231", "q232", 
        "q233", "q234", "q235", "q236", "q238", "q239", "q240", "q241", "q252", 
        "q253", "q254", "q255", "q256", "q257", "q258",
    ]

    # Join foriegn ownership column using ultfoc mapper for GB
    df_gb = map_o.join_fgn_ownership(df_gb, ultfoc_mapper, formtype=["0001", "0006"]) 
    
    # Map to the CORA statuses from the statusencoded column
    df_gb = map_o.create_cora_status_col(df_gb)
    
    # Select the columns we need
    need_columns = category_columns +  value_columns
    df_gb_need = df_gb[need_columns]
    df_ni_need = df_ni[need_columns]

    # Concatinate GB and NI
    df = df_gb_need.append(df_ni_need, ignore_index=True)
  
    # Deduplicate by aggregation
    if deduplicate:
        df_agg = aggregate_output(
            df, 
            category_columns, 
            value_columns, 
            "sum"
        )
    else:
        df_agg = df[category_columns + value_columns]
    
    # Add size bands
    df = map_o.map_sizebands(df)
    
    # Create blank and zero columns
    df_agg = df_agg.reindex(
        columns=df_agg.columns.tolist() + blank_columns + zero_columns
    )

    # Assign blank values
    blank_values = [pd.NA] * len(blank_columns)
    df_agg[blank_columns] = blank_values
    
    # Assign zero values
    zero_values = [0] * len(zero_columns)
    df_agg[zero_columns] = zero_values

    # Outputting the CSV file with timestamp and run_id
    tdate = datetime.now().strftime("%Y-%m-%d")
    filename = f"output_frozen_group_{tdate}_v{run_id}.csv"
    write_csv(f"{output_path}/output_frozen_group/{filename}", df_agg)
