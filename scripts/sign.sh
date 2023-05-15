#!/usr/bin/env bash

content_dir=$1
public_key=$2
private_key=$3

# These steps were derived from the adoptium documentation found at:
# https://adoptium.net/docs/marketplace-listing/
for json in $(ls ${content_dir}/*.json); do
    echo "$json"
    # Generate signature
    openssl dgst -sha256 -sign $private_key -out ${json}.sig $json

    # Verify
    openssl dgst -sha256 -verify $public_key -signature ${json}.sig $json

    # Base64 encode for publishing
    cat ${json}.sig | base64 -w 0 > ${json}.sha256.sign
done;