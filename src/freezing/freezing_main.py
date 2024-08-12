import logging
import os
from datetime import datetime
from typing import Callable

import pandas as pd

from src.freezing.freezing_utils import  _add_last_frozen_column
from src.freezing.freezing_apply_changes import apply_freezing
from src.staging.validation import validate_data_with_schema
from src.utils.helpers import convert_formtype


FreezingLogger = logging.getLogger(__name__)


def run_freezing(
    main_snapshot: pd.DataFrame,
    # secondary_snapshot: pd.DataFrame,
    config: dict,
    check_file_exists: Callable,
    write_csv: Callable,
    read_csv: Callable,
    run_id: int,
) -> pd.DataFrame:
    """Run the freezing module.

    Args:
        main_snapshot (pd.DataFrame): The staged and vaildated snapshot data.
        secondary_snapshot (pd.DataFrame): The staged and validated updated
            snapshot data.
        config (dict): The pipeline configuration
        check_file_exists (callable): Function to check if file exists. This will
            be the hdfs or network version depending on settings.
        write_csv (callable): Function to write to a csv file. This will be the
            hdfs or network version depending on settings.
        read_csv (callable): Function to read a csv file. This will be the hdfs or
            network version depending on settings.
        run_id (int): The run id for this run.
    Returns:
        constructed_df (pd.DataFrame): As main_snapshot but with records amended
            and added from the freezing files.
    """
    # return frozen snapshot if config allows
    run_first_snapshot_of_results = config["global"]["run_first_snapshot_of_results"]
    run_updates_and_freeze = config["global"]["run_updates_and_freeze"]
    frozen_data_staged_path = config["freezing_paths"]["frozen_data_staged_path"]

    if not run_first_snapshot_of_results:
        FreezingLogger.info("Loading frozen data...")
        prepared_frozen_data = read_csv(frozen_data_staged_path)
        validate_data_with_schema(
            prepared_frozen_data, "./config/frozen_data_staged_schema.toml"
        )

        prepared_frozen_data["formtype"] = prepared_frozen_data["formtype"].apply(
            convert_formtype
        )
        FreezingLogger.info(
            "Frozen data successfully read from {frozen_data_staged_path}"
        )

    else:
        prepared_frozen_data = main_snapshot.copy()
        prepared_frozen_data = _add_last_frozen_column(prepared_frozen_data, run_id)

    # # Skip this module if the secondary snapshot isn't loaded
    # load_updated_snapshot = config["global"]["load_updated_snapshot"]
    # load_manual_freezing = config["global"]["load_manual_freezing"]
    # if load_manual_freezing is False:
    #     freezing_logger.info("Skipping freezing...")
    #     return main_snapshot

    # # ! For now, we add the year column since neither file has it
    # main_snapshot["year"] = 2022
    # if load_updated_snapshot is True:
    #     secondary_snapshot["year"] = 2022

    #     # Use the secondary snapshot to generate freezing files for the next run
    #     additions_df = get_additions(main_snapshot, secondary_snapshot)
    #     amendments_df = get_amendments(main_snapshot, secondary_snapshot)
    #     output_freezing_files(
    #         amendments_df, additions_df, config, write_csv, run_id
    #     )

    # # Read the freezing files from the last run and apply them
    constructed_df = apply_freezing(
        main_snapshot, config, check_file_exists, read_csv, run_id, FreezingLogger
    )
    constructed_df.reset_index(drop=True, inplace=True)

    if run_first_snapshot_of_results or run_updates_and_freeze:
        frozen_data_staged_output_path = config["freezing_paths"]["frozen_data_staged_output_path"]
        FreezingLogger.info("Outputting frozen data file.")
        tdate = datetime.now().strftime("%y-%m-%d")
        survey_year = config["years"]["survey_year"]
        filename = (
            f"{survey_year}_FROZEN_staged_BERD_full_responses_{tdate}_v{run_id}.csv"
        )
        write_csv(os.path.join(frozen_data_staged_output_path, filename), prepared_frozen_data)

    return prepared_frozen_data

def read_frozen_csv():
    # new functionality
    pass

