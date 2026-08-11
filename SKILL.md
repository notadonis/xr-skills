---
name: xr-development
description: >
  Full-stack AR/VR/MR/XR spatial computing expertise: frontend engines (Unity, Unreal, WebXR,
  visionOS/RealityKit, Android XR), backend (multiplayer networking, spatial anchors, cloud
  rendering, asset delivery), and spatial UX/UI design (comfort science, locomotion, hand/eye
  tracking, accessibility). Use whenever building for Meta Quest 2/3/3S, Apple Vision Pro,
  Samsung Galaxy XR / Android XR, HoloLens 2, PCVR (Valve Index, Vive), phone AR (ARKit/ARCore),
  or WebXR. Also trigger on mentions of: OpenXR, XRI, MRTK, passthrough, room-scale, 6DoF,
  spatial anchors, hand tracking, eye tracking, foveated rendering, spatial audio, stereoscopic
  rendering, guardian/boundary, VR locomotion, or comfort guidelines, even without the explicit
  word "XR". If a Unity or Unreal project targets headsets, use this skill. Do NOT use for:
  flat-screen games with no headset target, social-video "AR filters" (Lens Studio, Effect
  House), 3D web scenes that never request an XR session, or general game-dev questions with
  no spatial computing component.
---

# XR Development Skill

Production-tested spatial computing knowledge for the full stack: rendering budgets, comfort
physiology, interaction design, multiplayer architecture. XR is the one software domain where
bad code physically sickens users. Treat comfort rules as medical constraints, not style advice.

## Operating Mode: Default and Declare

This skill is built for low-oversight execution. Do not stall on missing context.

1. **Resolve the target.** Device, engine, interaction model, performance tier.
2. **If unspecified and the decision is cheap to reverse** (prototypes, code review, isolated
   features, learning tasks): assume the default stack below, declare the assumption in one
   line, and proceed.
3. **Ask only when the decision is expensive to reverse**: engine selection for a funded
   project, store submission, backend architecture for a shipping product, anything touching
   biometric data.

**Default stack when unspecified:**

```
Device:        Meta Quest 3 (standalone). Largest installed base, strictest budget.
Engine:        Unity 6 LTS + OpenXR + XR Interaction Toolkit (XRI)
Rendering:     URP, single-pass instanced stereo
Interaction:   Controllers primary, hand tracking secondary
Locomotion:    Teleport + snap turn (45 degree increments)
Framerate:     72 Hz floor, 90 Hz target
```

Declare it like this: "Assuming Quest 3 standalone with Unity 6 + XRI. Flag me if the target
differs." Then do the work. Code that hits the Quest 3 budget runs everywhere.

## Routing

This file holds decision frameworks, hard rules, and the exit gate. Depth lives in the
references. Read the relevant file before writing code. Do not answer from generic priors
when a reference exists.

| Resource | When to use |
|---|---|
| `references/platform-specs.md` | Target device is known. **Read first.** Canonical source for every performance budget and hardware spec in this skill. |
| `references/frontend-engines.md` | Writing Unity, Unreal, WebXR, or visionOS code. Packages, project structure, starter code, shader rules, physics. |
| `references/backend-infrastructure.md` | Multiplayer, spatial persistence, cloud rendering, asset delivery, analytics, XR auth. |
| `references/spatial-ux-design.md` | Designing anything user-facing. Comfort science, the 12-pattern spatial UI library, locomotion, onboarding, accessibility. |
| `references/quality-and-security.md` | Testing, profiling, CI/CD, biometric privacy law, store submission requirements, the full PR review checklist. |
| `references/task-recipes.md` | End-to-end procedures: scaffold a Quest project, scaffold WebXR, run a ship-readiness audit. Prefer a recipe over improvising when one exists. |
| `scripts/xr_lint.py` | Executable check for known XR anti-patterns in Unity C#, Unity scenes/prefabs, manifests, and WebXR JS/TS. Zero dependencies. Run it whenever a project directory exists: `python3 scripts/xr_lint.py <project-path>`. |

## Terminology

Use these terms precisely. Misusing them signals to XR-literate users that you don't know
the domain.

