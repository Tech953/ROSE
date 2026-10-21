# Rose 0.13.0 — Commentary, lore and particle integration

Rose now keeps the available past and present design commentary in a versioned lore record. It connects the setting to descriptions, five resident dialogue topics, optional narration context, individually persistent particles and a playable `void_null` expedition. The register distinguishes confirmed framing, developing hypotheses, implemented mechanics and later production work.

The sources are the supplied Thorns/Stem/Rose history, DOCX references, map photographs and scale corrections, October 3 voice discussion, Aurora developer guide and compiled simulator bundle. The original Aurora guide and a size/hash inventory of the supplied bundle are retained in `reference/aurora`. The bundled Windows program was inspected as data and code reference; it was not executed or modified. No Aurora runtime is required to play Rose.

## Play the particulate field

Open **Info-particles / Percept Expeditions**. The left readout shows individually registered positions. The right readout derives a fractal potential from current mass, charge, frequency, phase and polarity. Exact measurements and the transfer ledger remain available as text.

Select a particle and choose **Isolate Selected Potential** to calculate the right readout from that single object. **Export Selected Particle** downloads its current measurements and lineage. **Export Particle Field** downloads all present objects. These operations observe; they do not extract, spend AP or change the saved revision. Sampling is a separate checked operation.

| Operation | Gate and actual consequence |
| --- | --- |
| Read field | Archive/Percept check, or NullSurvey in void. An uncertain interpretation does not hide measured properties. No personal time cost. |
| Excite | Baseline field, adjacent maintained workshop, one actual public power per attempt, Light/Tech/context/standing check. Success changes phase and x velocity. |
| Sample | Installed registered Meta-Fingers and `black.dot`, Fractech check, at most five carried individuals. Success moves the same object into the owner's instrument. |
| Deposit | Own a selected sample, available field capacity and Fractech check. Success returns that same object to the current field. |
| Import | Host only, paused clock, baseline, no active encounters and current revision. Full validation precedes adding objects; rejects duplicate source identities and malformed or nonfinite values. |

Every materialized object has a stable ID, mass, charge, frequency, phase, element, matter type, polarity, position, velocity, form, lineage and bounded history. Opposite-polarity proximity can change objects into radiant forms; it does not delete their IDs or mass. Formations reference member IDs instead of replacing their constituents. Sampling and depositing move identity rather than copying it.

EUNIX particles respond to baseline moisture and soil. Dry stress can make them dormant; suitable conditions can reactivate them. Coherent physical interacts may acquire EUNIX form. Complexity and degradation are abstract game indices. They do not implement the setting's full bio-nano physiology, skin-pore treatment or medical healing account.

All already materialized fields advance on shared ecological ticks, including fields outside the current view. Carried objects advance once per tick, grouped by owner. Interactions are pairwise within each field, or within an owner's carried group; particles in separate addresses are not evaluated as one planet-wide force matrix. Sufficient coherent EUNIX contributes a small moisture input, while substantial radiant concentration adds local stress. Existing weather, soil, survival and production remain authoritative.

## Prepare and traverse tangible void_null

1. Obtain the existing bounded `black.dot` registration. At a sheltered baseline field with a maintained workshop and nonnegative combined local standing, choose **Prepare**. A Needlurgy check uses three actual scrap and one water per attempt. Success adds forty Life-String protection and two finite Immunix doses, within their caps.
2. **Enter void_null**. Each outward interact, including entry, requires and consumes five protection and one dose. NullSurvey checks include context, faction standing, depth and accumulated strain.
3. Choose outward branch 0, 1 or 2. The resulting address deterministically materializes its own retained particles and a geometric description. Revisit an address to find its existing identities and evolved state.
4. **Retreat One Interact** or **Follow Return Trace**. Recorded returns remain possible with depleted supplies and despite a failed route-reading check. Returning retains carried particles and the world anchor.

The baseline isometry and world-map controls yield to the text expedition and particle instrument. Shells, recursive monoliths, water/steel lattices and folded stairways describe tangible interacts. Baseline building, travel, trade and combat cannot execute from the void address. This prevents an expedition from granting remote physical work or administrative rights. Survival, food, water and waiting remain part of preparation and travel.

