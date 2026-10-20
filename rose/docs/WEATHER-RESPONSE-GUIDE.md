# Rose.ENGINE 0.17.0 — Weather, surfaces and canopy care

15 October 2026 · systems update

Rose’s existing climate now drives persistent surface wetness, deposited dust and canopy-lashing condition. Rain wets surfaces and washes dust away; dry air drains surface water, and airborne dust settles during wind. The AETHER fabric refuge responds with restrained, anchored cloth-surface animation. These changes use the existing environment and materials rather than introducing another map or replacing prepared art.

## Play

Select an existing structure or rock and open **Object Actions**. **Inspect Material** includes a description of the surface and, where applicable, canopy lashings. The ordinary location description also reflects maintained surfaces. Existing regions and travel routes remain available.

| Action | Requirement and cost | Result |
| --- | --- | --- |
| CLEAN SURFACE / 1 WATER | Stand one hex beside the object; one personal water; Resource/Tech check against 9 | Success lifts up to 50 game-scale dust points. The attempt wets the surface even on failure. It spends one survival action and does not repair condition. |
| BRACE CANOPY / 1 SCRAP | A completed fabric refuge; stand one hex beside it; one personal scrap; seamLLurgy/Tech check against 11 | Success tightens the existing lashings by up to 35 game-scale points. A failed attempt still spends its material. It does not repair structural condition or create salvage. |

Typed equivalents are `clean surface structure ID`, `clean surface project ID`, `clean surface hex Q,R`, and `brace canopy ID`. Use the object’s registered ID from its record. The same actions and prerequisites are used by the menus and parser. The optional model interpreter does not propose these operations without registered field targets; use the explicit menu or command.

Tight lashings reduce the existing material-weathering contribution and remove the canopy-specific extra storm wear while sufficiently maintained. Ordinary infrastructure wear and other damage continue. Sustained storm load loosens the bindings, so the benefit requires maintenance. Bracing does not affect generators, numerical energy accounts, collision, AP rules or access rights.

Every check uses the existing skill resolver, including training, local conditions, faction standing and eligible companion support. The host rejects distance, stock, ownership, destroyed objects, remote viewing, percept expeditions, pause and combat restrictions before consuming a treatment input. Another player’s private foundation remains under that player’s control.

## What persists

Each registered material object retains its own surface state inside `material_state`. Wetness, dust, lashing condition, stable appearance phase and treatment-input receipts survive normal JSON/SQLite saving. Construction transfers the material record into the completed node through the existing material-transfer behavior. Treatment does not increase the object’s embodied-scrap budget.

The host advances surface state once per observed ecological cycle. Polling, descriptions, hover, rendering, repeated calls within one tick and old ticks do not accumulate weather. Pause and active tactical encounters hold the surface clock. A cold save starts the newly introduced surface record at its current time; it receives no invented past rain, dust, maintenance or damage. A large timestamp gap applies only one observed surface update rather than simulating an unobserved history.

Wetness and dust are bounded indices for appearance and play. Their rates and the bracing thresholds are authored game constants, not physical measurements or calibrated material coefficients. The existing shared weather selection supplies the stimulus; nearby fields in one region share its wind direction and strength.

## Rendering and motion

The prepared surfaces darken when wet and acquire a restrained dust deposit. Saturated practical-light pixels remain distinct. The AETHER refuge’s visible fabric panel uses a registered interior patch; its three patch boundaries stay pinned while interior texture and shading respond to wind. Tighter lashings reduce the response, and a wet panel has a lower visual excursion. Rigid structures receive surface appearance changes without fabric flutter.

The output keeps the original pixel alpha exactly, so foundations, contact shadows, silhouettes, collision, cover, sprite picking and occlusion retain their existing authority. The patch changes interior color sampling and shading; this is a bounded cloth-surface approximation, not a deforming mesh or a mass-spring cloth solver. It does not move the building, its poles or its collision footprint. The dedicated moving patch is registered only for the current AETHER refuge sprite family; older art styles keep static surface response rather than receiving an invented mask.

Full motion animates the panel. Reduced motion retains wet/dust appearance and removes flutter. System motion follows the user’s reduced-motion preference. Pause and combat holds freeze the phase; resume continues from the held phase. Remote viewing and `void_null` do not receive a live bodily weather driver. Collapse and impact cues retain their established playback rather than being overridden by ambient cloth motion.

The renderer retains at most 32 modified frames and 12 decoded source-frame buffers. It changes display data only. Drawing does not spend supplies, add forces, run the solver or alter the host world.

## Source and scope

The wind-worked tent requirement follows `AETHERGALE - THORNS.docx`, particularly paragraphs 2–6, 23–26 and 31–38 in the recovered numbered extract. Those passages establish desert winds, bio-plast, tent constructions and storage. The new rates, maintenance actions and rendering approximation are Rose adaptations. They are not literal parameters supplied by the lore or CODE concept sheets.

`physics.py`, `vrex.py`, `photonics.py` and `research.py` retain their bytes. Numerical measurements remain off the play screen. The original prepared sprite PNGs, art-source files and art manifests are preserved. No new city has been assigned coordinates, and RED>GATE> remains closed to ordinary traversal.

The recovered source corpus still consists of 13 complete documents and four complete test images. The original upload ended inside `Designer (2).png`; this update does not recover that interrupted member or unseen later references. ArK assimilation, AquiSphere morphology, mollusk lifecycles and Mesas vehicle/market topology remain later source handoffs.

## Verification record

The focused weather checks cover rain/wash/drying, bounded dust and lashing strain, shared regional wind, unchanged geometry, same/old-tick idempotence, held clocks, cold migration, newly seen objects, successful and failed treatment costs, range/stock/ownership rejection, destroyed and rigid objects, reduced existing wear, remote/percept isolation, bounded optional interpretation and SQLite round trips.

Native rendering checks compare exact alpha and pinned boundaries, visible patch motion, wet/dust response, tighter restraint, rigid exclusion, pause/hold/resume, reduced and System preferences, remote/percept isolation and cache limits. The live-host interface supplies surface data and exposes guarded care actions. `Rose-weather-response-preview.png` contains native prepared-surface captures.

`docs/validation-results-v017.json` and the `validation-*-v017.txt` logs record the completed regression results. Full browser layout, Windows launch, LAN sessions, audible playback and human balance are not verified in this environment.
