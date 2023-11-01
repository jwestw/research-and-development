"""This is a stand alone pipeline to selectively transfer output files from
the output folder to the outgoing folder, along with their manifest file."""


import os
import logging
from datetime import datetime
import toml
from typing import List
from pathlib import Path

from src.utils.helpers import Config_settings
from src.outputs.manifest_output import Manifest


# Set up logging
OutgoingLogger = logging.getLogger(__name__)


config_path = os.path.join("src", "developer_config.yaml")

# Load config
conf_obj = Config_settings(config_path)
config = conf_obj.config_dict

# Get logging level
logging_level = config["logging_level"]

# Check the environment switch
network_or_hdfs = config["global"]["network_or_hdfs"]

if network_or_hdfs == "network":

    from src.utils.local_file_mods import local_move_file as move_files
    from src.utils.local_file_mods import local_copy_file as copy_files
    from src.utils.local_file_mods import local_search_file as search_files
    from src.utils.local_file_mods import local_isfile as isfile
    from src.utils.local_file_mods import local_delete_file as delete_file
    from src.utils.local_file_mods import local_md5sum as hdfs_md5sum
    from src.utils.local_file_mods import local_stat_size as hdfs_stat_size
    from src.utils.local_file_mods import local_isdir as isdir
    from src.utils.local_file_mods import local_read_header as read_header
    from src.utils.local_file_mods import (
        local_write_string_to_file as write_string_to_file,
    )

elif network_or_hdfs == "hdfs":

    from src.utils.hdfs_mods import hdfs_move_file as move_files
    from src.utils.hdfs_mods import hdfs_copy_file as copy_files
    from src.utils.hdfs_mods import hdfs_search_file as search_files
    from src.utils.hdfs_mods import hdfs_isfile as isfile
    from src.utils.hdfs_mods import hdfs_delete_file as delete_file
    from src.utils.hdfs_mods import hdfs_md5sum as hdfs_md5sum
    from src.utils.hdfs_mods import hdfs_stat_size as hdfs_stat_size
    from src.utils.hdfs_mods import hdfs_isdir as isdir
    from src.utils.hdfs_mods import hdfs_read_header as read_header
    from src.utils.hdfs_mods import hdfs_write_string_to_file as write_string_to_file


else:
    OutgoingLogger.error("The network_or_hdfs configuration is wrong")
    raise ImportError

OutgoingLogger.info(f"Using the {network_or_hdfs} file system as data source.")


# Define paths
paths = config[f"{network_or_hdfs}_paths"]
output_path = paths["output_path"]
export_folder = paths["export_path"]


def get_schema_headers(file_path_dict: dict, paths: dict = paths):

    schema_paths = {
        output_name: path
        for output_name, path in paths.items()
        if "schema" in output_name
    }

    # Get the headers for each
    schema_headers_dict = {
        output_name: toml.load(path) for output_name, path in schema_paths.items()
    }

    # Stringify the headers (keys of the dict)
    schema_headers_dict.update(
        {
            output_name: ",".join(keys)
            for output_name, keys in schema_headers_dict.items()
        }
    )

    return schema_headers_dict


# Create a datetime object for the pipeline run - TODO: replace this with
# the pipeline run datetime from the runlog object
pipeline_run_datetime = datetime.now()


def get_file_choice(paths, config: dict = config):
    """Get files to transfer from the 'export_choices' section of the config.

    Returns:
        selection_list (list): A list of the files to transfer."""

    # Get the user's choices from config
    output_paths = {
        output_name: path
        for output_name, path in config["export_choices"].items()
        if "output" in output_name
    }

    root_output = paths["output_path"]

    # Use dictionary comprehension to create the selection list dict
    selection_dict = {
        dir[7:]: Path(f"{root_output}/{dir}/{file}").with_suffix(".csv")
        for dir, file in output_paths.items()
        if file is not None
    }

    # Log the files being exported
    logging.info(f"These are the files being exported: {selection_dict.values()}")

    return selection_dict


def check_files_exist(file_list: List):
    """Check that all the files in the file list exist using
    the imported isfile function."""

    # Check if the output dirs supplied are string, change to list if so
    if isinstance(file_list, str):
        file_list = [file_list]

    # Check the existence of every file using is_file
    for file in file_list:
        file_path = Path(file)  # Changes to path if str
        if not file_path.is_file():
            OutgoingLogger.error(
                f"File {file} does not exist. Check existence and spelling"
            )
            raise FileNotFoundError
    OutgoingLogger.info("All output files exist")


def run_export(paths=paths, config=config):
    """Main function to run the data export pipeline."""

    # Get list of files to transfer from user
    file_select_dict = get_file_choice(paths, config)

    # Check that files exist
    check_files_exist(list(file_select_dict.values()))

    # Creating a manifest object using the Manifest class in manifest_output.py
    manifest = Manifest(
        outgoing_directory=output_path,
        export_directory=export_folder,
        pipeline_run_datetime=pipeline_run_datetime,
        dry_run=False,
        delete_file_func=delete_file,
        md5sum_func=hdfs_md5sum,
        stat_size_func=hdfs_stat_size,
        isdir_func=isdir,
        isfile_func=isfile,
        read_header_func=read_header,
        string_to_file_func=write_string_to_file,
    )

    schemas_header_dict = get_schema_headers(file_select_dict, paths)

    # Add the short form output file to the manifest object
    for file_name, file_path in file_select_dict.items():
        manifest.add_file(
            file_path,
            column_header=schemas_header_dict[f"{file_name}_schema"],
            validate_col_name_length=True,
            sep=",",
        )

    # Write the manifest file to the outgoing directory
    manifest.write_manifest()

    # Move the manifest file to the outgoing folder
    manifest_file = search_files(manifest.outgoing_directory, "_manifest.json")

    manifest_path = os.path.join(manifest.outgoing_directory, manifest_file)
    move_files(manifest_path, manifest.export_directory)
    OutgoingLogger.info(
        f"Files {manifest_path} successfully moved to {manifest.export_directory}."
    )

    # Copy or Move files to outgoing folder
    c_m_choice = config["export_choices"]["copy_or_move_files"]
    copy_move_func = {"copy": copy_files, "move": move_files}[c_m_choice]

    for file_path in file_select_dict.values():
        file_path = os.path.join(file_path)
        copy_move_func(file_path, manifest.export_directory)

        # Log success message
        OutgoingLogger.info(
            f"Files {file_path} transferred successfully using {c_m_choice}."
        )

    OutgoingLogger.info("Exporting files finished.")


if __name__ == "__main__":
    run_export()
