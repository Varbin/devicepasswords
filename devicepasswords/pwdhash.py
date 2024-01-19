from passlib.context import CryptContext


hasher = CryptContext(
    schemes=[
        "plaintext",
        "ldap_md5", "ldap_sha1", "ldap_salted_md5", "ldap_salted_sha1",
        "ldap_salted_sha256", "ldap_salted_sha512",
        "ldap_sha1_crypt", "ldap_sha256_crypt", "ldap_sha512_crypt",
        "ldap_bcrypt", "roundup_plaintext",
        "scram", "nthash",
        "bcrypt", "scrypt", "argon2",
        "md5_crypt", "sha1_crypt", "sha256_crypt", "sha512_crypt"
    ],
)