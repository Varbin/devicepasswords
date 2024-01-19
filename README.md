# Simple device password management

![Screenshot](docs/example.png)

Device passwords fix the gap for accessing resources when clients do not support
the companies single-sign on protocol. The most prominent example is e-mail, 
where OAuth requires both server and client integration.

This software allows users to manage their own device passwords.

[Read the docs](https://devicepasswords.readthedocs.io/)

## Caveats

 - Only a single identity provider is supported.
 - Username and e-mail-address of a user is updated (only) on user login.
 - It is assumed the identity provider controls access to its apps and user registration.
 - The application assumes email-adresses and usernames are unique for your IdP.
   If you use a "public IdP" (such as Microsoft or Google), restrict app access 
   to your tenant.
