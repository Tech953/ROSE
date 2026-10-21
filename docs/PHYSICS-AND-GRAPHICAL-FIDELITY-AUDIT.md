# Rose 0.13.1 — Physics and graphical fidelity audit

3 October 2026 · audited baseline: delivered Rose 0.13.0 · world schema 1

The physics update passes its conservation, application and persistence checks after targeted repairs. Graphical fidelity is a **partial pass** against the requested Fallout-inspired hyper/faux-realism. The engine has original prepared 3D sprites, tactile materials, fixed dimetric framing, regional lighting and restrained CRT presentation. Its shared characters and sparse scene library still fall short of a fully individualized, richly dressed world.

## Confirmed findings and repairs

Priority describes the observed prototype defect. Medium affects a promised simulation or presentation behavior; low affects defensive authoring or visual consistency. These findings do not establish an exploit through ordinary player commands.

| ID | Priority | Verified defect | Delivered repair |
| --- | --- | --- | --- |
| P01 | Medium | An angled elastic impact gave a horizontal rail body sideways velocity and position, while its energy audit still passed. | Impulses, effective mass, positional correction, forces and dashpots use the same constrained inverse-mass response. The independent angled-impact check reverses horizontal speed and retains the rail exactly. |
| P02 | Medium | Equal negative input/heat entries could cancel in the energy balance; malformed entries or off-rail geometry were not reliably rejected. | Read-only mechanical audits reject invalid types, missing ledger entries, negative ownership channels and off-rail position/velocity. Combined audits expose invalid source/downstream records as failures. |
| P03 | Low | A zero rail direction silently became horizontal; extremely small positive mass could overflow inverse mass. | Authoring rejects zero rails and dynamic mass below 0.0001 before registration. Perpendicular paid work is refused before recording a receipt. |
| P04 | Medium | Assembly shutdown reset static wall angles and discarded a dynamic body's authored assembly angle. Resetting under gravity or applied load also exceeded the helper's intended scope. | Shutdown preserves static geometry, restores registered dynamic assembly angles, and requires zero external loading and zero spring potential at assembly origins. Legacy workshop records retain their original zero-angle default. |
| G01 | Medium | Actor light respected blocking hexes, but ground pools could illuminate a passable area behind the same solid hex. | Ground pools share the blocking-ray rule and clip to visible passable ground. Removing the blocker restores illumination in the native-pixel control. |
| G02 | Low | Only the strongest practical contributed to actor illumination, losing overlapping regional light colors. | Visible practical contributions combine into a bounded RGB response. Alpha, graded shadows, prepared frames and the 64-frame response cache retain their existing roles. |
| G03 | Medium | Path textures filled whole tactical hexes, exposing a repeated hex patchwork during exploration. | Connected rounded surface strips follow the same registered path cells. Logical hexes, route previews, AP and picking remain authoritative. |

The shutdown helper remains an assembly reset for the fitted zero-gravity rigs. It is not a general physical braking controller. Contact geometry remains circle/box based; a rail cannot resolve overlap in a direction in which it has no allowed motion.

## Physics and application result

The final suite passes **330 Python tests**, including 43 mechanics/application checks. Nine new solver regressions extend the delivered baseline. Independent solutions cover translation, rotation, gravity refinement, spring period, momentum, elastic collisions and known temporal delay. The new checks exercise oblique rail collisions, reaction work, constrained dashpots, invalid receipts/audits and shutdown geometry.

All **nine isolated device controls pass**: pump, press and damper, each with loaded, unloaded and no-input cases. Unloaded/no-input controls create no downstream useful work. The previous coarse press failure and timestep refinement remain recorded; the one-percent mechanical tolerance was not relaxed and heat was not adjusted to conceal integration error.

Application checks retain actual water conservation, public power costs, construction escrow and contributor attribution, same-cycle failure shutdown, duplicate-cycle refusal, source outages, paid restarts and SQLite replay. The upstream VREX model and optical/research modules retain their prior implementation. Solver measurements, traces and correlation records remain off screen; physical workshop controls and observable world effects remain available.

