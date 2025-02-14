"""Tests for path_helpers.py """
import pytest
import logging

from src.utils.path_helpers import (
    get_paths,
    create_staging_config,
    create_ni_staging_config,
    create_construction_config,
    create_mapping_config,
    create_module_config,
    create_exports_config,
    update_config_with_paths,
    snapshot_validation,
    snapshot_validation_logger
)


@pytest.fixture(scope="module")
def config():
    config = {
        "global": {"platform": "network"},
        "network_paths": {
            "root": "R:/DAP_emulation/",
            "snapshot_path": "/2023_snapshots/snapshot_file-202212.json",
            "updated_snapshot_path": "2023_snapshots/updated_snapshot_file-202212.json",
            "postcode_masterlist": "postcode_masterlist_path/postcode.csv",
            "ni_full_responses_path": "03_northern_ireland/2021/TEST_ni.csv",
            "manual_imp_trim_path": "06_imputation/man_trim/trim_qa.csv",
            "manual_outliers_path": "07_outliers/man_out/man_out.csv",
            "backdata_path": "2021_data/backdata.csv",
            "all_data_construction_file_path": (
                "04_construction/man_con/construction_file.csv"
            ),
            "postcode_construction_file_path": (
                "04_construction/man_con/postcode_construction_file.csv"
            ),
            "construction_file_path_ni": "04_construction/man_con/con_file_ni.csv",
            "frozen_data_staged_path": "02_freezing/frozen_data_staged/staged.csv",
            "freezing_changes_to_review_path": "02_freezing/changes_to_review/review.csv",
            "freezing_amendments_path": "02_freezing/freezing_updates/updates.csv",
            "freezing_additions_path": "02_freezing/freezing_updates/additions.csv",
        },
        "survey": {
            "survey_type": "BERD",
            "survey_year": 2022
        },
        "staging_paths": {
            "folder": "01_staging",
            "feather_output": "feather",
        },
        "ni_paths": {
            "folder": "03_northern_ireland",
            "ni_staging_output_path": "ni_staging_qa",
        },
        "construction_paths": {
            "folder": "04_construction",
            "qa_path": "construction_qa",
        },
        "freezing_paths": {
            "folder": "02_freezing",
            "frozen_data_staged_path": "frozen_data_staged",
            "freezing_changes_to_review_path": "changes_to_review",
            "freezing_amendments_path": "freezing_updates",
            "freezing_additions_path": "freezing_updates",
        },
        "2022_mappers": {
            "mappers_version": "v1",
            "postcode_mapper": "pcodes_2022.csv",
            "itl_mapper_path": "itl_2022.csv",
        },
        "mapping_paths": {
            "folder": "05_mapping",
            "qa_path": "mapping_qa",
        },
        "imputation_paths": {
            "folder": "06_imputation",
            "qa_path": "imputation_qa",
            "manual_trimming_path": "manual_trimming",
        },
        "outliers_paths": {
            "folder": "07_outliers",
            "qa_path": "outliers_qa",
            "auto_outliers_path": "auto_outliers",
        },
        "pnp_paths": {"staging_qa_path" : "01_staging/pnp_staging_qa"},
        "export_paths": {"export_folder": "outgoing_export"},

    }
    return config


def test_get_paths(config):
    """Test get_paths function."""
    expected_network_paths = {
        "root": "R:/DAP_emulation/",
        "snapshot_path": "/2023_snapshots/snapshot_file-202212.json",
        "updated_snapshot_path": "2023_snapshots/updated_snapshot_file-202212.json",
        "postcode_masterlist": "postcode_masterlist_path/postcode.csv",
        "ni_full_responses_path": "03_northern_ireland/2021/TEST_ni.csv",
        "manual_outliers_path": "07_outliers/man_out/man_out.csv",
        "manual_imp_trim_path": "06_imputation/man_trim/trim_qa.csv",
        "backdata_path": "2021_data/backdata.csv",
        "all_data_construction_file_path": (
            "04_construction/man_con/construction_file.csv"
        ),
        "postcode_construction_file_path": (
            "04_construction/man_con/postcode_construction_file.csv"
        ),
        "construction_file_path_ni": "04_construction/man_con/con_file_ni.csv",
        "frozen_data_staged_path": "02_freezing/frozen_data_staged/staged.csv",
        "freezing_changes_to_review_path": "02_freezing/changes_to_review/review.csv",
        "freezing_amendments_path": "02_freezing/freezing_updates/updates.csv",
        "freezing_additions_path": "02_freezing/freezing_updates/additions.csv",
        "year": 2022,
        "berd_path": "R:/DAP_emulation/2022_surveys/BERD/",
        "pnp_path": "R:/DAP_emulation/2022_surveys/PNP/",
    }
    network_paths = get_paths(config)

    assert network_paths == expected_network_paths, "Network paths are not as expected"


