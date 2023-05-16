#!/usr/bin/env bash
set -eux

PROGRAM_NAME="${0##*/}"
# Set defaults
secret_key_file="../private.pem"
public_key_file="../public.pem"
HELP=false

# Read input args
while [[ "$#" -gt 0 ]]; do
    case $1 in
        -h|--help) HELP=true ;;
        -d|--directory) content_dir="$2"; shift ;;
        -s|--secret-key) secret_key_file="$2"; shift ;;
        -p|--public-key) public_key_file="$2"; shift ;;
        *) echo "Unknown parameter passed: $1"; exit 1 ;;
    esac
    shift
done

if [ "$HELP" = true ] ; then
    echo "Usage: $PROGRAM_NAME [options]"
    echo ""
    echo "Signs all .json files within input directory"
    echo ""
    echo "Options:"
    echo "-h, --help                Show this help message and exit."
    echo "-d, --directory <path>    Required. Input folder containing .json files to sign."
    echo "-s, --secret-key <path>   Required. Path to secret key used for signing."
    echo "                          Default: '../private.pem'"
    echo "-s, --public-key <path>   Required. Path to public key used for signing."
    echo "                          Default: '../public.pem'"
    exit 0
fi

# These steps were derived from the adoptium documentation found at:
# https://adoptium.net/docs/marketplace-listing/
for json in $(ls ${content_dir}/*.json); do
    echo "Signing and checking: $json"
    # Use secret key to sha256-sign json file
    openssl dgst -sha256 -sign "$secret_key_file" -out ${json}.sig $json

    # Verify that the generated signature is correct using public key
    openssl dgst -sha256 -verify "$public_key_file" -signature ${json}.sig $json

    # Dump signature to base64 encoded file for human readability
    cat ${json}.sig | base64 -w 0 > ${json}.sha256.sign
done;