Companions remain at the baseline anchor and retain their own cycles. This release does not yet provide full isometric void cities, physical companion expeditions, administrator extraction contracts, Endcap capture or an Absolutix protection mechanic.

## The Aurora adaptation

The supplied program measures resonance in abstract units. Rose adapts the actual compiled behavior where it differs from the prose guide and records deliberate continuity changes.

| Component | Rose 0.10 adaptation |
| --- | --- |
| Resonance amplification | `cos(phase difference) × exp(-absolute frequency difference)`, combined with the symmetric five-element compatibility matrix. |
| Gravity term | `0.5 × effective mass A × effective mass B / distance²`; dark objects double gravitational effective mass. |
| Charge term | The compiled backend's `-0.5 × effective charge A × effective charge B`, rather than the guide's inverse-square charge formula. Antimatter flips effective charge. Rose excludes dark objects from this term, following the stated dark-matter rule. |
| Polarity term | `2 / distance` for opposite polarities; total force scale 0.1. Distances below twenty contribute no pair force, as in the source backend. |
| Integration | One game-cycle step, equal/opposite pair forces, mass-dependent acceleration, damping 0.99, per-axis velocity cap four, reflected 600 × 400 abstract field boundary and advancing phase. |
| RAS | Mean of `(amplification + 1) / 2 × compatibility`, displayed on a 0–100 scale. This follows the compiled backend's aggregation rather than treating all guide formulas as identical. |
| Formation | Pair cohesion at least 0.6 produces member references, preserving all constituent identities. |
| Collision | The source removes normal opposite-polarity objects. Rose records radiant form changes and retains identity/mass. |
| Fractal readout | Phase/frequency potential, mass weighting, charge-dependent power falloff, capped potential and a 96 × 96, 36-iteration escape calculation. It depicts the current field or selected object rather than a generic preset fractal. |

Mass and identity accounting cover generated and imported fields and carried particles. Kinetic energy is measured, but damping, caps, boundary reflection and explicit external drive mean this is not an exact conservative physical solver. It is not presented as empirical evidence for time crystals or quantum behavior. The author's research account is retained as an author report. The new optics and temporal-response reference corpus is registered separately in `reference/science/source-register-v010.json`; it does not validate the game's heuristic force model.

Aurora STRATA `.aurora` and Rose `.json` exports are parsed as data. One import contains 1–64 objects; retained plus imported objects must fit sixty-four in the target field. The browser accepts a file up to 180,000 bytes. The host particle-import envelope is raised from 64 KiB to 192 KiB; ordinary requests keep their 64 KiB bound. Mass, charge, frequency, phase, types, position and velocity have finite validated bounds. Imported names/properties cannot grant inventory, rules, faction access, administrator credentials or executable behavior. Source IDs survive in lineage under new local IDs. Interoperability was verified through serialized exports and Rose's live HTTP import flow; the original Windows application was not launched for a cross-application exchange.

## Runtime scale and persistence

The current archive budgets are 256 materialized particle fields, sixty-four objects per field and five carried samples per explorer. Each new field starts with twelve seeded individuals. Branch addresses describe further fictional recursion; materializing them still requires available archive capacity. Reaching the budget refuses new particle materialization, without deleting existing individuals or return routes. Baseline exploration and environmental observation continue beyond that budget with a clearly unresolved particle readout.

No claim is made to render literal infinity or every atom of an Africa-scale continent. Disk paging and more detailed resolution levels are future engine work. The current representation makes continuity, coalescence and preparation concrete at the registered field level within ordinary hardware limits.

The host's SQLite save retains particle registries, generated/imported mass totals, import identity guards, forms, samples, void addresses, return paths and supplies. Particle JSON is an exchange record, rather than a replacement for that complete world save. Stop the host and back up its database for full continuity.

## Registered character and lore engagement

