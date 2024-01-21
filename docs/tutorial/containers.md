# 1. Create the containers

Use the following Docker Compose file:

=== "docker-compose.yml"

    ```yaml
    version: "3"
    
    services:
      devicepasswords:
        image: ghcr.io/varbin/devicepasswords:trunk
        environment:
          DP_OIDC_DISCOVERY_URL: "http://127.0.0.1:8080/realms/master/.well-known/openid-configuration"
          DP_OIDC_CLIENT_ID: "device-password-manager"
          DP_OIDC_CLIENT_SECRET: "BBpwYZEtC3IT9zfvLlulBuaegK5Bi2no"  # Add your secret here
          DP_PASSWORD_HASH: "bcrypt"
          DP_SQLALCHEMY_DATABASE_URI: "postgresql://postgres:postgres@127.0.0.1/postgres"
          GUNICORN_CMD_ARGS: "--bind=127.0.0.1:5000"
        depends_on: [postgres, keycloak]
        # Only required as devicepasswords and keyloak run on the same machine as
        # containers. If your computer has an external hostname, you can replace
        # all references to 127.0.0.1:5000 and 127.0.0.1:8000 with your external
        # hostname.
        network_mode: host
    
      keycloak:
        image: quay.io/keycloak/keycloak:23.0
        environment:
          KEYCLOAK_ADMIN: admin
          KEYCLOAK_ADMIN_PASSWORD: Pa55w0rd
          KC_HOSTNAME_STRICT: false
        command: start-dev
        network_mode: host
    
      dovecot:
        image: alpine
        volumes:
          - ./dovecot:/etc/dovecot
        entrypoint: "sh -c 'apk add --no-cache --upgrade dovecot dovecot-sql dovecot-pgsql dovecot && dovecot -F'"
        ports:
          - '127.0.0.1:143:143'
    
      postgres:
        image: postgres
        environment:
          POSTGRES_PASSWORD: postgres
        ports:
          - '127.0.0.1:5432:5432'
    ```

Start the containers with `docker compose up`.
You can check the container state with `docker compose ps`,
the output should list four containers: 

```
NAME                        IMAGE                                  COMMAND                                                                                          SERVICE           CREATED          STATUS          PORTS
contrib-devicepasswords-1   ghcr.io/varbin/devicepasswords:trunk   "gunicorn -b 0.0.0.0:8000 devicepasswords:create_app()"                                          devicepasswords   12 seconds ago   Up 11 seconds   127.0.0.1:5000->8000/tcp
contrib-dovecot-1           alpine                                 "sh -c 'apk add --no-cache --upgrade dovecot dovecot-sql dovecot-pgsql dovecot && dovecot -F'"   dovecot           8 minutes ago    Up 8 minutes    127.0.0.1:1143->143/tcp
contrib-keycloak-1          quay.io/keycloak/keycloak:23.0         "/opt/keycloak/bin/kc.sh start-dev"                                                              keycloak          8 minutes ago    Up 8 minutes    127.0.0.1:8080->8080/tcp, 8443/tcp
contrib-postgres-1          postgres                               "docker-entrypoint.sh postgres"                                                                  postgres          8 minutes ago    Up 8 minutes    5432/tcp
```