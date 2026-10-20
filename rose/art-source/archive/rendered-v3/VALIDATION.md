# Rose 0.6.0 validation

## Completed verification

**163 Python tests pass.** The real-HTTP interface flow and native canvas checks also pass. These results cover the shipped prototype and the checks below; they do not establish full browser or Windows compatibility.

### Individual art and stable identity

- The Blender 4.2.0 Cycles CPU bake contains **42 source models and 1,240 raw frames**: five anatomical body families and one construct with 192 frames each, 28 regional infrastructure models, four obstacle prefabs and four modeled ground fills. All eight body actions have six registered facings. Every raw frame passes the exporter’s mesh/shadow clipping check or opaque central ground-sample check.
- **116 indexed PNG atlases register 128 game entries** with the same 256-entry palette and transparent index zero. Seventy-four atlases are two additional palette treatments of existing models. They preserve every alpha pixel; they are not additional meshes. All five body families have distinct rendered pixels and silhouettes, and all 28 buildings have visibly different healthy/worn frame pixels.
- Character cells remain 128 × 128. Scenery cells use 192 × 224 transparent margins while retaining the original 32 pixels per world unit and foot offsets from the cell center. Ground fills remain 128 × 160. Camera projection, six facing directions, frame origins and complete action clips are checked. The enlarged margins corrected clipped roof shadows; market damage was moved onto the visible counter face and apron.
- Fifteen art-pipeline tests verify projection, the unique 1–1,240 timeline, complete clips, opaque-black safety, palette learning, deterministic alpha coverage, identical palettes, atlas bounds, opaque ground, source/output checksums, original-pack preservation, registration, distinct body silhouettes, tone alpha, building wear and exact body-source provenance.
- Nine visual-designation tests verify old-template migration, rejected presentation values, independent stats/pronouns, automatic Metal-kin selection and explicit presentation, stable travel/recruitment/JSON identity, condition-independent structure identity, sector-qualified IDs, complete profile/region registration and matching player/unit identity in the first host snapshot. Visual inspection does not change simulation RNG or collision geometry.
- The shipped body frames retain their exact archived `.blend` and renderer recipe. The current source supplies the 88 scenery/ground frames. The dependency proof checks that all six body models retain the same geometry, transforms, modifiers, shaders, animation curves, body camera, lighting, shadow floor and render settings. The composed render catalog records each model’s actual source checksum. The original 3D and grounded-v2 source recipes and atlases remain preserved.
- Four sampled frames were rendered again from the final saved source: Wayfarer and Metal-kin idle facing 4, Enact Hills workshop idle, and WN Tower ground. **Every RGBA byte matches** the shipped raw frame in all four samples, including alpha. Raw dimensions are 256 × 256, 384 × 448 and 256 × 320 as appropriate for 2× supersampling. Measurements, frame checksums and repeat-render identity are in `art-source/rerender-check-v3.json`. This is a four-frame repeat check, not a second render of every frame.

### Interface, display and loading

- Native canvas checks render each of the five selected body families and verify the selected sprite’s alpha picking. They check regional asset resolution, original-bank fallbacks, healthy/worn changes, stable designations and unchanged host state. Drawing, bounds, selection and foreground fading resolve the same asset and current frame.
- Sprite loading previously started 134 image requests at once; a diagnostic run observed connection delays exceeding 14 seconds. The loader now shares a **six-image queue** across banks and caches each URL. Its regression checks bounded requests, alias reuse, complete readiness, independent banks and continued queue progress after a decode failure. A diagnostic of the complete interface flow after the fix recorded no image response taking over two seconds. Those timings describe this local run, not a performance guarantee.
- The interface downloads and decodes 128 entries in the default bank and 16 each in the original 3D and material banks, switches all four art choices and preserves preferences. All eight advertised JavaScript routes are fetched successfully from the actual Python HTTP host.
- Display checks verify exact pixel preservation for Sharp Pixels and CRT Off, changed Soft Phosphor pixels, aspect-preserving buffers, buffer reuse, context restoration and unavailable-canvas fallback. Host-flow checks verify native label settings and painting order, unchanged picking/world state and stored preferences. Reduced-motion and blocked-storage paths are exercised.
- Local interaction checks cover cursor cycling, no-roll hover, held-menu suppression, keyboard/touch fallback controls, blocked-action conservation, default Look, one-click movement, discovery preferences, room changes, civilian rejection and combat prerequisites. Native pixel checks verify transparent padding, real foreground overlap, changed fade pixels and picking through to a covered character.
- The actual renderer exports field, world and interaction panels at **1000 × 620**. The display comparison is assembled from the same frozen field in Sharp Pixels and Soft Phosphor. The prefab panels and animated walk preview use shipped indexed pixels. These are renderer outputs, not screenshots of the complete webpage.
- The mocked Web Audio contract verifies explicit enable, mute, bounded panning, short envelopes and node cleanup. Audible playback and browser autoplay behavior were not tested.

