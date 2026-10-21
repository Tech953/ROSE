# Rose resonance and source integration

**Rose 0.13.0 · 3 October 2026 · persistent world schema 1**

Rose now connects its resonance inspector to a finite optical reservoir, individual particle frequencies, workshop condition and public power. The recovered blue projection reference informs the instrument's cyan palette and facet shading. It is accessible through the game. The original JPEG is 146 × 121 pixels; this update adds an authored instrument motif rather than reconstructing high-resolution geometry from it.

## Using the instrument

1. Select a workshop in **Scene Objects**, then choose **APPROACH SELECTION**. Its local actions include **Look → READ RESONANCE**, **Skill → TUNE SPECTRUM**, and **Use → EXCITE / 1 PUBLIC POWER** or **QUENCH RESONANCE**. The **INFO-PARTICLES / PERCEPT EXPEDITIONS** inspector remains an alternative view of the same field instrument.
2. Approach an adjacent hex of an enabled, connected workshop with condition at least 30. Choose Jade, Amber, Cyan, Rose or Violet, then Steady, Programmed Alternating or Boundary Modulation. **TUNE** applies a Light skill check with the existing context, reputation and companion modifiers. A failed roll retains the previous setting. Tuning uses one survival/world cycle and no public power.
3. From an adjacent maintained workshop, **EXCITE / 1 PUBLIC POWER** consumes one unit from the actual public store, including on a setback. An empty store refuses the action. Operating wind collectors replenish stores on infrastructure cycles, six cycles by default.
4. Read the material-response curve, chosen carrier, current exposure, thermal load, energy balance and retained 48-cycle signal history. The inspector's numbers and colors come from the current saved field. Pending tuning choices survive polls.
5. From the assigned workshop's adjacent approach, **QUENCH** requests a Light check to divert the remaining optical reservoir into heat. It refunds no public power. Overheating and a disabled, damaged or disconnected source trigger an automatic quench.

Baseline optical work is unavailable during remote observation, combat, a paused clock or a `void_null` expedition. Observation still displays registered measurements. The host pause required for particle JSON import remains separate from physical instrument work.

## Workshop scope, repair and shared play

Each materialized baseline field has one shared reservoir and one assigned workshop. Local menu requests retain the selected building's exact ID. They cannot silently use a different healthy workshop. A live reservoir must be quenched at its assigned workshop before tuning or pumping from another workshop. A cold reservoir can be rebound after physically approaching the new workshop.

Tuning, excitation and manual quenching require the same adjacent, maintained workshop approach through object menus, inspector buttons and typed commands. The current network is checked directly, including broken links and failed power collectors. Ordinary six-cycle utility wear is reconciled before publishing the resulting state, so a source crossing below condition 30 is quenched in that cycle.

An outage preserves the source ID, band and response mode while diverting remaining energy into heat. Repair spends the normal scrap and cycle cost; enable isolated equipment separately. A workshop whose recorded utility status remains offline or in power deficit must complete an operating utility cycle before accepting optical work. Repair and reconnection never replenish optical energy. Restart by spending a fresh public-power input.

**READ RESONANCE** records a Perception/Light check and the workshop's faction context. It spends no AP, supplies or survival cycle, and preserves world travel and combat turns. Remote readings are marked as projections. A full particle archive reports an unresolved reading instead of inventing an empty reservoir. Successful and failed physical attempts record actor, action and outcome in the workshop ledger; optical work does not count as contract repair evidence.

All seats observe the same saved field instrument. Each operator still needs a physical approach, a contextual skill check and current public stock. Requests use the saved revision; a stale second-player action is refused before spending anything. Pending local tuning choices persist across polls and selection changes within the field, and clear on a different world, seat or field. Dropdown arrow keys and focus are retained in the object menu.

Example text commands:

```text
tune spectrum cyan alternating
excite particles
inspect particles
quench resonance
ask about resonance
```

The resonance dialogue topic uses the existing resident system, character designation, conversation memory and checks. It includes the actual rig setting and stored energy. The optional narrator receives current optical measurements; prose cannot alter the rig or grant access.

