# Rose 0.13.1 - Physics emulation systems update

Rose now has a bounded local rigid-body component and practical workshop mechanisms around the retained VREX-TETHER model. Measurements, correlations, numerical tests and energy records remain on the authoritative host. Gameplay exposes fitted hardware, its operating condition and the resulting resource or construction changes.

## Guidance and implementation

The supplied *Game Physics Engine Development* by Ian Millington and *Anatomy of a Physics Engine* by Erwin Coumans guide the mechanics pipeline. Both PDFs are retained unchanged in `reference/physics/`. The 481-page textbook was indexed, with selected integration, spring, contact and planar rotation sections reviewed; the complete 40-page presentation text was reviewed, with selected diagrams rendered. `source-register-v013.json` records hashes and exact coverage.

| Component | Implementation | Role |
|---|---|---|
| Body and force records | `physics.py` | Persistent position, velocity, angle, angular velocity, mass and shape inertia; explicit gravity and applied force/torque |
| Springs and damping | `physics.py` | Equal/opposite endpoint forces, local attachment torque, spring potential and time-dependent damping |
| Collision pipeline | `physics.py` | Sorted AABB broadphase; circle/circle, circle/oriented-box and oriented-box SAT contacts |
| Contact constraints | `physics.py` | Up to ten impulse iterations, restitution, Coulomb friction and positional correction |
| Fixed local motion | `physics.py` | Axial carriage constraints, quiet connected spring sets and wake on nonzero input |
| VREX load connection | `machines.py` | One downstream receiver per field, with monotonic work receipts after committed RK4 steps |
| World applications | `machines.py` | Finite pump transfers, reserved construction work and mechanical fatigue |
| Internal comparisons | `physics.py`, `machines.py` | Network-to-tether, tether-to-mechanism and identity-scoped particle-to-network cross-correlation |

The mechanical solver uses symplectic Euler at **1/256 model time unit**. The retained VREX equations, work channels and RK4 solver remain unchanged; an optional callback observes committed steps. An independent regression verifies identical upstream coordinates, traces and ledgers with and without that callback.

The component supports sixteen fitted local mechanisms, at most 32 bodies and 32 springs per solver, and a 256-substep budget per advance. Substeps also bound predicted displacement relative to collider thickness. Over-budget motion is rejected before stepping. Existing world-map travel, tactical hex movement and AP costs retain their own authority.

The 0.13.1 audit applies rail mobility consistently to contact impulses/corrections, force response and spring dashpots. Zero rails, dynamic masses below 0.0001 and perpendicular work receipts are rejected before mutation. Assembly shutdown preserves static shapes and authored dynamic angles; it requires zero gravity/applied loading and zero-potential assembly origins. This helper is intended for the fitted rigs. Read-only energy audits also validate ownership channel bounds and rail geometry. See [the audit](PHYSICS-AND-GRAPHICAL-FIDELITY-AUDIT.md) for independent regressions and remaining emulation limits.

## Practical use in the game

Approach an adjacent hex of a maintained, enabled, connected workshop. Its physical action menu offers **Fit Pump**, **Fit Press** and **Fit Damper**, each consuming two personal scrap and one survival cycle, including on a failed metallurgy check. Existing motion must be disengaged before refitting.

**Operate Machine** performs a Tech/Fractech check using the workshop faction and existing contextual reputation rules. It consumes one actual public power and one survival cycle. Successful input starts the finite source drive; a failed input becomes heat. **Disengage Machine** uses the same physical approach and a check, dissipates remaining motion and drive storage, and refunds no power. Typed equivalents are `fit pump`, `fit press`, `fit damper`, `operate machine` and `disengage machine`; a workshop ID can follow `at`.

| Hardware | Practical effect | Boundaries |
|---|---|---|
| Transfer pump | One unit of existing local source water enters the public cistern after sufficient useful work | Requires an operating connected cistern, real source water and store capacity; maximum one transfer per world cycle |
| Construction press | One actual work step on an owned active project within three workshop hexes | Materials must already be reserved; the machine has its own contributor identity and cannot create personal repair-contract proof |
| Vibration damper | Dissipates its received load with a lower mechanical fatigue factor | Produces no water, construction credit or returned public power; it does not repair building condition |