@pytest.fixture(scope="module")
def expected_staging_dict():
    expected_staging_dict = {
        "feather_output": "R:/DAP_emulation/2022_surveys/BERD/01_staging/feather",
        "snapshot_path": "/2023_snapshots/snapshot_file-202212.json",
        "updated_snapshot_path": "2023_snapshots/updated_snapshot_file-202212.json",
        "postcode_masterlist": "postcode_masterlist_path/postcode.csv",
        "manual_outliers_path": (
            "R:/DAP_emulation/2022_surveys/BERD/07_outliers/man_out/man_out.csv"
        ),
        "manual_imp_trim_path": (
            "R:/DAP_emulation/2022_surveys/BERD/06_imputation/man_trim/trim_qa.csv"
        ),
        "backdata_path": "2021_data/backdata.csv",
        "pnp_staging_qa_path": (
            "R:/DAP_emulation/2022_surveys/PNP/01_staging/pnp_staging_qa"
        ),
    }
    return expected_staging_dict


def test_create_staging_config(config, expected_staging_dict):
    """Test create_staging_config function."""

    staging_dict = create_staging_config(config)

    assert staging_dict == expected_staging_dict, "Staging config is not as expected"


def test_validate_snapshot_files_success(config, caplog):
    """Tests for staging_validation function."""
    config = {'survey' : {'survey_year': 2023,},
              'global': {'platform': "network"},
              'network_paths': { 'root': "R:/DAP_emulation/",
              'snapshot_path': "/2023_snapshots/snapshot_file-202312.json",
              'updated_snapshot_path': '2023_snapshots/updated_snapshot_file-202312.json',
              }
        }

    msg = 'The snapshot paths are valid.'
    with caplog.at_level(logging.INFO):
        snapshot_validation_logger(config)
        assert msg in caplog.text

def test_validate_snapshot_files_fail(config, caplog):
    """Tests for staging_validation function."""
    config = {

        'survey' : {'survey_year': 2023,},
              'global': {'platform': "network"},
              'network_paths': {'root': "R:/BERD Results System Development 2023/DAP_emulation/",
              'snapshot_path': "/ons/rdbe_dev/spp_snapshots/2023_snapshots/snapshot-20212-002-b9b6048a-51c9-4669-919a-e92fc6e9c433.json",
              'updated_snapshot_path': '/ons/rdbe_dev/berd_survey/anonymised/v1/snapshot-202312-002.json',
              }
        }

    msg = "2023 is not included in the frozen snapshot path.\n"
    with pytest.raises(ValueError, match=msg):
        snapshot_validation_logger(config)



def test_validate_snapshot_files_success_blank(config, caplog):
    """Tests for staging_validation function."""
    config = {

        'survey' : {'survey_year': 2023,},
              'global': {'platform': "network"},
              'network_paths': {'root': "R:/BERD Results System Development 2023/DAP_emulation/",
              'snapshot_path': "/ons/rdbe_dev/spp_snapshots/2023_snapshots/snapshot-202312-002-b9b6048a-51c9-4669-919a-e92fc6e9c433.json",
              'updated_snapshot_path': "",
              }
        }

    msg = 'The snapshot paths are valid.\n'
    with caplog.at_level(logging.INFO):
        snapshot_validation_logger(config)
        assert msg in caplog.text




