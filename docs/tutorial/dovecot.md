# 3. Dovecot

The next step is to configure the IMAP server dovecot to the device passwords application.
Connecting with `telnet localhost 143` should result in a similar output similar to the following one:

```shell
* OK [CAPABILITY IMAP4rev1 SASL-IR LOGIN-REFERRALS ID ENABLE IDLE LITERAL+ STARTTLS AUTH=PLAIN] Dovecot ready.
```

On the database enable the *pgcrypto* extension:

```shell
docker compose exec postgres psql -U postgres -c 'CREATE EXTENSION IF NOT EXISTS pgcrypto'
```

Set configuration in `dovecot/dovecot.conf` and `dovecot/dovecot-sql.conf.ext`:

=== "dovecot/dovecot.conf"

    ```
    mail_home=/opt/%Lu
    mail_location=sdbox:~/Mail
    mail_uid = 500
    mail_gid = 500
    
    auth_mechanisms = plain login
    disable_plaintext_auth = no
    
    log_path = /dev/stdout
    
    passdb {
        driver = sql
        args = /etc/dovecot/dovecot-sql.conf.ext
    }
    
    userdb {
        driver = sql
        args = /etc/dovecot/dovecot-sql.conf.ext
    }
    ```

=== "dovecot/dovecot-sql.conf.ext"

    ```
    driver = pgsql
    
    connect = host=postgres dbname=postgres user=postgres password=postgres
    
    password_query = SELECT users.username as username, NULL AS password, 'Y' as nopassword FROM users LEFT OUTER JOIN tokens on users.sub = tokens.sub WHERE users.username = '%n' AND (expires IS NULL OR expires > NOW()) AND crypt('%w', REPLACE(tokens.token, '$2b$', '$2a$')) = REPLACE(tokens.token, '$2b$', '$2a$')
    user_query = SELECT username FROM users WHERE username = '%n'
    iterate_query = SELECT username FROM users

    ```

Restart the dovecot container to apply this configuration:

```shell
docker compose restart dovecot
```

You are now able to log in using an IMAP client by using the devicee password. 

!!! question "How to integrate other applications?"

    If you use other applications in production,
    look at the guide on how to [integrate applications](../how-to/app-integration.md).