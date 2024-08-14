"""All general functions for the s3 bucket file system which uses boto3.
"""

import boto3
import raz_client
import json
import pandas as pd
from io import StringIO
import logging
from typing import List
import subprocess
import os

from rdsa_utils.cdp.helpers.s3_utils import *

# set up logging
rd_logger = logging.getLogger(__name__)

#########################################################################

working_dir = r"/home/cdsw/research-and-development"
os.chdir(working_dir)
print(os.getcwd())

#########################################################################

from src.utils.wrappers import time_logger_wrap

# set up logging
s3_logger = logging.getLogger(__name__)

#########################################################################
# Load configuration; this could be from a file, environment, etc.
config = {"s3": {
   "ssl_file": "/etc/pki/tls/certs/ca-bundle.crt",
   "s3_bucket": "onscdp-dev-data01-5320d6ca",
}}
#########################################################################
def create_client(config):
    client = boto3.client("s3")
    raz_client.configure_ranger_raz(client, ssl_file=config["s3"]["ssl_file"])
    return client


################################################################################
# Read a CSV file into a Pandas dataframe
def rd_read_csv(filepath: str, **kwargs) -> pd.DataFrame:
    """Reads a csv from s3 bucket into a Pandas Dataframe using pydoop. 
    If "thousands" argument is not specified, sets it to ",". 
    Allows to use any additional keyword arguments of Pandas read_csv method.

    Args:
        filepath (str): Filepath (Specified in config)
        kwargs: Optional dictionary of Pandas read_csv arguments
    Returns:
        pd.DataFrame: Dataframe created from csv
    """
    # Open the boto3 client
    s3_client = config["client"]
    with s3_client.get_object(
        Bucket=config["s3"]["s3_bucket"],
        Key=filepath
    )['Body'] as file:
        
        # If "thousands" argument is not specified, set it to ","
        if "thousands" not in kwargs:
            kwargs["thousands"] = ","

        # Read the scv file using the path and keyword arguments
        try:
            df = pd.read_csv(file, **kwargs)
        except Exception:
            if "usecols" in kwargs:
                rd_logger.info("Columns not found: " + str(kwargs["usecols"]))
            rd_logger.error(f"Could not read specified file: {filepath}")

            raise ValueError
    return df
  

###############################################################################

s3_client = create_client(config)
config["client"] = s3_client

###############################################################################
#mypath = 'user/george.zorinyants/pg_num_alpha_2023.csv'
#mydf = rd_read_csv(mypath, usecols=["coutry"])
#mydf.head()

def rd_write_csv(filepath: str, data: pd.DataFrame) -> None:
    """Writes a Pandas Dataframe to csv in s3 bucket

    Args:
        filepath (str): Filepath (Specified in config)
        data (pd.DataFrame): Data to be stored
    """
    # Create an Unput-Output buffer
    csv_buffer = StringIO()
    
    # Write the dataframe to the buffer in the CSV format 
    df.to_csv(csv_buffer, header=True, date_format="%Y-%m-%d %H:%M:%S.%f+00", index=False)
    
    # "Rewind" the stream to the start of the buffer
    csv_buffer.seek(0) 
    
    # Use the boto3 client from the config
    s3_client = config["client"]
    
    # Write the buffer into the s3 bucket
    _ = s3_client.put_object(
        Bucket=config["s3"]["s3_bucket"], 
        Body=csv_buffer.getvalue(), 
        Key=filepath
    )
    return None

# Create a dataframe and write to a CSV file
#my_data = {"coutry": ["a", "b"], "value": [1, 2]}
#df = pd.DataFrame(my_data)
#df.head()
#mypath = "user/george.zorinyants/test2_rd_write.csv"
#rd_write_csv(mypath, df)


def rd_load_json(filepath: str) -> dict:
    """Function to load JSON data from s3 bucket
    Args:
        filepath (string): The filepath in Hue
    """
    # Use the boto3 client from the config
    s3_client = config["client"]
    
    # Load the json file using the client method
    with s3_client.get_object(Bucket=config["s3"]["s3_bucket"], Key=filepath)['Body'] as json_file:
        datadict = json.load(json_file)
    
    return datadict

