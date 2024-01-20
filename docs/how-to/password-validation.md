# Configure database-side password validation

The most applications read the password (hash) from a database to compare it with the user provided ones.
An alternative is to validate the password inside the database by using a stored procedure.
The application now cannot even read the password hash.
Additionally, the 'last used' value of device passwords is automatically updated on each use.

Unfortunately, this technique has its downside: 

 - Some applications do need password (hash) access and do not work with database-side validation
   For example a RADIUS server performing MS-CHAPv2 authentication does need password access. 
 - The password must be transferred to the database server. 
   If query logging is enabled, this may lead to the plaintext password being logged.
 - It is highly database specific. Therefore, this guide will only cover some configurations.

## Postgres

This guide requires the [pgcrypto](https://www.postgresql.org/docs/current/pgcrypto.html) extension to be installed.
The [password hashing algorithm](password-hashing.md) must be either set to _bcrypt_ (recommended!) or _md5_crypt_.

### Enable and validate the pgcrypto extension

Enable the extension first, if not already enabled:

```postgresql
CREATE EXTENSION IF NOT EXISTS "pgcrypto";
```

Validate if the extension works by validating the `crypt(password, salt or hash)` works:
```postgresql
SELECT 
    crypt('valid', REPLACE('$2b$12$Se3ZAEkAhdiF8yOBSLWN/eKg5SVFGZdm2SweJiMwWkjs0nUPPlbqO', '$2b$', '$2a$')) = '$2a$12$Se3ZAEkAhdiF8yOBSLWN/eKg5SVFGZdm2SweJiMwWkjs0nUPPlbqO' as bcrypt_works,
    crypt('valid', '$1$y6yBElVm$.QubZncgyfJEM7BOd.grj/') = '$1$y6yBElVm$.QubZncgyfJEM7BOd.grj/' as md5_crypt_works;
```
If the extension works correctly, it will return the columns `bcrypt_works` and `md5_crypt_works` with a true value:
```
 bcrypt_works | md5_crypt_works 
--------------+-----------------
 t            | t
```

### Add the stored procedure

The following SQL statements create three functions:

 * `valid_password_no_audit(IN password TEXT, IN password_hash TEXT) RETURNS BOOLEAN`: Check if a password matches the given hash.
 * `valid_password(IN password TEXT, IN password_hash TEXT, IN token_id uuid) RETURNS BOOLEAN`: Check if a password matches the given hash matches. If it matches, this will audit this.
 * `valid_login(IN given_user TEXT, IN given_email TEXT, IN password TEXT) RETURNS TABLE(sub VARCHAR, username VARCHAR, email VARCHAR)`:
   Returns the subject claim, username and email address of a user only if the password matches a non expired token.
   If username lookup should not be based upon either username or password, set parameter to a blank value. 
   The last used value will be updated if the password is correct.

```postgresql
CREATE OR REPLACE FUNCTION 
    valid_password_no_audit(IN password TEXT, IN password_hash TEXT)
RETURNS BOOLEAN
LANGUAGE SQL
BEGIN ATOMIC 
    RETURN crypt(password, REPLACE(password_hash, '$2b$', '$2a$')) = REPLACE(password_hash, '$2b$', '$2a$');
END;

CREATE OR REPLACE FUNCTION
    valid_password(IN password TEXT, IN password_hash TEXT, IN token_id uuid)
RETURNS BOOLEAN
LANGUAGE plpgsql
AS $$
BEGIN
    IF valid_password_no_audit(password, password_hash) THEN
        INSERT INTO logs(date, "tokenId") VALUES (now(), token_id);
        RETURN TRUE;
    end if;
    RETURN FALSE;
END;
$$;

CREATE OR REPLACE FUNCTION 
    valid_login(IN given_user TEXT, IN given_email TEXT, IN password TEXT)
RETURNS TABLE(sub VARCHAR, username VARCHAR, email VARCHAR) ROWS 1
LANGUAGE plpgsql
AS $$
BEGIN 
    RETURN QUERY
        SELECT
            users.sub, users.username, users.email
        FROM
            users
        INNER JOIN
            public.tokens t on users.sub = t.sub
        WHERE 
            ((given_user <> '' AND users.username = given_user) OR
             (given_email <> '' AND users.email = given_email)) AND
            (t.expires ISNULL OR t.expires < now()) AND
            valid_password(password, t.token, t.id);
END;
$$;
```

The following statement shows an example validation function:

```postgresql

SELECT username FROM valid_login(:user, '', :password); 
```