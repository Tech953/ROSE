# Rose 0.13.0 — VREX background physics component

VREX is an integrated game physics and measurement subsystem. It runs a finite driven Duffing network, modulated spring tether, passive load, owned return channel and bounded controller. Directed dialogue links regenerate through local rules. Retained particle IDs join the existing particulate engine to VREX observations; explicit stimulus settings permit off-screen development tests alongside ordinary play.

## Gameplay integration

VREX measurement and testing run behind the gameplay view. There is no VREX dashboard, measurement chart, audit control, system-export button or VREX workshop menu. Ordinary state polling omits the internal solver state, observation histories, diagnostics and measurement journal. These fields are excluded before the display copy is made, avoiding repeated copying of the archive.

The authoritative host still owns the full component. Existing configured fields advance on ordinary world cycles, track particle IDs, conserve their finite bank and persist in SQLite. Removing the display does not reset an active system, discard a record, disable numerical tests or supply new energy. Unconfigured fields keep the previous lazy initialization behavior; this presentation update does not automatically start or fund drives.

NPC resonance dialogue and narrator input use perceptible world context. VREX technical lore remains in the source register for engineering use, without being selected by ordinary NPC briefings. The optional intent interpreter cannot propose internal physics actions.

The physics emulation extension adds practical pumps, presses and dampers to physical workshop menus. An optional committed-step observer transfers only newly measured passive-load output into their separate downstream ledger. Source equations and RK4 results are retained; ordinary snapshots also omit the mechanism archive. See [PHYSICS-EMULATION-GUIDE.md](PHYSICS-EMULATION-GUIDE.md) for the combined ownership audit, guarded hardware actions and relational cross-correlations.

## Off-screen development interface

The existing authenticated host API remains available for development and future integration. Read-only `vrex_export` returns the full retained state and energy audit; `research_export` returns the latest recorded measurement. Both preserve revision and omit session tokens from their exports. Full saves retain canonical state; normal gameplay snapshots provide the smaller presentation projection.

Internal `act` intents retain configuration, stimulus, paid drive, perturbation, tests, stop and graph expansion. They are absent from gameplay help and object menus. Development clients supply the existing room code, seat token and current revision. For example, the intent `{"action":"vrex_configure","target":"WORKSHOP_ID|returned"}` selects the Return preset; `{"action":"vrex_stimulus","target":"WORKSHOP_ID|0.42:1.9"}` changes the stimulus. The registered actions are:

| Action | Effect |
|---|---|
| vrex_configure | Choose Static, Modulated, Loaded, Returned or Gain while dissipated |
| vrex_stimulus | Set bounded force/frequency with continuous phase |
| vrex_pump | Meter one public power into the finite bank |
| vrex_stop | Dissipate storage into heat |
| vrex_perturb | Disturb forty percent of dialogue links |
| vrex_expand | Add two unique states at rest, up to twenty |
| vrex_diagnose | Test isolated copies without advancing the live clock |
| particle_audit | Capture the current scoped systems measurement |

Source, adjacency, skill/context/reputation, finite stock, combat, pause, void and revision guards are retained. Internal physical adjustments use Tech/Light and one survival cycle, including on setback; tests use Perception/Light. Failed interpretation preserves measured data. Drive work still consumes actual public power. The four-unit bank accepts up to 0.8 per successful excitation; rejected input becomes heat.

## Generation and physics

Twelve unique states begin at zero mechanical energy, mapping to retained particle IDs and their sampled local coordinates. Each oscillator stores displacement, velocity and natural frequency. RK4 advances coordinates, drive phase, stiffness and work channels together at dt=1/32. One world cycle advances 0.5 model time units.

Oscillators use linear/cubic restoring forces, damping, explicit periodic drive and optional bounded controller. Directed link gains set dissipative velocity coupling. The oscillator mean couples reciprocally to the tether, with its interaction potential included in storage. The tether uses positive stiffness, damping and a nonnegative passive load. Changing stiffness contributes explicitly measured modulation work.

| Preset | Modulation | Load | Return fraction | Bounded gain |
|---|---:|---:|---:|---:|
| Static | 0 | 0 | 0 | 0 |
| Modulated | 0.24 | 0 | 0 | 0 |
| Loaded | 0.24 | 0.18 | 0 | 0 |
| Returned | 0.24 | 0.18 | 0.5 | 0 |
| Gain | 0.24 | 0.18 | 0.5 | 0.08 |

Nearest-three directed links carry gain and phase. Triangle loops report gain products and wrapped phase sums; local reference shifts cancel around each loop. Recovery receives local states and current links, with no evaluator reference in its API. These are defined software topology rules; link phases do not add mechanical energy or implement QCD.

