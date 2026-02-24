# Platform Specifications & Hardware Reference

Read this file first when the target device is known. Every downstream decision — polygon budget,
shader complexity, interaction model, SDK choice — flows from the hardware constraints.

## Table of Contents
1. [Device Specifications](#device-specs)
2. [Performance Budgets by Platform](#budgets)
3. [OpenXR Architecture](#openxr)
4. [Cross-Platform Strategy](#cross-platform)

---

## Device Specifications {#device-specs}

### Standalone / Mobile XR (Battery-Powered, Mobile GPU)

**Meta Quest 3**
- SoC: Snapdragon XR2 Gen 2
- GPU: Adreno 740
- RAM: 8 GB (shared CPU/GPU)
- Display: 2064×2208 per eye, 72/80/90/120 Hz
- Tracking: Inside-out 6DoF (head), 6DoF controllers, hand tracking, eye tracking (limited API)
- Passthrough: Full-color stereo, ~18 ms latency
- Scene Understanding: Room mesh, plane detection, semantic labels (couch, table, wall, etc.)
- GPU API: Vulkan (preferred), OpenGL ES 3.2
- Primary SDK: Meta XR SDK (OpenXR-based), Unity or Unreal
- Storage: 128/512 GB. App install limit considerations: keep APK < 2 GB
- Thermal: Sustained workloads throttle after 10–20 min. Use `OVRManager.performanceMetrics`
- Key constraint: This is a MOBILE chip. Think phone-class GPU, not desktop.

**Meta Quest 3S**
- Same SoC as Quest 3 (XR2 Gen 2), 8 GB RAM
- Lower resolution displays than Quest 3
- Same SDK, same performance budget — code targeting Quest 3S runs on Quest 3

**Apple Vision Pro**
- SoC: M2 (compute) + R1 (sensor fusion, 12 ms photon-to-display pipeline)
- RAM: 16 GB
- Display: 23 million pixels total (micro-OLED), ~90 Hz (system-managed)
- Tracking: Inside-out 6DoF, hand tracking (primary input), eye tracking (primary input)
- Input: Eyes + hands. No controllers exist for this device.
- GPU API: Metal only
- Primary SDK: RealityKit + ARKit + SwiftUI
- Scene Understanding: Room mesh, plane detection, object classification
- Key constraint: No controller fallback. Every interaction must work with gaze + pinch.
  Shared Space apps compete for GPU with other apps. Full Space gets more budget.

**Android XR Devices (Samsung, etc.)**
- Snapdragon XR-series chips, Android-based
- OpenXR on Android
- Emerging ecosystem — SDK surfaces still stabilizing
- Target Quest 3-equivalent budgets as a safe baseline

### PC-Tethered VR (Desktop GPU, Wired or Wi-Fi Streaming)

| Device | Resolution/Eye | Refresh | Tracking | Key Notes |
|---|---|---|---|---|
| **Valve Index** | 1440×1600 | 80–144 Hz | Lighthouse 2.0 | Finger tracking on Knuckles controllers |
| **HTC Vive Pro 2** | 2448×2448 | 90–120 Hz | Lighthouse 2.0 | Very high res, demands RTX 3080+ |
| **Bigscreen Beyond** | 2560×2560 | 75–90 Hz | Lighthouse 2.0 | Ultra-compact, custom-fit headset |
| **Meta Quest 3 (via Link/Air Link)** | 2064×2208 | 72–120 Hz | Inside-out | Standalone headset acting as PC display |

PC VR can push 5–10× the geometry of standalone. Budget ~2–4M triangles/eye, ~500–1000 draw calls.
Real-time shadows and moderate post-processing acceptable with modern desktop GPUs.

### Enterprise AR (Optical See-Through)

**HoloLens 2** (End-of-life but widely deployed)
- Display: Optical waveguide, ~52° FOV (narrow — content disappears at edges)
- Tracking: Inside-out 6DoF, hand tracking, eye tracking
- Platform: UWP / Windows, MRTK 2/3, OpenXR
- Key constraint: FOV is tiny. Design UI for a small viewport. Users will "look around" to find content.

**Magic Leap 2**
- Display: ~70° FOV, dimming for outdoor use
- Platform: Android, Vulkan, OpenXR
- Enterprise-focused (healthcare, manufacturing)

### Mobile AR (Phone/Tablet)

| Platform | Key Capabilities |
|---|---|
| **iOS ARKit 6+** | LiDAR on Pro models, scene geometry, object capture, RoomPlan API, body tracking |
| **Android ARCore** | Depth API, Geospatial API (Google VPS for outdoor anchoring), Scene Semantics, Streetscape Geometry |

Phone AR is single-eye (not stereoscopic). Performance budgets are generous compared to headset XR,
but battery drain and thermal throttling are the primary constraints.

---

## Performance Budgets by Platform {#budgets}

These are ceilings. Build with headroom — thermal throttling will eat 10–30% of your peak budget
within 15 minutes of sustained load.

### Standalone XR (Quest 3 / 3S)

```
FRAME RATE
  Minimum:              72 Hz (13.88 ms total frame time)
  Recommended:          90 Hz (11.11 ms total frame time)
  Stretch:              120 Hz (8.33 ms — only for very simple scenes)

GEOMETRY
  Draw calls:           < 100–150 (after batching, instancing, SRP Batcher)
  Triangles:            < 750K per eye (1M absolute ceiling)
  Bones per skinned mesh: < 75 (combine where possible)

TEXTURES
  Total texture memory: < 1.5 GB (out of 8 GB shared)
  Format:               ASTC 4×4 for color, ASTC 6×6 for normals (Android/Quest)
  Max individual size:  1024×1024 preferred, 2048×2048 for hero assets only
  Use texture atlases aggressively

SHADERS
  Fragment operations:  Minimize per-pixel math. Avoid multi-light per-pixel.
  Dynamic lights:       ≤ 1 real-time directional light. Zero point/spot.
  Shadows:              BAKED ONLY. Blob shadows for characters.
  Transparency:         Minimize. Alpha-tested (cutout) preferred over alpha-blended.
  Post-processing:      NONE. No bloom, SSAO, DOF, motion blur, color grading.

RENDERING
  Stereo method:        Single-pass instanced (mandatory)
  Foveated rendering:   Enable FFR at Medium or High via OVRManager
  MSAA:                 4× (required for readable text)
  HDR:                  OFF (too expensive on mobile)
  Render scale:         1.0 (reduce to 0.8 if thermally constrained)

AUDIO
  Simultaneous sources: < 32 (pool and prioritize by distance)
  Spatialization:       Meta Spatializer or Resonance Audio
  Format:               Ogg Vorbis, 128 kbps for music, 96 kbps for SFX

MEMORY
  Total app memory:     < 3.5 GB (OS reserves ~4.5 GB of the 8 GB)
  GC allocations:       ZERO per frame during gameplay (pool everything)

PHYSICS
  Rigidbodies:          < 50 active simultaneously
  Colliders:            Prefer boxes/spheres over mesh colliders
  Fixed timestep:       Match display rate or use interpolation
```

### PC VR (Tethered)

```
FRAME RATE:     90 Hz minimum (11.1 ms). 120+ Hz for competitive.
DRAW CALLS:     < 500–1000
TRIANGLES:      < 2–4M per eye
TEXTURES:       BC7 (DX11/12), up to 4096×4096 for hero assets
SHADOWS:        Real-time OK (cascaded shadow maps, 2–3 cascades)
POST-PROCESSING: FXAA or TAA. Bloom acceptable. Avoid heavy motion blur.
STEREO:         Single-pass instanced or Multi-view
```

### WebXR (Browser)

```
FRAME RATE:     72 Hz target
TRIANGLES:      < 500K for mobile AR, < 1M for PC VR
DRAW CALLS:     < 200 (WebGL overhead higher than native)
TEXTURES:       Power-of-two, max 2048×2048
ASSET FORMAT:   glTF 2.0 / GLB with Draco or meshopt compression
SCENE SIZE:     < 25 MB for first meaningful paint
AUDIO:          Web Audio API + Resonance Audio for spatialization
```

### Apple Vision Pro

```
FRAME RATE:     90 Hz (system-managed, you don't control the render loop)
RENDERER:       RealityKit / Metal. You submit entities, Apple renders them.
TRIANGLES:      Target < 500K for responsive Shared Space volumes
                Full Space gets more budget — still target < 1.5M
TEXTURES:       Metal-optimized. System handles foveated rendering automatically.
KEY CONSTRAINT: Shared Space apps share GPU with Mail, Safari, other volumes.
                Design for your volume being one of many things on screen.
```

---

## OpenXR Architecture {#openxr}

OpenXR is the Khronos Group standard abstracting XR runtimes. **Always prefer OpenXR** over
vendor-specific legacy SDKs (OVRPlugin, SteamVR Plugin) unless you need a vendor-exclusive feature
with no OpenXR extension equivalent.

### Stack

```
┌──────────────────────┐
│   Your Application   │
├──────────────────────┤
│   OpenXR API Layer   │  ← Standardized C API (or engine wrapper)
├──────────────────────┤
│   Runtime            │  ← Meta OpenXR Runtime / SteamVR / Monado / WMR
├──────────────────────┤
│   Driver / HAL       │  ← Device-specific driver
├──────────────────────┤
│   Hardware           │  ← Quest / Index / Vive / HoloLens / etc.
└──────────────────────┘
```

### Key Extensions

**Multi-Vendor (KHR_ / EXT_) — Use for Portability:**
| Extension | Purpose |
|---|---|
| `XR_EXT_hand_tracking` | Hand skeleton (26 joints per hand) |
| `XR_EXT_eye_gaze_interaction` | Eye gaze as input source |
| `XR_KHR_composition_layer_equirect2` | 360° video playback layer |
| `XR_EXT_local_floor` | Floor-relative reference space |

**Meta (FB_) — Quest-Specific Features:**
| Extension | Purpose |
|---|---|
| `XR_FB_passthrough` | Passthrough camera for MR |
| `XR_FB_scene` | Room mesh, planes, semantic labels |
| `XR_FB_spatial_entity` | Spatial anchor CRUD |
| `XR_FB_hand_tracking_mesh` | Hand mesh (for occlusion, not just skeleton) |
| `XR_FB_eye_tracking_social` | Eye tracking (social-safe subset, not raw gaze) |
| `XR_FB_face_tracking2` | 63 face blend shapes for avatar expressions |
| `XR_FB_body_tracking` | Upper body tracking (torso + arms) |
| `XR_META_spatial_entity_sharing` | Shared anchors between Quest devices |

**Microsoft (MSFT_) — HoloLens / WMR:**
| Extension | Purpose |
|---|---|
| `XR_MSFT_spatial_anchor` | Spatial anchor management |
| `XR_MSFT_scene_understanding` | Room mesh and plane detection |
| `XR_MSFT_hand_interaction` | Hand interaction model |
| `XR_MSFT_secondary_view_configuration` | Spectator view |

### Extension Guard Pattern

Always check extension availability at runtime. Never assume:

```csharp
// Unity C# — guard vendor extensions
if (OpenXRRuntime.IsExtensionEnabled("XR_FB_passthrough"))
{
    EnablePassthrough();
}
else
{
    // Fallback: render a skybox or environment
    FallbackToSkybox();
}
```

```javascript
// WebXR — check feature support
if (xrSession.enabledFeatures.includes('hand-tracking')) {
    initHandTracking(xrSession);
} else {
    initControllerFallback(xrSession);
}
```

---

## Cross-Platform Strategy {#cross-platform}

### The Layered Abstraction Pattern

When shipping to multiple devices, structure your code in layers:

```
┌─────────────────────────────┐
│  Game / App Logic            │  ← Platform-agnostic. Pure C# / JS.
├─────────────────────────────┤
│  Interaction Abstraction     │  ← XRI / MRTK / custom input manager
│  (grab, teleport, UI press)  │
├─────────────────────────────┤
│  Platform Adapters           │  ← Quest adapter, PCVR adapter, Vision Pro adapter
│  (SDK calls, extensions)     │
├─────────────────────────────┤
│  OpenXR / Native Runtime     │  ← OS-level
└─────────────────────────────┘
```

Rules:
- Game logic never references `OVRInput`, `SteamVR_Action`, or `ARSession` directly
- Interaction logic goes through XRI Interactables/Interactors or equivalent abstraction
- Platform-specific code lives in isolated adapter classes with `#if UNITY_ANDROID` or assembly definitions
- Asset quality tiers: "Low" (Quest), "Medium" (Quest 3 at 90 Hz), "High" (PCVR)
- Test on the lowest-spec target first. If it works on Quest 3S, it works everywhere in that tier.

### Quality Tier Configuration

```csharp
// Example: runtime quality tier selection
public enum XRQualityTier { Low, Medium, High }

public static XRQualityTier DetectTier()
{
    #if UNITY_ANDROID && !UNITY_EDITOR
    string device = SystemInfo.deviceModel;
    if (device.Contains("Quest 3")) return XRQualityTier.Medium;
    if (device.Contains("Quest 2")) return XRQualityTier.Low;
    return XRQualityTier.Low; // Safe fallback
    #else
    // PC VR
    if (SystemInfo.graphicsMemorySize > 8000) return XRQualityTier.High;
    return XRQualityTier.Medium;
    #endif
}
```

Use this tier to control: texture resolution, LOD bias, shadow distance, audio source limits,
particle counts, and physics simulation detail.