mypath = "user/george.zorinyants/snapshot.json"
mydict = rd_load_json(mypath)
print(mydict)

# def hdfs_file_exists(filepath: str, raise_error=False) -> bool:
#     """Function to check file exists in hdfs.

#         Args:
#             filepath (string) -- The filepath in Hue

#         Returns:
#             Bool - A boolean value which is true if file exists
#     .
#     """

#     file_exists = hdfs.path.exists(filepath)

#     if not file_exists and raise_error:
#         raise FileExistsError(f"File: {filepath} does not exist")

#     return file_exists


# def hdfs_file_size(filepath: str) -> int:
#     """Function to check the size of a file on hdfs.

#     Args:
#         filepath (string) -- The filepath in Hue

#     Returns:
#         Int - an integer value indicating the size
#         of the file in bytes
#     """
#     file_size = hdfs.path.getsize(filepath)

#     return file_size


# def check_file_exists(filepath) -> bool:
#     """Checks if file exists in hdfs and is non-empty.

#     If the file exists but is empty, a warning is logged.

#     Args:
#         filepath (str): The filepath of the file to check.

#     Returns:
#         bool: True if the file exists and is non-empty, False otherwise.

#     Raises: a FileNotFoundError if the file doesn't exist.
#     """
#     output = False

#     file_exists = hdfs_file_exists(filepath)

#     # If the file exists on hdfs, check the size of it.
#     if file_exists:
#         file_size = hdfs_file_size(filepath)

#     if not file_exists:
#         raise FileNotFoundError(f"File {filepath} does not exist.")

#     if file_exists and file_size > 0:
#         output = True
#         hdfs_logger.info(f"File {filepath} exists and is non-empty")

#     elif file_exists and file_size == 0:
#         output = False
#         hdfs_logger.warning(f"File {filepath} exists on HDFS but is empty")

#     return output


# def hdfs_mkdir(path):
#     """Function to create a directory in HDFS

#     Args:
#         path (string) -- The path to create
#     """
#     hdfs.mkdir(path)
#     return None


# def hdfs_open(filepath, mode):
#     """Function to open a file in HDFS

#     Args:
#         filepath (string) -- The filepath in Hue
#         mode (string) -- The mode to open the file in
#     """
#     file = hdfs.open(filepath, mode)
#     return file


# @time_logger_wrap
# def hdfs_write_feather(filepath, df):
#     """Function to write dataframe as feather file in HDFS"""
#     with hdfs.open(filepath, "wb") as file:
#         df.to_feather(file)
#     # Check log written to feather
#     hdfs_logger.info(f"Dataframe written to {filepath} as feather file")

#     return True


# @time_logger_wrap
# def hdfs_read_feather(filepath):
#     """Function to read feather file from HDFS"""
#     with hdfs.open(filepath, "rb") as file:
#         df = pd.read_feather(file)
#     # Check log written to feather
#     hdfs_logger.info(f"Dataframe read from {filepath} as feather file")

#     return df


# def _perform(
#     command,
#     shell: bool = False,
#     str_output: bool = False,
#     ignore_error: bool = False,
#     full_out=False,
# ):
#     """
#     Run shell command in subprocess returning exit code or full string output.
#     _perform() will build the command that will be put into HDFS.
#     This will also be used for the functions below.
#     Parameters
#     ----------
#     shell
#         If true, the command will be executed through the shell.
#         See subprocess.Popen() reference.
#     str_output
#         output exception as string
#     ignore_error
#     """
#     process = subprocess.Popen(
#         command, shell=shell, stdout=subprocess.PIPE, stderr=subprocess.PIPE
#     )
#     stdout, stderr = process.communicate()

#     if str_output:
#         if stderr and not ignore_error:
#             raise Exception(stderr.decode("UTF-8").strip("\n"))
#         if full_out:
#             return stdout
#         return stdout.decode("UTF-8").strip("\n")

#     return process.returncode == 0


# def hdfs_delete_file(path: str):
#     """
#     Delete a file. Uses 'hadoop fs -rm'.

