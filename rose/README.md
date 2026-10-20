# Rose 0.18.0 — source-linked art direction

All 80 distinct image references now have explicit roles linked to the world-lore and biome text. A bounded material finish on existing rendered structures and rocks is available alongside Baked Surfaces. Open **Art direction and text interpretation** from the reference links to inspect regional briefs, the full interpretation register, 110 unit recipes, 43 qualitative product briefs and matched engine scenes. See [the guide](docs/ART-DIRECTION-AND-TEXT-INTERPRETATION.md). New models and sprite bakes remain production work.

The current 0.18 audit passes **438 Python tests** and all six isolated HTTP/native interface flows. Run `python3 -m unittest discover -s tests -v`, then `node tests/ui-smoke.cjs`; see [validation](docs/VALIDATION.md) for scope and limitations.

# Rose

**The third field record after THORNS and Stem · engine foundation 0.18.0**

**Visual reference integration:** 93 supplied PNG names resolve to 80 unique original images. Open **World Map → Atlas Record → Visual reference archive** to search source names, material, lighting, architecture and scale studies, review caveats and preview one original at a time. Current-region narrator context receives scoped art guidance. Existing sprites, manifests, numeric physics and travel geography retain their bytes. New modeled sprite bakes remain production work. Read [the visual reference review](docs/VISUAL-REFERENCE-REVIEW.md).

**Weather response:** rain and wind now leave persistent wet/dust surface state, while AETHER refuge lashings loosen under storms. Approach and choose **CLEAN SURFACE / 1 WATER** or **BRACE CANOPY / 1 SCRAP** in Object Actions. Treatment uses contextual skill checks and personal supplies. Anchored cloth-surface motion follows Full/Reduced/System preferences; fixed foundations and collision remain authoritative. Read `docs/WEATHER-RESPONSE-GUIDE.md`.

The recovered lore transport pack adds 11 source profiles, 58 paragraph-cited facts and 43 individual product specifications. Existing regions use the new sensory context; ask a route custodian about **biomes** for a checked briefing. Open **World Map → Atlas Record → Lore and biome source archive** to inspect the four historically recovered test images, with a link to the new 80-image archive. New places remain unplaced. The uploaded ZIP ends inside an image; this is a partial source recovery. Read `docs/LORE-TRANSPORT-INTEGRATION.md` for coverage and physics/art handoffs.

Rose is a separate, runnable engine prototype. It carries forward the supplied world references, interpreted geography, character creation, survival, skill/context/reputation checks, contracts, dialogue records and up to two autonomous companions. It adds seeded public works and an animated hex field that stays in place when exploration enters tactical combat.

The [physics animation update](docs/PHYSICS-ANIMATION-GUIDE.md) connects prepared footsteps, attack contact, confirmed-hit recoil, material settling and fitted machinery to committed actions and solver poses. Motion profiles support pause/resume and reduced motion. Drawing, inspection and picking share each current surface; measurements stay off screen.

The 0.15 physics-animation regression passed 391 Python tests and the complete HTTP/native interface flow. Preview motion is derived from prepared surfaces; fresh Blender animation bakes and rigid-body debris remain production work.

The [material aging and destruction update](docs/MATERIAL-AGING-AND-DESTRUCTION-GUIDE.md) adds persistent weathering, weapon durability, equipment failure, structural collapse and once-only salvage. Broken works lose their connections and cover; rubble blocks the foundation until cleared for rebuilding. Repair, replacement and demolition use the existing skill/context/standing checks and resource accounts. **GEAR / MATERIAL CONDITION** and individual object controls expose the work.

The [monolith scale update](docs/MONOLITH-SCALE-GUIDE.md) gives water, power and relay infrastructure solid monument cores standing approximately four to six character heights. Human-scale service hardware stays registered at their bases. Twelve original 3D meshes add regional materials, projected shadows and worn states; drawing, selection, occlusion and construction use the same composed assets. Destruction now derives lower debris and fracture frames from those prepared surfaces.