Expansion adds two zero-energy states at a time, preserving existing IDs and coordinates, up to twenty. Zero storage is required so changing the collective coordinate cannot introduce energy. Added states are explicitly unmapped to baseline particles. The world permits at most eight concurrently driven VREX fields within its 256-field archive. Each field retains 96 motion samples, 96 particle observations and 32 stimulus events.

## Particulate and temporal tracking

Observations join by source particle ID. Rows retain displacement, velocity, amplitude, local oscillator energy, model phase, source phase/position, source kinetic metric and frequency. Sampling temporarily marks a source absent; redepositing the same ID restores the join. Source identity and mass remain authoritative.

The existing particle clock reports radians per world cycle; VREX reports radians per model time unit. Phase residuals use wrapped differences with declared origins. Rate estimates require an earlier sample, and changes above π between samples can alias. These are usable in-game comparisons without calibration to seconds. Heuristic particle kinetic metrics and VREX energy are separate quantities and are never added into one ledger.

The temporal test compares an RK4 forward position against a second-order prediction at an offset of 1/32 model time unit, recording the normalized difference. This offset is a reference for comparison, not a new force. Stimulus events preserve operator ID, cycle, force, frequency, preset, source and cumulative input.

## Finite energy ownership

Storage includes the bank, oscillator and tether kinetic/potential energies and mean-to-tether interaction potential. Positive drive, modulation and controller work debit the bank. A substep cannot borrow from a future return. If it cannot be financed, the drive stops and mechanics coast with frozen modulation and drive phase.

Negative drive/modulation work enters one return channel. The selected fraction reenters the bank once; the rest becomes heat. Passive-load work goes to a measured sink and cannot mint public power or inventory. Damping, rejected input, unrecovered returns and bank overflow also become heat.

```text
residual = paid input - bank - mechanical storage - load output - heat
normalized residual = abs(residual) / (input + storage + load + heat + 1e-12)
```

A normalized residual above 1e-6 fails. Heat is never edited to hide numerical error. Internal drive, modulation, controller, return and reuptake counters remain inspectable. Optical energy keeps its own separately paid ledger.

Source failure dissipates storage, retains the workshop binding and prevents automatic restart. Final infrastructure wear is reconciled in the same cycle. Repair and reenabling cannot recreate energy; a fresh paid excitation is required. Optical/VREX adjustments are attributable but cannot serve as maintenance-contract repair proof.

## Practical tests and records

| Test | Computation | Recorded result |
|---|---|---|
| Convergence | Same configuration at dt=1/8, 1/16, 1/32 for twelve time units | State differences, refinement ratio and each ledger |
| Blind recovery | Forty-percent disturbance, forty local recovery steps, randomized control and gauge shift | Recovery score and loop invariance with reference hidden |
| Passive load | Static cycle null, loaded return run and bounded-gain control | Positive output, explicit work and closure |
| Collective order | Baseline, ±3% detuning, disabled coupling, perturbed initial phase, another seed and twenty states | Stroboscopic spectra, recurrence, coherence, participation and recurrence lifetime over 24 periods |
| Temporal comparison | RK4 forward positions versus offset kinematic prediction | Approximation residual |
| Metered duration | Explicitly supplied runs over 24 drive periods | Input/output accounting over that finite duration |
| Laboratory | No apparatus attached | Not Run |

The shipped example reports convergence, blind recovery, passive load and metered duration Pass; collective order is **Not Detected**. A screening Candidate would remain a numerical candidate. This finite driven network or a programmed optical echo does not establish a many-body DTC.

Reports retain seed, geometry, settings, field, operator, workshop, source hash, version and configuration hash. Changing preset, force, frequency or state count marks a prior report **Stale / Rerun**, preserving its original values. System measurements retain sixteen audit records. Read-only exports do not change revision or include session tokens. Particle JSON cannot inject VREX storage, observations or results; full SQLite saves preserve canonical state.

## Reference and verification

The complete supplied twelve-page systems reference remains unchanged at `reference/science/vrex-v3-systems-reference.pdf`, available through the development reference route `/vrex-reference.pdf`. SHA-256: `7d7b774360ed65f995f46b9726e8ced8e8c333089aa8919bff7c72e8c7d4cd73`. All 22 equation mappings are in `reference/vrex-systems-v012.json`; historical source records remain intact.

The update is checked against independent harmonic/conservative null solutions, finite exhaustion, owned return, nonnegative load, convergence, identity joins, outages, stale revisions, saved replay and guarded imports. The HTTP/interface flow walks to a real workshop and supplies power through normal collectors. Off-screen development requests configure, drive, test and export VREX while the game displays no measurement panels or test actions. An ordinary Wait advances its hidden observations. Existing independent numerical checks remain in place. See `VALIDATION.md` for final results.

The Blender source and sprite bank are preserved. Full browser layout, Windows launch, real audible playback, LAN sessions and human balance remain unverified. Units are dimensionless; legacy replay, physical or quantum calibration, laboratory certification and experimental time-crystal validation are outside this implementation.
