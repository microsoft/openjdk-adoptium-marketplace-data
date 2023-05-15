# Script usage

## sign.sh
This script is used to sign all json files within the input directory.

Example usage:

```
$cd scripts/
$chmod +x sign.sh
$./sign.sh --directory ../11 --public-key <path/to/public_key.pem> --secret-key <path/to/secret_key.pem>
```

**Dependencies**:
- openssl
- base64