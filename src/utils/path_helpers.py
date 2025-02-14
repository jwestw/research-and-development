"""This module contains helper functions for creating paths."""
import os
import logging

PathHelpLogger = logging.getLogger(__name__)


def get_paths(config: dict) -> dict:
    """Return either network_paths or hdfs_paths despending on the environment."""
    platform = config["global"]["platform"]
    paths = config[f"{platform}_paths"]
    paths["year"] = config["survey"]["survey_year"]
    paths["berd_path"] = os.path.join(paths["root"], f"{paths['year']}_surveys/BERD/")
    paths["pnp_path"] = os.path.join(paths["root"], f"{paths['year']}_surveys/PNP/")
    return paths


def create_module_config(config: dict, module_name: str) -> dict:
    """Create a dictionary with all the paths needed for a named module.

    This dict will update the module section of the config with full paths.
    Examples of module names are "imputation", "outliers", "estimation".

    Args:
        config (dict): The pipeline configuration.

    Returns:
        dict: A dictionary with all the paths needed for the specified module.
    """
    paths = get_paths(config)
    berd_path = paths["berd_path"]

    module_conf = config[f"{module_name}_paths"]
    # add the folder to the BERD path
    folder_path = os.path.join(berd_path, module_conf["folder"])

    # we next prefix the folder path to the imputation paths.
    module_dict = {
        k: f"{folder_path}/{v}" for k, v in module_conf.items() if k != "folder"
    }

    return module_dict


def snapshot_validation(config: dict) -> dict:
    paths = get_paths(config)
    survey_year = str(config["survey"]["survey_year"])
    msg = ""

    if f"{survey_year}12" not in paths["snapshot_path"]:
        msg += f"{survey_year} is not included in the frozen snapshot path.\n"

    if (paths["updated_snapshot_path"] != "") and (
        f"{survey_year}12" not in paths["updated_snapshot_path"]
    ):
        msg += f"{survey_year} is not included in the updated snapshot path.\n"

    return msg


def snapshot_validation_logger(config: dict) -> dict:
    """Checks that the mapping filenames are valid"""
    msg = snapshot_validation(config)

    if msg == "":
        PathHelpLogger.info("The snapshot paths are valid.\n")
    else:
        PathHelpLogger.error("There are errors with the snapshot paths.\n")
        raise ValueError(msg)
    return None


def create_staging_config(config: dict) -> dict:
    """Create a configuration dict with all full paths needed for staging.

    This dictionary will update the staging_paths section of the config with full paths.
    See the unit test for examples of the expected output.

    Args:
        config (dict): The pipeline configuration.

    Returns:
        dict: A configuration dictionary will all paths needed for staging.
    """
    paths = get_paths(config)
    berd_path = paths["berd_path"]

    staging_dict = create_module_config(config, "staging")

    # add new paths to the staging section of the config
    staging_dict["snapshot_path"] = paths["snapshot_path"]
    staging_dict["updated_snapshot_path"] = paths["updated_snapshot_path"]
    staging_dict["postcode_masterlist"] = paths["postcode_masterlist"]
    staging_dict["backdata_path"] = paths["backdata_path"]
    staging_dict[
        "pnp_staging_qa_path"
    ] = f"{paths['pnp_path']}{config['pnp_paths']['staging_qa_path']}"
    staging_dict["manual_outliers_path"] = f"{berd_path}{paths['manual_outliers_path']}"
    staging_dict["manual_imp_trim_path"] = f"{berd_path}{paths['manual_imp_trim_path']}"

    return staging_dict


def create_ni_staging_config(config: dict) -> dict:
    """
    Create a configuration dictionary with all paths needed for staging NI data.

    This dictionary will update the ni_paths section of the config with full paths.

    Args:
        config (dict): The pipeline configuration.

    Returns:
        dict: A dictionary with all the paths needed for the NI staging module.
    """
    paths = get_paths(config)
    berd_path = paths["berd_path"]

    ni_staging_dict = create_module_config(config, "ni")

    # add in the path to the ni_full_responses
    ni_path = paths["ni_full_responses_path"]
    ni_staging_dict["ni_full_responses"] = os.path.join(berd_path, ni_path)

    return ni_staging_dict


def create_mapping_config(config: dict) -> dict:
    """Create a configuration dictionary with all paths needed for mapping module.

    This dictionary will update the mappers section of the config with full paths.

    Args:
        config (dict): The pipeline configuration.

    Returns:
        dict: A dictionary with all the paths needed for the mapping module.
    """
    paths = get_paths(config)
    root_path = paths["root"]

    year = paths["year"]
    year_dict = config[f"{year}_mappers"]

    version = year_dict["mappers_version"]

    map_folder = os.path.join(root_path, f"{paths['year']}_surveys/mappers/{version}/")

    paths["mappers"] = map_folder

    mapping_dict = {
        k: f"{map_folder}{v}" for k, v in year_dict.items() if k != "mappers_version"
    }

    # add in the other mapping paths, such as the qa path
    module_dict = create_module_config(config, "mapping")
    mapping_dict.update(module_dict)

    return mapping_dict


