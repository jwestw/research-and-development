"""The main pipeline"""
# Core Python modules
import time
import logging

# Our local modules
from src.utils import runlog
from src._version import __version__ as version
from src.utils.helpers import Config_settings
from src.utils.wrappers import logger_creator
from src.staging import spp_parser, history_loader
from src.staging import spp_snapshot_processing as processing
from src.staging import validation as val
from src.staging.staging_main import run_staging


MainLogger = logging.getLogger(__name__)


# load config
conf_obj = Config_settings()
config = conf_obj.config_dict

# Check the environment switch
network_or_hdfs = config["global"]["network_or_hdfs"]


if network_or_hdfs == "network":
    HDFS_AVAILABLE = False

    from src.utils.local_file_mods import load_local_json as load_json
    from src.utils.local_file_mods import local_file_exists as check_file_exists
    from src.utils.local_file_mods import local_mkdir as mkdir
    from src.utils.local_file_mods import local_open as open_file
    from src.utils.local_file_mods import read_local_csv as read_csv
    from src.utils.local_file_mods import write_local_csv as write_csv

elif network_or_hdfs == "hdfs":
    HDFS_AVAILABLE = True

    from src.utils.hdfs_mods import hdfs_load_json as load_json
    from src.utils.hdfs_mods import hdfs_file_exists as check_file_exists
    from src.utils.hdfs_mods import hdfs_mkdir as mkdir
    from src.utils.hdfs_mods import hdfs_open as open_file
    from src.utils.hdfs_mods import read_hdfs_csv as read_csv
    from src.utils.hdfs_mods import write_hdfs_csv as write_csv

else:
    MainLogger.error("The network_or_hdfs configuration is wrong")
    raise ImportError

# Conditionally load paths
paths = config[f"{network_or_hdfs}_paths"]


def run_pipeline(start):
    """The main pipeline.

    Args:
        start (float): The time when the pipeline is launched
        generated from the time module using time.time()
    """
    # Set up the run logger
    global_config = config["global"]
    runlog_obj = runlog.RunLog(
        config, version, open_file, check_file_exists, mkdir, read_csv, write_csv
    )

    logger = logger_creator(global_config)
    MainLogger.info("Launching Pipeline .......................")
    logger.info("Collecting logging parameters ..........")
    # Data Ingest
    MainLogger.info("Starting Data Ingest...")

    # Load historic data
    curent_year = config["years"]["current_year"]
    years_to_load = config["years"]["previous_years_to_load"]
    years_gen = history_loader.history_years(curent_year, years_to_load)

    if years_gen is None:
        MainLogger.info("No historic data to load for this run.")
    else:
        MainLogger.info("Loading historic data...")
        history_path = paths["history_path"]
        dict_of_hist_dfs = history_loader.load_history(
            years_gen, history_path, read_csv
        )
        if isinstance(dict_of_hist_dfs, dict):
            MainLogger.info(
                "Dictionary of history data: %s loaded into pipeline",
                ", ".join(dict_of_hist_dfs),
            )
            MainLogger.info("Historic data loaded.")

    # Load SPP data from DAP

    # Staging and validatation
    MainLogger.info("Starting Staging and Validation...")
    full_responses = run_staging(config, check_file_exists, load_json)
    # Check data file exists
    snapshot_path = paths["snapshot_path"]
    check_file_exists(snapshot_path)

    snapdata = load_json(snapshot_path)
    contributors_df, responses_df = spp_parser.parse_snap_data(snapdata)
    MainLogger.info("Finished Data Ingest...")

    # Data Transmutation
    MainLogger.info("Starting Data Transmutation...")
    full_responses = processing.full_responses(contributors_df, responses_df)
    print(full_responses.sample(5))

    # Load SPP data from

    # Check the postcode column
    postcode_masterlist = paths["postcode_masterlist"]
    val.validate_post_col(contributors_df, postcode_masterlist)

    # Outlier detection

    # Data cleaning

    # Data processing: Imputation

    # Data processing: Estimation

    # Data processing: Regional Apportionment

    # Data processing: Aggregation

    # Data display: Visualisations

    # Data output: Disclosure Control

    # Data output: File Outputs

    MainLogger.info("Finishing Pipeline .......................")

    runlog_obj.retrieve_pipeline_logs()

    run_time = round(time.time() - start, 5)
    runlog_obj._record_time_taken(run_time)

    runlog_obj.retrieve_configs()
    runlog_obj._create_runlog_dicts()
    runlog_obj._create_runlog_dfs()
    runlog_obj.create_runlog_files()
    runlog_obj._write_runlog()