The [continuous scenery update](docs/CONTINUOUS-TERRAIN-AND-PORTRAIT-GUIDE.md) removes the hex-shaped field cutout and painted circulation cells, adds worn approaches and smooth ground-light shadows, and keeps structure labels contextual. Seven supplied references inform terrain and sculpted-portrait direction. Movement, AP, resources and physical work retain their existing rules.

The earlier [physics and graphical fidelity audit](docs/PHYSICS-AND-GRAPHICAL-FIDELITY-AUDIT.md) repairs rail constraints and assembly shutdown and strengthens ownership audits. Its nine device controls and refinement results remain retained.

World travel and bodily movement use separate views. The world map supports named destinations and arbitrary land points with continuous travel, interruption and explicit local entry. Inside a location, exploration and AP combat share the same isometric scene with hidden movement hexes. Grid, route and target feedback are available when requested or during combat.

Original Blender meshes provide 1,244 prepared frames from 46 source models, with a fixed dimetric camera and one shared 256-entry palette. The default **Detailed / Regional Spectrum** bank adds physical regional fixtures, stronger material response and prepared jade/amber, ochre/jade, cyan/rose and violet/crystal lighting. Its 92 environment frames are newly rendered at doubled sampling and supersampled resolution. The 1,152 raw body/construct frames, geometry, animations, foot registration and exported alpha are preserved; their current RGB is reindexed into the new v6 palette. Five shared body families, 28 infrastructure models, four obstacles and eight field/path surfaces retain their world scale. Earlier v1–v5 source/atlas banks remain preserved. Signature and Subdued Radiance add local light spill; Baked Light Only retains the prepared frames. Soft Phosphor gently blends field pixels; Sharp Pixels and CRT Off retain native art. Display changes spend no game resources or turns.

The new monument cores use a separate parameterized software 3D rasterizer with NumPy and Pillow; they are not a new Blender/Cycles bake. The complete Detailed bank now contains 132 indexed PNGs and 144 game entries. Their meshes, tool and render receipts are included alongside the retained Blender sources.

Character creation offers a rendered field presentation independently of stats and pronouns. Written appearance remains registered for dialogue; it does not generate a new mesh. Shared body families may repeat. Unique portraits, inventory-matched weapon/body layers, voice acting and a finished third-game story remain production work.

The editable Blender source, materials, keyframes, render settings and locked palette are included. See [the 3D sprite pipeline](docs/3D-SPRITE-PIPELINE.md) to rebuild or edit the assets. Playing the bundled sprites does not require Blender or Pillow. See [the prefab reference guide](docs/PREFAB-REFERENCE-GUIDE.md) for all 22 sheet mappings and implemented coverage. See [the art direction and display guide](docs/ART-DIRECTION-AND-DISPLAY.md) for the material recipe, verified references and portrait production plan.

Local play now has Move, Interact and Target cursor modes, target-bound Look/Use/Item/Skill actions, sprite-aware prop fading and a Scene Objects selector. Sensory Look records a Perception/context/standing check without spending AP or supplies. Adjacent willing companions can be asked to make room. See [the local interaction guide](docs/LOCAL-INTERACTION-GUIDE.md) for controls, costs and verified scope.


The environment now saves soil health, detritus, erosion, planted succession and physical construction. Foundations reserve material and block their actual hex; completed structures join operating networks. Willing companions can approach and contribute through their existing work cycles. The larger drawing is converted into selectable continental cartography with three confirmed anchors and marked inferred forms, while the original image stays accessible.

The available design commentary is registered in **44 lore records**. The supplied Aurora simulator informs persistent individual particles, form degradation/reactivation, resonance measurements, transfers and single-particle export/isolation. Prepared `void_null` expeditions branch into tangible text percepts with finite protection and Immunix, retained world anchors and usable return traces. These are bounded game mechanics in abstract units; the engine does not claim literal infinite rendering or experimental physics.

See [the environment and construction guide](docs/ENVIRONMENT-AND-CONSTRUCTION-GUIDE.md), [the commentary and particle integration guide](docs/WORLD-LORE-AND-PARTICLE-INTEGRATION.md), and [the continental survey guide](docs/CONTINENTAL-SURVEY-GUIDE.md) for controls, costs, implemented lore and remaining production work.


