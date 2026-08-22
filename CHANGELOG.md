## Features

* **Listmonk User ID Custom Field**: Added the `listmonk_id` custom field to the User doctype for mapping external newsletter subscribers ([02a6034](https://github.com/aurumorcom/frappe-cadence/commit/02a60345)).
* **User Sync Job and Client Method**: Implemented the `get_listmonk_users` client method alongside a dedicated user synchronization job for background processing ([7745b60](https://github.com/aurumorcom/frappe-cadence/commit/7745b606)).
* **Automatic Setup and Hooks**: Configured an `on_update` document hook for automatic setup enqueueing, backed by comprehensive integration, unit, and e2e test suites ([33a85e8](https://github.com/aurumorcom/frappe-cadence/commit/33a85e81)).
