# Security Policy

## Reporting a vulnerability

Please report vulnerabilities privately through GitHub's private vulnerability reporting:
https://github.com/lukislp/portfolio/security/advisories/new

Do not open a public issue for security problems. You will get an acknowledgement within a few
days and a fix or mitigation plan before any public disclosure.

## Scope

This repository contains a static personal website with no backend, no form handling and no
user data. The interesting surface is therefore the delivery configuration rather than the
content: the response headers in `public/_headers` (including the Content-Security-Policy) and
the GitHub Actions workflows.

## Supported versions

Only the current state of `main` is deployed and receives fixes.