`ask about void`, `ask about particles`, `ask about resonance`, `ask about administration`, and `ask about greatweb` use the existing resident conversation system. Registered appearance, voice, disposition, dialogue memory, skill/context/standing checks and selected resident identity remain attached to the conversation. Lore selections combine authored records and current measurements; they cannot mint items or access rights. The optional local narrator receives the observer, public ecology, active construction, particulate/percept state and relevant lore. It remains a prose adapter; the server resolves actions and owns all consequences.

Pyry/PYRI, EUNIX/UNIX/newnix, RED and Scarlet spelling variants are preserved as aliases. Absolutix and Snowl Wood spellings remain provisional where the discussion was tentative. ENACT's collective, distributed Fractech pillars, KHO/Pyry oversight, the Great Web and Aqua-sphere inform registered dialogue. Mezzes remains southern expansion lore awaiting its map. Corporate life remains socially complex, with provision, protection and access obligations; druid culture remains one part of the full spectrum.

## Commentary register

The machine-readable source is `reference/lore-record-v010.json`. Status is part of each record and should be preserved when extending generated descriptions.

| Record | Retained direction | Current status |
| --- | --- | --- |
| series | Rose is the third game after Thorns and Stem. It reuses their survival, dialogue, characterization and contract foundation without inventing an ending for either prior game. | implemented foundation |
| presentation | Original pre-rendered 3D-to-2D assets, a fixed dimetric view, six local hex directions, AP combat, contextual Look/Use/Item/Skill actions and a CRT presentation. Overworld journeys select any accessible land point and enter local fields explicitly. | implemented |
| spectrum | Druid/natural, nano and cyber-neon form one artistic continuum. Regional signatory lighting follows authored motifs rather than applying one universal neon palette. | implemented regional art |
| ecology | Environmental change includes weather, degradation, growth, decay and construction. Character preparation, skill, situation and faction standing influence the work. | implemented bounded simulation |
| scale | Africa is the closest approximate size comparison. The perceived environment is compared with square planetary coverage; monuments defy comprehension. No exact dimensions or kilometer conversion are fixed. | author-confirmed framing |
| substrate | A perceived continent is a coalescence of interacting indivisible info-particles, with complex geometric instances and fractal influence. Unknown forces are part of the setting. | author-confirmed lore; abstract particle foundation implemented |
| continuity | Every registered info-particle retains identity through movement, form change, degradation and transfer. A field inspector can isolate and export its current state for fractal study. | implemented for materialized objects |
| void | void_null is tangible and traversable, not an inaccessible visual backdrop. Interacts and apogean geometric constructs can present unfamiliar properties. Perception and preparedness determine what a traveler can resolve. | implemented branching text expedition; geometric fiction recorded |
| apogean | Apogean denotes a prospect/perspective of an infinite geometric construct. A local reading is measurable within its moment even when the entire construct cannot be perceived. | author-confirmed conceptual framing |
| enact | Upper-left ENACT_HILLS is an administrative region. Its network, light projection and memetic advertisements influence the wider environment. The collective behind this office lacks ordinary public visibility. | author-confirmed lore; dialogue implemented |
| cusp | Beyond ENACT, a cusp resembles a waterfall off the world edge into geometric iterations. Administrative operations siphon interacts for energy/material generation. The reasons and administrator generation remain developing lore. | developing author hypothesis; geography not assigned |
| red | RED>GATE> is a lower-right field, possibly a trail of arcane energy through particulate layers. Shell-like constructs may connect to an arcane mollusk aesthetic associated with Snowl Wood; their origin is a hypothesis. | region confirmed; mechanism developing |
| mezzes | The southern MEZZ/Mezzes metropolis has a north and south, and a perceived endless interior reminiscent of labyrinth/backroom spaces. Civilian, contract and Pilgrim lives continue through and beneath freeways. A southern page is still forthcoming. | author-confirmed direction; expansion not mapped |
| life-string | Life-String .co provides deliberately designed protection for expeditions into void_null. Administrators contract for extraction of obtains, interacts and fractals. Protective equipment is connected to the setting's life-string account of a person. | author-confirmed lore; scoped expedition preparation adapted |
| immunix | Immunix is a luminous blue preparation associated with extracted Darkwood materials. A recorded dose helps hold stance, semblance and perception through each newly encountered interact; finite supplies limit an expedition's preparation. | author-confirmed lore; finite outward-interact supplies implemented |
| absolutix | Absolutix is a provisional spoken name for a refined consolidation/solidifier preparation that counters repeated administrative percept overlays. This is protection from influence, not a verified engine permission or automatic credential. | provisional name; full mechanic reserved |
| endcaps | Company-made bronze-like metal orbs can consolidate a person's biomods, arcane ink, fractal tendencies and consciousness as an engram/save state. Contract enforcement and AI/unit uploads are described uses. | author-confirmed lore; capture/upload mechanic reserved |
| druid | Natural cultures and environments participate in reciprocal flows of life, energy and expansion. Druid-punk is a useful part of the spectrum, and not the exclusive definition of this world. | author-confirmed aesthetic; regional descriptions retained |
| institutions | Corporations provide housing, provisions, equipment access and contracts while exerting social expectations. They are not universally evil. Pilgrims bridge contract society and subsistence life. | author-confirmed lore; existing faction/contract framework |
| economy | Resource access often depends on contracts, reputation and regulated extraction. Physical goods have changed significance under meta-break and meta-finger technology; prior trade balances are prototype rules, not an assertion of canonical money economics. | author-confirmed direction; comprehensive economy redesign reserved |
| meta-fingers | Regulated Meta-Fingers connect neurological function to a projection/extraction field. Injury stories and protective advertising contribute to corporate authority. Sampling transfers a real retained particle, and does not create free material. | author-confirmed lore; particle transfer and existing mod gates implemented |
| signatories | KHO and Pyry are signatory intelligences associated with network oversight. Pyry is connected to ENACT and city readouts, functioning in an OS-like role rather than as a public office with universal visible access. | author-confirmed lore; dialogue implemented |
| fractech | Fractech information pillars provide contracts, weather and directions across a distributed network, rather than one central public office. Signatory intelligences exercise layered oversight. | author-confirmed lore; dialogue and existing pillars retained |
| great-web | The Great Web coalesces beneath WN_TOWER, extends far underground and across the perceived continent, and has connections beyond ordinary Fractech scope. Corporate connections and unknown branches remain. | author-confirmed lore; dialogue implemented |
| aqua-sphere | Aqua-sphere is antiquated military technology associated with liquids, water/metal relations and changing material properties under meta-break. Its link to the Great Web is described; exact mechanisms and access remain unspecified. | author-confirmed lore; full mechanic reserved |
| eunix | EUNIX is a pervasive bio-nano cloud/biomod associated with skin pores, healing, data collection and preservation. UNIX, newnix and other spoken variants are retained as aliases rather than separate new species. | author-confirmed lore; particle form tracked, full physiology reserved |
| strain | Perceptual strain is derived from interaction and preparation, not a hard fictional edge of reality. Tools and faction access can make changes legible. The current engine has finite storage and numerical precision. | implemented strain/preparation; physical hardware limit recorded |
| aurora | The supplied Aurora program is a resonance simulator with abstract units, object properties, compatibility, pair forces, RAS, emergent formations and fractal visualization. Its compiled source differs from some guide equations; the adapter documents the differences. | source-audited adaptation |
| research | The author reports a time-crystal result and a prior scientific proposal/review. The supplied package contains simulation labels and heuristics; no experimental data or peer-review document has been supplied in this turn. | author report retained; no experimental verification claimed |
| autonomy | Up to two companion NPCs keep descriptions, lore, personal items, stats, attitude, reputation, work cycles, skill checks and bounded survival needs. Their decisions and refusal stay registered. | implemented existing foundation; construction support added |
| open-prompt | Text intentions and optional local model prose support rich descriptions. The server owns validated state and consequences; an optional narrator does not grant powers, objects, credentials or completed actions. | implemented bounded parser/model adapter |
| engram-json-capacity | The earlier request to raise .json Engram upload capacity informs a larger Rose particle-import envelope: 192 KiB on the host and a 180,000-byte file limit. Ordinary requests retain 64 KiB. Endcap engram capture/upload remains future work; this release does not modify the separate Engram application. | Rose particle JSON threshold increased; separate Engram/Endcap work retained |