#     Returns
#     -------
#     True for successfully completed operation. Else False.
#     """
#     command = ["hadoop", "fs", "-rm", path]
#     return _perform(command)


# def hdfs_md5sum(path: str):
#     """
#     Get md5sum of a specific file on HDFS.
#     """
#     return _perform(
#         f"hadoop fs -cat {path} | md5sum",
#         shell=True,
#         str_output=True,
#         ignore_error=True,
#     ).split(" ")[0]


# def hdfs_stat_size(path: str):
#     """
#     Runs stat command on a file or directory to get the size in bytes.
#     """
#     command = ["hadoop", "fs", "-du", "-s", path]
#     return _perform(command, str_output=True).split(" ")[0]


# def hdfs_isdir(path: str) -> bool:
#     """
#     Test if directory exists. Uses 'hadoop fs -test -d'.

#     Returns
#     -------
#     True for successfully completed operation. Else False.
#     """
#     command = ["hadoop", "fs", "-test", "-d", path]
#     return _perform(command)


# def hdfs_isfile(path: str) -> bool:
#     """
#     Test if file exists. Uses 'hadoop fs -test -f.

#     Returns
#     -------
#     True for successfully completed operation. Else False.

#     Note
#     ----
#     If checking that directory with partitioned files (i.e. csv, parquet)
#     exists this will return false use isdir instead.
#     """
#     if path is None:
#         return False

#     command = ["hadoop", "fs", "-test", "-f", path]
#     return _perform(command)


# def hdfs_read_header(path: str):
#     """
#     Reads the first line of a file on HDFS
#     """
#     return _perform(
#         f"hadoop fs -cat {path} | head -1",
#         shell=True,
#         str_output=True,
#         ignore_error=True,
#     )


# def hdfs_write_string_to_file(content: bytes, path: str):
#     """
#     Writes a string into the specified file path
#     """
#     _write_string_to_file = subprocess.Popen(
#         f"hadoop fs -put - {path}", stdin=subprocess.PIPE, shell=True
#     )
#     return _write_string_to_file.communicate(content)


# def hdfs_copy_file(src_path: str, dst_path: str):
#     """
#     Copy a file from one location to another. Uses 'hadoop fs -cp'.
#     """
#     command = ["hadoop", "fs", "-cp", src_path, dst_path]
#     return _perform(command)


# def hdfs_move_file(src_path: str, dst_path: str):
#     """
#     Move a file from one location to another. Uses 'hadoop fs -mv'.
#     """
#     command = ["hadoop", "fs", "-mv", src_path, dst_path]
#     return _perform(command)


# def hdfs_list_files(path: str, ext: str = None, order=None):
#     """
#     List files in a directory. Uses 'hadoop fs -ls'.
#     """
#     # Forming the command line command and executing
#     command = ["hadoop", "fs", "-ls", path]
#     if order:
#         ord_dict = {"newest": "-t", "oldest": "-t -r"}
#         command = ["hadoop", "fs", "-ls", ord_dict[order], path]
#     files_as_str = _perform(command, str_output=True)

#     # Breaking up the returned string, and stripping down to just paths of files
#     file_paths = [line.split()[-1] for line in files_as_str.strip().split("\n")[1:]]

#     # Filtering the files to just those with the required extension
#     if ext:
#         ext = f".{ext}"
#         file_paths = [file for file in file_paths if os.path.splitext(file)[1] == ext]

#     return file_paths


# def hdfs_search_file(dir_path, ending):
#     """Find a file in a directory with a specific ending using grep and hadoop fs -ls.

#     Args:
#         dir_path (_type_): _description_
#         ending (_type_): _description_
#     """
#     target_file = _perform(
#         f"hadoop fs -ls {dir_path} | grep {ending}",
#         shell=True,
#         str_output=True,
#         ignore_error=True,
#     )

#     # Handle case where file does not exist
#     if not target_file:
#         raise FileNotFoundError(
#             f"File with ending {ending} does not exist in {dir_path}"
#         )

#     # Return file path + name
#     target_file = target_file.split()[-1]

#     return target_file
