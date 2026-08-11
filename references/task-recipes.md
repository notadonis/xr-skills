# Task Recipes

> Last verified: 2026-08. Versions and store policies here are defaults, not facts.
> Confirm against official docs before pinning (see Freshness Protocol in SKILL.md).

End-to-end procedures for the three most common XR tasks. When a recipe exists, follow it
instead of improvising. Each recipe ends with a verification step. A recipe is not done
until verification passes.

## Table of Contents
1. [Recipe 1: Scaffold a Quest Unity Project](#quest-scaffold)
2. [Recipe 2: Scaffold a WebXR (Three.js) Project](#webxr-scaffold)
3. [Recipe 3: Ship-Readiness Audit](#audit)

---

## Recipe 1: Scaffold a Quest Unity Project {#quest-scaffold}

**Produces:** a Unity project that builds to Quest 3/3S, hits framerate on an empty scene,
and has comfort-correct defaults baked in from commit one.

**Assumptions (declare, then proceed):** Unity 6 LTS, URP, OpenXR + XRI, controllers primary.

### Steps

1. **Create the project.** Unity 6 LTS, URP template (not HDRP, not Built-in for new work).

2. **Packages.** Add to `Packages/manifest.json`:
   - `com.unity.xr.openxr`
   - `com.unity.xr.interaction.toolkit`
   - `com.unity.xr.hands`
   - `com.unity.inputsystem`
   - `com.unity.render-pipelines.universal`
   - Meta XR SDK (via Meta developer hub / UPM) for passthrough, scene API, anchors
   Do NOT add `com.unity.postprocessing`. Verify current package versions against the
   Unity registry before pinning.

3. **Project Settings.**
   - Player: Android target, IL2CPP, ARM64 only, Linear color space
   - Graphics API: Vulkan
   - Texture compression: ASTC
   - XR Plug-in Management: OpenXR enabled for Android, Meta Quest feature group on
   - OpenXR interaction profiles: Oculus Touch Controller + Hand Interaction
   - Quality: shadows OFF for the Android tier, no HDR on standalone tier

4. **Rendering settings (URP asset, mobile tier).**
   - MSAA 4x (cheap on tiled mobile GPUs, big visual win)
   - Single-pass instanced stereo (Render Mode in XR settings)
   - Realtime shadows off, reflection probes baked

5. **Scene setup.**
   - XR Origin (XR Rig) from XRI samples: Camera Offset + Main Camera + controllers
   - Locomotion: Teleportation Provider + Snap Turn Provider (45°). No continuous
     turn in the default build.
   - One world-space Canvas at z = 1.5 m for any UI, inside the comfort cone
   - Directional light: baked mode. Lightmap the environment.

6. **Folder structure.** Use the layout in `references/frontend-engines.md`.

### Verification (all must pass)

```
[ ] python3 scripts/xr_lint.py <project> → 0 BLOCK
[ ] Build && Run to headset succeeds
[ ] OVR Metrics / Meta XR Simulator shows 72 Hz on the empty scene with headroom
[ ] Snap turn works, no smooth rotation reachable by default
[ ] Canvas is world-space at 1.2–2.0 m
```

---

## Recipe 2: Scaffold a WebXR (Three.js) Project {#webxr-scaffold}

**Produces:** a browser-based immersive scene that enters VR on Quest Browser and
falls back to inline 3D on desktop/mobile.

**Assumptions (declare, then proceed):** Three.js + Vite, no framework. Use React Three
Fiber only if the user already lives in React.

### Steps

1. **Scaffold.** `npm create vite@latest` (vanilla or TS), `npm i three`.

2. **Renderer, the three lines that matter:**
   ```js
   renderer.xr.enabled = true;
   document.body.appendChild(XRButton.createButton(renderer));  // or VRButton
   renderer.setAnimationLoop(render);   // NEVER window.requestAnimationFrame
   ```
   `window.requestAnimationFrame` does not fire inside an immersive session. Using it
   ships a scene that freezes the moment the user enters VR. The linter blocks this.

3. **Input, progressive:** touch/mouse orbit → `renderer.xr.getController(i)` for
   controllers → hand tracking via the WebXR Hand Input module where available. Feature-
   detect, never assume.

4. **Serve over HTTPS.** WebXR requires a secure context. For LAN headset testing use
   Vite's `--host` with a local TLS cert, or adb reverse port forwarding to the Quest.

5. **Performance floor:** target the same standalone budgets as Quest native, then
   subtract browser overhead. Draw calls under ~100, no per-frame allocations in the
   render loop, compressed textures (KTX2/Basis).

### Verification

```
[ ] python3 scripts/xr_lint.py <project> → 0 BLOCK (catches the rAF mistake)
[ ] Desktop browser: scene renders inline, orbit works
[ ] Quest Browser: XR button appears, session enters, controllers tracked
[ ] Scene keeps rendering after entering AND after exiting the session
```

---

## Recipe 3: Ship-Readiness Audit {#audit}

**Produces:** a written go/no-go with findings, for an existing project approaching
release. Run this when asked to "review", "audit", or "get X ready to ship".

### Steps

1. **Lint.** `python3 scripts/xr_lint.py <project>`. Every BLOCK is a no-go until fixed
   or explicitly waived by the user. WARNs go in the findings list.

2. **Manual pass against SKILL.md's Exit Gate**, then the full PR checklist in
   `references/quality-and-security.md`. Focus order: comfort → performance → input →
   privacy. Comfort violations outrank everything.

3. **Performance evidence, not vibes.** Ask for (or capture) a profile: OVR Metrics /
   Perfetto on Quest, RealityKit debugger on visionOS, Chrome tracing for WebXR.
   Sustained framerate over 15+ minutes matters more than peak. Thermal throttling is
   the silent killer.

4. **Privacy sweep.** Grep for gaze, room mesh, hand skeleton, and mic data leaving the
   device. Check the consent flow exists and is opt-in. See the biometric section of
   `references/quality-and-security.md`.

5. **Store gate.** Check against the store submission requirements in
   `references/quality-and-security.md` for the target store. Data disclosures and
   HMD-removal behavior are the most common first-submission rejections.

### Output format

```
GO / NO-GO: <verdict>
Blockers:   <numbered, each with file:line where applicable, and the fix>
Risks:      <warnings worth fixing before launch>
Evidence:   <what was actually verified vs. assumed — be honest about gaps>
```

Never issue a GO with unverified framerate. "It should be fine" ships nausea.