The new [resonance instrument](docs/RESONANCE-AND-SOURCE-GUIDE.md) adds workshop tuning, finite public-power input, material response, heat and controller quenching. Workshops expose source-bound Read, Tune, Excite and Quench actions; physical controls share the same approach and power guards in the inspector and typed commands. Link outages quench the reservoir while preserving its settings and source binding. Repairs need a new paid input to restart. Its saved optical ledger and 48-cycle signal are game approximations informed by the supplied references. `ask about resonance` registers these ideas with the resident conversation system.

## Run Rose

On **Windows**, install Python 3.10 or newer, extract the ZIP, open the `rose` folder and double-click **Start-Windows.bat**. The host opens **http://localhost:8778**. Keep its console open. If startup fails, the launcher leaves the error visible.

On **Linux/macOS**, run:

```sh
python3 server.py
```

Playing requires Python and a JavaScript-enabled browser. The host uses Python's standard library; Node and the optional native canvas library are used only for development checks. No model or third-party Python package is required.

Rose saves separately to `%LOCALAPPDATA%\Rose\worlds.sqlite3` on Windows, or `~/.local/share/Rose/worlds.sqlite3` elsewhere. Stop the host before copying that database for a backup. Rose rejects a Stem database supplied as `--db`. Rose accepts THORNS v1, Stem v2 and Rose v2 character creation templates; these transfer creation choices, rather than earned possessions, reputation or world saves.

## Create the first field

1. Enter your character name and discipline. Open comprehensive creation to set rendered presentation, appearance, pronouns, embodiment, origin, affiliation, biography, voice, mannerisms, goals, boundaries, attributes and proficiency training.
2. Give the world a seed. Open **Infrastructure Generation / New World** and select Balanced, Frontier or Settlement. The nineteen variables can be edited independently within their displayed bounds.
3. Enter the field and select **Begin World**. Another explorer can join the same host with the room code; one world supports up to six human seats.
4. In **Move**, click ground to walk or a structure to approach. In **Interact**, click for Look/Talk, then hold or choose **Object Actions** for explicit work. Repair and supply draws require an adjacent approach; every step and attempt is checked by the host.
5. Recruit up to two nearby traveling NPCs. Their designation includes stable generated lore, appearance, voice, personal items, training, conditions, pack, faction standing, attitude and contract readiness.

The Scene Objects and destination selectors support keyboard operation. Focus the canvas to use **1/2/3** for cursor modes, **F** for selected actions, and **W/E/D/X/Z/A** or arrows for six-direction movement. Right-click cycles modes; Shift reveals objects. Prop fading, grid, network and CRT scanlines have individual toggles. The field's **Motion** selector follows System, Full or Reduced preferences. Audio starts muted and can be enabled explicitly.

Live refresh preserves open NPC records, pending task/supply choices and keyboard focus. Unchanged destination menus retain their options. Controls explain missing turn/AP, range, equipment or approach prerequisites; the server still validates every submitted action. Vital meters state whether higher or lower is better and label critical care needs. Invalid imports retain your prior character draft.

## World map and local entry

Select **World Map** after beginning the world. Click any reachable land point, including dark unexplored ground, to start traveling. Clicking again replaces the destination from your current position. Named destinations and numeric X/Y controls offer the same travel operation. **Stop Travel** halts without snapping your marker back; **Resume Journey** continues the retained route.

Opening the world map preserves an active journey. Resume replans from the current bodily sector. Field-station recovery and a successful withdrawal cancel the obsolete destination; choose a new one after relocation. Ordinary needs and encounter stops retain their onward destination.

The marker moves continuously on the host clock. Underlying survey-sector crossings apply Body/transversal checks, terrain-dependent survival costs and shared ecological time. Water channels, bridges and the closed border retain their actual passability. Mountains, woodland and dustland take longer. Crossing a hostile site interrupts the route and enters the existing local scene for AP combat. The route remains available after resolution; survival needs also halt automatic travel before critical exhaustion.

Arrival keeps you on the world map. Click the arrival triangle, or select **Enter Location**, to enter the local field. Visited places appear in a separate return list. Discovery reveals the surrounding ground as you travel. **Show Drawing Cartography** exposes the converted source-map layer without granting visits, NPC knowledge or resources; return to Field Discovery for the fog view.