| Term | Meaning | NOT This |
|---|---|---|
| **VR** | Fully immersive, replaces the physical world | Don't say VR when you mean AR |
| **AR** | Digital overlaid on the real world via camera or transparent optics | Don't say AR when the user is fully immersed |
| **MR** | Digital objects spatially aware of, and interacting with, physical surfaces | Not just "AR but fancier". MR implies scene understanding. |
| **XR** | Umbrella for VR + AR + MR | Use when guidance applies regardless of immersion level |
| **Passthrough** | Camera feed inside a VR headset enabling AR/MR modes | Not the same as optical see-through (HoloLens) |
| **6DoF** | Six degrees of freedom: rotation AND translation tracking | 3DoF is rotation only (Cardboard, old GearVR) |
| **Spatial Anchor** | Persistent, world-locked coordinate surviving app restarts | Not a Unity Transform. Anchors are OS/cloud managed. |
| **Reprojection / ASW / SpaceWarp** | Runtime-synthesized frames when the app misses framerate | A safety net, never a target. Relying on it means you've failed. |
| **IPD** | Interpupillary distance, the spacing between the user's eyes | Always use the OS-reported value. Never hardcode. |
| **Guardian / Boundary** | Physical play-area boundary set during headset setup | Respect it. Never encourage users to leave it. |
| **Foveated Rendering** | Reduced resolution in peripheral vision to save GPU | Fixed (GPU-driven) vs. Dynamic (eye-tracking-driven) |

## Decision Frameworks

### Engine Selection

```
Cross-platform (Quest + PC + mobile)?           → Unity
Photorealistic PC VR / arch-viz / automotive?   → Unreal Engine
Browser-based, zero install?                    → WebXR (Three.js / React Three Fiber / Babylon.js)
Deep visionOS / Apple ecosystem?                → Native SwiftUI + RealityKit
Android XR native (Galaxy XR)?                  → Jetpack XR (Compose) or Unity OpenXR
Ship fast, minimal XR experience?               → Unity + XRI (largest community, most tutorials)
Enterprise with existing Unreal pipeline?       → Unreal + OpenXR
Open-source stack, full code ownership?         → Godot 4 + OpenXR (smaller ecosystem, more DIY)
Lightweight AR on phones only?                  → Native ARKit (iOS) or ARCore (Android)
```

### Multiplayer / Networking

```
Prototype or small team (≤ 8 users)?            → Normcore (fastest to production)
Competitive game needing precise physics?       → Photon Fusion (tick-based determinism)
Self-hosted enterprise (data sovereignty)?      → Mirror + dedicated servers
WebXR multi-user?                               → LiveKit or Multisynq (formerly Croquet)
Large social space (50+ concurrent)?            → Custom server + spatial partitioning
Apple SharePlay integration?                    → GroupActivities framework + custom sync
```

### Interaction Model

```
Quest 3 game?                   → Controllers primary, hand tracking secondary
Quest 3 productivity / MR?      → Hand tracking primary, controllers optional
Apple Vision Pro?               → Eyes + hands only (no controllers exist)
Samsung Galaxy XR?              → Gaze + pinch primary (Vision Pro model), controllers optional
HoloLens 2 enterprise?          → Hands + voice commands (MRTK 3)
Phone AR?                       → Touch screen + device pose (ARKit/ARCore)
WebXR (device unknown)?         → Progressive: touch → controller → hand tracking
Accessibility-first?            → Support ALL inputs. Test each in isolation.
```

## Non-Negotiable Rules

Violating these causes nausea, eye strain, or broken experiences. No exceptions. The numbers
below are the Quest-class standalone baseline. `references/platform-specs.md` is canonical
per device. If the two ever disagree, platform-specs wins.

### Comfort (the physics of not making people sick)

1. **Never move the camera.** The user's head IS the camera. Programmatic camera movement in
   VR causes instant vestibular mismatch, then nausea. The only acceptable camera manipulation
   is a fade-to-black during teleportation (0.1–0.3 s). Locomotion moves the XR Origin/rig,
   never the camera itself.

2. **UI distance: 1.2–2.0 m preferred. 0.5 m absolute minimum.** Below 0.5 m the eyes can't
   converge comfortably on stereoscopic content. Eye strain, blurry text.

3. **Content angle: ±30° horizontal, +20°/−12° vertical from resting gaze.** Content outside
   this cone requires uncomfortable neck rotation. Persistent UI lives in this zone.

4. **Minimum text size: 1.0° of visual arc.** At 2 m that's 3.5 cm tall. At 1 m, 1.75 cm.
   Smaller is unreadable on current headset optics. Vision Pro recommends 35 pt minimum.

5. **Hit framerate. Every frame.** 72 Hz minimum on Quest (13.8 ms budget). 90 Hz preferred
   (11.1 ms). A single dropped frame is felt. Sustained drops cause nausea. This is a medical
   safety requirement, not a quality bar.

### Performance (standalone / mobile XR)

