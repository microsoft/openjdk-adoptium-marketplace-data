"""create_new_jsons

This script is used to create new json entries for new psu versions.
This script will also update json indexes for the new psu versions.

Note: YOU WILL STILL NEED TO:
    1. Run sign.sh to sign the new psu version jsons
    2. Ensure that the filenames for the `aqavit_results_link` enties are correct

Requirements:
    1. python 3.8 and higher

Usage:
  create_new_jsons --folder=<str> --new_version=<str> --psu_tag=<str>

Options:
    --folder=<str>          Folder containing the json files
    --new_version=<str>     New version to be added
    --psu_tag=<str>         Tag for the new version
    --help                  Show this help message
Example:
  create_new_jsons --folder=../11 --new_version=11.0.26+4 --psu_tag=jan-2025-psu
"""

import json
import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Tuple

import requests
from docopt import docopt
from jinja2 import Environment, FileSystemLoader

logging.basicConfig(format="%(message)s", level=logging.DEBUG)
logger = logging.getLogger(__name__)
DATE_FORMAT = "%Y-%m-%dT%H:00:00Z"


def update_index_file(
    folder: str,
    new_filename: str,
):
    """
    Ensure existing index file has entry for new PSU's json.
    Args:
        folder (str): The folder containing the JSON files.
        new_filename (str): The name of the new JSON file.
    """
    # Read the existing JSON file
    index_file_path = Path(folder).joinpath("index.json")
    with index_file_path.open("r") as index_file:
        index_data = json.load(index_file)

    # Insert the new filename at the beginning of the "releases" list
    if new_filename not in index_data["releases"]:
        index_data["releases"].insert(0, new_filename)

        # Write the updated index data back to the index file
        with index_file_path.open("w") as index_file:
            json.dump(index_data, index_file, indent=4)

        logger.info(
            f"Updated index file {index_file_path} with new entry {new_filename}"
        )

    else:
        logger.info(f"{new_filename} already exists in {index_file_path}")


def create_new_json(
    version: str,
    psu_tag: str,
    folder: str,
) -> Path:
    """
    Create the new JSON file for new PSU with updated info.
    Args:
        version (str): The new version to be added.
        psu_tag (str): The psu tag for the new version.
        folder (str): The folder containing the JSON files.
    Returns:
        new_file_path (Path): The path to the new JSON file.
    """
    path = str(Path(__file__).parent.parent.joinpath("templates"))
    env = Environment(loader=FileSystemLoader(path))
    template = env.get_template("jdk_version_template.json")

    today = datetime.now().strftime(DATE_FORMAT)

    major_version = version.split(".")[0]
    minor_version = version.split(".")[1]
    security_version = version.split(".")[2].split("+")[0]
    build_version = version.split("+")[1]

    new_file_contents = template.render(
        major=major_version,
        minor=minor_version,
        security=security_version,
        build=build_version,
        psu_tag=psu_tag,
        timestamp=today,
    )

    # Get rid of the build number and replace '.' with '_'
    formatted_version = version.split("+")[0].replace(".", "_")
    new_filename = f"jdk_{formatted_version}.json"
    new_file_path = Path(folder).joinpath(new_filename)

    with open(new_file_path, "w") as new_file:
        new_file.write(new_file_contents)
    logger.info(f"Created new JSON file at {new_file_path}")

    return new_file_path


def update_shasum(
    entry: dict,
):
    """
    Update the shasum for a given entry.
    Args:
        entry (dict): The entry wit a shasum that needs updating.
    """
    logger.info(f"Updating shasum for: {entry}")
    download_link = entry["sha256sum_link"]

    for attempt in range(3):
        try:
            response = requests.get(download_link)
            response.raise_for_status()
            new_shasum = response.text.strip().split(" ")[0]
            break
        except requests.RequestException as e:
            logger.error(f"Attempt {attempt + 1} failed: {e}")
            if attempt == 2:
                logger.error(
                    f"Max attempts reached, failed to download shasum from link: {download_link}"
                )
                raise

    entry["sha256sum"] = new_shasum
    logger.info(f"Updated shasum for {entry['name']}")


def update_all_shasums(
    file_path: Path,
):
    """
    Update the shasums in the new JSON file.
    Args:
        file_path (Path): The path to the new JSON file.
    """
    # Load the contents of the new JSON file into a dictionary
    with file_path.open("r") as f:
        file_data = json.load(f)

    binaries = file_data["releases"][0]["binaries"]
    # Update shasums
    for entry in binaries:
        if "package" in entry:
            update_shasum(entry["package"])
        if "installer" in entry:
            update_shasum(entry["installer"][0])

    # Write the updated contents back to the file
    with file_path.open("w") as f:
        json.dump(file_data, f, indent=4)

    logger.info(f"Updated {file_path} with new shasums")


def main(
    folder: str,
    new_version: str,
    psu_tag: str,
):
    new_file_path = create_new_json(
        version=new_version,
        psu_tag=psu_tag,
        folder=folder,
    )

    update_all_shasums(
        file_path=new_file_path,
    )

    update_index_file(
        folder=folder,
        new_filename=new_file_path.name,
    )

    logger.info(
        f"\n*IMPORTANT*:\nPlease make sure that that the filenames at the end of the 'aqavit_results_link' entries are correct"
    )


if __name__ == "__main__":
    logging.info(sys.argv)
    arguments = docopt(__doc__)
    logging.info(arguments)

    main(
        folder=arguments["--folder"],
        new_version=arguments["--new_version"].replace("_", "+"),
        psu_tag=arguments["--psu_tag"],
    )
