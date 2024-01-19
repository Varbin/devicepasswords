## Dovecot

To integrate dovecot with device passwords, 
you do need to use a supported database.
Grant the dovecot database user sufficient right to SELECT the users and tokens table.
See [dovecot configuration manual](https://doc.dovecot.org/configuration_manual/authentication/password_schemes/) what password hashing algorithms are supported.
The `ldap_sha512_crypt` hash does work.
For general database integration you can use the [dovecot configuration manual](https://doc.dovecot.org/configuration_manual/authentication/sql/#user-iteration) regarding SQL.

An example SQL query to look up 
```sql
SELECT email as user, token as password 
FROM users 
LEFT OUTER JOIN tokens t ON users."primary" = t.user
WHERE user = '%n'
```

!!! warning "Untested configuration"

    This configuration has not been tested.