## Extend the engine

`particles.py` owns materialization, pair forces, form changes, transfers and expeditions. `lore.py` connects authored records to dialogue and narration. `static/particulate.js` owns the observational instrument and exchange controls. `world.py` owns time, skill checks, action authority and habitat coupling. The original Aurora compiled bundle and its maintainer restrictions do not become executable dependencies in Rose; its supplied source guide is retained as reference.

## Powered resonance in Rose 0.10

The instrument now records finite optical input, retained energy, emitted light and heat. Material frequencies, moisture and degradation affect the response; a maintained workshop anchors colored spill and allows adjacent tuning through the existing Light/context/standing check. Programmed alternating and boundary-modulated responses consume a paid reservoir. Quenching, settings and a 48-cycle trace persist. Five new lore records retain the source distinctions. See [Resonance and source guide](RESONANCE-AND-SOURCE-GUIDE.md) for controls, equations, all ten source mappings and limits.

The five optical records added in this release are:

| Record | Retained direction | Current status |
| --- | --- | --- |
| driven-light | Light projection belongs to a maintained rig and a paid reservoir. Tuning can favor jade canopy tones, amber hearth light, cyan faceted projections, rose signals or violet field contours; the recorded output diminishes as the reservoir empties. | implemented abstract optical game mechanic |
| temporal-response | A programmed alternating response repeats at twice its four-cycle reference interval. A fluctuating boundary redistributes stored optical energy. These instruments provide temporal motifs for Rose; the game reading does not establish a quantum time crystal or a vacuum energy source. | implemented programmed response; scientific analogy bounded |
| spectral-materials | An individual particle retains its own resonance frequency. Spectral response changes with those frequencies, local moisture and registered degradation. Useful light depends on actual material and field conditions. | implemented authored line-response model |
| energy-controller | The optical ledger records public input, retained energy, emitted energy and heat. An overheated or disabled workshop quenches its optical reservoir; a trained traveler can request a manual quench. The controller dissipates stored energy without refunding public power. | implemented finite optical ledger and controller |
| faceted-projection | The supplied resonance projection image suggests blue facets joined to organic folds. Its cyan vocabulary informs the live instrument projection alongside the existing regional spectrum. | implemented instrument motif; small reference accessible |