## Finite behavior

All quantities below are **optical game units**. Frequencies have no conversion to Hz or wavelength; thermal load has no conversion to kelvin.

| Quantity | Implemented rule |
| --- | --- |
| Input | Each attempted excitation records 1 optical input unit because 1 public power was consumed. |
| Accepted energy | Successful drive accepts up to 0.8 units, within capacity 4. Remainder enters the heat ledger. A failed drive puts its full unit into heat. |
| Line response | Mass-weighted Lorentzian profiles centered on each retained particle's frequency. Physical particles have weight 1, other elements 0.65. Moisture and recorded degradation broaden the authored line width. |
| Carrier | Amber 0.75, Jade 1.00, Cyan 1.40, Rose 1.65 and Violet 1.90. Colors are artistic RGB assignments. |
| Gain threshold | Stored energy at least 0.25 increases the release fraction. This is a game proxy for pumped gain, not a population-rate solver. |
| Decay | Each new world cycle divides the retained reservoir into damping heat, emitted energy and remaining energy. Output also depends on actual phase coherence and spectral response. |
| Steady mode | Positive decaying optical response. |
| Alternating mode | Programmed signal polarity changes every four cycles, repeating after eight. Brightness uses positive emitted energy. This is an authored echo, not evidence of an emergent many-body phase. |
| Boundary mode | A bounded periodic release modifier redistributes a paid reservoir. It creates no particle identities or mass. |
| Thermal controller | Thermal load cools faster in a wet field. Load at least 2.5 quenches remaining energy. Controller resets retain their ledger. |
| Habitat | Online jade exposure at least 0.04 adds at most 1 growth per cycle when moisture is at least 35 and soil health at least 25. Online rose/violet exposure at least 0.12 adds at most 1 stability stress. These couplings are authored ecological rules. |
| Scene light | A maintained source workshop adds a condition-gated colored emitter. Existing wall blocking, alpha masks, shadow registration and lighting display modes apply. The sprite bake is unchanged. |

The optical ledger obeys `input = retained + emitted + heat`, up to floating-point rounding. The interface displays its residual. It accounts for this reservoir only. Aurora-derived particle forces and kinetic energy remain separate heuristic game measurements; this update does not imply that those equations form a conservative quantum solver.

SQLite retains settings, source identity, energy totals, thermal load and history. Existing 0.9 fields acquire a cold reservoir with zero energy. Particle imports cannot inject optical energy or controller settings. Particle JSON remains an object exchange format; back up the host database for a complete world save.

## What the references contribute

The ten prior supplied files were recovered and indexed. Their five PDFs contain 503 pages in total; four CSV exports contain 10,871 parsed records. The additional twelve-page VREX v3 systems reference was read in full, rendered on every page and retained unchanged in the engine; the combined corpus now contains six PDFs and 515 pages. Review focused on the relevant sections below. Full textbook indexing does not constitute a line-by-line audit of every chapter. Seventeen selected PDF pages were rendered to check figures, equations and the molecular report's missing text layers. Exact file hashes and review coverage are in `reference/science/source-register-v011.json`.

