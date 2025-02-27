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
$./sign.sh --directory ../11 --public-key <path/to/public_key.pem> --secret-key <path/to/secret_key.pem>
```

**Dependencies**:
- openssl
- base64

## create_new_jsons.py
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
python create_new_jsons.py --folder=<str> --new_version=<str> --psu_tag=<str>
```
Example:
```
python create_new_jsons.py --folder=../11 --new_version=11.0.26+4 --psu_tag=jan-2025-psu
```

**Dependencies**:

(Note: this can be downloaded into your `venv` with the command `pip install -r scripts/requirements.txt`)
- docopt
- types-docopt
- types-requests
- requests
- datetime