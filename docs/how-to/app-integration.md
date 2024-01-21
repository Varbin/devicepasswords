# Integrate your applications

## Dovecot

Dovecot separates user lookup (userdb) and password verification (passdb).
Both user and password database to not need to be the same source.
Therefore, it is possible to use e.g. LDAP for user lookup and the device password manager for authentication.
Additionally, multiple password providers are supported.
This makes it possible to seamlessly migrate.

!!! info "Dovecot documentation"

     * [Authentication](https://doc.dovecot.org/configuration_manual/authentication/)
     * [SQL](https://doc.dovecot.org/configuration_manual/authentication/sql/)
     * [Password schemes](https://doc.dovecot.org/configuration_manual/authentication/password_schemes/)

Dovecot supports MySQL/MariaDB, PostgreSQL and SQLite.
You need to install the respective extension.
See [dovecot manual regarding password schemes](https://doc.dovecot.org/configuration_manual/authentication/password_schemes/) for the supported hashing algorithms.
To support multiple hashes, you need to use prefixes for the password hashes.
Otherwise, you can set the (default) hash with `default_pass_scheme`.
This software currently only prefixes the `ldap_` variants.

!!! tip "Password query returned multiple matches"

     Password lookups must only a single entry for Dovecot.
     As users can have multiple device passwords,
     the query must validate the password.
     As this is database specific, you may want to look at [database side password validation](password-validation.md).

     This may make the use of challenge-response authentication – e.g. SCRAM or NTLM – with multiple device passwords impossible.   

Below is a configuration example for _plaintext_ passwords. 

=== "dovecot.conf"

    ```
    passdb {
        driver = sql
        args = /etc/dovecot/dovecot-sql.conf.ext
    }
    # If you have an old authentication scheme, you can leave it active while migrating.
    # e.g.
    #
    # passdb {
    #   driver = ldap
    #   ...
    # }
    
    # Optional, if you want to use it for user lookup
    userdb {
        driver = sql
        args = /etc/dovecot/dovecot-sql.conf.ext
    }
    # Alternatively, use your existing user lookup.
    ```

=== "dovecot-sql.conf.ext (plaintext passwords)"

    ```
    driver = pgsql  # Database specific
    connect = host=postgres dbname=postgres user=postgres password=postgres  # Can be specified multiple times for high availability.

    password_query = SELECT users.username as username, tokens.token AS password FROM users LEFT OUTER JOIN tokens on users.sub = tokens.sub WHERE users.username = '%n' AND (expires IS NULL OR expires > NOW()) AND password = '%w'
    user_query = SELECT username FROM users WHERE username = '%n'  # Only required for userdb
    iterate_query = SELECT username FROM users  # Only required for userdb
    ```

=== "dovecot-sql-conf.ext (bcrypt passwords, PostgreSQL specific)"

    ```
    driver = pgsql  # Database specific
    connect = host=postgres dbname=postgres user=postgres password=postgres  # Can be specified multiple times for high availability.

    password_query = password_query = SELECT users.username as username, NULL AS password, 'Y' as nopassword FROM users LEFT OUTER JOIN tokens on users.sub = tokens.sub WHERE users.username = '%n' AND (expires IS NULL OR expires > NOW()) AND crypt('%w', REPLACE(tokens.token, '$2b$', '$2a$')) = REPLACE(tokens.token, '$2b', '$2a')
    user_query = SELECT username FROM users WHERE username = '%n'  # Only required for userdb
    iterate_query = SELECT username FROM users  # Only required for userdb
    ```

=== "dovecot-sql-conf.ext (database-side validation)"
    See [database-side validation](password-validation.md).

    ```
    driver = pgsql  # Database specific
    connect = host=postgres dbname=postgres user=postgres password=postgres  # Can be specified multiple times for high availability.

    password_query = SELECT username, NULL as password, 'Y' as nopassword FROM verify_login('%n', '', '%w')
    user_query = SELECT username FROM users WHERE username = '%n'  # Only required for userdb
    iterate_query = SELECT username FROM users  # Only required for userdb
    ```

!!! warning "Validate your configuration in a test environment"

     Dovecot will log queries with errors, including parameters.
     To avoid accidential logging of your production passwords,
     test your database integration in a test environment.


## FreeRADIUS


