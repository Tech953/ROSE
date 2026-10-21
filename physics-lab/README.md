# Rose.ENGINE / Physics Lab

A private, buildless browser workbench derived from the supplied Rose 0.18 art direction and requirements. Serve `dist/` as static files. No third-party scripts, remote assets, runtime backend, or API key is required.

## What works

- Six materials, five structures, four forcing modes and four quick-start scenarios.
- Age, exposure, use, friction, damping, force angle and magnitude controls.
- A fixed-step spring/damper emulation, structural damage, gravity/bounce/friction debris, and motion-coupled mechanism proxies.
- Matched baseline/current comparison, telemetry and integrity trace.
- Collapse → blocked footprint + disconnected service → finite once-only salvage → paid rebuilding. Repair consumes stock and retains material age. Setup/reset explicitly starts a new sandbox specimen and allocation.
- Continuous terrain, optional independent tactical lattice, three inspection scales, hidden-hex ground selection, and a matched visual review.
- Browser-local persistence, reduced motion, keyboard force shortcut and JSON experiment export.
- Unchanged source reference documents and the uploaded art-direction comparison under `dist/references/`, with SHA-256 provenance.

## Scope

The browser lab is a separate game-tuned proxy implementation. It does not run or replace the archive's Python solver, RPG systems, VREX–TETHER, source-world save files or prepared sprite banks. Unit labels are useful comparison scales rather than calibrated engineering predictions. The supplied archive's prior audit counts are not validation results for this lab.

## Verification

Run `node tests/validate.mjs` with the installed `@napi-rs/canvas` runtime dependency. The tests execute numerical controls, lifecycle accounting, original app event handlers in a modeled DOM and real native Canvas renders. Results are recorded in `qa/validation.json`. Set `ROSE_QA_OUTPUT` to a temporary directory to write render fixtures.

Browser layout, live pointer/touch hardware, assistive technology and real download behavior require supported browser QA; they are not established by the modeled DOM. No preview server is started where the supported browser skill is unavailable.

The tracked hosting manifest binds this source to its owner-private Site. Source and build output must be synchronized through the Sites helper before deployment; audience must remain owner-only unless the owner requests a change.
