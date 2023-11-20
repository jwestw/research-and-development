"""The main file for the total FTE output."""
import logging
import pandas as pd
from datetime import datetime
from typing import Callable, Dict, Any


OutputMainLogger = logging.getLogger(__name__)


def qa_output_total_fte(
    df: pd.DataFrame,
    config: Dict[str, Any],
    write_csv: Callable,
    run_id: int
):
    """Run the outputs module.

    Args:
        df (pd.DataFrame): The main dataset with weights not applied
        config (dict): The configuration settings.
        write_csv (Callable): Function to write to a csv file.
         This will be the hdfs or network version depending on settings.
        run_id (int): The current run id

    """
    NETWORK_OR_HDFS = config["global"]["network_or_hdfs"]
    est_path = config[f"{NETWORK_OR_HDFS}_paths"]["estimation_path"]

    imp_marker_list = ["R", "TMI", "CR", "MoR"]
    sliced_df = df.copy().loc[df["imp_marker"].isin(imp_marker_list)]

    totals_names = ["Total",
                    "Scientists and engineers",
                    "Technicians, laboratory assistants and draughtsmen",
                    "Administrative, clerical, industrial and other staff"]
    totals_values = [sliced_df["emp_total"].sum(),
                     sliced_df["emp_researcher"].sum(),
                     sliced_df["emp_technician"].sum(),
                     sliced_df["emp_other"].sum()]
    qa_total_fte_df = pd.DataFrame(list(zip(totals_names, totals_values)),
                                   columns=["Column", "Total"]
                                   )

    # Outputting the CSV file with timestamp and run_id
    tdate = datetime.now().strftime("%Y-%m-%d")
    filename = f"estimation_total_fte_qa_{tdate}_v{run_id}.csv"
    write_csv(f"{est_path}/estimation_qa/{filename}", qa_total_fte_df)
