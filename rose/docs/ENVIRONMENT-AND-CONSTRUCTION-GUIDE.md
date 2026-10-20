# Rose 0.9 — Living environments and construction

Rose now saves soil, planted succession, detritus, erosion and staged construction alongside its existing weather, survival, resource and infrastructure records. These changes affect local movement, utility production, shelter, field appearance and descriptions. They persist through SQLite saves and host restarts.

The rates are bounded game-cycle approximations. Moisture and soil health are indices, rather than measured millimeters or chemical concentrations. The host clock and permitted actions advance the simulation; a closed host does not simulate elapsed offline wall time. A paused world holds, and shared environmental time holds during active tactical encounters.

## Read and care for a field

Open **Environment / Succession and Construction**, or type `inspect environment`. Moisture, growth, soil health, detritus and erosion remain readable even when the contextual Druid observation check is uncertain. Hovering and opening the panel do not roll; the explicit survey records a check without consuming a survival cycle.

| Change | Inputs and consequences |
| --- | --- |
| Growth | Existing climate, moisture and grazing continue to govern growth. Soil below 15 prevents a positive growth gain; soil below 35 caps the gain at one per cycle. Expanding cover gradually uses soil health. |
| Decay | Lost growth adds detritus. Every fourth suitable damp cycle consumes two detritus and restores one soil health. |
| Erosion | Particulate storms and contrail squalls damage sparse cover and soil. Established damp cover gradually reduces erosion. |
| Plant succession | A successful planting records its local hex, species, owner, age and stress. Four favorable cycles produce a seedling; twelve establish the patch. Establishment adds growth once. Poor conditions cause wilt and then decay into detritus. |
| Tend soil | Requires and uses one actual pack water on the attempt. A successful Druid/context/standing check improves moisture and soil. |
| Compost litter | Requires four local detritus. A successful check converts it into six soil health; no resource appears from an empty litter store. |
| Infrastructure wear | Organic structures respond to damp exposure, city metal to corrosion, exposed Aethergale fabric to squalls, and gardens to dry/poor growth. Condition, supply and network state select working or worn presentation. |

Planting gives a small initial growth gain; it no longer grants instant mature cover. A mature patch cannot pay its establishment bonus repeatedly. There are at most twelve living registered patches in a local field. Decayed patch records are replaced as new patches are planted; soil and the finite history retain their consequences.

Ground moisture tint, detritus marks and erosion traces follow actual indices. Registered patches appear at their planted coordinates. These are bounded material overlays and stage variants of original prefabs; the engine does not create a new botanical mesh for each seed.

## Build beside an actual hex

Choose a blueprint and an adjacent candidate in the construction panel. The host rejects the field center, occupied or solid ground, a living unit's hex, and placements that cut the remaining walking paths to the center or structure aprons. Construction is physical baseline work, outside combat and remote observation.

| Blueprint | Reserved scrap | Successful work steps | Main proficiency | Base difficulty |
| --- | ---: | ---: | --- | ---: |
| Garden | 4 | 4 | Druid | 11 |
| Shelter | 5 | 5 | Metallurgy | 11 |
| Water collector | 6 | 6 | Resource | 12 |
| Power collector | 7 | 6 | Fractech | 12 |
| Workshop | 7 | 6 | Metallurgy | 12 |
| Relay | 6 | 5 | Fractech | 12 |

Planning checks training, context and faction standing. Success reserves the full scrap cost from your pack and registers a foundation on the chosen hex. A failed plan spends no scrap. The site immediately blocks walking; a foundation remains transparent to line of sight, while its frame and finishing stages become opaque.

Work requires an adjacent approach and the blueprint's check. Progress reveals progressively more of the same regional prepared building. The drawn portion owns its click bounds; its undrawn upper portion cannot intercept a selection. The registered project remains available through Scene Objects and its project card.

Completion creates a real enabled infrastructure node at that coordinate, with condition 100, capacity two and a link to the nearest existing node. Network state is recalculated. A completed shelter increases the local shelter value within the existing cap. The resulting node uses ordinary production, repairs, finite public stores, contracts and adjacency rules.

Cancel beside a project you own. A successful cancellation check restores the previous tile and refunds only unused reserved scrap, subject to pack capacity. Used material is retained as expenditure; repeated cancellation cannot refund twice. Continued storm exposure can remove work progress without refunding consumed material.

The field permits six active projects and at most twenty-eight public structures. Project records retain contributor IDs and material spending. The panel shows exact blocked reasons, reserved/spent material, work remaining and a bounded history.

## Work alongside companions

Up to two owned companions retain their existing personality, faction standing, conditions, energy and observe → plan → work → reflect → recover cycles. Propose the **repair** assignment. A willing companion can prioritize an owned unfinished project, walk toward its hex, and attempt work in a later work period with the relevant blueprint skill. Reserved project material permits contribution even when their personal scrap pack is empty. Repairing existing infrastructure still uses real material.

Nearby trained companions can support your own checks. They cannot work remotely, pass through blocked tiles, skip recovery or guarantee success. During a `void_null` expedition they remain at the retained baseline anchor; this release does not give them void expedition bodies.

## Typed intentions

```text
inspect environment
plant
tend soil
compost litter
plan shelter 1,0
work project project-ID
cancel project project-ID
```

Use the actual project ID shown in the panel and an available adjacent coordinate. Unknown, blocked and stale requests are revalidated by the host. Accepted attempts retain their material and time costs on a setback; the client does not automatically retry them.

## Persistent scope

Old Rose saves gain lifecycle records from their existing growth and moisture, preserving structures, characters and stock. Ordinary saves retain plant and project identities, escrow, construction tiles, completed nodes and links. The Infrastructure export is a public generation blueprint, not a complete world backup; it excludes player-owned project/plant records, seat credentials and particle archives. Back up the stopped host's SQLite database for full continuity.

The prototype does not yet simulate structural collapse debris, fire propagation, excavated interiors, hydraulic fluids, a metric seasonal climate, individual unplanted trees or construction at continent-wide atomic resolution. The new systems provide concrete extension points in `lifecycle.py`, `infrastructure.py`, `world.py` and `static/environment.js`.
