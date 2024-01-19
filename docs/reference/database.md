## Supported databases

The docker container contains drivers for sqlite, MySQL/MariaDB, Postgres and (Microsoft) SQL Server by default.
See the following table for the URL schemata.

Consult the [sqlalchemy documentation regarding dialects](https://docs.sqlalchemy.org/en/20/dialects/) for further details.

## Database schema

For client integrations, two tables are relevant: `users` and `tokens`.

`users`:

 - primary (text): value of the *sub* claim
 - user (text): value of the configured username claim
 - email (text): value of the email claim

`tokens`:

 - primary (int): Internal identifier of the token
 - user (text): value of the configured username claim
 - name (text): user set name of the token
 - token (text): the device password, see the configuration for configuring hashing
 - expires (datetime, nullable): user configured expiration data
