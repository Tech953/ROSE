# Rose 0.13.0 local interactions

Movement, interaction and targeting share Rose's local isometric field. Continuous world-map travel remains a separate view. Local hexes are hidden by default; HEX GRID reveals them. Combat walking costs one AP per adjacent hex by default. The host measures weapon and mapped-object ranges in hexes; visual interpolation and CRT treatment change only the displayed pixels. All four graphics styles and the existing RPG systems are retained.

## Controls

| Control | Result |
|---|---|
| **1 / MOVE** | Click ground to follow a physical route, or a structure/person to approach it. Each adjacent step is checked by the host. |
| **2 / INTERACT** | Click for the registered default: Look on structures, ground and self; conversation on NPCs. A blocked conversation explains the missing approach and spends nothing. |
| **3 / TARGET** | In an encounter, click the hostile construct for the selected staff strike or crystallin shot. Other people cannot become combat targets. |
| Right-click | Cycle Move/Interact; active encounters add Target. |
| Hold in Interact | A 450 ms hold opens object actions. Pointer movement cancels the hold. The release click is suppressed, preventing an accidental default action. |
| **OBJECT ACTIONS / F** | Open actions for the selection. Scene Objects plus this button provide a keyboard/touch alternative to finding a sprite. |
| Escape / Close | Dismiss actions and return focus to the field. Escape also stops an active route. |
| Up/Down, Home, End in the panel | Move among enabled buttons. Tab and Enter also work. |
| Shift / **REVEAL** | Reveal object bounds, rock coordinates and names. Shift is temporary on the focused field; the button preference persists. |
| **PROP FADE** | Fade foreground rocks/public works that cover the player or selected character. Enabled by default. |
| W/E/D/X/Z/A or arrows | Move in six local directions. Enter walks in Move, performs the default in Interact, or attempts the selected attack in Target. |
| **AUDIO** | Explicitly enable short original procedural cues. New pages start muted. |
| **Display profile / CRT** | Soft Phosphor blends field art before labels; Sharp Pixels and CRT Off keep native pixels. Selection geometry and checks stay authoritative. |

Scene Objects lists infrastructure, people, constructs and rocks. Walkable Destination remains the keyboard route selector. Names use separated backing plates and leader lines to avoid overlap. These presentation controls do not grant resources, visits or passage.

## Actions and costs

| Category | Actual operations |
|---|---|
| **Look** | Registered character appearance/health, structure material/status, or terrain/cover, with regional scent and ambient sound. A Perception check records training, context, standing and support. A setback keeps confirmed records readable and labels interpretation uncertain. |
| **Use / Talk** | Scope toggling, finite public supply draws, exchange-ledger review, NPC plans, selected-resident dialogue and companion make-room requests. Dialogue retains character voice, NPC memory, relationships and factions. |
| **Use Item On** | Scrap repair, companion provision sharing and medkit care. Repair spends one scrap even on failure; treatment spends its medkit on an attempt. Sharing transfers one actual supply between packs. Self-care in combat costs a medkit and 3 AP. |
| **Use Skill On** | Inspections, lore/history, recruitment, maintenance commitments and construct combat approaches. Existing skill, context, reputation, equipment, consent and AP checks remain authoritative. |

Every option shows proficiency, training rank, attribute, base difficulty, cost and blocked reason. These are prerequisites, not a success guarantee or hit percentage. Completed rolls show the full modifier record. Disabled options spend nothing. Allowed attempts can fail or become stale; the host revalidates and the client never retries mutations automatically.

Look spends no AP, supplies, energy or survival cycle. It records a check/result and increments the saved revision, preserves world journeys and does not advance combat. Remote Look is labelled as an unverified projection. Hovering only identifies a subject; it never rolls or submits an action.

## Companion make-room request

Select an adjacent owned companion and choose **Use → Ask To Make Room**, or type `ask NAME to make room`. They must be willing, have at least 35 health and 15 energy, and be outside recovery and combat. A contextual Community/Rapport check includes their faction, attitude and relationship. Success moves them one physical step to a free passable neighbor, spends one of their energy and records the engagement. A setback leaves position/energy unchanged. No free side space means another approach must be cleared; no teleporting or movement through people is allowed. Normal following resumes on later movement.

## Visual and audio behavior

Raster picking samples the current frame's alpha and follows the draw depth order. Transparent cell padding does not intercept clicks. Sampled overlapping opaque pixels trigger prop fading; the character's ground-shadow margin is excluded. Faded scenery permits selection of the covered character. Vector/image-load fallback uses approximate prefab bounds. Passability, cover and line of sight remain server rules.

Audio uses short oscillator envelopes and horizontal panning for acknowledged attempts from local controls, including setbacks. Hover and menu opening remain silent. These are prototype cues; authored environmental/mechanical recordings and voice remain future production work.

Current cutaways cover existing rocks and public works. Interior roof groups, walls, doors, containers, body-part attacks and critical limb conditions need further scene/rule content.

## Reference and validation

The supplied Fallout manual was checked at printed **4-8 through 4-11** (PDF 47-50); the command-cursor page was rendered and inspected. Rose adapts cursor/action principles with explicit buttons and a panel that waits for an action click instead of executing a hovered icon on release. Printed **5-3 through 5-4** (PDF 81-82) uses targeted-attack/shot terminology. Rose's current Target mode attacks the whole construct and is not labelled V.A.T.S.

