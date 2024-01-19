This is the list of supported variables:

| Variable                       | Meaning                                                                                                                                 | Default                                                            |
|--------------------------------|-----------------------------------------------------------------------------------------------------------------------------------------|--------------------------------------------------------------------|
| `DP_SECRET_KEY`                | Secret key for signing the session cookies.                                                                                             | *Random generated*, set a fixed key one for a load balanced setup. |
| `DP_SQLALCHEMY_DATABASE_URI`   | URL to the database (any supported scheme supported by SQLAlchemy)                                                                      | *None* (Mandatory)                                                 |
| `DP_OIDC_DISCOVERY_URL`        | [Discovery endpoint](https://openid.net/specs/openid-connect-discovery-1_0.html) of your identity provider.                             | *None* (Mandatory to set)                                          |
| `DP_OIDC_CLIENT_ID`            | Registered client id of the registered app.                                                                                             | *None* (Mandatory to set)                                          |
| `DP_OIDC_CLIENT_SECRET`        | Client secret of the registered app.                                                                                                    | *None* (Recommended)                                               |
| `DP_OIDC_SCOPE`                | Scope to request, must include *openid*.                                                                                                | openid email profile                                               |
| `DP_OIDC_CLAIM_EMAIL`          | In what claim the user's mail address is found.                                                                                         | email                                                              |
| `DP_OIDC_CLAIM_EMAIL_VERIFIED` | What claim to check if the email has been verified. Set empty to accept all emails.                                                     | email_verified                                                     |
| `DP_OIDC_CLAIM_USERNAME`       | In what claim the preferred username is found. In case your IdP does not hand out them, you may use the same value as for email.        | preferred_username                                                 |
| `DP_OIDC_CLAIMS_FROM_PROFILE`  | Load the email and username claim from the profile instead of the id token.                                                             | false                                                              |
| `DP_OIDC_REQUIRED_CLAIM`       | Require the given claim to be present to allow user access.                                                                             | *None*                                                             |
| `DP_OIDC_REQUIRED_CLAIM_VALUE` | Require the required claim to have a specific value.                                                                                    | *None*                                                             |
| `DP_OIDC_GROUP_MEMBERSHIP`     | Require the given group membership to allow access.                                                                                     | *None*                                                             |
| `DP_OIDC_GROUP_CLAIM`          | The group claim. The claim must be JSON array.                                                                                          | groups                                                             |                                                          |
| `DP_WORDLIST`                  | Path to the wordlist for the generated passwords. The container ships with *wordlist.txt* and *wordlist-de.txt*.                        | wordlist.txt                                                       |
| `DP_PASSWORD_HASH`             | Enable password hashing. See below for valid values, and the [password hasing guide](../how-to/password-hashing.md) for details.        | plaintext                                                          |
| `DP_UI_HEADING`                | Heading.                                                                                                                                | Device Passwords                                                   |
| `DP_UI_HEADING_SUB`            | Add a subtext after "Device Passwords", none by default.                                                                                | *None*                                                             |
| `DP_UI_SHOW_SUBJECT`           | Show the subject identifier below the heading                                                                                           | true                                                               |
| `DP_UI_SHOW_LAST_USED`         | Show last used timestamp for each device password. You must use database-side password validation for the last used time to be updated. | true                                                               |
| `DP_UI_NO_AWOO`                | Do not display "Awooo!" after creating the device passwords. By default the system howls.                                               | false                                                              |
| `DP_MAX_EXPIRATION_DAYS`       | Maximum time in days a device password is valid. Any value ≤ 1 disables forced expiration.                                              | 0                                                                  |

Additionally, the Docker container supports the following options:

| Variable | Meaning                                           | Default |
|----------|---------------------------------------------------|---------|
| WORKERS  | Amount of worker processes to spawn.              | 4       |
| CLASS    | Worker class to use. Consult the gunicorn manual. | gevent  |

<details>
<summary>Supported password hashing values</summary>

plaintext, ldap_md5, ldap_sha1, ldap_salted_md5, ldap_salted_sha1, 
ldap_salted_sha256, ldap_salted_sha512, ldap_sha1_crypt, ldap_sha256_crypt, 
ldap_sha512_crypt, ldap_bcrypt,  roundup_plaintext, scram, nthash, bcrypt, 
scrypt, argon2, md5_crypt, sha1_crypt, sha256_crypt, sha512_crypt
</details>

!!! info "Related How-To guides"

    * [Identity provider integration](../how-to/idp-integration.md)
    * [User interface customization](../how-to/interface.md)
    * [Password hashing](../how-to/password-hashing.md)