6. **Single-pass instanced stereo rendering.** Always on.
7. **Draw calls < 100–150.** GPU instancing, texture atlases, SRP Batcher.
8. **Triangles < 750K–1M per eye.** Aggressive LODs. Imposters for distant objects.
9. **No real-time shadows.** Bake lightmaps. Blob shadows for characters.
10. **No real-time post-processing.** No bloom, SSAO, motion blur, or DOF on standalone.
11. **Texture compression: ASTC 4×4** on Quest/Android. BC7 on PC.
12. **Never block the main/render thread.** All I/O async. Object pool everything. GC spikes
    = frame drops = nausea.

### Input

13. **Never assume controllers exist.** Vision Pro ships without them. Hand tracking is
    increasingly the default. Abstract through an interaction system (XRI, MRTK, WebXR input
    sources).
14. **Generous hit targets.** 6 cm × 6 cm minimum for poke/touch. 4 cm for pinch/gaze.
15. **Always support seated mode.** Never hardcode player height. Calibrate from the
    OS-reported floor level.

### Privacy

16. **Eye tracking = biometric data** under GDPR (Article 9), BIPA, CCPA. Explicit opt-in
    consent. Process on-device. Never store raw gaze vectors without anonymization.
17. **Room mesh = PII.** It reveals home layout, furniture, valuables. Never upload full
    meshes without consent. Prefer semantic plane abstractions.
18. **Hand skeleton geometry can fingerprint individuals.** Aggregate, don't store per-user.

## Common Mistakes That Ship Broken Products

`scripts/xr_lint.py` detects most of these automatically. Run it before reviewing by hand.

| Mistake | Why It's Bad | Fix |
|---|---|---|
| UI canvas in screen space | Follows head rigidly: nausea, breaks presence | World-space canvas. Lazy follow with heavy damping at most. |
| `Time.timeScale = 0` for pause menus | Freezes animation/physics context, head feels "stuck" | Pause game logic only, never tracking/rendering |
| Synchronous `WWW`/`UnityWebRequest` on main thread | Frame hitch → ASW artifact → nausea chain | `async/await` with `SendWebRequest()` |
| Importing 3D models without checking scale | Objects at 100× or 0.01×, invisible or world-filling | Verify units (meters). FBX scale factor = 1.0. |
| Continuous smooth rotation | Strongest nausea trigger after camera movement | Snap turn (30–45° increments) as default |
| Placing UI at z = 0.3 m | Eyes can't converge, text blurs, headache in minutes | Enforce z ≥ 0.5 m, prefer 1.2–2.0 m |
| No tracking-loss handling | Objects teleport or vanish when a user walks through a wall | "Tracking lost" overlay, graceful re-anchor on recovery |
| Hardcoded IPD (e.g., 63 mm) | Stereo mismatch, headache for anyone else | Use the OS-reported IPD |
| Physics at variable rate | Jitter on grabbed objects, non-deterministic netcode | `FixedUpdate` at matched rate (72/90 Hz) or interpolation |
| Ignoring thermal throttling | Quest throttles after ~15 min sustained load | Thermal headroom API. Budget for sustained, not peak. |

## Exit Gate: Definition of Done

Before declaring any code or design task complete, verify every line below. State exceptions
explicitly in your summary. "Done" with silent violations is a failed task.

```
[ ] 1.  Nothing added blocks the render thread: no per-frame allocations, no sync I/O
[ ] 2.  No code writes the camera transform. Locomotion moves the XR Origin.
[ ] 3.  UI is world-space, 1.2–2.0 m (never < 0.5 m), inside the comfort cone
[ ] 4.  Text ≥ 1.0° visual arc at its placed distance
[ ] 5.  Input works with controllers AND hands (or the platform's native model)
[ ] 6.  Seated mode works. No hardcoded height or IPD.
[ ] 7.  Tracking loss is handled gracefully
[ ] 8.  Comfort defaults: snap turn / teleport. Smooth motion is opt-in, with vignette.
[ ] 9.  No raw gaze, room mesh, or hand skeleton data leaves the device without consent
[ ] 10. `python3 scripts/xr_lint.py <project>` reports zero BLOCK findings,
        or each finding is explained in the summary
```

For full PR reviews, use the extended checklist in `references/quality-and-security.md`.

## Freshness Protocol

Every reference file carries a `Last verified` date. Two rates of decay:

- **Physiology doesn't rot.** Comfort thresholds, visual-arc math, vestibular constraints are
  stable science. Trust them as written.
- **Hardware and SDKs rot fast.** Package versions, device specs, framework picks, and store
  policies in the references are *defaults*, not facts. Before writing a manifest, pinning a
  version, or citing a spec in user-facing output: confirm against official docs if the file's
  `Last verified` date is more than 6 months old or you have web access.

Never invent SDK methods or device capabilities. If unsure whether an API exists or a feature
shipped: say so, recommend the official docs, and suggest on-device verification. Wrong XR
advice ships products that make people physically ill.
