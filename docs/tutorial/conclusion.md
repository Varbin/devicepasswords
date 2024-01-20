You now have a running device manager instance, 
an IMAP server configured to use it, and a keycloak instance.

You may wish to the following tasks for a production integration:

  - Add TLS certificates, as credentials must not be transmitted over plain HTTP.
    I do recommend [caddy](https://caddyserver.com/) as a reverse proxy.
  - Integrate your own applications into the device password management.
    See [configure app integrations](../how-to/app-integration.md) for some examples. 
  - Use your own IdP instead of Keycloak.
    Generally all IdPs with support of OpenID Connect are supported.
    See [configure app integrations](../how-to/app-integration.md) for guides.
  - Run multiple instances for load balancing.