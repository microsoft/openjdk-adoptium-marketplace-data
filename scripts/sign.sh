#!/usr/bin/env bash

# Pull directory to sign, public key, and secret key from input args
while getopts d:s:p: flag
do
    case "${flag}" in
        d) content_dir=${OPTARG};;
        s) secret_key_file=${OPTARG};;
        p) public_key_file=${OPTARG};;
    esac
done

# These steps were derived from the adoptium documentation found at:
# https://adoptium.net/docs/marketplace-listing/
for json in $(ls ${content_dir}/*.json); do
    echo "$json"
    # Generate signature
    openssl dgst -sha256 -sign $secret_key_file -out ${json}.sig $json

    # Verify
    openssl dgst -sha256 -verify $public_key_file -signature ${json}.sig $json

    # Base64 encode for publishing
    cat ${json}.sig | base64 -w 0 > ${json}.sha256.sign
done;