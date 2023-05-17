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