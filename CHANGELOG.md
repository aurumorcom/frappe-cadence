# Changelog v16.11.1

## Breaking Changes

- **Schema Simplification**: Replace list schema fields and rename listmonk identifiers ([cc5588bd](https://github.com/aurumorcom/frappe-listmonk/commit/cc5588bd))

## New Features

- **Safe Eval Utilities**: Expose frappe utilities in safe evaluation environment ([5521bed5](https://github.com/aurumorcom/frappe-listmonk/commit/5521bed5))
- **Filter Syntax Validation**: Add AST parsing to validate filter condition syntax ([1dd04650](https://github.com/aurumorcom/frappe-listmonk/commit/1dd04650))

## Improvements

- **Filter Condition**: Use get method for filter condition attribute access ([40f807c1](https://github.com/aurumorcom/frappe-listmonk/commit/40f807c1))
- **List Defaults**: Change default list type to private and cleanup request models ([c36f59a6](https://github.com/aurumorcom/frappe-listmonk/commit/c36f59a6))

## Bug Fixes

- **Field Identifiers**: Rename Listmonk field identifiers across doctypes ([877d339c](https://github.com/aurumorcom/frappe-listmonk/commit/877d339c), [9a34ef6e](https://github.com/aurumorcom/frappe-listmonk/commit/9a34ef6e))
- **Datetime Serialization**: Convert datetime objects to ISO format strings ([45e4867c](https://github.com/aurumorcom/frappe-listmonk/commit/45e4867c))
- **Numeric Comparisons**: Handle string numeric values using cint in AST conditions ([82278f50](https://github.com/aurumorcom/frappe-listmonk/commit/82278f50))
- **Frappe Import**: Handle missing frappe import gracefully with try-except ([579037af](https://github.com/aurumorcom/frappe-listmonk/commit/579037af))

## Other

- **Subscriber Tests**: Add mock for create_subscriber in subscriber test ([2e0f0490](https://github.com/aurumorcom/frappe-listmonk/commit/2e0f0490))
- **Filter and Job Tests**: Add validation and unit tests for filters and jobs ([83768692](https://github.com/aurumorcom/frappe-listmonk/commit/83768692), [6382fa86](https://github.com/aurumorcom/frappe-listmonk/commit/6382fa86))
- **List Assertions**: Add assertions to verify list type and optin settings ([fb7ef015](https://github.com/aurumorcom/frappe-listmonk/commit/fb7ef015))