| Supplied file | Reviewed material | Rose use and evidence boundary |
| --- | --- | --- |
| Time Crystal Commentary.pdf | All eight PDF pages | Temporal motifs. Ground-state/no-input statements conflict with its own driven-system discussion and require the qualifications below. No lossless generator is inferred. |
| Time Crystal Commentary.csv | Matching title and text | Export of the same commentary; not an independent experiment. |
| Time Crystal Overview - Copy.csv | Zaletel et al., 2023, sections I–II and opening of V | Rigid subharmonic response, interactions, ergodicity and driven/dissipative distinctions. Rose's programmed echo does not claim these many-body properties. |
| Dynamical_Casimir_Effect_.pdf | Thesis introduction, moving boundaries, retarded approximation and conclusions; selected equation/figure pages | Boundary-modulation motif with an explicit energy source. The thesis itself records limits of its approximate retarded approach. Its force equations are not ported. |
| Dynamical_Casimir_Effect_.csv | Matching thesis title and conclusions | Text export of the same thesis. Ragged rows and broken mathematical layout are unsuitable as numeric measurements. |
| Lossless Energy Transfer Commentary.csv | Haddad et al., 2007; introduction, hybrid-system framework and thermodynamic conclusion | Energy ledger and dissipating controller reset. The paper stabilizes a lossless plant through dissipation; it does not establish an energy-generating device. Rose does not implement its general stability or entropy theorem. |
| Molecular Lasers.pdf | Cornell technical report, 1974; deactivation, collisions, fluorescence decay and double resonance | Material-dependent damping motif. No empirical rate constants are transcribed from its noisy OCR. Five pages without extracted text were visually checked. |
| Molecular_and_laser_spectroscopy_6249695618748137365.pdf | Gupta, 2018; contents and relevant near-IR material, water and sensing sections | Material response and an observation curve. Synthetic Rose peaks do not identify real chemicals. |
| Unit-4_LASER_Physics_P-6.pdf | All thirteen PDF pages, especially pumping and gain on pages 9–13 | Paid excitation, threshold, reservoir and cavity motifs. No real laser construction parameters are used. |
| Resonance Light Projection Fractal.jpg | Original image inspected at its available resolution | Cyan/blue facets alongside organic folds. The filename supplies no measurable fractal law or spectral calibration. |

The broad equilibrium/no-input claims in the short time-crystal commentary should not be used as engine physics. Watanabe and Oshikawa's [equilibrium no-go result](https://arxiv.org/abs/1410.2143) applies under its stated Hamiltonian assumptions. Zhang et al.'s [trapped-ion observation](https://arxiv.org/abs/1609.08684) uses a periodic Hamiltonian and finds a robust subharmonic response. These are distinct settings. A programmed sign change in this game is only an aesthetic and mechanical analogy.

Wilson et al.'s [Dynamical Casimir experiment](https://arxiv.org/abs/1105.4714) uses a superconducting circuit whose effective boundary is modulated at high frequency and reports two-mode squeezing. Rose uses the driven-boundary motif; it does not simulate that experiment or treat a stationary vacuum as an unlimited power source.

## Verification and limits

The release passes 321 Python tests, including 34 new mechanics/application cases, plus live HTTP/interface/native-canvas checks. Coverage includes source-bound controls, all physical entry points, attribution and contract separation, direct link failures, same-cycle wear shutdown, repair followed by a fresh paid restart, second-player revision refusal, full-archive observations, long constructed-workshop IDs, selector drafts, focus and native dropdown keys. Earlier reservoir, restart, migration and import isolation checks remain covered. `VALIDATION.md` records the broad interface checks and corrected focused run separately.

`Rose-workshop-preview.png` combines the actual 1000 × 620 local field with the current spectral/history canvas and state/audit captions. It shows a repaired workshop after a new paid excitation; it is not a screenshot of the HTML action menu.

The code runs within the existing Python/JavaScript engine and finite particle budgets. No new graphics dependency is required. The existing Blender source, raw body frames and v6 sprite atlases are retained. Full browser layout, Windows launch, audible playback, multiplayer LAN, live local-model narration and human balance remain unverified.


## VREX background physics

The oscillator/tether component continues to record particle comparisons, stimulus, work, load and reuptake on the host. Its dashboard, tests and audit controls are removed from the gameplay screen. Normal snapshots omit solver state and histories before copying them. Authenticated development APIs preserve guarded controls, numerical diagnostics and read-only export. The numerical model and reference bytes remain unchanged. See [VREX-INTEGRATION-GUIDE.md](VREX-INTEGRATION-GUIDE.md).

The new planar mechanical component consumes each committed passive-load packet once. Hardware turns that motion into finite source-water transfers, reserved construction work or damping; its internal cross-correlations measure network/tether/mechanism response. The supplied Millington and Coumans PDFs are retained unchanged, with review coverage and hashes in `reference/physics/source-register-v013.json`. See [PHYSICS-EMULATION-GUIDE.md](PHYSICS-EMULATION-GUIDE.md).