## Graphical fidelity against the requested aesthetic

This assessment combines native scene inspection, actual sprite contact sheets, registered frame/palette checks, source provenance and the supplied WN_TOWER/CITY_CLOUD_S regional text. It is a qualitative art review, rather than an automated photorealism score.

| Criterion | Result | Evidence and remaining gap |
| --- | --- | --- |
| Prepared 3D-to-2D rendering | Pass within the prototype | 46 original source models and 1,244 prepared raw frames; indexed palette and registered feet. The current art and Blender sources match the delivered baseline. |
| Fixed dimetric local view | Pass | Matching camera, six facings, shared exploration/combat scene, unchanged sampled picking. Continuous destination/point overworld travel remains separate. |
| Tactile materials and silhouettes | Partial | Fitted timber, cloth, mineral and metal detail reads at field scale. Characters occupy roughly 15–21 × 57–63 opaque pixels at standard scale; enlarged inspection reveals coarse faces and repeated costume silhouettes. |
| Individual characters and equipment | Gap | Five shared character body families plus a construct; individual lore/appearance records do not produce bespoke likenesses. Inventory-matched garments, weapons and portraits need prepared assets. |
| Druid-to-cyber-neon lighting | Improved partial pass | Four authored regional signatures, physical baked fixtures and bounded combined runtime spill. Ground occlusion uses hex visibility; runtime illumination is an RGB display approximation, without material normal maps or a dynamic mesh shadow renderer. |
| Biome/building richness | Partial | 28 regional infrastructure models, four obstacle models and eight terrain/path surfaces. Repeated floor motifs, open field edges, limited undergrowth, interiors, walls/roofs and landmark silhouettes remain visible gaps. |
| Growth, decay and construction appearance | Partial | Existing ecological stages, condition frames and construction cuts follow saved state. Construction is a clipped worn structure; it does not yet have individually modeled foundations, framing and finishing assets. Fitted pump/press/damper bodies also need dedicated art. |
| CRT readability | Pass within tested scope | Sharp/Off bypass the compositor exactly; Soft Phosphor preserves native labels and controls. The effect cannot add missing source geometry or texture detail. |

## Visual evidence and performance scope

`Rose-audit-before-after.png` compares shipped 0.13.0 and audited 0.13.1 renderer code on identical frozen geometry and sprite assets, in WN_TOWER and CITY_CLOUD_S. Regional enabled/condition copies are presentation fixtures; they do not change the live world. **127 hex-center picks match per region**, and host state remains identical. Separate native-pixel controls isolate blocking and overlapping colored emitters. The full regional and individual-prefab previews provide additional building/body coverage.

Native drawing of the seven-structure fixture averaged approximately **25.7 ms** for WN_TOWER and **33.8 ms** for CITY_CLOUD_S over twenty frozen frames per region. This is one Linux canvas backend measurement, excluding full browser layout and screen refresh. It is not a Windows/GTX 1650 FPS claim. Additional scene density needs target-device profiling before a large art expansion.

The full real-HTTP/interface harness passes character creation, regional/style loading, display preferences, alpha picking, prop fading, two companions, local actions, construction, travel, combat, conservation, hidden physics and recovery checks. Browser layout, Windows launch, audible playback, LAN sessions and human balance remain unverified.

## Next asset production priorities

1. Give named companions and recurring residents stable original likenesses, clothing and equipment layers across every facing/action. Review silhouettes at native scale before adding fine textures.
2. Add authored terrain clusters, understory, repaired road edges and regional debris that fit actual passability, plant state and object ownership. Extend the small repeated floor samples without painting over usable routes.
3. Produce dedicated construction stages, fitted mechanisms, interiors and wall/roof occlusion assets, followed by regional monument silhouettes tied to the converted geography.
4. Add sculptural talking-head atlases with persistent NPC identity and dialogue/attitude binding. Then review material detail, palette, shadows and CRT softness together on the user's target hardware.

These are remaining production milestones. This release improves the engine and establishes review evidence; it does not certify a completed hyper-realistic art library.
