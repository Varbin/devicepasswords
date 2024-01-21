---
hide:
  - navigation
  - toc
---

# Overview

In the modern day, authentication with only passwords shows increasing weaknesses:
They are reused and often compromised.
Instead, multifactor authentication together with web-based single sign-on (SSO) is deployed.
Unfortunately, many applications are unable to implement such methods.
A classic example is email, where the only reliably widespread login method is using a password.

The device passwords fill this gap:
After signing in with SSO, users can create unique passwords for their devices to login to such systems.

## Documentation structure

The documentation is organized in the following way:

<div class="grid cards" markdown>

-   :material-clock-fast:{ .lg .middle } **How do I get started?**

    ---

    Get a running instance within a few minutes.<br>
    Integrates with Dovecot and Keycloak.

    ---

    [:octicons-arrow-right-24:{ .middle } Tutorial](tutorial/index.md)

-   :material-notebook:{ .lg .middle } **How can I…?**

    ---

    …integrate application? …customize it?<br>
    Reach your goals by following the how-to guides.

    ---
  
    [:octicons-arrow-right-24:{ .middle } How-To](how-to/index.md)
</div>
<div class="grid cards" markdown>
-   :material-lightbulb-cfl:{ .lg .middle } **Why does it work? Where are the limits?**

    ---

    Find answers for your questions here.<br>
    This section has the background information.

    ---

    [:octicons-arrow-right-24:{ .middle } Explanation](explanation/index.md)

-   :material-bookmark:{ .lg .middle } **What was it again?**

    ---

    Find all options and settings here.<br>
    Use this section to lookup technical details.

    ---

    [:octicons-arrow-right-24:{ .middle } Reference](reference/index.md)
</div>

<center markdown>
![](images/example.png)
</center>