# Script usage

## sign.sh
This script is used to sign all json files within the input directory,
and produces the `.sha256sum.sign` files required by the adoptium marketplace

Required input:
- `--directory`: Path to the directory that contains `.json` files to be signed.
- `--secret-key`: Path to the secret key used to create signatures.
    - Default: `../private.pem`
- `--public-key`: Path to the public key used to verify signatures.
    - Default: `../public.pem`

Optional input:
- `--help`: prints options to command line and exits

Example usage:

```
$cd scripts/
$chmod +x sign.sh
$./sign.sh --public-key <path/to/public_key.pem> --secret-key <path/to/secret_key.pem> --directory ../11
# Full example: ./sign.sh --public-key ../public.pem --secret-key ../private.pem --directory ../11
```

**Dependencies**:
- openssl
- base64

## create_marketplace_json.py
This is a Python script designed to generate new JSON file entries for new PSUs.
This script will also update the index.json files to include references to these new files.

Note:

    1. You will still need to run `sign.sh` after creating these files (see entry above for info)
    1. You will need to make sure that the filenames at the end of the `aqavit_results_link` entries are correct

Required inputs:
- `--folder`: Path to the directory where new JSON files will be created.
- `--new_version`: The new version string to be included in the JSON files.
- `--psu_tag`: The PSU tag to be associated with the new JSON files.

Optional input:
- `--help`: prints options to command line and exits

## Usage
To run the script, `cd` into the `scripts` folder and use the following command:
```
python create_marketplace_json.py --folder=<str> --new_version=<str> --psu_tag=<str>
```
Example:
```
python create_marketplace_json.py --folder=../11 --new_version=11.0.26+4 --psu_tag=jan-2025-psu
```

**Dependencies**:

(Note: this can be downloaded into your `venv` with the command `pip install -r scripts/requirements.txt`)
- docopt
- types-docopt
- types-requests
- requests
- datetime

## update_microsoft-openjdk-versions.py
This Python script scans one or more version directories for new JDK releases and adds any missing entries to microsoft-openjdk-versions.json.

Required inputs:
- `--versions-file`:    Path to microsoft-openjdk-versions.json
- `--dir`:              A directory containing an index.json, can be used multiple times (one per dir input)

Optional input:
- `--exclude_alpine`:   Exclude Alpine package entries (for jdk11 and jdk17) from generated files. (Boolean flag)
- `--help`:             prints options to command line and exits

## Usage
To run the script, `cd` into the `scripts` folder and use the following command:
```
python update_microsoft-openjdk-versions.py --versions-file=<path> --dir=<dir> --dir=<dir> ...
```
Examples:
```
python update_microsoft-openjdk-versions.py --versions-file=general_info/microsoft-openjdk-versions.json --dir=25 --dir=21 --dir=17 --dir=11
python update_microsoft-openjdk-versions.py --versions-file=general_info/microsoft-openjdk-versions.json --dir=25 --dir=21 --dir=17 --dir=11 --exclude_alpine
```

**Dependencies**:

(Note: this can be downloaded into your `venv` with the command `pip install -r scripts/requirements.txt`)
- docopt