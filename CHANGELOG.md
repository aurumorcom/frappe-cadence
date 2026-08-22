## Breaking Changes

- **Rename contact to subscriber terminology**: Updated function names, parameters, database fields (`listmonk_contact_id` to `listmonk_subscriber_id`), and API references for consistency with Listmonk API conventions. Commits: [7a84e97](https://github.com/aurumorcom/frappe-cadence/commit/7a84e977), [fab3b19](https://github.com/aurumorcom/frappe-cadence/commit/fab3b19d), [4ac0bf9](https://github.com/aurumorcom/frappe-cadence/commit/4ac0bf96)
- **Renamed contact terminology and database fields to subscriber**: High severity breaking change affecting custom scripts, API references, and database fields. Migration path: Update any custom scripts, API references, and database fields referencing `listmonk_contact_id` to `listmonk_subscriber_id`.

## New Features

- **Add update_sequence_status method**: Added new method to `ListmonkClient` class to update sequence/campaign status via the Listmonk API. Commit: [d65bb6e](https://github.com/aurumorcom/frappe-cadence/commit/d65bb6ec)

## Improvements

- **Rename sequence to campaign terminology**: Updated terminology, functions, variables, database fields, and API endpoints from sequence to campaign to align with Listmonk API conventions. Commits: [cdf5e2f](https://github.com/aurumorcom/frappe-cadence/commit/cdf5e2fc), [0fa28d7](https://github.com/aurumorcom/frappe-cadence/commit/0fa28d72), [a8bee74](https://github.com/aurumorcom/frappe-cadence/commit/a8bee747)

## Documentation

- **Update Listmonk terminology**: Updated documentation, architecture diagrams, and component guides to reflect campaign and subscriber terminology. Commits: [6d8ecad](https://github.com/aurumorcom/frappe-cadence/commit/6d8ecad2), [4987f05](https://github.com/aurumorcom/frappe-cadence/commit/4987f052), [658bf08](https://github.com/aurumorcom/frappe-cadence/commit/658bf089)