The route atlas retains the 28 named landmarks interpreted from the supplied photographs and documents. The separate larger survey converts nineteen features and links only the two established approaches; no continent-to-grid metric transform is invented. Both original photographs remain available in Atlas Record. World points allow fractional coordinates; the finite survey model covers 37 × 25 sectors and local fields contain 91–271 hexes according to radius. It is continuous traversal across that interpreted map, rather than an infinite terrain engine. Local scenes and utility networks remain Rose adaptations, without an assumed ending of THORNS or Stem.

The supplied Fallout manual's World Map section (printed pages 4—25 and 4—26) grounds this view/entry flow. The supplied Vision Statement guides the quieter interface and the audit of existing character and consequence systems. Read `docs/REFERENCE-AUDIT.md` for the precise mapping and remaining gaps.

## Public works

Structures have a type, seeded position, regional material, faction, capacity, condition, operating scope, network links and maintenance history. Their surrounding aprons connect to the walk network. Field water and wind collectors form the minimum local apparatus; refuge and exchange services are guaranteed where the landmark needs them. Additional cultivation, workshop, exchange, refuge and relay modules depend on density and seed.

Operating cycles generate bounded wind power, transfer actual local water and food into public stores, convert water into cultivation upkeep, reclaim actual local scrap, and meet resident demand. Power and wiring failures can interrupt production. Consumption, conversion, unmet demand and repairs are recorded in finite ledgers. Stores never exceed their configured cap.

Repairs require an adjacent character, one personal scrap, and the relevant check. Successful repairs restore 25 structure condition and reinforce adjoining links. Failed repairs spend their material. Water, food and scrap can be drawn only from actual public stock through the corresponding maintained apparatus. The exchange requires an adjacent character and an enabled, maintained building before a transaction; its goods and currency reserves remain finite.

A local maintenance commitment requires your own successful repair after acceptance and condition at least 85. Complete it beside the commissioned structure for three scrap, two XP and two faction standing. It closes once. The previous survey, delivery, restoration and diplomatic commitments also remain available.

NPCs preserve the observe → plan → work → reflect → recover cycle. They can walk toward a damaged structure and use their own material during a later work period. Companions physically follow local exploration paths, and relevant check support requires them to be within two hexes. Care needs, energy, attitude and agreements govern participation.

## Encounters on the field

Generated hostile maintenance constructs can occupy exposed unnamed sectors. Overworld crossing interrupts continuous travel and opens their local encounter. During local exploration, select **Engage**, or approach within the trigger range and clear line of sight. The existing scene becomes a sequence of player, companion and construct turns.

Action points pay for adjacent movement, melee, registered crystallin shots, guard, parley and field care. Melee range is one hex; crystallin range is six visible hexes; parley needs four visible hexes. Solid terrain and structures block line of sight. Cover and guard affect defensive checks. Companion actions follow their health, energy, attitude and assignment; guard support requires physical adjacency.

End Turn advances the queue and lets NPCs act. Each human's own End Turn applies one personal survival cycle. The shared ecological clock holds during any active encounter, including in other sectors, and advances one cycle after the final active encounter closes. This prevents autonomous changes from moving participants or altering operating conditions partway through a tactical sequence.

The host can advance a waiting guest turn if that guest disconnects; this does not spend the guest's personal needs. Seats can be released after encounters finish. A browser disconnect keeps its seat and saved turn.

Disconnect cancels further local walking steps and discards late interface responses. A step or action already submitted can complete on the host; reconnect shows that authoritative saved result. The interface never retries a time-consuming action automatically. A saved overworld journey can continue while its room remains active.

Disengagement requires an outer hex and a successful crossing check, then moves to a physical neighboring survey sector. Disabled constructs pay their bounded salvage cache once; a negotiated truce pays no cache. At zero player health the field-station recovery rule retains inventory and recorded injuries. This prototype has no permadeath, player-versus-player combat or civilian targeting.

## Engine configuration and reusable generation

Edit `rules.json` or load another validated file:

```sh
python server.py --rules my-rules.json --port 8778
```

