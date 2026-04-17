## 1. Overlay scaffolding

- [x] 1.1 Create the root-level `enterprise/{web,server}` overlay directory structure and add TypeScript alias/stub support so community builds can resolve optional enterprise portal modules safely.
- [x] 1.2 Extend the menu loading flow to read and merge enterprise menu patch sources alongside existing community menu definitions.

## 2. Portal extraction

- [x] 2.1 Remove `portal_settings` from the community `system-manager` base menu and add an enterprise patch that injects the portal menu under the existing settings group.
- [x] 2.2 Move the current portal settings page implementation into the enterprise overlay and convert `/system-manager/settings/portal` into a stable loader entry that renders the enterprise implementation or a controlled fallback.

## 3. Compatibility and validation

- [x] 3.1 Preserve the existing portal URL and portal settings data contract so the extracted enterprise page continues using current settings keys and APIs unchanged.
- [x] 3.2 Verify community behavior (no portal menu, safe fallback) and enterprise behavior (portal menu injected, portal page renders) through the existing web lint/type-check flow.
