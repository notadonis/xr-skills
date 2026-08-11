# Frontend Engines Reference

> Last verified: 2026-08. Hardware specs, SDK versions, and framework picks are defaults,
> not facts. Confirm against official docs before pinning (Freshness Protocol, SKILL.md).
> Physiology-based numbers (comfort, visual arc) are stable science.

## Table of Contents
1. [Unity](#unity)
2. [Unreal Engine](#unreal)
3. [WebXR](#webxr)
4. [Native visionOS](#visionos)
5. [Glossary](#glossary)

---

## Unity (Most Common XR Engine) {#unity}

### Essential Packages (Unity 6 LTS, 6000.x)

Unity 6 is the current LTS. Unity 2022.3 LTS is past end of support: use it only for
maintaining legacy projects, never for new ones.

```
REQUIRED:
  com.unity.xr.openxr                    OpenXR backend
  com.unity.xr.interaction.toolkit       XRI — cross-platform interaction layer
  com.unity.xr.hands                     OpenXR hand tracking subsystem
  com.unity.inputsystem                  New Input System (XRI depends on it)

PLATFORM-SPECIFIC:
  Meta XR SDK (via Meta dev hub)         Quest passthrough, scene, shared anchors, body tracking
  com.unity.polyspatial                  Unity → visionOS bridge (renders via RealityKit)
  MRTK 3 (via Mixed Reality Feature Tool) HoloLens and OpenXR interaction components

RENDERING:
  com.unity.render-pipelines.universal   URP (recommended for XR)
  Built-in RP                            Still works but URP is the modern path

ASSET MANAGEMENT:
  com.unity.addressables                 Remote asset loading, OTA updates without app store review

NEVER use the Built-in XR packages (legacy OVR, SteamVR plugin) for new projects.
```

### Project Structure

```
Assets/
├── _Project/
│   ├── Scripts/
│   │   ├── Core/                # App state, service locator, event bus (ScriptableObject-based)
│   │   ├── Interaction/         # Custom XRI Interactables & Interactors
│   │   ├── Networking/          # Photon/Mirror/Normcore wrappers
│   │   ├── Spatial/             # Anchor manager, scene understanding, room scanning
│   │   ├── Platform/            # Platform adapters (#if UNITY_ANDROID etc.)
│   │   ├── UI/                  # World-space canvas controllers, hand menus
│   │   └── Audio/               # Spatial audio manager, occlusion, reverb zones
│   ├── Prefabs/
│   │   ├── XRRig/               # XR Origin + controllers + hand models + teleport
│   │   ├── Interactables/       # Grab objects, buttons, sliders, dials
│   │   ├── Environment/         # Scene chunks with LOD groups
│   │   └── UI/                  # Curved canvas, hand menu, wrist UI, radial menu
│   ├── Scenes/
│   │   ├── Bootstrap.unity      # Lightweight scene for initialization
│   │   ├── MainMenu.unity       # Comfort settings, onboarding
│   │   └── Experience.unity     # Primary experience scene(s)
│   ├── Shaders/                 # URP-compatible, optimized for mobile XR
│   ├── Materials/               # Material instances (minimize unique materials)
│   └── ScriptableObjects/       # Config data, event channels, quality presets
├── Packages/
└── ProjectSettings/
    └── XRPluginManagement/      # Per-platform OpenXR settings
```

### XR Origin Setup (The Player Rig)

```
XR Origin (XR Origin component)
├── Camera Offset
│   ├── Main Camera (Tracked Pose Driver: Center Eye)
│   │   └── [XR Gaze Interactor — for eye tracking input]
│   ├── Left Controller (Tracked Pose Driver: Left Controller)
│   │   ├── XR Direct Interactor (grab at close range)
│   │   ├── XR Ray Interactor (point at distance, teleport)
│   │   └── Controller Model
│   ├── Right Controller (same structure)
│   ├── Left Hand (XR Hand Tracking, OpenXR Hand)
│   │   ├── XR Poke Interactor (index finger poke for UI)
│   │   └── XR Direct Interactor (hand grab)
│   └── Right Hand (same structure)
└── Locomotion System
    ├── Teleportation Provider
    ├── Snap Turn Provider (default: 45°, configurable)
    └── [Optional] Continuous Move Provider (behind comfort toggle)
```

### XRI Interaction Architecture

```
INTERACTORS (on controllers/hands — the "tools"):
  XRDirectInteractor       — close-range grab (hand reaches the object)
  XRRayInteractor          — distance pointing (laser beam)
  XRPokeInteractor         — finger poke for buttons/UI
  XRGazeInteractor         — eye-tracking gaze direction
  XRSocketInteractor       — snap-to zones (holster, slot, dock)

INTERACTABLES (on scene objects — the "targets"):
  XRGrabInteractable       — pick up and move objects
  XRSimpleInteractable     — hover/select events without movement
  XRBaseInteractable       — subclass for custom behavior

INTERACTION EVENTS (the connective tissue):
  Hover Enter / Exit       — interactor is near the interactable
  Select Enter / Exit      — user is actively grabbing/clicking
  Activate                 — trigger button while selected (e.g., spray a fire extinguisher)
  First/Last hover/select  — when the first or last interactor engages

INTERACTION GROUPS:
  Use Interaction Groups to prevent both a Ray and Direct interactor
  on the same hand from simultaneously interacting. Only one "wins."
```

### Shader Rules for Standalone XR

```
DO:
  ✓ Use URP/Lit or URP/Simple Lit for most surfaces
  ✓ Use Unlit shaders for UI panels (self-illuminated, no scene lighting dependency)
  ✓ Use alpha-cutout (clip) instead of alpha-blend where possible
  ✓ Bake ambient occlusion into vertex colors or lightmaps
  ✓ Use Shader Graph with Mobile target for custom shaders
  ✓ Sample textures at half-resolution in fragment shader where quality allows

DON'T:
  ✗ Use Standard/Built-in shaders (not SRP Batcher compatible)
  ✗ Use per-pixel multi-light evaluation on mobile
  ✗ Use screen-space effects (SSAO, SSR, screen-space shadows)
  ✗ Use tessellation or geometry shaders
  ✗ Use grab passes or refraction (requires rendering the scene twice)
  ✗ Use real-time reflection probes (bake them instead)
```

### Physics in XR

```
CRITICAL SETTINGS:
  Fixed Timestep:     0.01389 (72 Hz) or 0.01111 (90 Hz) — match your target framerate
  Gravity:            -9.81 (real-world gravity feels right in XR; cartoon gravity feels wrong)
  Max Depenetration:  Default is fine, but increase for fast-moving grabbed objects
  Solver iterations:  6 minimum for stable grabs

GRABBED OBJECTS:
  When the user grabs a physics object, you have two choices:
  1. Kinematic tracking: Set isKinematic = true, move via transform.
     Pro: Perfectly follows hand. Con: Can clip through walls.
  2. Velocity tracking: Keep non-kinematic, set velocity each frame to move toward hand.
     Pro: Respects physics. Con: Slight lag, can feel "spongy."
  
  XRI's XRGrabInteractable supports both via Movement Type:
  - Instantaneous (kinematic) — best for tools, UI props
  - Velocity Tracking — best for objects that should collide with the world
  - Kinematic — middle ground

CONTINUOUS COLLISION DETECTION (CCD):
  Enable CCD on any physics object the user can throw. Without it,
  fast-moving objects tunnel through walls. Set to Continuous Dynamic.

AVOID:
  ✗ Mesh colliders on grabbed objects (use simplified convex)
  ✗ > 50 active rigidbodies on standalone (budget carefully)
  ✗ Joint-heavy chains on mobile (ragdolls are expensive)
```

### Audio Spatialization

```
SETUP:
  Project Settings → Audio → Spatializer Plugin: Meta XR Audio (Quest) or Resonance Audio
  Every AudioSource on a 3D object: Spatial Blend = 1.0, enable spatialization

KEY PATTERNS:
  - Spatial audio is a UI tool, not just atmosphere. Use directional sounds
    to guide user attention (e.g., a chime from the direction of a notification).
  - Occlusion: Use Resonance Audio's room model or Meta's acoustic geometry
    to muffle sounds behind walls. This massively increases presence.
  - Voice chat: ALWAYS spatialize. Non-spatialized voice breaks co-presence.
  - Reverb: Match the virtual room's size. Small rooms = short reverb. Open spaces = long.
  - Falloff: Use logarithmic rolloff. Linear sounds unnatural. 
  - Budget: < 32 simultaneous AudioSources on Quest. Pool aggressively.
```

### Unity Quick Start (Quest 3 + PCVR)

```
1. Create Unity 6 LTS project with URP template
2. Package Manager → install: OpenXR Plugin, XR Interaction Toolkit (+ Starter Assets sample),
   XR Hands, Meta XR SDK
3. Project Settings → XR Plug-in Management:
     Android tab: ✅ OpenXR. Add Meta Quest feature group.
     Standalone tab: ✅ OpenXR. Add Interaction Profiles (Quest Touch, Index, Vive).
4. Project Settings → Player → Android:
     Minimum API Level: 32
     Scripting Backend: IL2CPP
     Target Architecture: ARM64 only
     Color Space: Linear
5. URP Asset Settings:
     MSAA: 4×
     HDR: OFF
     Render Scale: 1.0
     SRP Batcher: ON
6. Import XRI Starter Assets sample → drag XR Origin prefab into scene
7. Set up Teleportation: add Teleportation Area or Anchor components to floor surfaces
8. Test with XR Device Simulator in Editor (Play Mode without headset)
```

---

## Unreal Engine {#unreal}

### When to Use Unreal for XR

Unreal excels at: photorealistic PC VR, automotive visualization, architectural walkthroughs,
film/broadcast previz, and Pixel Streaming (cloud rendering to thin clients).

### Key Configuration

```
PLUGIN: OpenXR (built-in since UE 5.1) — enable in Plugin settings
INPUT:  Enhanced Input System + Motion Controller component
RENDER: Forward Shading with MSAA for VR (NOT deferred)

CRITICAL — FEATURES THAT DON'T WORK IN VR:
  ✗ Nanite       — Not supported in VR (as of UE 5.4). Use traditional LODs.
  ✗ Lumen        — Too expensive for VR. Bake GI with Lightmass. Use reflection captures.
  ✗ TSR          — Temporal super-resolution causes ghosting with head movement. Use MSAA.
  ✗ Virtual Shadow Maps — Too expensive on standalone. Use traditional cascaded shadow maps.

FOR QUEST STANDALONE:
  - Vulkan Mobile Multi-View (stereo rendering)
  - Forward shading, no deferred
  - Mobile HDR: OFF
  - Target 72 fps at minimum
  - Same geometry/texture budgets as Unity standalone
```

### Unreal VR Project Essentials

```
- VR Pawn with MotionControllerComponent (left + right)
- Camera component as root of pawn (auto-tracked by runtime)
- EnhancedInput actions for grab, teleport, menu
- Grab = Physics Handle (velocity tracking) or direct attach (kinematic)
- Teleport = line trace → Nav Mesh query → fade → set actor location
- UI = Widget Component set to World space (never Screen space)
```

---

## WebXR (Three.js / React Three Fiber / Babylon.js) {#webxr}

### When to Use WebXR

No-install experiences. Demos, product configurators, AR try-on, educational content, and
experiences where you want to link someone a URL and have them in XR in seconds.

### Minimal Three.js WebXR

```javascript
import * as THREE from 'three';
import { VRButton } from 'three/addons/webxr/VRButton.js';
import { XRControllerModelFactory } from 'three/addons/webxr/XRControllerModelFactory.js';

const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
renderer.xr.enabled = true;
renderer.setPixelRatio(window.devicePixelRatio);
renderer.setSize(window.innerWidth, window.innerHeight);
document.body.appendChild(renderer.domElement);

// VR entry button
document.body.appendChild(VRButton.createButton(renderer));
// For AR: use ARButton with { requiredFeatures: ['hit-test'] }

const scene = new THREE.Scene();
const camera = new THREE.PerspectiveCamera(70, window.innerWidth / window.innerHeight, 0.01, 100);

// Controllers
const controllerModelFactory = new XRControllerModelFactory();
const controller1 = renderer.xr.getController(0);
scene.add(controller1);
const grip1 = renderer.xr.getControllerGrip(0);
grip1.add(controllerModelFactory.createControllerModel(grip1));
scene.add(grip1);

// Hand tracking
const hand1 = renderer.xr.getHand(0);
scene.add(hand1);

// Render loop
renderer.setAnimationLoop((time, frame) => {
  if (frame) {
    const session = renderer.xr.getSession();
    const refSpace = renderer.xr.getReferenceSpace();
    // Use frame.getViewerPose(refSpace) for head tracking
    // Use frame.getHitTestResults(hitTestSource) for AR
  }
  renderer.render(scene, camera);
});
```

### React Three Fiber + @react-three/xr

```bash
npm install three @react-three/fiber @react-three/xr @react-three/drei
```

```jsx
import { Canvas } from '@react-three/fiber'
import { XR, createXRStore, useXRInputSourceState } from '@react-three/xr'

const store = createXRStore({ hand: true })

function GrabbableCube() {
  return (
    <mesh position={[0, 1.5, -1]}>
      <boxGeometry args={[0.2, 0.2, 0.2]} />
      <meshStandardMaterial color="royalblue" />
    </mesh>
  )
}

export default function App() {
  return (
    <>
      <button onClick={() => store.enterVR()}>Enter VR</button>
      <button onClick={() => store.enterAR()}>Enter AR</button>
      <Canvas>
        <XR store={store}>
          <ambientLight intensity={0.5} />
          <directionalLight position={[5, 5, 5]} />
          <GrabbableCube />
        </XR>
      </Canvas>
    </>
  )
}
```

### Key WebXR APIs

```javascript
// Session types
'immersive-vr'          // Full VR
'immersive-ar'          // AR with passthrough
'inline'                // Non-immersive (preview in browser)

// Reference spaces (choose based on experience type)
'local'                 // Seated/standing, origin at initial head position
'local-floor'           // Standing, origin at floor level
'bounded-floor'         // Room-scale with defined boundary
'unbounded'             // World-scale AR (walking around a city)

// Features to request
'hand-tracking'         // XRHand (25 joints per hand)
'hit-test'              // AR surface detection
'anchors'               // Persistent world-locked points
'mesh-detection'        // Room mesh (Quest browser, etc.)
'plane-detection'       // Horizontal/vertical planes
'dom-overlay'           // Overlay HTML on top of AR view

// Asset format: ALWAYS glTF 2.0 / GLB
// Compression: Draco (geometry) + meshopt (geometry) + KTX2/Basis (textures)
```

### WebXR Performance Checklist

- [ ] glTF/GLB with Draco or meshopt compression
- [ ] Textures: KTX2 with Basis Universal, max 2048×2048
- [ ] Total scene < 25 MB for fast first load
- [ ] < 500K triangles (mobile AR) / < 1M (PCVR)
- [ ] Implement LOD manually (`THREE.LOD`)
- [ ] Use `InstancedMesh` for repeated objects
- [ ] Dispose geometries/textures when no longer needed (WebGL leaks)
- [ ] Framerate: requestAnimationFrame → renderer.setAnimationLoop

---

## Native visionOS (Apple Vision Pro) {#visionos}

### Stack: SwiftUI + RealityKit + ARKit

This is fundamentally different from Unity/Unreal. You declare 3D content in SwiftUI,
Apple's RealityKit renders it, and the system manages the render loop, compositing, foveated
rendering, and hand/eye input. You don't get a raw render loop.

### Immersion Levels

```
SHARED SPACE (default):
  Your app is one of many volumes floating in the user's space.
  Think: a floating 3D widget alongside Safari and Messages.
  Constraints: Limited volume size. Competing for GPU. No custom hand gestures.
  Use for: Productivity tools, data viz, utilities.

FULL SPACE (exclusive):
  Your app takes over the entire field of view.
  Two sub-modes:
    .mixed     — virtual content composited with passthrough (MR)
    .full      — complete virtual environment (VR)
  Use for: Games, training, immersive media.

ORNAMENTS:
  2D SwiftUI views that float at the edge of a volume.
  Like a toolbar or caption that belongs to your 3D content.
```

### Minimal Volume App

```swift
import SwiftUI
import RealityKit

@main
struct MyApp: App {
    var body: some Scene {
        // A resizable volume in Shared Space
        WindowGroup {
            ContentView()
        }
        .windowStyle(.volumetric)
        .defaultSize(width: 0.5, height: 0.5, depth: 0.5, in: .meters)

        // An immersive space (opt-in by user action)
        ImmersiveSpace(id: "ImmersiveScene") {
            ImmersiveView()
        }
        .immersionStyle(selection: .constant(.mixed), in: .mixed, .full)
    }
}

struct ImmersiveView: View {
    var body: some View {
        RealityView { content in
            let mesh = MeshResource.generateSphere(radius: 0.1)
            let material = SimpleMaterial(color: .blue, isMetallic: true)
            let entity = ModelEntity(mesh: mesh, materials: [material])
            entity.position = [0, 1.5, -1]
            
            // Make it interactive
            entity.components.set(InputTargetComponent())
            entity.components.set(CollisionComponent(
                shapes: [.generateSphere(radius: 0.1)]
            ))
            
            content.add(entity)
        }
        .gesture(TapGesture().targetedToAnyEntity().onEnded { event in
            // Handle tap on entity
            print("Tapped \(event.entity.name)")
        })
    }
}
```

### visionOS-Specific Patterns

```
INPUT:
  Primary: Look (eye tracking selects target) + Pinch (thumb-to-index confirms)
  The user NEVER touches virtual objects directly. They look at an object, it highlights,
  then they pinch in mid-air to select. Design around this indirection.
  
  Custom hand gestures require Full Space + ARKit hand tracking permission.

ENTITY COMPONENT SYSTEM:
  RealityKit uses ECS. Entities have Components. Systems operate on them.
  Key components: Transform, ModelComponent, CollisionComponent,
  InputTargetComponent, PhysicsBodyComponent, AudioMixGroupsComponent

SPATIAL PERSONAS:
  In SharePlay (FaceTime), the system renders each user as a Spatial Persona.
  You don't control avatar appearance — Apple does.
  Use GroupActivities framework for shared state.

ENTERPRISE APIS (require entitlements, not available to all developers):
  Main camera access, barcode/QR tracking, object tracking, neural engine access.
```

---

## Glossary {#glossary}

| Term | Framework | Meaning |
|---|---|---|
| `XR Origin` | Unity | Root transform of the player rig. Camera + controllers are children. |
| `Interactable` | XRI (Unity) | Component that can be grabbed, poked, gazed at, or interacted with. |
| `Interactor` | XRI (Unity) | Component on a controller/hand that initiates interactions. |
| `Interaction Manager` | XRI (Unity) | Singleton mediating all interactor↔interactable communication. |
| `Locomotion Provider` | XRI (Unity) | Base class for teleport, snap turn, continuous move. |
| `Affordance` | MRTK 3 | Visual feedback (glow, scale, color) signaling interactivity. |
| `Solver` | MRTK 3 | Component that positions UI relative to the user (tag-along, orbital, radial). |
| `Entity` | RealityKit | Basic scene graph node (equivalent of Unity GameObject). |
| `Component` | RealityKit ECS | Data attached to an entity (transform, model, physics, custom). |
| `System` | RealityKit ECS | Logic operating on entities with matching component sets. |
| `XRFrame` | WebXR | Per-frame state from the browser's XR session (poses, inputs, hit tests). |
| `XRRigidTransform` | WebXR | Position (DOMPointReadOnly) + orientation (DOMPointReadOnly quaternion). |
| `XRInputSource` | WebXR | A controller, hand, or gaze input device in a WebXR session. |
| `XRHand` | WebXR | 25-joint hand skeleton accessible per frame. |
| `Guardian` | Meta | Physical play-area boundary set during Quest setup. |
| `Passthrough` | Meta/Generic | Camera feed rendered as the "real world" layer in MR mode. |
| `Shared Space` | visionOS | Default mode: your volume coexists with other apps. |
| `Full Space` | visionOS | Exclusive mode: only your app renders. |
| `Ornament` | visionOS | 2D SwiftUI view attached to a volume's edge. |
| `ASW / SpaceWarp` | Meta Runtime | Synthesized frames when the app misses target FPS. A safety net, NOT a target. |
| `Reprojection / ATW` | Generic Runtime | Rotational-only correction for late frames. Reduces judder but not position error. |
