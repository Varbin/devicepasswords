## Supported databases

The docker container contains drivers for sqlite, MySQL/MariaDB, Postgres and (Microsoft) SQL Server by default.
Generally all [drivers supported by SQLAlchemy](https://docs.sqlalchemy.org/en/20/dialects/) generally can be used.

The Docker container only contains drivers for the below database.
See the following table for the supported connection string strings.
The connection strings support additional arguments, see the linked reference for further details.

| Database               | Schema                                        | Reference                                                                                                       |
|------------------------|-----------------------------------------------|-----------------------------------------------------------------------------------------------------------------|
| SQLite                 | sqlite:///file                                | [🔗](https://docs.sqlalchemy.org/en/20/dialects/sqlite.html#pysqlite)                                           |
| MySQL  / MariaDB       | mysql+pymysql://user:password@host/database   | [🔗](https://docs.sqlalchemy.org/en/20/dialects/mysql.html#module-sqlalchemy.dialects.mysql.pymysql)            |            |
| PostgreSQL             | postgresql://user:password@host:port/database | [🔗](https://docs.sqlalchemy.org/en/20/dialects/postgresql.html#module-sqlalchemy.dialects.postgresql.psycopg2) |
| (Microsoft) SQL Server | mssql+pymssql://user:password/name            | [🔗](https://docs.sqlalchemy.org/en/20/dialects/mssql.html#module-sqlalchemy.dialects.mssql.pymssql)            |                                                                                                           |


## Database schema

For client integrations, two tables are relevant: `users` and `tokens`.

`users`:

 - sub (text): value of the *sub* claim
 - user (text): value of the configured username claim
 - email (text): value of the email claim

`tokens`:

 - id (UUID/text): Internal identifier of the token
 - sub (text): value of the *sub* claim of the user
 - name (text): user set name of the token
 - token (text): the device password, see the configuration for configuring hashing
 - expires (datetime, nullable): user configured expiration data
