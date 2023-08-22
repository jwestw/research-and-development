"""The main pipeline"""
# Core Python modules
import time
import logging

# Our local modules
from src.utils import runlog
from src._version import __version__ as version
from src.utils.helpers import Config_settings
from src.utils.wrappers import logger_creator
from src.staging.staging_main import run_staging
from src.imputation.imputation_main import run_imputation
from src.outlier_detection.outlier_main import run_outliers
from src.estimation.estimation_main import run_estimation


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
    from src.utils.local_file_mods import local_file_exists as file_exists
elif network_or_hdfs == "hdfs":
    HDFS_AVAILABLE = True

    from src.utils.hdfs_mods import hdfs_load_json as load_json
    from src.utils.hdfs_mods import hdfs_file_exists as check_file_exists
    from src.utils.hdfs_mods import hdfs_mkdir as mkdir
    from src.utils.hdfs_mods import hdfs_open as open_file
    from src.utils.hdfs_mods import read_hdfs_csv as read_csv
    from src.utils.hdfs_mods import write_hdfs_csv as write_csv
    from src.utils.hdfs_mods import hdfs_file_exists as file_exists
else:
    MainLogger.error("The network_or_hdfs configuration is wrong")
    raise ImportError


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
    run_id = runlog_obj.run_id

    MainLogger.info("Launching Pipeline .......................")
    logger.info("Collecting logging parameters ..........")
    # Data Ingest
    MainLogger.info("Starting Data Ingest...")

    # Load SPP data from DAP

    # Staging and validatation and Data Transmutation
    MainLogger.info("Starting Staging and Validation...")

    full_responses, manual_outliers, pg_mapper, cellno_df = run_staging(
        config, check_file_exists, load_json, read_csv, write_csv, run_id
    )
    MainLogger.info("Finished Data Ingest...")
    print(full_responses.sample(10))
    print(manual_outliers.head())

    # Imputation module
    # MainLogger.info("Starting Imputation...")
    # imputed_df = run_imputation(full_responses, pg_mapper)
    # MainLogger.info("Finished  Imputation...")
    # print(imputed_df.sample(10))

    # Outlier detection module
    MainLogger.info("Starting Outlier Detection...")
    outliered_responses = run_outliers(
        full_responses, config, write_csv, run_id
    )
    print(outliered_responses.sample(10))
    MainLogger.info("Finished Outlier module.")

    # Estimation module
    MainLogger.info("Starting Estimation...")
    run_estimation(outliered_responses, cellno_df)
    MainLogger.info("Finished Estimation module.")

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