Primary reference: [the original manual distributed with Fallout on Steam](https://cdn.cloudflare.steamstatic.com/steam/apps/38400/manuals/Fallout_manual_English.pdf?t=1572025441). The broader source mapping remains in [REFERENCE-AUDIT.md](REFERENCE-AUDIT.md). No original Fallout assets, characters, geography or numerical rules are included.

**321 Python tests pass**, including 34 new physics/application cases. Expanded real-HTTP/interface checks cover cursor cycling, passive hover, hold suppression, blocked costs, default Look, keyboard opening/dismissal, discovery, room changes, one-click movement, civilian rejection and blocked targeting. Native canvas checks verify decoded alpha, actual overlap, fade pixels and click-through. A mocked audio-node contract checks explicit enable, mute, panning, envelopes and cleanup.

`Rose-interaction-preview.png` is actual local canvas output with Reveal enabled; it does not show the full HTML panel. The harness models DOM attachment, disabled controls and focus. Full browser layout, live touch, screen readers, audible playback, Windows launching, LAN multiplayer and human balance remain unverified. See [VALIDATION.md](VALIDATION.md).

## Individual field graphics

Character creation selects a rendered presentation independently of stats and pronouns. Automatic follows discipline and embodiment; appearance prose remains available in Look/dialogue. NPC identity persists through recruitment and travel. Structures use their regional prefab and a worn frame below 50 condition or while disabled. Repairs restore the existing condition value. None of these visual treatments create items, AP, cover or permissions. All four styles retain their own drawing/picking bank; the current bank uses the actual selected variant for bounds, masks and foreground fading.

## Enlarged field appearance

Selecting a person, infrastructure object or solid obstacle opens a 360 × 360 view of its current field appearance. It uses the same family, patina, facing, action frame and condition as the scene. It is a read-only view: selecting or inspecting spends no AP, changes no inventory and grants no costume equipment. Walkable ground does not invent an illustration. The view resets with the room/seat and remains usable in the preserved graphics styles.

## Environmental work and percept expeditions

The Environment panel adds measured soil/plant state and six construction blueprints. A chosen adjacent site must retain walking connectivity. Successful planning reserves material; work progresses through foundation/frame/finishing, with physical collision and clipped selection matching the stage. Completion creates an operating regional node and link. Only unused reserved material can be refunded once. Repair-assigned companions approach and work within their ordinary energy, attitude and rest cycles. See [ENVIRONMENT-AND-CONSTRUCTION-GUIDE.md](ENVIRONMENT-AND-CONSTRUCTION-GUIDE.md).

The Info-particles panel supports checked surveys, public-power excitation, owned samples, source-preserving imports and read-only field/single-particle export. Isolating the potential only changes the instrument. Prepared `void_null` outward interacts consume protection and a dose; a recorded return stays available with depleted supplies. The baseline field and map controls yield to the tangible text expedition, with physical work gated until return. See [WORLD-LORE-AND-PARTICLE-INTEGRATION.md](WORLD-LORE-AND-PARTICLE-INTEGRATION.md).

The larger drawing has actual converted selectable features in World Map. Only confirmed existing approach links prepare destinations; travel still requires its normal explicit action. See [CONTINENTAL-SURVEY-GUIDE.md](CONTINENTAL-SURVEY-GUIDE.md).


## Workshop resonance actions

Select a workshop and approach it through the normal hex route. **Look → READ RESONANCE** reads the shared field ledger with a Perception/Light check; it spends no AP or survival cycle. **Skill → TUNE SPECTRUM** offers the five carriers and three response modes. **Use → EXCITE / 1 PUBLIC POWER** pumps the saved reservoir, and **QUENCH RESONANCE** converts its remaining energy into heat on a successful Light check. All three physical attempts use one survival cycle, including on a setback. An excitation always spends one actual public power after passing its prerequisites; tuning and quenching refund no power.

Menus identify the exact selected workshop and display its material, network state, assigned optical source, current setting and stored energy. Inspector and typed controls use the same adjacent-workshop guards. A live reservoir cannot be moved to another workshop before quenching. Pending selections remain attached to their workshop within this field; menu and selection controls share the draft. Polls preserve focus and native select keys.

Broken links, failed collectors, disabled equipment and condition below 30 stop the source. Source identity and tuning survive the outage; remaining optical energy becomes heat. Repair, reconnection and a healthy utility cycle restore eligibility, after which a fresh paid input is required. Optical events retain actor/action/outcome and cannot satisfy repair contracts. Shared requests still require a current revision. See [RESONANCE-AND-SOURCE-GUIDE.md](RESONANCE-AND-SOURCE-GUIDE.md).



## Internal physics measurements

VREX measurements and development controls are off screen. Workshop menus and ordinary help show no VREX or systems-audit actions. The underlying host continues to step configured fields, track particles and save observations. Normal refreshes omit the full internal archive. Read-only development exports and guarded tests remain available through the host API. See [VREX-INTEGRATION-GUIDE.md](VREX-INTEGRATION-GUIDE.md).

## Fitted workshop mechanisms

Adjacent maintained workshops offer Fit Pump, Fit Press and Fit Damper, each costing two personal scrap and a survival cycle with a Tech/Metallurgy check. Operate Machine uses a contextual Tech/Fractech check and one actual public power. Disengage Machine dissipates stored motion with no refund. Fitting and operating do not count as personal maintenance repair proof.

The pump transfers actual local water into a connected cistern. The press contributes reserved work to an owned project within three workshop hexes. The damper absorbs motion with reduced mechanical fatigue. Look reports the installed hardware and its observable status. Numerical traces, correlations and tests remain internal. See [PHYSICS-EMULATION-GUIDE.md](PHYSICS-EMULATION-GUIDE.md).
