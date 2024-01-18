This is the list of supported variables:

| Variable                       | Meaning                                                                                                                          | Default                                                            |
|--------------------------------|----------------------------------------------------------------------------------------------------------------------------------|--------------------------------------------------------------------|
| `DP_SECRET_KEY`                | Secret key for signing the session cookies.                                                                                      | *Random generated*, set a fixed key one for a load balanced setup. |
| `DP_SQLALCHEMY_DATABASE_URI`   | URL to the database (any supported scheme supported by SQLAlchemy)                                                               | *None* (Mandatory)                                                 |
| `DP_OIDC_DISCOVERY_URL`        | [Discovery endpoint](https://openid.net/specs/openid-connect-discovery-1_0.html) of your identity provider.                      | *None* (Mandatory to set)                                          |
| `DP_OIDC_CLIENT_ID`            | Registered client id of the registered app.                                                                                      | *None* (Mandatory to set)                                          |
| `DP_OIDC_CLIENT_SECRET`        | Client secret of the registered app.                                                                                             | *None* (Recommended)                                               |
| `DP_OIDC_SCOPE`                | Scope to request, must include *openid*.                                                                                         | openid email profile                                               |
| `DP_OIDC_CLAIM_EMAIL`          | In what claim the user's mail address is found.                                                                                  | email                                                              |
| `DP_OIDC_CLAIM_EMAIL_VERIFIED` | What claim to check if the email has been verified. Set empty to accept all emails.                                              | email_verified                                                     |
| `DP_OIDC_CLAIM_USERNAME`       | In what claim the preferred username is found. In case your IdP does not hand out them, you may use the same value as for email. | preferred_username                                                 |
| `DP_OIDC_CLAIMS_FROM_PROFILE`  | Load the email and username claim from the profile instead of the id token.                                                      | false                                                              |
| `DP_OIDC_REQUIRED_CLAIM`       | Require the given claim to be present to allow user access.                                                                      | *None*                                                             |
| `DP_OIDC_REQUIRED_CLAIM_VALUE` | Require the required claim to have a specific value.                                                                             | *None*                                                             |
| `DP_OIDC_GROUP_MEMBERSHIP`     | Require the given group membership to allow access.                                                                              | *None*                                                             |
| `DP_OIDC_GROUP_CLAIM`          | The group claim. The claim must be JSON array.                                                                                   | groups                                                             |                                                          |
| `DP_WORDLIST`                  | Path to the wordlist for the generated passwords. The container ships with *wordlist.txt* and *wordlist-de.txt*.                 | wordlist.txt                                                       |
| `` | | |


Additionally, the Docker container supports the following options:

| Variable | Meaning                                   | Default |
|----------|-------------------------------------------|---------|
| WORKERS | Amount of worker processes to spawn.      | 4 |
| CLASS | Worker class to use. Consult the gunicorn | gevent |