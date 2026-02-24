# Quality, Security & Code Review Reference

## Table of Contents
1. [Testing Strategies](#testing)
2. [Performance Profiling Workflow](#profiling)
3. [CI/CD for XR](#cicd)
4. [Biometric Privacy & Security](#security)
5. [XR Pull Request Review Checklist](#review)

---

## Testing Strategies {#testing}

XR testing is hard because input is physical. You can't easily script "user reaches forward,
grabs fire extinguisher, aims at fire, squeezes trigger." Compensate with layered strategies.

### Testing Pyramid for XR

```
                    ╱╲
                   ╱  ╲         On-Device QA (manual)
                  ╱    ╲        Accessibility audit, comfort, presence
                 ╱──────╲
                ╱        ╲      Simulated Integration Tests
               ╱          ╲     XR Device Simulator + PlayMode tests
              ╱────────────╲
             ╱              ╲   Performance Benchmarks
            ╱                ╲  Automated frame budget checks
           ╱──────────────────╲
          ╱                    ╲ Unit Tests
         ╱                      ╲ Pure logic (scoring, state machines, math)
        ╱────────────────────────╲
```

### Unit Tests (Automated, Fast)

Test all platform-agnostic logic without a headset:
- State machines (game flow, training step progression)
- Score/achievement calculations
- Network message serialization/deserialization
- Spatial math (distance checks, angle calculations, anchor transforms)
- Configuration loading and validation

```csharp
// Example: testing spatial distance check
[Test]
public void InteractionZone_WithinRange_ReturnsTrue()
{
    var userPos = new Vector3(0, 1.7f, 0);
    var objectPos = new Vector3(0, 1.5f, -1.5f);
    
    bool inRange = InteractionZone.IsWithinGrabRange(userPos, objectPos, maxDistance: 2f);
    
    Assert.IsTrue(inRange);
}
```

### Simulated Integration Tests (XR Device Simulator)

Use the XR Device Simulator (Unity) or Meta XR Simulator to drive input with mouse/keyboard:

```
WHAT TO TEST:
  - Grab → move → release interactions
  - Teleportation to valid/invalid surfaces
  - UI button presses (poke and ray)
  - Hand menu open → select → close flow
  - Scene loading and transitions
  - Tracking loss → recovery

SETUP:
  Unity: Install XR Device Simulator package, add simulator prefab to test scenes.
  Meta: Use Meta XR Simulator for Quest-specific features (passthrough, scene understanding).
  Both run in Editor Play Mode — no headset required.
```

### Input Replay System

Record real sessions, replay for regression testing:

```json
{
  "recording": {
    "device": "quest_3",
    "duration_ms": 45000,
    "framerate": 72
  },
  "frames": [
    {
      "timestamp_ms": 0,
      "head": {
        "position": [0.0, 1.72, 0.0],
        "rotation": [0.0, 0.0, 0.0, 1.0]
      },
      "left_hand": {
        "position": [-0.25, 1.2, -0.35],
        "rotation": [0.0, 0.1, 0.0, 0.995],
        "grip_strength": 0.0,
        "trigger_value": 0.0
      },
      "right_hand": {
        "position": [0.28, 1.15, -0.4],
        "rotation": [0.0, -0.05, 0.0, 0.999],
        "grip_strength": 0.85,
        "trigger_value": 0.0
      }
    }
  ]
}
```

Replay in headless mode to verify: interactions trigger correctly, physics behave consistently,
no exceptions thrown. Useful for catching regressions in interaction tuning.

### On-Device QA Matrix

Always test on the **lowest-spec target device**. If it works on Quest 3S, it works on Quest 3.

```
PER BUILD, VERIFY:
  [ ] Launches without crash
  [ ] Frame rate holds target for 10+ minutes (check thermal throttling)
  [ ] All interactions work (grab, teleport, UI, hand tracking)
  [ ] Passthrough / scene understanding functions (if MR)
  [ ] Audio spatialization correct (sounds from correct directions)
  [ ] Text readable at intended distances
  [ ] Comfort: no nausea after 15 min session
  [ ] Controller AND hand tracking both work
  [ ] Seated mode works
  [ ] Guardian/boundary integration (no clipping through walls)
```

---

## Performance Profiling Workflow {#profiling}

### Quest (Meta)

```
TOOLS:
  OVR Metrics Tool       — overlay showing FPS, GPU/CPU time, thermal, memory
  Meta Quest Developer Hub — frame capture, GPU profiling, trace recording
  Unity Profiler           — CPU timeline, memory, GC allocations
  RenderDoc               — GPU frame analysis (draw calls, shader cost)

WORKFLOW:
  1. Enable OVR Metrics Tool overlay in Developer Settings
  2. Play your app for 10–15 minutes (thermal throttling is TIME-dependent)
  3. Identify: Is the bottleneck CPU or GPU?
     - CPU bound:  Frame time > 11ms on CPU, GPU has idle time
     - GPU bound:  GPU frame time > 11ms, CPU completes faster
  4. CPU bound: Profile with Unity Profiler → find hot functions → optimize
  5. GPU bound: RenderDoc frame capture → find expensive draw calls / shaders

KEY METRICS TO WATCH:
  GPU frame time:    < 11 ms (90 Hz) or < 13.8 ms (72 Hz)
  CPU frame time:    < 11 ms (90 Hz) or < 13.8 ms (72 Hz)
  Draw calls:        < 150
  Triangles:         < 1M per eye
  Texture memory:    < 1.5 GB
  Thermal headroom:  > 0.3 (below this, thermal throttling imminent)
  GC alloc/frame:    0 bytes (any allocation risks a GC spike)
```

### PC VR

```
TOOLS:
  fpsVR (SteamVR overlay)  — FPS, frame timing, reprojection ratio
  Unity Profiler            — same as above
  NVIDIA Nsight / AMD RGP   — GPU profiling
  SteamVR Frame Timing      — system-level frame timing graph

TARGET: GPU frame time < 11 ms at 90 Hz. < 5% reprojected frames.
```

### Common Performance Killers (Quick Reference)

```
SYMPTOM                     LIKELY CAUSE                    FIX
FPS drops when looking       Too many draw calls in view     Occlusion culling, LODs, batching
  in one direction
Periodic frame spikes        GC collection                   Object pooling, no per-frame allocs
Slow loading                 Synchronous I/O                 Addressables, async loading
Thermal throttling           Sustained high GPU load         Reduce render scale, increase FFR
  after 10 min
Jittery grabbed objects      Physics at wrong timestep       Match FixedUpdate to display rate
Blurry text                  Render scale < 1.0 or MSAA off  Render scale = 1.0, MSAA 4×
Flickering shadows           Shadow cascades fighting        Bake shadows (Quest) or adjust
                                                             cascade distances (PC)
```

---

## CI/CD for XR {#cicd}

### Unity XR CI Pipeline

```yaml
# .github/workflows/xr-build.yml
name: XR Build & Validate
on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]

jobs:
  # ─── LINT & UNIT TESTS ───
  unit-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: game-ci/unity-test-runner@v4
        with:
          testMode: EditMode
          unityVersion: 2022.3.20f1

  # ─── QUEST BUILD ───
  build-quest:
    needs: unit-tests
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with:
          lfs: true  # 3D assets are often in LFS

      - uses: game-ci/unity-builder@v4
        with:
          targetPlatform: Android
          buildMethod: BuildPipeline.BuildQuest
          androidAppBundle: false  # APK for Quest
          androidKeystoreName: ${{ secrets.ANDROID_KEYSTORE_NAME }}
          androidKeystoreBase64: ${{ secrets.ANDROID_KEYSTORE_BASE64 }}
          androidKeystorePass: ${{ secrets.ANDROID_KEYSTORE_PASS }}

      - name: PlayMode tests with XR Simulator
        uses: game-ci/unity-test-runner@v4
        with:
          testMode: PlayMode
          customParameters: -enableXRSimulator

      - name: Upload APK
        uses: actions/upload-artifact@v4
        with:
          name: quest-apk-${{ github.sha }}
          path: build/Android/*.apk

  # ─── PC VR BUILD ───
  build-pcvr:
    needs: unit-tests
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with:
          lfs: true
      - uses: game-ci/unity-builder@v4
        with:
          targetPlatform: StandaloneWindows64
      - uses: actions/upload-artifact@v4
        with:
          name: pcvr-build-${{ github.sha }}
          path: build/StandaloneWindows64/

  # ─── ASSET VALIDATION ───
  validate-assets:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with:
          lfs: true
      - name: Check asset sizes
        run: |
          # Fail if any texture exceeds 2048×2048
          python scripts/validate_textures.py --max-size 2048
          # Fail if any mesh exceeds 100K triangles without LODs
          python scripts/validate_meshes.py --max-tris 100000 --require-lods
```

### Deployment Flow

```
develop branch → automatic Quest + PC build → artifacts stored
    ↓ (PR review + on-device QA)
main branch → build + tag → upload to:
    Quest: Meta Quest Developer Hub (via CLI: ovr-platform-util)
    PC:    Steam (via steamcmd) or internal distribution
    Web:   CDN deploy (Vercel, Cloudflare, S3+CloudFront)
```

---

## Biometric Privacy & Security {#security}

### Data Classification

| Data | Classification | Key Regulations | Handling |
|---|---|---|---|
| **Eye tracking / gaze** | Biometric | GDPR Art. 9, BIPA, CCPA | Explicit opt-in. Process on-device. Anonymize before storage. |
| **Room mesh** | PII | GDPR, local privacy | Reveals home layout. Use plane abstractions. Never upload raw mesh without consent. |
| **Hand skeleton** | Biometric | BIPA, GDPR | Geometry fingerprints individuals. Aggregate only. |
| **Voice** | PII | GDPR, wiretap laws | Encrypt in transit (DTLS-SRTP). Clear mic-active indicator. |
| **Body pose** | Behavioral biometric | GDPR | Movement patterns identify users. Same rules as gaze. |
| **IPD** | Biometric | BIPA | Unique per person. Never log or transmit. |
| **Passthrough frames** | PII | GDPR, local laws | May contain faces, screens, documents. Never record without explicit consent. |

### Implementation Checklist

- [ ] Explicit opt-in consent UI (world-locked panel, not buried in settings) before any biometric collection
- [ ] On-device processing for biometric data. Send only aggregated/derived results.
- [ ] Encryption: TLS 1.3 for REST, DTLS 1.2+ for real-time UDP
- [ ] Biometric data encrypted at rest with per-user keys
- [ ] Retention policy: auto-delete gaze/hand data after 30 days max
- [ ] Audit third-party SDKs for hidden data collection
- [ ] Data minimization: if you only need "user looked left or right," don't store gaze vectors
- [ ] Clear visual indicator when mic/camera is actively recording
- [ ] Consent revocable. Provide "delete my data" functionality.
- [ ] For enterprise: confirm SOC 2, HIPAA (healthcare), FedRAMP (government) as applicable

---

## XR Pull Request Review Checklist {#review}

Copy this into your PR template. Every item matters.

### Performance
- [ ] Frame budget: Does this add draw calls, triangles, or per-frame allocations that could exceed budget?
- [ ] Main thread: Any synchronous I/O, heavy compute, or GC-triggering allocations on the render thread?
- [ ] Shader complexity: New shaders appropriate for target platform? No screen-space effects on standalone?
- [ ] Memory: Large assets loaded synchronously? References properly released?
- [ ] Thermal: Does this add sustained GPU load? Tested for 10+ minutes on device?

### Interaction & Input
- [ ] Input abstraction: Goes through XRI/MRTK, not direct controller/button reads?
- [ ] Hand tracking: Degrades gracefully without controllers?
- [ ] Hit targets: New UI elements ≥ 6 cm (poke) or ≥ 4 cm (pinch)?
- [ ] Multi-modal: Supports controller + hand + gaze (where applicable)?

### Spatial Correctness
- [ ] Tracking loss: Handles `TrackingState.None` gracefully?
- [ ] World scale: Objects scaled correctly in meters?
- [ ] Coordinate system: Correct up-vector and handedness for target platform?
- [ ] Anchor lifecycle: Handles expired, unavailable, or drifted anchors?

### Comfort & UX
- [ ] UI distance: ≥ 0.5 m minimum, 1.2–2.0 m preferred?
- [ ] Viewing angle: Within ±30° horizontal, +20°/−12° vertical?
- [ ] Text size: ≥ 1.0° visual arc at intended distance?
- [ ] Camera: Does this PR EVER move, rotate, or shake the camera? (Reject if yes, with rare exceptions.)
- [ ] Time.timeScale: If used for pausing, does tracking/rendering continue?

### Cross-Platform
- [ ] Multi-platform: Works on all target devices (or degrades gracefully)?
- [ ] Extension guards: Vendor-specific OpenXR extensions behind runtime checks?
- [ ] Quality tiers: Respects device-appropriate asset quality?

### Privacy & Security
- [ ] New sensor data: Introduces gaze, hand, room mesh, or voice collection?
- [ ] Consent: User consent obtained before biometric collection?
- [ ] Transmission: Any biometric data sent off-device is anonymized + encrypted?

### Accessibility
- [ ] Seated mode: Feature works while seated?
- [ ] One-handed: Works with a single controller or hand?
- [ ] Non-visual feedback: Audio/haptic alternatives to visual-only cues?
- [ ] Color: Not relying on color alone to convey meaning?
- [ ] Text: Respects user's text scale preference?
