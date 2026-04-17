## 1. Enterprise input contract

- [x] 1.1 Define the `web/enterprise` manifest contract, including route manifest shape, menu manifest shape, and expected source/public directory locations.
- [x] 1.2 Add build-time checks so the community build can detect whether `web/enterprise` exists and branch cleanly between community-only and enterprise-enabled assembly.

## 2. Build-time route assembly

- [x] 2.1 Implement a pre-build script that reads `web/enterprise/manifests/routes.json` and generates the required Next App Router page shims for each declared enterprise route.
- [x] 2.2 Ensure generated route files are recreated or skipped deterministically for community-only versus enterprise-enabled builds, without requiring hand-maintained community loaders.

## 3. Shared resource aggregation

- [x] 3.1 Extend menu aggregation to read `web/enterprise/manifests/menus.json` and merge enterprise menu patches into the community menu tree only when the enterprise link is present.
- [x] 3.2 Extend locale and static asset aggregation to scan `web/enterprise/src/**/locales` and `web/enterprise/public/**`, while preserving successful community-only builds when those inputs are absent.
