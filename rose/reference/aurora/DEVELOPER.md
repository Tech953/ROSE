# Aurora OS — Developer Reference

**Resonance Runtime Environment v1.0.0**

This document is the authoritative technical reference for contributors and integrators. It covers architecture, data models, API, subsystem internals, and development workflow.

---

## Table of Contents

1. [Quick Start](#1-quick-start)
2. [Repository Layout](#2-repository-layout)
3. [Technology Stack](#3-technology-stack)
4. [Architecture Overview](#4-architecture-overview)
5. [Shared Data Model](#5-shared-data-model)
6. [Backend](#6-backend)
7. [Frontend](#7-frontend)
8. [REST API Reference](#8-rest-api-reference)
9. [Physics Engine](#9-physics-engine)
10. [Fractal Renderer](#10-fractal-renderer)
11. [VREX ODE Engine](#11-vrex-ode-engine)
12. [Hardware Plugin SDK](#12-hardware-plugin-sdk)
13. [STRATA Archival System](#13-strata-archival-system)
14. [Build and Deployment](#14-build-and-deployment)
15. [Environment Variables](#15-environment-variables)
16. [Security Notes](#16-security-notes)
17. [Coding Conventions](#17-coding-conventions)

---

## 1. Quick Start

```bash
# Install dependencies
npm install

# Start development server (Express + Vite, port 5000)
npm run dev

# Type-check
npm run check

# Production build → dist/
npm run build

# Run production build
npm start
```

All traffic — API and frontend — goes through a single port (default `5000`). There is no separate dev proxy.

---

## 2. Repository Layout

```
/
├── client/                     # React frontend (Vite root)
│   └── src/
│       ├── App.tsx             # Router setup (Wouter)
│       ├── main.tsx            # React entry point
│       ├── pages/
│       │   ├── dashboard.tsx   # Main simulation UI
│       │   └── not-found.tsx   # 404 page
│       ├── components/
│       │   ├── resonance-canvas.tsx         # Main 2D simulation canvas
│       │   ├── geometric-research-canvas.tsx # Fractal + research visualizations
│       │   ├── enhanced-physics-panel.tsx   # Tabbed physics monitor (Anti/Quarks/Leptons/VREX/…)
│       │   ├── hardware-plugin-panel.tsx    # Hardware instrument interface
│       │   ├── control-panel.tsx            # Simulation controls
│       │   ├── advanced-analysis-panel.tsx  # ML pattern analysis
│       │   ├── object-inspector.tsx         # Per-object property editor
│       │   ├── physics-monitor.tsx          # Real-time force readouts
│       │   ├── ras-chart.tsx                # RAS trend chart (Recharts)
│       │   ├── strata-viewer.tsx            # STRATA layer navigator
│       │   ├── pipeline-panel.tsx           # Data pipeline builder
│       │   ├── research-export-panel.tsx    # JSON/CSV export UI
│       │   ├── dual-bank-seed.tsx           # Dual-bank snapshot UI
│       │   ├── pop-out-window.tsx           # Generic panel pop-out
│       │   ├── system-health-indicator.tsx  # LED-style health display
│       │   ├── synchrony-status-bar.tsx     # Synchrony metric bar
│       │   └── ui/                          # Shadcn/UI component library
│       ├── hooks/
│       │   ├── use-audio.ts    # Web Audio API hook for simulation sounds
│       │   ├── use-mobile.tsx  # Breakpoint detection
│       │   └── use-toast.ts    # Toast notifications
│       └── lib/
│           ├── hardware-plugin-sdk.ts  # Hardware plugin types + built-in plugins
│           ├── queryClient.ts          # TanStack Query + apiRequest helper
│           └── utils.ts               # Tailwind class merging utility
│
├── server/
│   ├── index.ts        # Express bootstrap, port binding
│   ├── routes.ts       # All REST route handlers
│   ├── storage.ts      # In-memory simulation engine + IStorage interface
│   ├── static.ts       # Production static file serving
│   └── vite.ts         # Vite dev server integration (dev only)
│
├── shared/
│   └── schema.ts       # All Zod schemas and TypeScript types (single source of truth)
│
├── script/
│   └── build.ts        # Production build script (esbuild + Vite)
│
├── vite.config.ts      # Vite config with path aliases
├── tailwind.config.ts  # Tailwind theme
├── tsconfig.json       # TypeScript project config
├── README.md           # End-user documentation
├── DEVELOPER.md        # This file
└── VREX_Proposal.md    # VREX theoretical research proposal
```

---

## 3. Technology Stack

### Runtime
| Layer | Technology | Version |
|---|---|---|
| Frontend framework | React | 18.3 |
| Language | TypeScript | 5.6.3 |
| Build tool | Vite | 7.3.2 |
| Backend | Express.js | 5.0 |
| Server runtime | Node.js / tsx | via tsx 4.20 |

### Frontend Libraries
| Library | Purpose |
|---|---|
| TanStack Query v5 | Server state, caching, background refetch |
| Wouter | Client-side routing (lightweight) |
| Shadcn/UI + Radix UI | Accessible component primitives |
| Tailwind CSS | Utility-first styling |
| Recharts | RAS trend charts |
| Framer Motion | Merge/annihilation animations |
| react-hook-form + zod | Form validation |
| lucide-react | Icon set |

### Backend Libraries
| Library | Purpose |
|---|---|
| Multer 2.1.1 | Multipart file upload for `.aurora` import |
| Zod | Request body validation (shared schemas) |
| drizzle-orm 0.45.2 | ORM (types only; no active DB — in-memory storage) |
| ws | WebSocket support (hardware plugin bridge) |

### Path Aliases (Vite + TypeScript)
| Alias | Resolves to |
|---|---|
| `@/` | `client/src/` |
| `@shared/` | `shared/` |
| `@assets/` | `attached_assets/` |

---

## 4. Architecture Overview

```
Browser
  │
  ├─ React (Vite dev server or dist/public)
  │     └─ TanStack Query ──► GET/POST /api/*
  │
HTTP (port 5000)
  │
  └─ Express.js (server/index.ts)
        ├─ API routes (server/routes.ts)
        │     └─ storage.tick() / storage.addObject() / …
        │
        └─ InMemoryStorage (server/storage.ts)
              Physics engine, particle simulation, STRATA, modules, pipelines
```

**Key design decisions:**

- **Single-port, same-origin.** In development, Vite's dev server is mounted as Express middleware (after all API routes). In production, Express serves the compiled `dist/public/` statically. There is no CORS configuration and no separate frontend server.
- **All state is in memory.** `InMemoryStorage` holds the full `RuntimeState` object. No database is connected. Persistence is achieved by exporting to `.aurora` files (JSON).
- **Shared schema.** `shared/schema.ts` defines every Zod schema and TypeScript type used by both frontend and backend. There is one canonical type definition per entity.
- **Frontend polls, not pushes.** TanStack Query refetches `/api/state` on a timer driven by the simulation tick loop. There is no WebSocket feed for simulation state (WebSockets are used only for hardware plugin connections via the browser's native WebSocket API).

---

## 5. Shared Data Model

All types live in `shared/schema.ts`. The primary entities are:

### ResonanceObject — core simulation unit
```typescript
{
  id: string
  name: string
  mass: number          // 0.1–100, resistance to change
  charge: number        // -1–1, attraction/repulsion
  frequency: number     // 0.1–10, natural oscillation rate
  phase: number         // 0–2π, position in oscillation cycle
  element: "cognitive" | "emotional" | "physical" | "temporal" | "ethereal"
  polarity: "matter" | "antimatter"
  matterType: "normal" | "dark"
  position: { x, y }
  velocity: { x, y }
  acceleration?: { x, y }
  trajectory?: TrajectoryPoint[]
  clusterId?: string
  bondStrength?: number
}
```

### Emergent Structures
| Type | Formation | Key field |
|---|---|---|
| `Cluster` | Objects bound by associative physics | `memberIds[]`, `cohesion` |
| `Compound` | RAS ≥ 60 | `resonanceScore`, `growthRing` |
| `SuperCompound` | RAS ≥ 80 | `compoundIds[]`, `totalEnergy` |

### Event Types
- `AnnihilationEvent` — matter-antimatter collision record
- `MergeEvent` — compound formation/split animation data
- `TickEvent` — per-tick performance and action log
- `TimeCrystalManifestation` — automatically archived time crystal detections
- `StressWave` — propagating energy rings from high-energy events

### Analysis Types
- `Quark` / `QuarkGroup` — flavor, color charge, confinement state
- `Lepton` / `LeptonPair` — generation, orbital motion, weak interaction
- `AntiParticle` — temporal offset, self-rectification tracking
- `DeltaLayer` / `NablaLayer` — STRATA immutable/transient archival layers
- `ConservationState` — energy/momentum/velocity conservation metrics

### RuntimeState
`RuntimeState` is the single object returned by every `/api/state` and `/api/tick` call. It contains all of the above arrays plus configuration and derived metrics.

---

## 6. Backend

### server/index.ts

Bootstraps Express, attaches JSON/urlencoded body parsers, registers routes, then mounts either the Vite dev middleware (development) or static file serving (production). Listens on `process.env.PORT` (default `5000`, bound to `0.0.0.0`).

An API request logger middleware captures every `/api/*` call with method, path, status, duration, and abbreviated response body.

### server/routes.ts

Thin route handlers — all business logic lives in storage. Input validation uses Zod schemas imported from `@shared/schema`. Route list: see [§8 REST API Reference](#8-rest-api-reference).

### server/storage.ts — IStorage interface

```typescript
interface IStorage {
  getState(): RuntimeState
  tick(config: SimulationConfig, canvasSize?): RuntimeState
  reset(): RuntimeState
  addObject(obj: InsertResonanceObject): ResonanceObject
  updateObject(id, updates): ResonanceObject | undefined
  deleteObject(id): boolean
  exportState(): string          // JSON serialization
  importState(data: string): RuntimeState
  // Module system
  getModules(): Module[]
  registerModule(module): Module
  updateModuleStatus(moduleId, enabled): Module | undefined
  // Pipeline system
  getPipelines(): Pipeline[]
  createPipeline(pipeline): Pipeline
  runPipeline(pipelineId): PipelineResult
  // Semantic map
  updateSemanticMap(updates): SemanticMap
  // SEED snapshots
  getSeedSnapshots(): SeedSnapshot[]
  restoreFromSnapshot(snapshotId): RuntimeState | null
  compareSnapshots(): { bank0, bank1, diff }
  exportSeedSnapshot(snapshotId): string | null
  switchActiveBank(): "bank_0" | "bank_1"
  // Audio
  toggleAudio(enabled: boolean): void
}
```

`InMemoryStorage` is the sole implementation. The `tick()` method is the physics engine entry point — it advances the simulation by one step and returns the full updated state.

**Important:** changes to `server/` require explicit approval from the project maintainer before modification (see `replit.md` preferences).

---

## 7. Frontend

### client/src/App.tsx

Registers two routes via Wouter:
- `/` → `dashboard.tsx`
- `*` → `not-found.tsx`

Wraps everything in `QueryClientProvider` and `ThemeProvider`.

### client/src/pages/dashboard.tsx

The entire application UI. Fetches `RuntimeState` from `/api/state` on mount, then drives a polling/tick loop. Renders:
- `ResonanceCanvas` — primary 2D simulation canvas
- `ControlPanel` — simulation controls
- `EnhancedPhysicsPanel` — tabbed physics monitor
- `GeometricResearchCanvas` — fractal + research visualizations
- `HardwarePluginPanel` — instrument interface
- `AdvancedAnalysisPanel` — ML analysis
- `ObjectInspector` — per-object property editor
- Various status/chart panels

### client/src/lib/queryClient.ts

Configures TanStack Query with `staleTime: 0` and a default `queryFn` that calls `apiRequest`. The `apiRequest` helper throws on non-2xx responses and parses JSON automatically. Import for mutations:

```typescript
import { apiRequest, queryClient } from "@/lib/queryClient";

// Mutation pattern
await apiRequest("POST", "/api/objects", body);
queryClient.invalidateQueries({ queryKey: ["/api/state"] });
```

### client/src/components/pop-out-window.tsx

Wraps any panel child in `window.open()`. Uses `createPortal` to render React children into the new window's DOM. The new window is bootstrapped with a static HTML template (no user-controlled interpolation). Theme class and title are set via DOM API after the document opens to avoid XSS.

### Custom Hooks

| Hook | Purpose |
|---|---|
| `use-audio.ts` | Web Audio API — synthesizes tones for merge, split, and annihilation events |
| `use-toast.ts` | Shadcn toast notification queue |
| `use-mobile.tsx` | `768px` breakpoint detection via `matchMedia` |

---

## 8. REST API Reference

Base URL: `http://localhost:5000`

All request and response bodies are JSON. File upload endpoints use `multipart/form-data`.

### Simulation Core

| Method | Path | Body | Response | Description |
|---|---|---|---|---|
| `GET` | `/api/state` | — | `RuntimeState` | Full simulation state snapshot |
| `POST` | `/api/tick` | `{ config?: SimulationConfig, canvasSize?: {w,h} }` | `RuntimeState` | Advance simulation by one tick |
| `POST` | `/api/reset` | — | `RuntimeState` | Reset to genesis state |

### Resonance Objects

| Method | Path | Body | Response | Description |
|---|---|---|---|---|
| `POST` | `/api/objects` | `InsertResonanceObject` | `ResonanceObject` | Create new object |
| `PATCH` | `/api/objects/:id` | `Partial<ResonanceObject>` | `ResonanceObject` | Update object properties |
| `DELETE` | `/api/objects/:id` | — | `{ success: true }` | Remove object |

### Import / Export

| Method | Path | Body | Response | Description |
|---|---|---|---|---|
| `GET` | `/api/export` | — | `.aurora` file download | Export full state as STRATA JSON |
| `POST` | `/api/import` | `multipart/form-data` (field: `file`) | `RuntimeState` | Import `.aurora` file |

### Module System

| Method | Path | Body | Response | Description |
|---|---|---|---|---|
| `GET` | `/api/modules` | — | `Module[]` | List all modules |
| `POST` | `/api/modules` | `Omit<Module, "id">` | `Module` | Register new module |
| `PATCH` | `/api/modules/:id` | `{ enabled: boolean }` | `Module` | Enable/disable module |

### Pipeline System

| Method | Path | Body | Response | Description |
|---|---|---|---|---|
| `GET` | `/api/pipelines` | — | `Pipeline[]` | List all pipelines |
| `POST` | `/api/pipelines` | `Omit<Pipeline, "id"|"status">` | `Pipeline` | Create pipeline |
| `POST` | `/api/pipelines/:id/run` | — | `PipelineResult` | Execute pipeline |

### Semantic Map

| Method | Path | Body | Response | Description |
|---|---|---|---|---|
| `GET` | `/api/semantic-map` | — | `SemanticMap` | Get current semantic map |
| `PATCH` | `/api/semantic-map` | `Partial<SemanticMap>` | `SemanticMap` | Update semantic map fields |

### SEED Snapshots (Dual-Bank)

| Method | Path | Response | Description |
|---|---|---|---|
| `GET` | `/api/seed-snapshots` | `SeedSnapshot[]` | List both banks |
| `GET` | `/api/seed-snapshots/compare` | `{ bank0, bank1, diff }` | Diff bank 0 vs bank 1 |
| `POST` | `/api/seed-snapshots/:id/restore` | `RuntimeState` | Restore from snapshot |
| `GET` | `/api/seed-snapshots/:id/export` | JSON file download | Export one snapshot |
| `POST` | `/api/seed-snapshots/switch-bank` | `{ activeBank }` | Toggle active bank |

### Analytics and Events

| Method | Path | Response | Description |
|---|---|---|---|
| `GET` | `/api/ras-history` | `{ history, predictedRAS, currentRAS }` | RAS trend data |
| `GET` | `/api/tick-events` | `{ events, priority, batchSize }` | Tick debug log |
| `GET` | `/api/merge-events` | `MergeEvent[]` | Formation/split events |
| `GET` | `/api/audio-events` | `{ events, enabled }` | Audio feedback queue |
| `GET` | `/api/module-statuses` | `ModuleStatus[]` | Pipeline module health |
| `POST` | `/api/audio/toggle` | `{ enabled: boolean }` | Enable/disable audio |

### SimulationConfig schema

```typescript
{
  gravitationalConstant?: number   // default 0.5
  dampingFactor?: number           // default 0.99
  resonanceThreshold?: number      // default 60 (RAS for compound formation)
  tickRate?: number                // ms per tick
  annihilationRadius?: number      // px — matter-antimatter trigger distance
  darkMatterMultiplier?: number    // gravitational scaling for dark matter
}
```

---

## 9. Physics Engine

All physics runs server-side inside `storage.tick()` in `server/storage.ts`.

### Force Model

Each tick, every pair of objects computes:

```
F_gravity    = G × (m₁ × m₂) / r²
Amplification = cos(Δphase) × exp(-|Δfrequency|)
F_resonance  = F_gravity × Amplification × Compatibility
F_charge     = k × (q₁ × q₂) / r²  (same sign repels, opposite attracts)
F_polarity   = matter-antimatter attraction modifier
F_total      = F_resonance + F_charge + F_polarity
```

`Compatibility` is looked up from `elementCompatibility` — a 5×5 matrix in `shared/schema.ts` encoding elemental affinities between cognitive, emotional, physical, temporal, and ethereal types.

### Resonance Alignment Score (RAS)

```
RAS(a, b) = 100 × cos(Δphase) × (1 − |Δfrequency / maxFreq|) × elementCompatibility[a.el][b.el]
```

- RAS ≥ 60 → objects merge into a **Compound**
- RAS ≥ 80 → Compounds merge into a **SuperCompound**

The global RAS is the mean pairwise score across all objects.

### Anti-Particle Physics

Antimatter objects attract matter via polarity force. Within `annihilationRadius`, an annihilation event fires:
- Both objects are removed
- An `AnnihilationEvent` is logged with `energyReleased = m₁ + m₂`
- A `StressWave` propagates outward from the collision point
- Nearby objects receive an outward velocity impulse proportional to `1/r²`

### Dark Matter

Dark matter objects (`matterType: "dark"`) exert gravitational force but have zero charge interaction and do not trigger annihilation. They are rendered as faint dashed circles on the canvas.

### Escapement Mechanics

Each tick analyzes oscillation patterns to extract:
- **PendulumState** — swing amplitude, period, synchronization degree, damping coefficient
- **GearConnection** — frequency coupling ratio between object pairs, slip detection, transmission efficiency
- **SubharmonicCrystal** — detects objects oscillating at exact integer subharmonics of a reference; these are archived as `TimeCrystalManifestation` records when phase coherence criteria are met

### Conservation Tracking

Per-tick deltas are computed for total kinetic energy, linear momentum, and velocity bound violations. When drift exceeds thresholds, passive rectification applies a corrective impulse proportional to the violation magnitude.

---

## 10. Fractal Renderer

`client/src/components/geometric-research-canvas.tsx`

The fractal renderer has three display modes selectable from the controls bar:

| Mode | Function | Description |
|---|---|---|
| Flat 2D | `drawFractalBasin()` | Full-resolution pixel raster, physics palette |
| 3D Height Field | `draw3DHeightField()` | 72×72 lit mesh, painter's sort |
| Split View | `drawSplitView()` | Four simultaneous 3D perspectives |

### Resonance Anomaly Algorithm

**Step 1 — N-body resonance potential**

For every pixel at complex coordinate `c`:

```
Φ(c) = Σᵢ  signᵢ · wᵢ · strengthᵢ · e^(i·φᵢ) / |c − pᵢ|^νᵢ

pᵢ = (phase_i/π − 1) + i·(freq_i/maxFreq − 0.5)   // attractor position
wᵢ = mass_i / Σmass                                  // mass-normalized weight
strengthᵢ = |charge_i|                               // field intensity
νᵢ = 1 + 0.4·|charge_i|                             // power-law exponent
signᵢ = −1 if antimatter                             // polarity inversion
```

Result is normalized: `|Φ| ≤ 0.9`.

**Step 2 — Escape iteration**

```
z₀ = 0
z_{n+1} = z_n² + Φ(c)
```

Smooth iteration count: `t = iter + 1 − log₂(log₂|z|)` eliminates banding.

**Step 3 — Escape angle for hue offset**

The argument of `z` at escape is quantized and blended: `angleContrib = (angle / 255) × 0.12`, producing rotationally structured banding unique to each particle configuration.

### Physics-Derived Color Palette

The 9 palette stops are computed from particle state every render:

| Input | Controls |
|---|---|
| Mass-weighted circular mean of phase vectors `atan2(Σw·sinφ, Σw·cosφ)` | Base hue |
| Average `νᵢ` (charge power-law) | Hue sweep width |
| Mean field strength `Σw·|charge|` | Saturation |
| Antimatter mass fraction | Hue shift toward complementary (+π for pure antimatter) |

Stops use a `t^0.5` value gamma (dark interior → bright at fast escape) with sinusoidal saturation peaking in mid-range.

The annotation bar shows the live readout: `Palette: hue 127°  sweep 64°  sat 72%  |  physics-derived`.

### Caching

```typescript
fractalCacheRef: { smoothIter: Float32Array, rootId: Uint8Array, w, h, key }
heightMapCacheRef: { values: Float32Array, N, key }
```

Cache keys encode the full particle configuration (`px`, `py`, `w`, `nu`, `sign` per attractor). The escape-time data is reused across frames; only the palette application runs per frame (driven by `currentTick * 0.003` color shift). The cache invalidates automatically when any simulation object changes.

### 3D Renderer

- 72×72 vertex grid → 5,041 quads
- Height: `Z(i,j) = smoothIter(i,j) / maxSmoothIter × 1.8`
- Surface normals via cross product of adjacent edge vectors
- Diffuse shading: `brightness = max(0, dot(normal, [0.45, −0.45, 0.77]))`
- Quads sorted by average projected Z (painter's algorithm)
- Wireframe edges for quads with height > 15% of max

### Recording

- **PNG**: `canvas.toDataURL("image/png")` at device pixel ratio
- **WebM**: `canvas.captureStream(60)` → `MediaRecorder` at VP9 / 12 Mbps (Chromium-based browsers only)

---

## 11. VREX ODE Engine

Located in `EnhancedPhysicsPanel` → VREX tab.

The engine integrates a coupled 4-variable ODE system at 20 Hz (50 ms interval, 15 substeps per tick using Euler integration):

### State Variables

```typescript
odeRef: { A: number, dA: number, N: number, phi: number, t: number }
```

| Variable | Equation | Description |
|---|---|---|
| `A` (crystal amplitude) | `Ä + Γ·Ȧ + ωT²·A + α·A³ = F·cos(ωD·t)` | Duffing oscillator; `ωT = ωD/2` |
| `N` (photon population) | `dN/dt = η_eff·A_eff² − γN·N` | DCE photon extraction |
| `phi` (coherence) | `dφ/dt = −φ/τ` | Phase decoherence; `A_eff = A·phi` |

### Parameters

```
α = 0.1        // Duffing nonlinearity
ε = 0.05       // Cavity boundary displacement amplitude
β = 0.4        // SEF coupling coefficient
L₀ = 1.0      // Rest cavity length
HISTORY_LEN = 80  // Sparkline buffer
```

### Derived Metrics

```
EGR  = P_photon / P_drive           // Energy Gain Ratio
P_photon = ħωc · max(dN/dt, 0)     // Photon power output
τ ~ exp(c·ωD / F)                  // Prethermal lifetime (Abanin 2017)
```

To add a new derived metric, extend `odeRef` with additional state variables and compute them in the `stepODE` function. Add a sparkline entry to the history array and a display row in the panel JSX.

---

## 12. Hardware Plugin SDK

`client/src/lib/hardware-plugin-sdk.ts`

### Core Interfaces

```typescript
interface HardwarePlugin {
  id: string
  name: string
  deviceType: "oscilloscope" | "signal_generator" | "daq" | "vrex_sensor" | "custom"
  transport: "serial" | "websocket" | "simulated"
  description: string
  channels: string[]
  baudRate?: number      // for serial transport
  wsUrl?: string         // for websocket transport
  protocol: "scpi" | "json" | "binary" | "nmea" | "custom"
  mapToSimulation: (frame: PluginDataFrame) => SimulationMapping | null
}

interface PluginDataFrame {
  timestamp: number
  channel: string
  value: number
  unit: string
  metadata?: Record<string, unknown>
}

interface SimulationMapping {
  targetProperty: "mass" | "charge" | "frequency" | "phase" | "vrex_sef" | "vrex_drive" | "custom"
  value: number
  objectId?: string
}
```

### Writing a Custom Plugin

```typescript
import type { HardwarePlugin, PluginDataFrame, SimulationMapping } from "@/lib/hardware-plugin-sdk";

const myPlugin: HardwarePlugin = {
  id: "my-daq-v1",
  name: "My DAQ Board",
  deviceType: "daq",
  transport: "websocket",
  description: "Streams voltage readings from channel 0 into resonance object mass",
  channels: ["ch0", "ch1"],
  wsUrl: "ws://192.168.1.50:8080",
  protocol: "json",
  mapToSimulation: (frame: PluginDataFrame): SimulationMapping | null => {
    if (frame.channel === "ch0") {
      return { targetProperty: "mass", value: frame.value / 10 };
    }
    return null;
  },
};
```

Register by adding to the `BUILT_IN_PLUGINS` array in `hardware-plugin-sdk.ts`, or pass it to the `HardwarePluginPanel` component at runtime via its plugin registry.

### Built-In Plugins

| ID | Device | Transport | Protocol | Channels |
|---|---|---|---|---|
| `vrex-sensor-v1` | VREX Prototype Sensor | Serial 115200 | JSON | phase_lock, photon_rate, cavity_freq, egr |
| `scpi-oscilloscope` | Generic SCPI Oscilloscope | Serial | SCPI | amplitude, frequency |
| `ni-daq-usb6001` | NI USB-6001 DAQ | Serial | JSON | ai0–ai3, di0–di7 |
| `ws-spectrum-analyzer` | WebSocket Spectrum Analyzer | WebSocket | JSON | frequency, amplitude, phase |
| `simulated-resonance` | Simulated Test Source | Simulated | — | mass, charge, frequency, phase |

### Transport Lifecycle

The `HardwarePluginPanel` manages `PluginSession` objects. On connect:

1. For `serial`: calls `navigator.serial.requestPort()` (Web Serial API — Chromium only) and opens at `baudRate`
2. For `websocket`: opens `new WebSocket(wsUrl)`
3. For `simulated`: starts a `setInterval` generating synthetic `PluginDataFrame` objects

Incoming frames pass through `plugin.mapToSimulation()`. Non-null results are applied to the target simulation object via `PATCH /api/objects/:id`.

---

## 13. STRATA Archival System

STRATA (v1.0.0) is the layered state persistence format used for `.aurora` files and internal archival.

### Layer Types

| Layer | Type | Description |
|---|---|---|
| **Genesis Block** | `DeltaLayer` (Full) | Initial state snapshot, checksum-verified |
| **Growth Blocks** | `DeltaLayer` (Incremental) | Per-milestone state deltas |
| **Overlay Blocks** | `DeltaLayer` (Keyframe) | Point-in-time full snapshots |
| **Pipeline Blocks** | `DeltaLayer` | Pipeline execution records |
| **Nabla (∇) Layers** | `NablaLayer` | Transient: stress waves, force fields, particle pairs |

### DeltaLayer schema

```typescript
{
  id: string
  type: "full" | "incremental" | "keyframe"
  tick: number
  timestamp: string
  checksum: string       // SHA-256 of serialized data
  objectCount: number
  data: Record<string, unknown>
}
```

### NablaLayer schema

```typescript
{
  id: string
  tick: number
  timestamp: string
  stressWaveData?: StressWave[]
  forceFieldData?: ForceVector[]
  transientEvents?: string[]
  particlePairData?: AntiParticle[]
}
```

### Semantic Map

The `SemanticMap` is attached to every exported state and describes the simulation context:

```typescript
{
  schema: "aurora-resonance.v1"
  units: "abstract"
  timebase: "utc"
  ethics: "observational"
  domain: "physics-simulation"
  intent: string
  annotations: string[]
}
```

### Dual-Bank SEED Snapshots

Two snapshot banks (`bank_0`, `bank_1`) are maintained automatically. Each contains a `checksum`-verified serialization of the full `RuntimeState`. Snapshots can be compared, exported, and restored independently — providing redundant state recovery in case of simulation instability.

---

## 14. Build and Deployment

### Development

```bash
npm run dev
# NODE_ENV=development tsx server/index.ts
# → Express on :5000 with Vite dev middleware attached
```

### Production Build

```bash
npm run build
# script/build.ts runs:
#   1. npx vite build  → dist/public/ (frontend)
#   2. esbuild server/index.ts  → dist/index.cjs (backend)
```

### Running Production Build

```bash
npm start
# NODE_ENV=production node dist/index.cjs
# → Express serves dist/public/ as static files
```

### Type Check

```bash
npm run check
# npx tsc --noEmit
```

### Schema Push (if a database is later added)

```bash
npm run db:push
# drizzle-kit push
```

---

## 15. Environment Variables

| Variable | Default | Description |
|---|---|---|
| `PORT` | `5000` | HTTP server port |
| `NODE_ENV` | `development` | `production` disables Vite middleware and enables static serving |
| `SESSION_SECRET` | — | Secret for express-session (set in environment secrets, not in code) |

No secrets should be committed to the repository. Use the environment secrets manager for sensitive values.

---

## 16. Security Notes

This section summarises the outcome of the May 2026 security audit.

### Dependency Posture (post-audit)

All findings from the May 2026 audit have been remediated. Current patched versions:

| Package | Version | Findings resolved |
|---|---|---|
| `vite` | 7.3.2 | Arbitrary file read via WebSocket, `server.fs.deny` bypass, path traversal |
| `multer` | 2.1.1 | Three DoS vectors (recursion, resource exhaustion, incomplete cleanup) |
| `path-to-regexp` | 8.4.0 | Two ReDoS / DoS patterns |
| `drizzle-orm` | 0.45.2 | SQL injection via identifier escaping |
| `postcss` | 8.5.10 | XSS via unescaped `</style>` in CSS stringify |
| `yaml` | 2.8.3 | Stack overflow on deeply nested YAML |
| `qs` | 6.14.2 | DoS via array limit bypass |
| `minimatch` | 9.0.7 | Three ReDoS patterns |
| `picomatch` | 2.3.2 | ReDoS + method injection |
| `rollup` | 4.59.0 | Arbitrary file write via path traversal |
| `brace-expansion` | 2.0.3 | Zero-step sequence DoS |

### Code-Level

- **`pop-out-window.tsx`** — `document.write()` no longer interpolates user-controlled variables. The new window is bootstrapped with a static HTML string; `document.title` and theme class are set via DOM API afterwards.
- **No SQL queries accept untrusted identifier input.** All drizzle-orm usage is against static schema objects.
- **Request bodies are validated with Zod** before reaching storage. Invalid payloads return HTTP 400.

### Remaining Acknowledged Risk

- `lodash` remains at 4.17.21 — the security-fix release 4.18.0 was recalled by the maintainer as a bad release. The lodash vulnerabilities (prototype pollution, code injection) affect dev tooling only as transitive dependencies; lodash is not called directly in application code paths that process untrusted input.

---

## 17. Coding Conventions

### General
- TypeScript strict mode. No `any` unless an explicit comment explains why.
- All shared types defined in `shared/schema.ts`. Do not duplicate type definitions between frontend and backend.
- Use Zod `safeParse` for request body validation; never trust `req.body` directly.

### Frontend
- Use TanStack Query for all server data. Do not use `fetch` directly outside `queryClient.ts`.
- Queries use array keys: `["/api/state"]`, `["/api/objects", id]` — never template literals as the sole key.
- After any mutation, invalidate the affected query key.
- Add `data-testid` attributes to all interactive elements using `{action}-{target}` pattern.
- No explicit `React` import — the Vite JSX transform handles it.
- Use `import.meta.env.VITE_*` for frontend environment variables.

### Canvas Renderers
- All canvas drawing functions (`drawFractalBasin`, `draw3DHeightField`, etc.) are `useCallback` with explicit dependency arrays.
- Heavy computation (escape iteration, height maps) is cached in refs. Only the coloring/animation pass runs per frame.
- Return early with a dark canvas + status message when no simulation data is present. Never fall back to a generic preset.

### Server
- Route handlers are thin. All business logic belongs in `storage.ts`.
- Do not add new packages to the server without confirming the change with the maintainer.
- Do not modify `server/vite.ts` or `vite.config.ts` — the dev server integration is pre-configured.

### Commit Style
- Commits describe the change from the user's perspective, not the implementation: `Fix fractal renderer returning blank canvas on empty simulation` not `Add early return to drawFractalBasin`.
