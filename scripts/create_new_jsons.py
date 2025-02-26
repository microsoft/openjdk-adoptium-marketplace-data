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

from docopt import docopt  # type: ignore

logging.basicConfig(format="%(message)s", level=logging.DEBUG)
logger = logging.getLogger(__name__)
DATE_FORMAT = "%Y-%m-%dT%H:00:00Z"


def create_new_json_file(
    folder: str,
    new_version: str,
) -> str:
    """Create a new JSON file based on an existing one.
    Args:
        folder (str): The folder containing the JSON files.
        new_version (str): The new version to be added.
    Returns:
        new_file_path (str): The path to the new JSON file.
    """
    # Read the existing JSON file
    index_file_path = Path(folder).joinpath("index.json")
    with index_file_path.open("r") as index_file:
        index_data = json.load(index_file)

    # Get the filename from the "releases" key
    old_filename = index_data["releases"][0]

    # Get rid of the build number and replace '.' with '_'
    formatted_version = new_version.split("+")[0].replace(".", "_")

    # Define the new filename
    new_filename = f"jdk_{formatted_version}.json"

    # Copy the original file to the new file
    old_file_path = Path(folder).joinpath(old_filename)
    new_file_path = Path(folder).joinpath(new_filename)
    new_file_path.write_text(old_file_path.read_text())

    logger.info(f"Copied {old_filename} to {new_filename}")

    # Insert the new filename at the beginning of the "releases" list
    index_data["releases"].insert(0, new_filename)

    # Write the updated index data back to the index file
    with index_file_path.open("w") as index_file:
        json.dump(index_data, index_file, indent=4)

    logger.info(f"Updated {index_file_path} with new entry {new_filename}")

    return new_file_path.as_posix()


def update_new_json_info(
    version: str,
    file_path: str,
) -> Tuple[str, str]:
    """Update the JSON file with new version information.
    Args:
        version (str):      The new version to be added.
        file_path (str):    The path to the new JSON file.
    Returns:
        old_version (str):  The version from the most resent JSON file.
        old_psu_tag (str):  The psu tag from the most resent JSON file.
    """
    # Load the contents of the new JSON file into a dictionary
    file_path = Path(file_path)
    with file_path.open("r") as new_file:
        file_data = json.load(new_file)

    # Setup needed vars
    content = file_data["releases"][0]
    today = datetime.now().strftime(DATE_FORMAT)
    old_version = content["openjdk_version_data"]["openjdk_version"]
    old_psu_tag = content["binaries"][0]["aqavit_results_link"].split("/")[-2]

    # Update overall JSON data
    content["release_name"] = f"jdk-{version}"
    content["last_updated_timestamp"] = today

    # Update openjdk_version_data
    content["openjdk_version_data"]["major"] = int(version.split(".")[0])
    content["openjdk_version_data"]["minor"] = int(version.split(".")[1])
    content["openjdk_version_data"]["security"] = int(
        version.split(".")[2].split("+")[0]
    )
    content["openjdk_version_data"]["build"] = int(version.split("+")[1])
    content["openjdk_version_data"]["openjdk_version"] = version

    # Update binary info
    for entry in content["binaries"]:
        if "timestamp" in entry:
            entry["timestamp"] = today

    # Write the updated contents back to the file
    with file_path.open("w") as new_file:
        json.dump(file_data, new_file, indent=4)

    logger.info(
        f"Updated {file_path} with new version info {version} and timestamp {today}"
    )

    return old_version, old_psu_tag


def update_new_json_full_versions(
    version: str,
    old_version: str,
    psu_tag: str,
    old_psu_tag: str,
    file_path: str,
):
    """Update the full version numbers in the new JSON file.
    Args:
        version (str): The new version to be added.
        old_version (str): The version from the most resent JSON file.
        psu_tag (str): The psu tag for the new version.
        old_psu_tag (str): The psu tag from the most resent JSON file.
        file_path (str): The path to the new JSON file.
    """
    # Load the contents of the new JSON file into a dictionary
    file_path = Path(file_path)
    with file_path.open("r") as f:
        file_data_str = f.read()

    # Replace all instances of old_version with version
    ## Replace full versions with '+' in it. Example: 11.0.25+9 -> 11.0.26+4
    file_data_str = file_data_str.replace(old_version, version)
    ## Replace full versions with '_' in it. Example: 11.0.25_9 -> 11.0.26_4
    file_data_str = file_data_str.replace(
        old_version.replace("+", "_"), version.replace("+", "_")
    )
    ## Replace full versions without build numbers. Example: 11.0.25 -> 11.0.26
    file_data_str = file_data_str.replace(
        old_version.split("+")[0], version.split("+")[0]
    )
    ## Replace psu_tags. Example: oct-2024-psu -> jan-2025-psu
    file_data_str = file_data_str.replace(old_psu_tag, psu_tag)

    # Write the updated contents back to the file
    with file_path.open("w") as f:
        f.write(file_data_str)

    logger.info(
        f"Updated {file_path} with new full version {version} and psu_tag {psu_tag}"
    )


def update_shasum(
    entry: dict,
):
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
    file_path: str,
):
    """Update the shasums in the new JSON file.
    Args:
        file_path (str): The path to the new JSON file.
    """
    # Load the contents of the new JSON file into a dictionary
    file_path = Path(file_path)
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
    new_file_path = create_new_json_file(
        folder=folder,
        new_version=new_version,
    )

    old_version, old_psu_tag = update_new_json_info(
        version=new_version,
        file_path=new_file_path,
    )

    update_new_json_full_versions(
        version=new_version,
        old_version=old_version,
        psu_tag=psu_tag,
        old_psu_tag=old_psu_tag,
        file_path=new_file_path,
    )

    update_all_shasums(
        file_path=new_file_path,
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