Pump and press output comes from their carriage damping: 65 percent of removed kinetic energy is terminal useful work, with the remainder recorded as heat. Work thresholds, efficiencies, fatigue and local geometry are authored dimensionless game rules. Blocked jobs retain at most one job's progress. Completed jobs consume that progress once. Construction completion still uses the existing project escrow, site, stage and infrastructure-network rules.

World effects are committed after weather, resident work and final utility wear. Source outages dissipate both source and mechanism storage. Fatigue that drops workshop condition below 30 shuts down before a pump transfer or construction step. Repairing or reconnecting a source does not restart it or recreate spent energy.

## One-owner work accounting

The existing VREX passive-load term remains a source output. Only its newly committed increment can enter the downstream carriage. A monotonic cursor prevents a retained or repeated packet from being credited again; a new fitting begins at the current source-load total and cannot claim earlier output.

The source ledger and downstream ledger remain separately inspectable. Their combined audit removes the internal transfer once:

```text
source input + declared initial/external mechanical work
  = source bank + source mechanical storage + downstream storage
    + source heat + downstream heat + terminal useful work
    + source load not delivered to this mechanism + measured residual
```

The source tolerance remains **1e-6**. The downstream symplectic solver and combined emulation use a declared **1 percent normalized error limit**. Heat is not altered to erase integration error. Output is stopped if the combined ownership or numerical check fails. Independent tests verify that unowned downstream input cannot create world output.

## Cross-correlation and persistence

Dense local samples retain the oscillator mean, tether displacement/velocity and carriage displacement/velocity. Pearson correlations scan up to sixteen positive and negative lags. Positive lag means the response follows the reference. Constant signals return **Insufficient Variation**; irregular sampling returns **Nonuniform Sampling**. A peak is an association within the declared window, not proof of causation or a new energy channel.

Particle comparisons use the retained source IDs at the world-cycle clock. Their sampled population is kept consistent, and correlation never crosses an identity-set change. These world-cycle lags are distinct from the dense model-time lags. Changing source parameters or application starts a new measurement segment; up to eight prior segment summaries remain retained.

SQLite saves preserve the full solver, load cursor, bounded traces, correlations, job progress and attribution. Ordinary snapshots omit the mechanism and VREX archives before copying them. NPC prose receives observable world context; the internal engineering records and source test actions remain excluded. No new instrument panel, chart or measurement export button is added to gameplay.

## Development checks

Run `python3 physics_bench.py` from the `rose` directory for the isolated application benchmark. It executes nine controls: loaded, unloaded and no-input cases for each hardware type, with four explicitly supplied diagnostic inputs in each driven case. It does not touch game stock or clock.

Authenticated development requests retain `physics_export` and `physics_diagnose`, alongside the existing VREX APIs. Exports are observational and omit session tokens; the tests use isolated copies. These operations have no gameplay buttons.

The coarse 1/128 press benchmark failed its unchanged 1 percent limit at approximately 0.012304 normalized residual. Refinement to 1/256 reduces that residual to approximately **0.006221**; 1/512 reduces it further to approximately **0.003121**. The failed coarse result is retained in the validation record. All nine final controls pass, while unloaded and no-input cases produce zero downstream work.

The full suite passes **330 Python tests**. Live HTTP/native-canvas checks verify fitting, paid operation, hidden records, ordinary-play stepping, read-only export and dissipative disengagement. `VALIDATION.md` and `validation-results-v0131.json` record exact verification and its scope. Original art sources and indexed sprite assets are retained; renderer surface/lighting fixes are recorded separately in the audit.

This is planar game emulation with primitive contact geometry. It does not implement a full 3D mesh solver, all-speed continuous collision detection, fluid fields, fracture or cloth, and it has no physical-unit or laboratory calibration. The modeled DOM checks do not establish full browser layout or Windows launch behavior.
