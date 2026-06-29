"""update_microsoft-openjdk-versions

Scans one or more version directories for new JDK releases and adds any
missing entries to microsoft-openjdk-versions.json.

Usage:
  update_microsoft-openjdk-versions --versions-file=<path> --dir=<dir>... [--exclude_alpine]

Options:
  --versions-file=<path>  Path to microsoft-openjdk-versions.json
  --dir=<dir>...          A directory containing an index.json, can be used multiple times (one per dir input)
  --exclude_alpine        Exclude Alpine package entries (for jdk11 and jdk17) from generated files.
  --help                  Show this help message

Example:
  update_microsoft-openjdk-versions --versions-file=general_info/microsoft-openjdk-versions.json --dir=25 --dir=21 --dir=17 --dir=11
  update_microsoft-openjdk-versions --versions-file=general_info/microsoft-openjdk-versions.json --dir=25 --dir=21 --dir=17 --dir=11 --exclude_alpine
"""

import json
import logging
from pathlib import Path

from docopt import docopt

logging.basicConfig(format="%(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)

OS_TO_PLATFORM = {
    "alpine_linux": "alpine",
    "linux": "linux",
    "mac": "darwin",
    "windows": "win32",
}

ARCH_ORDER = ["x64", "aarch64"]
PLATFORM_ORDER = ["darwin", "linux", "win32", "alpine"]
EXCLUDE_ALPINE = False


def files_sort_key(file: dict) -> tuple:
    arch_rank = ARCH_ORDER.index(file["arch"]) if file["arch"] in ARCH_ORDER else 99
    platform_rank = (
        PLATFORM_ORDER.index(file["platform"])
        if file["platform"] in PLATFORM_ORDER
        else 99
    )
    return (arch_rank, platform_rank)


def version_sort_key(version: str) -> tuple:
    numeric = version.split("+")[0]
    return tuple(int(x) for x in numeric.split("."))


def version_string(openjdk_version_data: dict) -> str:
    """Build a dotted version string from openjdk_version_data fields."""
    major = openjdk_version_data["major"]
    minor = openjdk_version_data["minor"]
    security = openjdk_version_data["security"]
    patch = openjdk_version_data.get("patch")
    if patch:
        return f"{major}.{minor}.{security}.{patch}"
    return f"{major}.{minor}.{security}"


def files_from_binaries(binaries: list, version: str = "") -> list:
    """Extract file entries for microsoft-openjdk-versions.json from a binaries list."""
    files = []
    alpine_already_exists = False
    for binary in binaries:
        os_name = binary.get("os")
        platform = OS_TO_PLATFORM.get(os_name)
        if platform is None:
            logger.warning(f"Unknown OS '{os_name}', skipping binary")
            continue
        elif platform == "alpine":
            alpine_already_exists = True

        package = binary.get("package")
        if not package:
            continue

        files.append(
            {
                "filename": package["name"].lower(),
                "arch": binary["architecture"],
                "platform": platform,
                "download_url": package["link"].lower(),
            }
        )

    if (
        not EXCLUDE_ALPINE
        and not alpine_already_exists
        and (version.startswith("11.") or version.startswith("17."))
    ):
        files.append(
            {
                "filename": f"microsoft-jdk-{version}-alpine-x64.tar.gz",
                "arch": "x64",
                "platform": "alpine",
                "download_url": f"https://aka.ms/download-jdk/microsoft-jdk-{version}-alpine-x64.tar.gz",
            }
        )

    return sorted(files, key=files_sort_key)


def load_release_entry(release_file: Path) -> dict | None:
    """
    Load a single release JSON file and return a microsoft-openjdk-versions entry,
    or None if the file cannot be parsed.
    """
    with release_file.open("r") as f:
        data = json.load(f)

    releases = data.get("releases")
    if not releases:
        logger.warning(f"No 'releases' key in {release_file}, skipping")
        return None

    release = releases[0]
    openjdk_version_data = release.get("openjdk_version_data")
    if not openjdk_version_data:
        logger.warning(f"No 'openjdk_version_data' in {release_file}, skipping")
        return None

    version = version_string(openjdk_version_data)
    binaries = release.get("binaries", [])
    files = files_from_binaries(binaries=binaries, version=version)

    return {
        "version": version,
        "stable": True,
        "release_url": "https://aka.ms/download-jdk",  # Note: we should doublecheck this is correct. This is a dead link, I suspect it should be https://aka.ms/msopenjdk-dl
        "files": files,
    }


def collect_new_entries(dirs: list[str], existing_versions: set[str]) -> list[dict]:
    """
    Walk each directory's index.json, load every listed release file, and
    return entries whose versions are not already in existing_versions.
    Entries are returned in the order they appear in the index files (newest first).
    """
    new_entries = []
    seen_versions = set()

    for dir_path_str in dirs:
        dir_path = Path(dir_path_str)
        index_file = dir_path / "index.json"

        if not index_file.exists():
            logger.warning(f"No index.json found in {dir_path}, skipping")
            continue

        with index_file.open("r") as f:
            index_data = json.load(f)

        for release_filename in index_data.get("releases", []):
            release_file = dir_path / release_filename
            if not release_file.exists():
                logger.warning(f"Release file {release_file} not found, skipping")
                continue

            entry = load_release_entry(release_file)
            if entry is None:
                continue

            version = entry["version"]
            if version in existing_versions or version in seen_versions:
                logger.info(f"Version {version} already exists, skipping")
                continue

            logger.info(f"Adding new version: {version}")
            new_entries.append(entry)
            seen_versions.add(version)

    return new_entries


def main(versions_file: str, dirs: list[str]) -> None:
    versions_path = Path(versions_file)

    with versions_path.open("r") as f:
        existing = json.load(f)

    existing_versions = {entry["version"] for entry in existing}
    logger.info(f"Loaded {len(existing)} existing versions from {versions_path}")

    new_entries = collect_new_entries(dirs, existing_versions)

    if not new_entries:
        logger.info("No new versions found, nothing to update.")
        return

    updated = sorted(
        new_entries + existing,
        key=lambda e: version_sort_key(e["version"]),
        reverse=True,
    )

    with versions_path.open("w") as f:
        json.dump(updated, f, indent=2)

    logger.info(
        f"Added {len(new_entries)} new version(s) to {versions_path}: "
        + ", ".join(e["version"] for e in new_entries)
    )


if __name__ == "__main__":
    arguments = docopt(__doc__)
    EXCLUDE_ALPINE = bool(arguments["--exclude_alpine"])
    main(
        versions_file=arguments["--versions-file"],
        dirs=arguments["--dir"],
    )
