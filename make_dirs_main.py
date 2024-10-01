"""Script that creates all directories"""
# import os

# from importlib import reload

from src.utils.helpers import tree_to_list
import src.utils.s3_mods as mods
from src.utils.singleton_boto import SingletonBoto

# boto3_client = mods.create_client(config)
boto3_client = SingletonBoto.get_client()


def run_make_dirs():
    # root = "s3a://onscdp-dev-data01-5320d6ca/bat/res_dev/project_data"

    global config
    root = "/user/anne.griffith/res_dev/2022_surveys"
    # root = "/bat/res_dev/project_data"

    tree = {
        "BERD": {
            "01_staging": {
                "feather": {},
                "staging_qa": {
                    "full_responses_qa": {},
                    "postcode_validation": {},
                    "Postcodes for QA": {},
                },
            },
            "02_freezing": {
                "changes_to_review": {},
                "freezing_updates": {},
                "frozen_data_staged": {},
            },
            "03_northern_ireland": {
                "2021": {},
                "ni_staging_qa": {},
            },
            "04_construction": {
                "manual_construction": {},
            },
            "05_mapping": {
                "mapping_qa": {},
            },
            "06_imputation": {
                "backdata_output": {},
                "imputation_qa": {},
                "manual_trimming": {},
            },
            "07_outliers": {
                "auto_outliers": {},
                "manual_outliers": {},
                "outliers_qa": {},
            },
            "08_estimation": {
                "estimation_qa": {},
            },
            "09_apportionment": {
                "apportionment_qa": {},
            },
            "10_outputs": {
                "output_fte_total_qa": {},
                "output_gb_sas": {},
                "output_intram_totals": {},
                "output_intram_by_civil_defence": {},
                "output_intram_by_pg_gb": {},
                "output_intram_by_pg_uk": {},
                "output_intram_by_sic": {},
                "output_intram_gb_itl1": {},
                "output_intram_gb_itl2": {},
                "output_intram_uk_itl1": {},
                "output_intram_uk_itl2": {},
                "output_long_form": {},
                "output_ni_sas": {},
                "output_short_form": {},
                "output_status_filtered_qa": {},
                "output_tau": {},
            },
        },
        "mappers": {
            "v1": {},
        },
        "PNP": {
            "01_staging": {},
        },
    }

    dir_list = tree_to_list(tree, path_list=[],prefix=root)
    for s in dir_list:
        print(s)
        mods.rd_mkdir(s)


if __name__ == "__main__":
    run_make_dirs()