def create_freezing_config(config: dict) -> dict:
    """Create a configuration dictionary with all paths needed for freezing module.

    Args:
        config (dict): The pipeline configuration.

    Returns:
        dict: A dictionary with all the paths needed for the freezing module.
    """
    freezing_dict = create_module_config(config, "freezing")

    # now update add freezing paths
    paths = get_paths(config)
    berd_path = paths["berd_path"]
    freezing_dict["frozen_data_staged_path"] = os.path.join(
        berd_path, paths["frozen_data_staged_path"]
    )
    freezing_dict["freezing_changes_to_review_path"] = os.path.join(
        berd_path, paths["freezing_changes_to_review_path"]
    )
    freezing_dict["freezing_additions_path"] = os.path.join(
        berd_path, paths["freezing_additions_path"]
    )
    freezing_dict["freezing_amendments_path"] = os.path.join(
        berd_path, paths["freezing_amendments_path"]
    )

    return freezing_dict


def create_construction_config(config: dict) -> dict:
    """Create a configuration dictionary with all paths needed for construction module.

    Args:
        config (dict): The pipeline configuration.

    Returns:
        dict: A dictionary with all the paths needed for the construction module.
    """
    construction_dict = create_module_config(config, "construction")

    # now update add construction paths
    paths = get_paths(config)
    berd_path = paths["berd_path"]
    construction_dict["all_data_construction_file_path"] = os.path.join(
        berd_path, paths["all_data_construction_file_path"]
    )
    construction_dict["construction_file_path_ni"] = os.path.join(
        berd_path, paths["construction_file_path_ni"]
    )
    construction_dict["postcode_construction_file_path"] = os.path.join(
        berd_path, paths["postcode_construction_file_path"]
    )

    return construction_dict


def create_exports_config(config: dict) -> dict:
    """Create a configuration dictionary with all paths needed for exports.

    Args:
        config (dict): The pipeline configuration.
    Returns:
        dict: A dictionary with all the paths needed for the exports module.
    """
    paths = get_paths(config)
    root_path = paths["root"]
    folder_name = config["export_paths"]["export_folder"]

    export_folder = os.path.join(root_path, folder_name)
    config["export_paths"] = {"export_folder": f"{export_folder}/"}
    return config["export_paths"]


def validate_mapping_filenames(config: dict) -> dict:
    year = str(config["survey"]["survey_year"])
    year_mapper_dict = config[f"{year}_mappers"]
    version = year_mapper_dict["mappers_version"]
    bool_dict = {}
    msg = ""

    for key, value in year_mapper_dict.items():
        bool_dict[key] = True
        # check string is not empty
        if (not value) or (value == ""):
            bool_dict[key] = False
            msg += f"{key} is empty."

        # check filename is correct
        if value != version:
            file_type = ".csv"
            if file_type not in value:
                bool_dict[key] = False
                msg += f"The file: {value} is not a {file_type} file type."

        # check year is correct
        if value != version:
            if year not in value:
                bool_dict[key] = False
                msg += f"{year} is not included in {key}."

    return bool_dict, msg


def filename_validation(config: dict) -> dict:
    """Checks that the snapshot and mapping filenames are valid"""
    # check the snapshot filenames have the current year in them
    snapshot_validation_logger(config)

    bool_dict, msg = validate_mapping_filenames(config)

    if all(bool_dict.values()):
        PathHelpLogger.info("All mapping filenames are valid.")
    else:
        PathHelpLogger.error("There are errors with the mapping filenames.")
        raise ValueError(msg)

    return config


def update_config_with_paths(config: dict, modules: list) -> dict:
    """Update the config with all the paths needed for the pipeline.

    Args:
        config (dict): The pipeline configuration.
        modules (list): A list of module names to update the paths for.

    Returns:
        dict: The updated configuration dictionary.
    """
    config["staging_paths"] = create_staging_config(config)
    config["freezing_paths"] = create_freezing_config(config)
    config["ni_paths"] = create_ni_staging_config(config)
    config["mapping_paths"] = create_mapping_config(config)
    config["construction_paths"] = create_construction_config(config)
    config["export_paths"] = create_exports_config(config)

    for module_name in modules:
        config[f"{module_name}_paths"] = create_module_config(config, module_name)

    return config
