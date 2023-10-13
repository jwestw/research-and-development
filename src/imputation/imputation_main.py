"""The main file for the Imputation module."""
import logging
import pandas as pd
from typing import Callable, Dict, Any
from datetime import datetime

from src.imputation import tmi_imputation as tmi
from src.imputation import expansion_imputation as ximp
from src.imputation.apportionment import run_apportionment

ImputationMainLogger = logging.getLogger(__name__)


def run_imputation(
    df: pd.DataFrame,
    mapper: pd.DataFrame,
    config: Dict[str, Any],
    write_csv: Callable,
    run_id: int,
) -> pd.DataFrame:

    target_vars = [
        "211",
        "305",
        "emp_researcher",
        "emp_technician",
        "emp_other",
        "headcount_res_m",
        "headcount_res_f",
        "headcount_tec_m",
        "headcount_tec_f",
        "headcount_oth_m",
        "headcount_oth_f",
    ]

    df = run_apportionment(df)

    imputed_df, qa_df = tmi.run_tmi(df, target_vars, mapper)

    imputed_df = ximp.run_expansion(imputed_df, config)

    imputed_output_df = imputed_df.loc[imputed_df["formtype"] == "0001"]

    NETWORK_OR_HDFS = config["global"]["network_or_hdfs"]
    imp_path = config[f"{NETWORK_OR_HDFS}_paths"]["imputation_path"]

    if config["global"]["output_imputation_qa"]:
        ImputationMainLogger.info("Outputting Imputation files.")
        tdate = datetime.now().strftime("%Y-%m-%d")
        trim_qa_filename = f"trimming_qa_{tdate}_v{run_id}.csv"
        full_imp_filename = f"full_responses_imputed_{tdate}_v{run_id}.csv"
        write_csv(f"{imp_path}/imputation_qa/{trim_qa_filename}", qa_df)
        write_csv(f"{imp_path}/imputation_qa/{full_imp_filename}", imputed_output_df)
    ImputationMainLogger.info("Finished Imputation calculation.")

    # Get the breakdown columns from the config
    bd_cols = config["breakdowns"]["2xx"] + config["breakdowns"]["3xx"]
    orig_cols = bd_cols + target_vars

    # Create names for imputed cols
    imp_cols = [f"{col}_imputed" for col in orig_cols]

    # Update the original breakdown questions and target variables with the imputed
    imputed_df[orig_cols] = imputed_df[imp_cols]

    # Drop imputed values from df
    imputed_df = imputed_df.drop(columns=imp_cols)

    return imputed_df