Host defaults and new-world choices are copied into every save. Editing the defaults does not change an existing world's configuration. Unknown keys, booleans, unsupported schemas and out-of-range values are rejected before creation.

Use **Export Infrastructure** to obtain the current seed, rules, local hex tiles and public works. The export omits seat tokens and character records; it is a blueprint, rather than a restorable save database.

The command-line generator works without a running server:

```sh
python tools/generate.py --seed rose-first-foundation --profile frontier --all-landmarks --output Rose-blueprint.json
python tools/generate.py --from-blueprint Rose-blueprint.json --all-landmarks --output Rose-regenerated.json
```

The second command reuses the seed and rules to generate an initial layout. It does not import later repairs, utility cycles or characters from that blueprint. `examples/Rose-foundation-blueprint.json` contains an inspectable generated atlas.

Read **docs/ENGINE-GUIDE.md** for all variables and extension points, **static/art/README.md** for sprite installation, and **docs/VALIDATION.md** for the verified scope. The earlier Stem guides are retained in `docs/stem-foundation` as source context; the Rose README and engine guide govern the changed systems.

The **docs/QUALITY-AND-ASSURANCE-AUDIT.md** records twelve repaired findings and the remaining live-validation work. If automatic updates fail, a notice appears for that world and its latest saved state remains available. The host can pause/resume to retry; other rooms keep running. Stop the host and retain a database backup before investigating a repeating failure. If browser storage is blocked, the current page can play but cannot remember its seat automatically.

## Text and optional local narration

The inherited procedural narrator supplies material, weather, scent, sound, growth, construction, inhabitants, resources and persistent traces. Typed intentions use a bounded parser. Examples:

```text
hex 1,-1
inspect structure water
repair structure water
draw structure water
accept infrastructure contract
complete infrastructure contract
ask about history
ask about void
ask about particles
ask about administration
ask about greatweb
inspect environment
plan shelter 1,0
prepare void expedition
enter void_null
advance void 2
return from void
accept delivery contract
go to ED.NET
go to -8.2,4.1
stop travel
resume travel
enter location
engage
guard
end turn
combat care
```

Unknown, hypothetical, negated and chained intentions spend nothing. A separately running loopback chat-completions service can expand scene prose; the model cannot create game facts or mutate the save:

```sh
python server.py --narrator-url http://127.0.0.1:8080/v1/chat/completions --narrator-model local
```

The adapter receives the observer's registered description, relevant NPC lore, recent dialogue, public works, soil/plant/construction records and current particulate/percept measurements. A model and GGUF inference runtime are not bundled. Live inference has not been verified.

All multiplayer explorers connect to the same host. A LAN client uses `http://HOST-LAN-ADDRESS:8778`. This package includes source and a local browser interface; a native Windows executable, matchmaking and public internet hosting are outside this release.


VREX is an internal physics and measurement component: finite RK4 oscillators, a modulated tether, passive load, paid controller and owned return channel. Particle IDs join both engines' measurements. The host advances configured fields and saves full records while gameplay snapshots omit detailed telemetry. VREX dashboards, workshop test actions and measurement exports are absent from the gameplay screen. Development APIs retain tests, bounded stimulus controls and read-only records. See [the background physics guide](docs/VREX-INTEGRATION-GUIDE.md).

The VREX numerical core remains unchanged from 0.12.0; a committed-step observer now connects its load output to local mechanical emulation. Units remain dimensionless; collective order in the archived example is Not Detected. Full browser layout and Windows launch remain unverified.

## Local physics and workshop mechanisms

Rose 0.13 adds persistent planar bodies, springs, damping, contact impulses, friction, angular motion and bounded substeps. Fit a pump, press or vibration damper at an adjacent maintained workshop, then operate it with real public power and contextual skill checks. Pumps transfer existing source water; presses contribute actual reserved construction work; dampers reduce mechanical fatigue. Source failure or unstable operation stops output, and a repair never recreates input. Numerical records and cross-correlations remain off screen. See [the physics emulation guide](docs/PHYSICS-EMULATION-GUIDE.md). Run `python3 physics_bench.py` for isolated metered controls.
