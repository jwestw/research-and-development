"""Tests for path_helpers.py """
import pytest

from src.utils.path_helpers import (
    get_paths,
    create_staging_config,
    create_ni_staging_config,
    create_mapping_config,
    create_module_config,
)


@pytest.fixture(scope="module")
def config():
    config = {
        "global": {"network_or_hdfs": "network"},
        "network_paths": {
            "root": "R:/DAP_emulation/",
            "snapshot_path": "snapshot_path/snap.csv",
            "secondary_snapshot_path": "secondary_snapshot_path/snap2.csv",
            "postcode_masterlist": "postcode_masterlist_path/postcode.csv",
            "ni_full_responses_path": "03_northern_ireland/2021/TEST_ni.csv",
            "manual_imp_trim_path": "06_imputation/man_trim/trim_qa.csv",
            "manual_outliers_path": "07_outliers/man_out/man_out.csv",
        },
        "years": {"survey_year": 2022},
        "staging_paths": {
            "folder": "01_staging",
            "feather_output": "feather",
        },
        "ni_staging_paths": {
            "folder": "03_northern_ireland",
            "ni_staging_output_path": "ni_staging_qa",
        },
        "2022_mappers": {
            "mappers_version": "v1",
            "postcodes_mapper": "pcodes_2022.csv",
            "itl_mapper_path": "itl_2022.csv",
        },
        "imputation_paths": {
            "folder": "06_imputation",
            "qa_path": "imputation_qa",
            "manual_trimming_path": "manual_trimming",
        },
        "outliers_paths": {
            "folder": "07_outliers",
            "qa_path": "outlier_qa",
            "auto_outliers_path": "auto_outliers",
            "manual_outliers_path": "manual_outliers",
        },
    }
    return config


def test_get_paths(config):
    """Test get_paths function."""
    expected_network_paths = {
        "root": "R:/DAP_emulation/",
        "snapshot_path": "snapshot_path/snap.csv",
        "secondary_snapshot_path": "secondary_snapshot_path/snap2.csv",
        "postcode_masterlist": "postcode_masterlist_path/postcode.csv",
        "ni_full_responses_path": "03_northern_ireland/2021/TEST_ni.csv",
        "manual_outliers_path": "07_outliers/man_out/man_out.csv",
        "manual_imp_trim_path": "06_imputation/man_trim/trim_qa.csv",
        "year": 2022,
        "berd_path": "R:/DAP_emulation/2022_surveys/BERD/",
    }
    network_paths = get_paths(config)

    assert network_paths == expected_network_paths


def test_create_staging_config(config):
    """Test create_staging_config function."""

    expected_staging_dict = {
        "feather_output": "R:/DAP_emulation/2022_surveys/BERD/01_staging/feather",
        "snapshot_path": "R:/DAP_emulation/snapshot_path/snap.csv",
        "secondary_snapshot_path": "R:/DAP_emulation/secondary_snapshot_path/snap2.csv",
        "postcode_masterlist": "R:/DAP_emulation/postcode_masterlist_path/postcode.csv",
        "manual_outliers_path": (
            "R:/DAP_emulation/2022_surveys/BERD/07_outliers/man_out/man_out.csv"
        ),
        "manual_imp_trim_path": (
            "R:/DAP_emulation/2022_surveys/BERD/06_imputation/man_trim/trim_qa.csv"
        ),
    }
    staging_dict = create_staging_config(config)

    assert staging_dict == expected_staging_dict


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

    assert ni_staging_dict == expected_ni_staging_dict


def test_create_mapping_config(config):
    """Test create_mapping_config function."""

    expected_mapping_dict = {
        "postcodes_mapper": "R:/DAP_emulation/2022_surveys/mappers/v1/pcodes_2022.csv",
        "itl_mapper_path": "R:/DAP_emulation/2022_surveys/mappers/v1/itl_2022.csv",
    }
    mapping_dict = create_mapping_config(config)

    assert mapping_dict == expected_mapping_dict


def test_create_module_config_imputation_case(config):
    """Test create_module_config function for the imputation module."""

    expected_imputation_dict = {
        "qa_path": "R:/DAP_emulation/2022_surveys/BERD/06_imputation/imputation_qa",
        "manual_trimming_path": (
            "R:/DAP_emulation/2022_surveys/BERD/06_imputation/manual_trimming"
        ),
    }
    imputation_dict = create_module_config(config, "imputation")

    assert imputation_dict == expected_imputation_dict


def test_create_module_config_outliers_case(config):
    """Test create_module_config function for the outliers module."""

    expected_outliers_dict = {
        "qa_path": "R:/DAP_emulation/2022_surveys/BERD/07_outliers/outlier_qa",
        "auto_outliers_path": (
            "R:/DAP_emulation/2022_surveys/BERD/07_outliers/auto_outliers"
        ),
        "manual_outliers_path": (
            "R:/DAP_emulation/2022_surveys/BERD/07_outliers/manual_outliers"
        ),
    }
    outliers_dict = create_module_config(config, "outliers")

    assert outliers_dict == expected_outliers_dict
