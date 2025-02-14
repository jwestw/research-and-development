"""The main file for the staging and validation module."""
# Core imports
import logging
from typing import Callable, Tuple
from datetime import datetime
import os

import pandas as pd

import src.staging.staging_helpers as helpers
from src.staging import validation as val

# from src.utils.breakdown_validation import run_breakdown_validation

StagingMainLogger = logging.getLogger(__name__)


def run_staging(  # noqa: C901
    config: dict,
    rd_file_exists: callable,
    rd_load_json: callable,
    rd_read_csv: callable,
    rd_write_csv: callable,
    rd_read_feather: Callable,
    rd_write_feather: Callable,
    run_id: int,
) -> Tuple:
    """Run the staging and validation module.

    The snapshot data is ingested from a json file, and parsed into dataframes,
    one for survey contributers and another for their responses. These are merged
    and transmuted so each question has its own column. The resulting dataframe
    undergoes validation.

    When running on the local network,

    Args:
        config (dict): The pipeline configuration
        rd_file_exists (Callable): Function to check if file exists
            Avaible in s3, hdfs or network version depending "platform".
        rd_load_json (Callable): Function to load a json file.
            Avaible in s3, hdfs or network version depending "platform".
        rd_read_csv (Callable): Function to read a csv file.
            Avaible in s3, hdfs or network version depending "platform".
        rd_write_csv (Callable): Function to write to a csv file.
            Avaible in s3, hdfs or network version depending "platform".
        rd_read_feather (Callable): Function to read feather files to Pandas
            Available in HDFS and Windows only.
        rd_write_feather (Callable): Function to write feather files from Pandas
            Available in HDFS and Windows only.
        run_id (int): The run id for this run.
    Returns:
        tuple
            full_responses (pd.DataFrame): The staged and vaildated snapshot data,
            secondary_full_responses (pd.Dataframe): The staged and validated updated
            snapshot data
            manual_outliers (pd.DataFrame): Data with column for manual outliers,
            ultfoc_mapper (pd.DataFrame): Foreign ownership mapper,
            cellno_df (pd.DataFrame): Cell numbers mapper,
            postcode_mapper (pd.DataFrame): Postcodes to Regional Code mapper,
            pg_alpha_num (pd.DataFrame): Product group alpha to numeric mapper.
            pg_num_alpha (pd.DataFrame): Product group numeric to alpha mapper.
            sic_pg_alpha (pd.DataFrame): SIC code to product group alpha mapper.
    """
    # Check the environment switch
    platform = config["global"]["platform"]
    is_network = platform == "network"
    load_from_feather = config["global"]["load_from_feather"]

    # set up dictionaries with all the paths needed for the staging module
    staging_dict = config["staging_paths"]

    stage_frozen_snapshot = (
        config["global"]["run_with_snapshot"]
        | config["global"]["run_with_snapshot_and_freeze"]
    )
    stage_updated_snapshot = config["global"]["load_updated_snapshot_for_comparison"]
    if stage_frozen_snapshot or stage_updated_snapshot:
        feather_path = staging_dict["feather_output"]

        if stage_frozen_snapshot:
            snapshot_name = os.path.basename(staging_dict["snapshot_path"]).split(
                ".", 1
            )[0]

            feather_file = os.path.join(feather_path, f"{snapshot_name}.feather")

        elif stage_updated_snapshot:
            snapshot_name = os.path.basename(
                staging_dict["updated_snapshot_path"]
            ).split(".", 1)[0]
            feather_file = os.path.join(feather_path, f"{snapshot_name}.feather")

        # Check if the if the snapshot feather exists
        feather_files_exist = rd_file_exists(feather_file)

        # Only read from feather if feather files exist and we are on network
        READ_FROM_FEATHER = is_network & feather_files_exist & load_from_feather
        if READ_FROM_FEATHER:
            # Load data from first feather file found
            StagingMainLogger.info("Skipping data validation. Loading from feather")
            full_responses = helpers.load_snapshot_feather(
                feather_file, rd_read_feather
            )

            # Read in postcode mapper (needed later in the pipeline)
            postcode_mapper = config["mapping_paths"]["postcode_mapper"]
            rd_file_exists(postcode_mapper, raise_error=True)
            postcode_mapper = rd_read_csv(postcode_mapper)

        else:  # Read from JSON
            # Check data file exists, raise an error if it does not.
            if stage_frozen_snapshot:
                snapshot_path = staging_dict["snapshot_path"]
            elif stage_updated_snapshot:
                snapshot_path = staging_dict["updated_snapshot_path"]

            rd_file_exists(snapshot_path, raise_error=True)
            full_responses, response_rate = helpers.load_val_snapshot_json(
                snapshot_path,
                rd_load_json,
                config,
            )

            StagingMainLogger.info(
                f"Response rate: {response_rate}"
            )  # TODO: We might want to use this in a QA output

            # Data validation of json or feather data
            is_dev = config["global"]["dev_test"]
            if is_dev:
                StagingMainLogger.info("Platform is DEV, check data shape skipped")
            else:
                StagingMainLogger.info("Checking data shape")
                val.check_data_shape(full_responses, raise_error=True)

            # Validate the postcodes in data loaded from JSON
            (
                full_responses,
                postcode_mapper,
            ) = helpers.stage_validate_harmonise_postcodes(
                config,
                full_responses,
                run_id,
                rd_file_exists,
                rd_read_csv,
                rd_write_csv,
            )

            # Write snapshot to feather file at given path
            if is_network:
                feather_fname = f"{snapshot_name}.feather"
                helpers.df_to_feather(
                    feather_path, feather_fname, full_responses, rd_write_feather
                )

        # Flag invalid records
        val.flag_no_rand_spenders(full_responses, "raise")

    else:
        StagingMainLogger.info(
            "Skipping json file staging and validation to read in frozen data..."
        )
        # create empty dataframe to pass to freezing
        full_responses = pd.DataFrame()

        StagingMainLogger.info("Loading postcode mapper")
        # Read in postcode mapper (needed later in the pipeline)
        postcode_mapper = config["mapping_paths"]["postcode_mapper"]
        rd_file_exists(postcode_mapper, raise_error=True)
        postcode_mapper = rd_read_csv(postcode_mapper)

    # Staging of the main snapshot data is now complete
    StagingMainLogger.info("Staging of main snapshot data complete.")
    # run validation on the breakdowns
    # run_breakdown_validation(full_responses, config, "staged")

    if not config["global"]["load_updated_snapshot_for_comparison"]:
        # Staging of the additional data
        if config["global"]["load_manual_outliers"]:
            # Stage the manual outliers file
            StagingMainLogger.info("Loading Manual Outlier File")
            manual_path = staging_dict["manual_outliers_path"]
            rd_file_exists(manual_path, raise_error=True)
            manual_outliers = rd_read_csv(manual_path)
            manual_outliers = manual_outliers.drop_duplicates(
                subset=["reference"], keep="first"
            )
            val.validate_data_with_schema(
                manual_outliers, "./config/manual_outliers_schema.toml"
            )
            StagingMainLogger.info("Manual Outlier File Loaded Successfully...")
        else:
            manual_outliers = None
            StagingMainLogger.info("Loading of Manual Outlier File skipped")

        # Get the latest manual trim file
        manual_trim_path = staging_dict["manual_imp_trim_path"]

        if config["global"]["load_manual_imputation"] and rd_file_exists(
            manual_trim_path
        ):
            StagingMainLogger.info("Loading Imputation Manual Trimming File")
            manual_trim_df = rd_read_csv(manual_trim_path)
            manual_trim_df["manual_trim"] = manual_trim_df["manual_trim"].fillna(False)
            manual_trim_df["instance"] = manual_trim_df["instance"].fillna(1)
            manual_trim_df = manual_trim_df.drop_duplicates(
                subset=["reference", "instance"], keep="first"
            )
            val.validate_data_with_schema(
                manual_trim_df, "./config/manual_trim_schema.toml"
            )
        else:
            manual_trim_df = None
            StagingMainLogger.info("Loading of Imputation Manual Trimming File skipped")

        # stage the backdata for MoR
        StagingMainLogger.info("Loading Backdata File")
        backdata_path = staging_dict["backdata_path"]
        rd_file_exists(backdata_path, raise_error=True)
        backdata = rd_read_csv(backdata_path)
        val.validate_data_with_schema(backdata_path, "./config/backdata_schema.toml")

        StagingMainLogger.info("Backdata File Loaded Successfully...")

        # Loading Civil or Defence detailed mapper
        civil_defence_detailed_mapper = helpers.load_validate_mapper(
            "civil_defence_detailed_mapper_path",
            config,
            StagingMainLogger,
            rd_file_exists,
            rd_read_csv,
        )

        # Loading SIC division detailed mapper
        sic_division_detailed_mapper = helpers.load_validate_mapper(
            "sic_division_detailed_mapper_path",
            config,
            StagingMainLogger,
            rd_file_exists,
            rd_read_csv,
        )

        pg_detailed_mapper = helpers.load_validate_mapper(
            "pg_detailed_mapper_path",
            config,
            StagingMainLogger,
            rd_file_exists,
            rd_read_csv,
        )

        # seaparate PNP data from full_responses (BERD data)
        if stage_frozen_snapshot or stage_updated_snapshot:
            full_responses, pnp_full_responses = helpers.filter_pnp_data(full_responses)

        if config["global"]["output_full_responses"]:
            StagingMainLogger.info("Starting output of staged BERD data...")
            staging_folder = staging_dict["staging_output_path"]
            tdate = datetime.now().strftime("%y-%m-%d")
            survey_year = config["survey"]["survey_year"]
            staged_filename = (
                f"{survey_year}_staged_BERD_full_responses_{tdate}_v{run_id}.csv"
            )
            rd_write_csv(f"{staging_folder}/{staged_filename}", full_responses)
            StagingMainLogger.info("Finished output of staged BERD data.")
        else:
            StagingMainLogger.info("Skipping output of staged BERD data...")

        # Output the staged PNP data.
        if config["global"]["output_pnp_full_responses"]:
            StagingMainLogger.info("Starting output of staged PNP data...")
            staging_folder = staging_dict["pnp_staging_qa_path"]
            tdate = datetime.now().strftime("%y-%m-%d")
            survey_year = config["survey"]["survey_year"]
            staged_filename = (
                f"{survey_year}_staged_PNP_full_responses_{tdate}_v{run_id}.csv"
            )
            rd_write_csv(f"{staging_folder}/{staged_filename}", pnp_full_responses)
            StagingMainLogger.info("Finished output of staged PNP data.")
        else:
            StagingMainLogger.info("Skipping output of staged PNP data...")

        # Return staged BERD data, additional data and mappers
        return (
            full_responses,
            manual_outliers,
            postcode_mapper,
            backdata,
            pg_detailed_mapper,
            civil_defence_detailed_mapper,
            sic_division_detailed_mapper,
            manual_trim_df,
        )

    else:
        return (
            full_responses,
            pd.DataFrame(),
            pd.DataFrame(),
            pd.DataFrame(),
            pd.DataFrame(),
            pd.DataFrame(),
            pd.DataFrame(),
            pd.DataFrame(),
        )
