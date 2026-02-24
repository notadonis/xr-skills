# Backend Infrastructure Reference

## Table of Contents
1. [Multiplayer & Real-Time Networking](#multiplayer)
2. [Spatial Data & Persistence](#spatial-data)
3. [Cloud Rendering & Streaming](#cloud-rendering)
4. [Asset Delivery & CDN](#asset-delivery)
5. [Analytics & Telemetry](#analytics)
6. [API Design for XR Clients](#api-design)
7. [Authentication in XR](#auth)

---

## Multiplayer & Real-Time Networking {#multiplayer}

XR multiplayer is harder than flatscreen multiplayer because the data volume is higher, the latency
tolerance is lower, and the consequences of failure (nausea, broken presence) are physical.

### Why XR Networking Is Different

| Requirement | Why It Matters | Solution |
|---|---|---|
| **< 50 ms RTT** | Head/hand lag breaks presence and causes discomfort | Dedicated regional servers, UDP, client-side prediction |
| **High-frequency pose sync** | 6DoF head + 2× hands + 25-joint fingers = hundreds of floats/frame | Delta compression, quantization, variable update rates |
| **Spatial voice** | Voice must come from the speaker's 3D position | Spatialized VOIP (Photon Voice, Normcore, Agora) |
| **Shared spatial anchors** | Users must agree on where physical surfaces are | Cloud anchors (ARCore, Azure, Meta) |
| **Avatar embodiment** | Users need to see each other's head, hands, body language | IK-driven avatar from 3-point tracking (head + 2 hands) |

### Bandwidth Math

```
PER USER, UPSTREAM:
  Head pose:        30 Hz × 28 bytes (vec3 + quat)           =    840 B/s
  Controller (×2):  30 Hz × 40 bytes (pose + buttons + axis)  =  2,400 B/s
  Hand skeleton:    15 Hz × 200 bytes (compressed 25 joints)  =  3,000 B/s per hand
  Voice (Opus):     50 Hz × 120 bytes (20 ms frames)          =  6,000 B/s
  Object state:     10 Hz × varies                             =  ~2,000 B/s
  ─────────────────────────────────────────────────────────
  TOTAL PER USER:   ~15–25 KB/s upstream

FOR 6 USERS: Each client receives 5 × 15 KB/s = ~75 KB/s downstream
```

Keep total per-client bandwidth under 50 KB/s upstream for mobile networks. On Wi-Fi 6, you have
more headroom, but don't waste it.

### Pose Compression Techniques

```
QUATERNION: Use smallest-three encoding.
  Full quaternion:  4 × 32-bit float = 16 bytes
  Smallest-three:   3 × 16-bit int + 2-bit index = 7 bytes (55% reduction)
  Encode the three smallest components as fixed-point int16.
  Reconstruct the fourth from unit-quaternion constraint (w² + x² + y² + z² = 1).

POSITION: Quantize to int16 relative to a known origin.
  Full position:    3 × 32-bit float = 12 bytes
  Quantized:        3 × 16-bit int = 6 bytes (50% reduction)
  Resolution: ±32m range with 1mm precision — sufficient for room-scale.

DELTA COMPRESSION:
  Send full state every N seconds. Between, send only the delta from previous frame.
  For slowly moving objects, deltas are near-zero and compress extremely well.

PRIORITY-BASED UPDATE RATES:
  Head pose:        30 Hz  (highest priority — others see where you look)
  Dominant hand:    30 Hz  (gesturing, interacting)
  Non-dominant hand: 15 Hz  (usually stationary)
  Body estimation:  10 Hz  (IK-interpolated locally)
  Objects:          5–10 Hz (interpolated between updates)
```

### Framework Comparison

| Framework | Protocol | Best For | Voice | Hosting |
|---|---|---|---|---|
| **Normcore** | Custom UDP | Fast prototyping, ≤ 8 users, Unity | Built-in | Managed |
| **Photon Fusion** | Enet/UDP | Competitive games, tick-based physics | Photon Voice 2 | Managed (Photon Cloud) |
| **Photon Quantum** | Deterministic sim | Precise physics, fighting/sports | Photon Voice 2 | Managed |
| **Unity Netcode for GameObjects** | Unity Transport | Teams deep in Unity ecosystem | Third-party | Self or Unity Relay |
| **Mirror** | KCP/Websocket/TCP | Self-hosted enterprise, data sovereignty | Third-party | Self-hosted |
| **LiveKit** | WebRTC | WebXR multi-user, hybrid web+native | Built-in | Self or managed |
| **Croquet** | Croquet reflector | Deterministic, low-code sync | Third-party | Managed |

### IK Avatar from 3-Point Tracking

Most XR multiplayer only tracks head + two hands. You need inverse kinematics (IK) to
fill in the rest of the body:

```
TRACKED INPUTS:
  Head transform    → drives neck/head IK target
  Left hand pose    → drives left arm IK chain
  Right hand pose   → drives right arm IK chain

IK CHAIN:
  Shoulder → Elbow → Wrist → (optional: fingers if hand tracking data available)

MISSING DATA (must be estimated):
  Torso:     Estimated from head position + head forward direction
  Hips:      Estimated ~0.5× head height below head
  Legs/feet: Either hidden (seated avatar) or estimated via locomotion (walking anim when moving)

SOLUTIONS:
  Unity: Final IK (paid asset, industry standard), Animation Rigging package (free)
  Unreal: IK Rig, Full Body IK solver (built-in)
  Custom: FABRIK algorithm for arm chains, look-at constraint for torso

CRITICAL:
  Run IK locally on each client, not on the server. Send only the 3 tracking points.
  This saves bandwidth and lets local IK run at render framerate.
```

**Real-world example:** An automotive design review with 6 participants. Photon Fusion server
in eu-west syncs head+hand poses at 30 Hz. Each client runs FABRIK IK locally. Azure Spatial
Anchors align the virtual car model to the physical clay model for the MR user on HoloLens 2.
Photon Voice 2 spatializes voice so the engineer "across the car" sounds across the car.

---

## Spatial Data & Persistence {#spatial-data}

### Anchor Services

| Service | Platforms | Persistence | Sharing | Use Case |
|---|---|---|---|---|
| **Azure Spatial Anchors (ASA)** | HoloLens, iOS, Android | Cloud (months+) | Cross-device via anchor ID | Enterprise, cross-platform |
| **Google Cloud Anchors** | ARCore | Cloud (365 days) | Cross-device via anchor ID | Android-first experiences |
| **Google Geospatial API** | ARCore | Infinite (GPS-based) | Inherently shared (lat/lon) | Outdoor AR (navigation, city-scale) |
| **Meta Shared Spatial Anchors** | Quest | Cloud | Quest-to-Quest colocation | Social VR, shared MR |
| **ARKit Collaborative Sessions** | iOS, visionOS | Session only | Peer-to-peer (no cloud) | Apple device colocation |

### Persistence Architecture

```
                         ┌──────────────────┐
                         │   XR Client      │
                         │   (Quest/Phone)   │
                         └────────┬─────────┘
                                  │
                    1. Visual scan resolves
                       anchor position
                                  │
                         ┌────────▼─────────┐
                         │  Anchor Service   │  (Azure ASA / ARCore Cloud / Meta Cloud)
                         │  Returns: pose    │
                         │  relative to      │
                         │  anchor ID        │
                         └────────┬─────────┘
                                  │
                    2. Fetch content tied
                       to anchor ID
                                  │
                         ┌────────▼─────────┐
                         │  Content API      │  (Your backend)
                         │  Returns: 3D      │
                         │  models, UI data,  │
                         │  annotations       │
                         └────────┬─────────┘
                                  │
                         ┌────────▼─────────┐
                         │  Content DB       │  (Postgres + PostGIS)
                         │  anchor_id (FK)    │
                         │  content_type      │
                         │  model_url         │
                         │  transform_offset  │
                         │  metadata (JSONB)  │
                         └──────────────────┘
```

### Database Schema Pattern

```sql
-- Spatial content linked to anchors
CREATE TABLE spatial_content (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    anchor_id       TEXT NOT NULL,               -- From anchor service (opaque ID)
    anchor_service  TEXT NOT NULL,               -- 'azure_asa', 'arcore_cloud', 'meta_ssa'
    content_type    TEXT NOT NULL,               -- 'model', 'annotation', 'waypoint'
    model_url       TEXT,                        -- CDN URL for 3D asset
    transform       JSONB NOT NULL DEFAULT '{}', -- Local offset from anchor (pos, rot, scale)
    metadata        JSONB DEFAULT '{}',          -- App-specific data
    location        GEOGRAPHY(POINT, 4326),      -- GPS for geo-queries (nullable for indoor)
    created_by      UUID REFERENCES users(id),
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    expires_at      TIMESTAMPTZ                  -- Auto-cleanup for temporary content
);

-- Spatial index for geo-queries
CREATE INDEX idx_spatial_content_location ON spatial_content USING GIST(location);
CREATE INDEX idx_spatial_content_anchor ON spatial_content(anchor_id);
```

### Anchor Lifecycle

```
1. CREATION: Client scans environment → creates anchor → gets anchor ID → sends to your API
2. RESOLUTION: Client scans environment → requests anchor by ID → service returns pose
3. CONTENT FETCH: Client uses anchor ID to query your API for associated 3D content
4. EXPIRY: Cloud anchors expire (ARCore: 365 days, Azure: configurable)
   Your API should handle 404 from anchor service gracefully — prompt user to re-scan.
5. DRIFT: Anchors drift over time (millimeters per week). Cache resolved poses with TTL.
   For precision applications (surgery, construction), re-resolve anchors each session.
```

---

## Cloud Rendering & Streaming {#cloud-rendering}

### Solutions

| Solution | Protocol | Source | Target | Latency |
|---|---|---|---|---|
| **NVIDIA CloudXR** | Custom streaming | SteamVR on cloud GPU | Quest / thin client | 30–80 ms |
| **Azure Remote Rendering** | Custom | Azure GPU | HoloLens 2 / PC | 40–100 ms |
| **Unreal Pixel Streaming** | WebRTC | UE on server | Browser / thin client | 30–60 ms |
| **Custom WebRTC** | WebRTC | Any renderer | Browser | 20–50 ms |

### Latency Budget

Motion-to-photon must stay under 20 ms for comfortable VR. Cloud adds 30–80 ms.

```
Comfortable: Motion-to-photon < 20 ms (local rendering only)
Tolerable:   < 50 ms (seated, slow movement, AR overlays)
Noticeable:  50–100 ms (AR annotations OK, VR uncomfortable)
Unusable:    > 100 ms (VR nausea guaranteed)
```

**Hybrid rendering** (the best pattern): render the environment and player interaction locally
on the headset. Stream in complex models (100M+ triangle CAD data, medical scans) as a composited
layer from the cloud. The user's head movement is always local-latency. Only the streamed model
has cloud latency, which is tolerable because it's not tied to vestibular feedback.

---

## Asset Delivery & CDN {#asset-delivery}

### Size Budgets

```
Quest standalone app:        < 2 GB total install
Individual scene download:   < 100 MB (reasonable load times on Wi-Fi)
Hero 3D model (standalone):  < 10 MB (LOD 0)
Texture atlas:               1024×1024 ASTC on Quest, 2048 on PC
Ambient audio loop:          < 2 MB (Ogg Vorbis 128 kbps)
Voice line:                  < 200 KB (Opus 64 kbps)
```

### Delivery Architecture

```
┌────────────┐     ┌──────────────┐     ┌─────────────┐
│  XR Client │────▶│  CDN Edge    │────▶│  Origin      │
│            │     │  (CloudFront │     │  (S3 / R2 /  │
│  Requests  │     │   / CF R2)   │     │   GCS)       │
│  by LOD    │     └──────────────┘     └─────────────┘
│  tier      │
└────────────┘

LOADING STRATEGY:
  1. Load LOD 0 (placeholder, < 100 KB) immediately
  2. Stream LOD 1 (visible quality) while user sees placeholder
  3. Stream LOD 2+ (full detail) as user approaches or has idle bandwidth
  4. Stream high-res texture mips on demand (virtual texturing)
```

### Unity Addressables for OTA Updates

```
- Host remote asset catalogs on your CDN
- Ship the app with baked content for offline fallback
- Check for catalog updates on app launch
- Download new/updated content bundles in background
- NO app store review required for content updates (only code changes need review)
- Version your catalogs. Support rollback. Tag builds by platform (Quest, PCVR, etc.)
```

---

## Analytics & Telemetry {#analytics}

### XR-Specific Signals

| Signal | What It Reveals | How to Collect | Privacy Level |
|---|---|---|---|
| **Gaze heatmap** | What users look at, for how long | Eye-tracking ray sampled at 10 Hz, projected onto scene geometry server-side | BIOMETRIC — opt-in |
| **Head trajectory** | How users physically navigate the space | Head position + rotation at 5 Hz, spaghetti plot | PII — consent needed |
| **Interaction funnel** | Where users fail or abandon tasks | Event log: `grabbed_tool → aimed → activated → success` | LOW — standard analytics |
| **Comfort metrics** | Whether the experience causes discomfort | Session duration, early quits, sudden head jerks | MEDIUM — aggregate OK |
| **Performance** | Frame drops, GPU time, thermal state | OVR Metrics Tool, Unity Profiler markers | LOW — device data |
| **Spatial dwell** | How long users spend in each area | Head position bucketed into spatial zones | PII if granular |

### Implementation Pattern

```
DO:
  ✓ Process biometric data (gaze, hand) on-device. Send only aggregated results.
  ✓ Get explicit opt-in before collecting any biometric signal.
  ✓ Batch telemetry and send in low-priority background requests (don't compete with frame budget).
  ✓ Use event-based logging (not continuous streams) for interaction funnels.

DON'T:
  ✗ Send raw gaze vectors to your server (biometric data + reveals what users read/look at).
  ✗ Store room meshes with user IDs (reveals home layout).
  ✗ Log during performance-sensitive moments (loading, physics-heavy scenes).
  ✗ Forget GDPR Article 9 / BIPA implications for biometric data.
```

---

## API Design for XR Clients {#api-design}

### Principles

1. **Minimize round-trips.** Every 100 ms of API latency is felt in XR. Bundle scene data,
   user state, and permissions into a single response. No waterfalls.

2. **Quality-tier-aware.** The client sends its device type; the server returns appropriately
   sized assets (Quest gets 512px textures, PCVR gets 2048px).

3. **Binary for real-time, JSON for REST.** Use Protobuf or FlatBuffers for state sync.
   JSON for infrequent API calls (login, scene list, settings).

4. **Idempotent mutations.** Clients retry due to tracking loss, network blips, or backgrounding.
   Anchor creation, content save — all must handle duplicate requests gracefully.

5. **Push, don't poll.** WebSockets or SSE for live session state. Polling wastes battery
   and competes with the frame budget.

### Example: Scene Load (Single-Request Pattern)

```
POST /api/v1/scene/load
{
  "scene_id": "warehouse-training",
  "anchor_ids": ["anc_abc123", "anc_def456"],
  "user_id": "usr_789",
  "device_type": "quest_3",
  "quality_tier": "medium",
  "locale": "en-US"
}

RESPONSE:
{
  "scene": {
    "id": "warehouse-training",
    "environment_url": "https://cdn.example.com/scenes/warehouse/medium.glb",
    "lightmap_url": "https://cdn.example.com/scenes/warehouse/lightmap-medium.ktx2"
  },
  "anchors": [
    { "id": "anc_abc123", "status": "active", "content": [ ... ] },
    { "id": "anc_def456", "status": "expired", "message": "Re-scan required" }
  ],
  "user": {
    "progress": { "completed_modules": [1, 2, 3], "current_module": 4 },
    "permissions": ["interact", "annotate"]
  },
  "session": {
    "websocket_url": "wss://rt.example.com/sessions/sess_xyz",
    "token": "eyJ..."
  }
}
```

One request. Everything the client needs to start the experience.

---

## Authentication in XR {#auth}

### The Problem

Typing on a virtual keyboard in a headset is painful. Password entry takes 3–5× longer than on
a phone. Users will abandon your app if login is friction-heavy.

### Solutions (Best → Worst)

```
1. QR CODE → PHONE AUTH → TOKEN TO HEADSET
   Show a QR code in the headset → user scans with phone → authenticates on phone →
   token syncs to headset via your backend. Best UX by far.
   Implementation: WebSocket connection from headset, phone POSTs auth token, headset receives.

2. DEVICE-BASED IDENTITY
   Use the headset's platform identity (Meta account, Apple ID, Microsoft AAD).
   No additional login required. Limited to platform ecosystem.

3. PIN CODE
   Short numeric PIN displayed on a companion web page.
   User enters PIN in headset (numeric keyboards are tolerable).
   Time-limited (5 min expiry). Like TV login flows.

4. SSO/SAML FOR ENTERPRISE
   HoloLens supports Azure AD natively (Iris recognition login).
   Quest for Business supports managed device enrollment.

5. VIRTUAL KEYBOARD (LAST RESORT)
   Full email + password entry in VR. Only if no alternative exists.
   Use large keys (≥ 5 cm), clear feedback, and show password option.
```

### Token Management

- Cache tokens aggressively. Re-authentication mid-session is deeply disruptive.
- Use long-lived refresh tokens (days/weeks for headset apps, not hours).
- Token refresh should happen silently in the background, never blocking the render thread.
- Store tokens in platform-secure storage (Android Keystore, iOS Keychain).
