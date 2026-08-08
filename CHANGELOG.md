# Changelog v16.1.1

## Improvements

- **Standardize n8n error log titles**: Updated error log titles to use fully qualified function names instead of generic descriptions for improved tracking and debugging ([de2c1ff](https://github.com/aurumorinc/frappe-cadence/commit/de2c1ffc)).
- **Add integration and error handling tests**: Added comprehensive test cases for `process_schedule` n8n integration failure scenarios, retry logic, and communication handling verification on callback failures ([891369f](https://github.com/aurumorinc/frappe-cadence/commit/891369f0), [f183ee6](https://github.com/aurumorinc/frappe-cadence/commit/f183ee61)).

## Fixes

- **Update cadence error handling**: Refined error handling for AI generation failures via Multi Channel Cadence status updates, added proper HTTPS URL handling in callbacks, simplified the cache key format by removing the `ai_req:` prefix, and ensured template status updates persist on API failures ([94eb695](https://github.com/aurumorinc/frappe-cadence/commit/94eb695c), [2f19be9](https://github.com/aurumorinc/frappe-cadence/commit/2f19be9c)).

## Docs

- **Remove developer checklist section**: Removed the redundant "✅ Developer Checklist" section from the pull request template ([1893135](https://github.com/aurumorinc/frappe-cadence/commit/18931354)).

## Other

- **Restructure cadence execution logic**: Reorganized the cadence execution flow for better readability, moved cache validation earlier in the lifecycle, consolidated webhook URL construction, and introduced explicit error handling for trigger failures and Sift configuration ([219e71b](https://github.com/aurumorinc/frappe-cadence/commit/219e71b4), [56bcfd0](https://github.com/aurumorinc/frappe-cadence/commit/56bcfd09)).
