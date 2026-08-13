# Changelog v16.2.0

## Features

* **Integrate Listmonk cadence system**: Refactored the cadence system to integrate Listmonk as the primary contact and sequence management platform, including the new Listmonk Settings doctype, API client, and webhook configuration ([8ef11d9](https://github.com/aurumorcom/frappe-cadence/commit/8ef11d93), [dda4f79](https://github.com/aurumorcom/frappe-cadence/commit/dda4f796)).

## Infrastructure

* **Migrate to bumpversion config**: Moved bumpversion configuration from `pyproject.toml` to a dedicated `bumpversion.toml` file and updated `.gitignore` ([392db39](https://github.com/aurumorcom/frappe-cadence/commit/392db399)).
* **Add release workflow**: Added a GitHub Actions workflow to automatically tag and release on pushes to the main branch ([bb132db](https://github.com/aurumorcom/frappe-cadence/commit/bb132dbd)).

## Docs

* **Update architecture documentation**: Removed the cadence provider abstraction layer from documentation and simplified architecture references across C4 diagrams, arc42, and workflows ([7279ff0](https://github.com/aurumorcom/frappe-cadence/commit/7279ff0d)).
* **Add listmonk skill documentation**: Added initial documentation for the listmonk skill detailing its purpose, configuration, and debugging procedures ([1c65de4](https://github.com/aurumorcom/frappe-cadence/commit/1c65de4e)).
