<h1><img src="docs/images/icon.svg" height="40"> Device password management</h1>
<h3>Individual passwords for services without 2FA</h3>

<hr>
<a href="https://github.com/Varbin/devicepasswords/actions/workflows/docker-image.yml">
   <img src="https://github.com/Varbin/devicepasswords/actions/workflows/docker-image.yml/badge.svg" alt="Docker Container CI">
</a>

<a href='https://devicepasswords.readthedocs.io/?badge=latest'>
   <img src='https://readthedocs.org/projects/devicepasswords/badge/?version=latest' alt='Documentation Status' />
</a>
<hr>


Device passwords fix the gap for accessing resources when clients do not support
the companies single-sign-on protocol.
The most prominent example is e-mail, 
where OAuth requires both server and client integration,
which is usually not feasible.

This software allows users to manage their own device passwords.

![Screenshot](docs/example.png)

## Caveats

 - Only a single identity provider is supported.
 - Username and e-mail-address of a user is updated (only) on user login.
 - It is assumed the identity provider controls access to its apps and user registration.
 - The application assumes email-adresses and usernames are unique for your IdP.
   If you use a "public IdP" (such as Microsoft or Google), restrict app access 
   to your tenant.