### Workshop operation in 0.11

The optical reservoir now belongs to the selected physical workshop through local Read, Tune, Excite and Quench options. Inspector and typed controls share adjacency, maintenance, network and stock guards. Actor-attributed optical events remain separate from repair-contract proof. Link loss and same-cycle utility wear quench stored energy while retaining the source binding and settings; a successful repair requires a new paid input before light returns. One active source serves the field's shared reservoir, with stale revisions refused before spending. The new source-bound controls preserve pending drafts and selector focus. The world, art bank and lore register retain their existing identities.


### VREX background physics

The source register retains its seven VREX technical records and numerical model. They remain engineering context and are excluded from ordinary resonance briefing selection and narrator input. Gameplay shows the world and its perceptible effects; the host retains detailed physics measurements, identity joins and diagnostics off screen. See [VREX-INTEGRATION-GUIDE.md](VREX-INTEGRATION-GUIDE.md).

### Practical mechanical infrastructure

Workshop pumps, presses and dampers use the underlying VREX-TETHER load output without displaying its measurements. Pumped water comes from the same finite local source used by cisterns; construction presses work only on reserved nearby projects and retain their own contributor identity. Wear, shutdown and repair feed the existing infrastructure and character action systems. The two additional physics guides, implementation mapping and declared emulation bounds are recorded in `reference/physics/source-register-v013.json`. See [PHYSICS-EMULATION-GUIDE.md](PHYSICS-EMULATION-GUIDE.md).
