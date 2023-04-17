from datetime import datetime
import pandas as pd
import os
from src.utils.helpers import Config_settings
from src.utils.hdfs_mods import hdfs_csv_creator, read_hdfs_csv, write_hdfs_csv
import pydoop.hdfs as hdfs


conf_obj = Config_settings()
config = conf_obj.config_dict
csv_filenames = config["csv_filenames"]

context = os.getenv("HADOOP_USER_NAME")  # Put your context name here
project = config["logs_foldername"]  # Taken from config file
main_path = f"/user/{context}/{project}"
hdfs.mkdir(main_path)


class RunLog:
    """Creates a runlog instance for the pipeline."""

    def __init__(self, config, version):
        self.config = config
        self.run_id = self._create_run_id()
        self.version = version
        self.logs = []
        self.timestamp = self._generate_time()

    def _create_run_id(self):
        """Create a unique run_id from the previous iteration"""
        # Import name of main log file
        runid_path = csv_filenames["main"]
        mainfile = f"{main_path}/{runid_path}"
        # Check if it exists in Hadoop context
        if hdfs.path.isfile(mainfile):
            # Open in read mode
            with hdfs.open(mainfile, "r") as file:
                # Find the latest run_id from Dataframe
                runfile = pd.read_csv(file)
                latest_id = max(runfile.run_id)
        else:
            # If no run_id is present then start from 1
            latest_id = 0
        run_id = latest_id + 1

        return run_id

    def _record_time_taken(self, time_taken):
        """Get the time taken for the pipeline to run.

        This is for the total pipeline run time, not the time taken for each step.

        """

        self.time_taken = time_taken

        return self.time_taken

    def retrieve_pipeline_logs(self):
        """
        Get all of the logs from the pipeline run
        and append them to self.logs list

        """
        f = open("logs/main.log", "r")
        lines = f.read().splitlines()
        self.logs.append(lines)

        return self

    def _generate_time(self):
        """Generate unqiue timestamp for when each run"""
        timestamp = datetime.now().strftime("%d/%m/%Y-%H:%M:%S")

        return timestamp

    def _create_runlog_dicts(self):
        """Create unique dictionaries for runlogs, configs
        and loggers with run_id as identifier"""

        self.runlog_main_dict = {
            "run_id": self.run_id,
            "timestamp": self.timestamp,
            "version": self.version,
            "duration": self.time_taken,
        }

        self.runlog_configs_dict = {
            "run_id": self.run_id,
            "configs": self.config,
        }

        self.runlog_logs_dict = {
            "run_id": self.run_id,
            "logs": self.logs,
        }

        return self

    def _create_runlog_dfs(self):
        """Convert dictionaries to pandas dataframes."""

        self.runlog_main_df = pd.DataFrame(
            [self.runlog_main_dict],
            columns=["run_id", "timestamp", "version", "duration"],
        )
        self.runlog_configs_df = pd.DataFrame(
            [self.runlog_configs_dict], columns=["run_id", "configs"]
        )
        self.runlog_logs_df = pd.DataFrame(
            [self.runlog_logs_dict], columns=["run_id", "logs"]
        )

        return self

    def _get_runlog_settings(self):

        """Get the runlog settings from the config file."""
        runlog_settings = self.config["runlog_writer"]
        write_csv = runlog_settings["write_csv"]
        write_hdf5 = runlog_settings["write_hdf5"]
        write_sql = runlog_settings["write_sql"]

        return write_csv, write_hdf5, write_sql

    def create_runlog_files(self):
        """Creates csv files with column names
        if they don't already exist.
        """

        main_columns = ["run_id", "timestamp", "version", "duration"]
        file_name = csv_filenames["main"]
        file_path = f"{main_path}/{file_name}"
        hdfs_csv_creator(file_path, main_columns)

        config_columns = ["run_id", "configs"]
        file_name = csv_filenames["configs"]
        file_path = f"{main_path}/{file_name}"
        hdfs_csv_creator(file_path, config_columns)

        log_columns = ["run_id", "logs"]
        file_name = csv_filenames["logs"]
        file_path = f"{main_path}/{file_name}"
        hdfs_csv_creator(file_path, log_columns)

        return None

    def _write_runlog(self):
        """Write the runlog to a file specified in the config."""

        # Get the runlog settings from the config file
        write_csv, write_hdf5, write_sql = self._get_runlog_settings()

        if write_csv:
            # write the runlog to a csv file

            file_name = csv_filenames["main"]
            file_path = f"{main_path}/{file_name}"
            df = read_hdfs_csv(file_path)
            newdf = df.append(self.runlog_main_df)
            write_hdfs_csv(file_path, newdf)

            file_name = csv_filenames["configs"]
            file_path = f"{main_path}/{file_name}"
            df = read_hdfs_csv(file_path)
            newdf = df.append(self.runlog_configs_df)
            write_hdfs_csv(file_path, newdf)

            file_name = csv_filenames["logs"]
            file_path = f"{main_path}/{file_name}"
            df = read_hdfs_csv(file_path)
            newdf = df.append(self.runlog_logs_df)
            write_hdfs_csv(file_path, newdf)

        if write_hdf5:
            # write the runlog to a hdf5 file
            self.runlog_main_df.to_hdf(
                "main_runlog.hdf", mode="a", index=False, header=False
            )
            self.runlog_configs_df.to_hdf(
                "configs_runlog.hdf", mode="a", index=False, header=False
            )
            self.runlog_logs_df.to_hdf(
                "logs_runlog.hdf", mode="a", index=False, header=False
            )
        if write_sql:
            # write the runlog to a sql database
            self.runlog_main_df.to_sql(
                "main_runlog.sql", mode="a", index=False, header=False
            )
            self.runlog_configs_df.to_sql(
                "configs_runlog.sql", mode="a", index=False, header=False
            )
            self.runlog_logs_df.to_sql(
                "logs_runlog.sql", mode="a", index=False, header=False
            )

        return None