def test_create_ni_staging_config(config):
    """Test create_ni_staging_config function."""

    expected_ni_staging_dict = {
        "ni_full_responses": (
            "R:/DAP_emulation/2022_surveys/BERD/03_northern_ireland/2021/TEST_ni.csv"
        ),
        "ni_staging_output_path": (
            "R:/DAP_emulation/2022_surveys/BERD/03_northern_ireland/ni_staging_qa"
        ),
    }
    ni_staging_dict = create_ni_staging_config(config)

    assert ni_staging_dict == expected_ni_staging_dict, "NI config is not as expected"


def test_create_mapping_config(config):
    """Test create_mapping_config function."""

    expected_mapping_dict = {
        "postcode_mapper": "R:/DAP_emulation/2022_surveys/mappers/v1/pcodes_2022.csv",
        "itl_mapper_path": "R:/DAP_emulation/2022_surveys/mappers/v1/itl_2022.csv",
        "qa_path": "R:/DAP_emulation/2022_surveys/BERD/05_mapping/mapping_qa",
    }
    mapping_dict = create_mapping_config(config)

    assert mapping_dict == expected_mapping_dict, "Mapping config is not as expected"


def test_create_construction_config(config):
    """Test create_construction_config function."""
    expected_construction_dict = {
        "qa_path": "R:/DAP_emulation/2022_surveys/BERD/04_construction/construction_qa",
        "all_data_construction_file_path": "R:/DAP_emulation/2022_surveys/BERD/04_construction/man_con/construction_file.csv",
        "postcode_construction_file_path": "R:/DAP_emulation/2022_surveys/BERD/04_construction/man_con/postcode_construction_file.csv",
        "construction_file_path_ni": (
            "R:/DAP_emulation/2022_surveys/BERD/04_construction/man_con/con_file_ni.csv"
        ),
    }
    construction_dict = create_construction_config(config)
    assert (
        construction_dict == expected_construction_dict
    ), "Construction config is not as expected"


def test_create_exports_config(config):
    """Test create_exports_config function."""
    expected_exports_dict = {"export_folder": "R:/DAP_emulation/outgoing_export/"}
    exports_dict = create_exports_config(config)

    assert exports_dict == expected_exports_dict, "Exports config is not as expected"


def test_create_module_config_imputation_case(config):
    """Test create_module_config function for the imputation module."""

    expected_imputation_dict = {
        "qa_path": "R:/DAP_emulation/2022_surveys/BERD/06_imputation/imputation_qa",
        "manual_trimming_path": (
            "R:/DAP_emulation/2022_surveys/BERD/06_imputation/manual_trimming"
        ),
    }
    imputation_dict = create_module_config(config, "imputation")

    assert imputation_dict == expected_imputation_dict, "Imp config is not as expected"


@pytest.fixture(scope="module")
def expected_outliers_dict():
    expected_outliers_dict = {
        "qa_path": "R:/DAP_emulation/2022_surveys/BERD/07_outliers/outliers_qa",
        "auto_outliers_path": (
            "R:/DAP_emulation/2022_surveys/BERD/07_outliers/auto_outliers"
        ),
    }
    return expected_outliers_dict


def test_create_module_config_outliers_case(config, expected_outliers_dict):
    """Test create_module_config function for the outliers module."""

    outliers_dict = create_module_config(config, "outliers")

    assert outliers_dict == expected_outliers_dict, "Outliers config is not as expected"


def test_update_config_with_paths(
    config, expected_staging_dict, expected_outliers_dict
):
    """Test update_config_with_paths function."""
    module_list = ["imputation", "outliers"]
    updated_config = update_config_with_paths(config, module_list)

    special_paths = ["staging_paths", "ni_paths", "mapping_paths"]
    for module_name in module_list + special_paths:
        assert (
            f"{module_name}_paths" in updated_config,
            f"{module_name}_paths are not present in updated_config",
        )

    assert (
        updated_config["staging_paths"] == expected_staging_dict,
        "Staging paths are not as expected",
    )
    assert (
        updated_config["outliers_paths"] == expected_outliers_dict,
        "Outliers paths are not as expected",
    )

    assert (
        updated_config["export_paths"]
        == {"export_folder": "R:/DAP_emulation/outgoing_export/"},
    )