### Existing simulation and quality-of-life checks

The 139 existing world, story, infrastructure, navigation, assurance and interaction tests remain passing. They cover continuous fractional overworld travel, routing and diagonal barriers, stopping/redirection, discovery and costs, survival interruption, companion/encounter transitions, hex movement, AP/range/line of sight, cover, care and once-only salvage. They also cover finite utility supplies, resident consumption, maintenance prerequisites/payment, rejected transfers, remote boundaries, saves/restarts, stale requests, authority, redaction, fault isolation and SQLite rollback.

The bounded generation check covers 96 seed/configuration combinations; every structure has a reachable physical apron. Seed and rules reproduce placement. The example blueprint reproduces all 28 initial scenes and 154 public structures, including their saved visual designations.

The real-HTTP flow completes continuous point travel, arrival and explicit local entry, cartography/discovery separation, creation, two companions, lore, guard assignments, physical approaches, maintenance, supply draws, exchanges, blueprint export, combat/AP/parley, input retention, remote boundaries, pause and resume. Assurance flows verify retained NPC details, unsubmitted choices and focus; contextual locks; rejected import rollback; quiet travel announcements; room/seat resets; malformed responses; serialized polling; stale-response rejection; disconnect during a delayed poll and committed walking step; timeout fallback; blocked storage and corrupt-session startup.

All **45 Python sources and 16 JavaScript/test sources** pass syntax checks. The HTML has 157 unique IDs and eight script references. Historical request benchmarks remain documented in earlier audit records; this graphics release does not repeat or extend them.

## Reproduce the checks

From the `rose` folder:

```sh
python -m unittest discover -s tests -v
node tests/ui-smoke.cjs
```

The interface test uses Node built-ins, a modeled DOM and the actual Python HTTP host. Its companion files exercise assurance, interaction, audio, display, individualized visuals and sprite loading. If `@napi-rs/canvas` is available, it also decodes the actual atlases, checks native pixels and exports previews. Without it, drawing checks are explicitly reported as skipped. Pillow enables the developer art checks. Node, Pillow and Blender are not required to play the exported graphics. See `3D-SPRITE-PIPELINE.md` for complete render/export and source-reuse commands.

## Remaining validation and production scope

A browser executable was unavailable for full Chrome/Firefox testing. Browser layout, live touch gestures, audible playback, screen-reader use, Windows launch, real multiplayer over a LAN and large-world performance still need live playtesting. The Windows batch launcher is supplied as source; no native EXE or installer is included. The optional model adapter has mocked-response checks; live model inference was not run.

The five original body families have individual proportions, faces, clothes and costume equipment; shared families can recur across NPCs. Written appearance stays registered for dialogue but does not generate a new sculpt. Decorative gear does not grant inventory or permissions. Bespoke likenesses for every named character, inventory-matched weapons, firearm-specific animation, sculptural talking portraits, expression/lip sync, voice acting and a finished third-game story remain production work. The current assets are tactile pre-rendered prototypes, not finished photorealistic human scans. Soft Phosphor is an art display profile, not a calibrated physical CRT simulation.

The source world documents continue to inform interpreted geography and motifs. The uploaded Fallout references inform the controls and art direction; numerical rules and generated infrastructure remain Rose adaptations.
