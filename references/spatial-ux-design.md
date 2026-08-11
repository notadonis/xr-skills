# Spatial UX/UI Design Reference

> Last verified: 2026-08. Hardware specs, SDK versions, and framework picks are defaults,
> not facts. Confirm against official docs before pinning (Freshness Protocol, SKILL.md).
> Physiology-based numbers (comfort, visual arc) are stable science.

This is the most important reference in this skill. Bad UX ships products that make people
physically uncomfortable or that nobody can figure out how to use. Read this before designing
any user-facing XR experience.

## Table of Contents
1. [Comfort Science](#comfort)
2. [Spatial UI Pattern Library](#patterns)
3. [Locomotion](#locomotion)
4. [Onboarding & First-Time Experience](#onboarding)
5. [Accessibility](#accessibility)
6. [Design Process](#process)

---

## Comfort Science {#comfort}

These aren't guidelines — they're constraints derived from human physiology. Violating them
causes measurable discomfort (eye strain, vestibular mismatch, neck fatigue).

### The Comfort Zone

```
              TOP VIEW (horizontal)
              
              30°        30°
               ╲         ╱
                ╲       ╱
                 ╲     ╱
                  ╲   ╱
                   ╲ ╱
              ──────●──────  ← user's head
                    
     Secondary      │      Secondary
     content        │      content
     (glanceable)   │   (glanceable)
                    │
              Primary content
              lives here
              
              SIDE VIEW (vertical)
              
                   20° up
                    ╱
                   ╱
              ────●────  ← resting eye line (roughly horizontal)
                   ╲
                    ╲
                   12° down
                    
              Primary UI: slightly below eye line (−5° to −10° is ideal)
              This matches natural resting gaze, which angles slightly downward.
```

### Distance Rules

```
ABSOLUTE MINIMUM:     0.5 m
  Below this, the eyes cannot converge on stereoscopic content.
  Result: eye strain, blurry text, headache within minutes.

COMFORTABLE RANGE:    1.2 – 2.0 m
  This is where you should place all primary UI by default.
  At 1.5 m, most headset optics produce sharp, comfortable imagery.

MAXIMUM FOR TEXT:     ~5 m
  Beyond this, text becomes too small to read at any practical font size
  (limited by headset angular resolution, typically 20–25 PPD).

DEPTH VARIATION:
  Avoid placing interactive elements at wildly different depths.
  Rapid focus changes (0.5 m → 3 m → 0.5 m) cause accommodation fatigue.
  Keep related UI elements within ±0.3 m depth of each other.
```

### Text Sizing

```
RULE: Text must subtend at least 1.0° of visual arc.

AT DISTANCE:        MINIMUM PHYSICAL HEIGHT:
  0.5 m             0.87 cm  (but don't put text this close)
  1.0 m             1.75 cm
  1.5 m             2.62 cm  ← most common UI distance
  2.0 m             3.49 cm
  3.0 m             5.24 cm

APPLE VISION PRO RECOMMENDATION: 35 pt minimum at default window distance (~1.5 m)

PRACTICAL ADVICE:
  Use Unity's TextMeshPro or RealityKit's text entities. Never Unity's legacy Text.
  Set auto-size with a generous minimum. Test readability ON DEVICE — emulators lie
  about text clarity because they render at monitor resolution, not headset resolution.
```

### Motion Rules

```
NEVER:
  ✗ Move or rotate the camera programmatically (vestibular mismatch → nausea)
  ✗ Apply head bob or camera shake
  ✗ Animate FOV changes
  ✗ Lock the horizon (the user's vestibular system expects the world to be stable)
  ✗ Move the ground plane while the user is standing on it

TELEPORTATION TRANSITION:
  Duration:     0.1 – 0.3 s
  Method:       Fade to black → move → fade in. OR: Blink (instant cut to black, brief hold, cut in)
  Never:        Slide or fly the camera to the destination

SNAP TURN:
  Angle:        30° or 45° (configurable in comfort settings)
  Transition:   Instant (< 1 frame). No animation. The brain accepts discontinuity
                better than smooth rotation.

IF YOU MUST OFFER SMOOTH LOCOMOTION:
  - Default OFF. Behind a comfort toggle.
  - Add a vignette (darken peripheral vision) that increases with speed.
  - Cap speed. Walking speed (1.4 m/s) is tolerable. Running (3+ m/s) is not for most.
  - Add a visible "nose" or cockpit reference frame to reduce discomfort.
```

---

## Spatial UI Pattern Library {#patterns}

### Pattern 1: World-Locked Panel

The fundamental "window" of XR. A flat surface pinned in 3D space.

```
┌─────────────────────────────────────────┐
│  📋 Task List           [?]  [—]  [✕]  │ ← Title bar + controls
│─────────────────────────────────────────│
│  ☑ Inspect hydraulic line               │
│  ☐ Check pressure gauge                 │ ← Content
│  ☐ Sign off maintenance log             │
│─────────────────────────────────────────│
│  [ Complete All ]                       │ ← Action button (≥ 6cm)
└─────────────────────────────────────────┘

SPECS:
  Distance:       1.5 m from user (default)
  Width:          0.4 – 0.8 m (fills 15–30° FOV)
  Curvature:      Slight concave (2–5°) for wide panels (improves edge readability)
  Background:     Semi-transparent (70–85% opacity) for spatial awareness
  Text:           Unlit/emissive shader (not affected by scene lighting)
  Interaction:    Grab bar at top for repositioning. Poke/pinch for buttons.
  Orientation:    Faces user. Optionally billboards on Y-axis only (stays upright).
```

### Pattern 2: Hand Menu

Appears on the user's non-dominant palm when they look at it.

```
TRIGGER:     Palm-up gesture detected + gaze intersects palm region
POSITION:    Anchored to wrist/palm, billboarded toward user's eyes
CONTENT:     3–5 buttons max. Large icons (≥ 4 cm). Minimal text.
DISMISS:     Palm down, or hand moves out of tracking volume
LAYOUT:      Vertical stack or 2×2 grid above the palm
LATENCY:     Appear within 1–2 frames of trigger. Disappear within 2 frames.

IMPLEMENTATION:
  Unity: MRTK 3 HandMenu solver + HandConstraint
  Custom: Track wrist joint (XR_EXT_hand_tracking joint index 0),
          face detection from palm normal toward eye, show/hide UI prefab
```

### Pattern 3: Wrist UI

Always-visible display on the inner wrist, like a smartwatch.

```
SIZE:        ~8 × 4 cm maximum
USE FOR:     Status (health bar, time, notification count, mode indicator)
DON'T:       Extended reading or complex interaction (wrist angle is fatiguing)
ANCHOR:      Wrist joint. Follows arm naturally.
VISIBILITY:  Always rendered, but only legible when user turns wrist toward face.
```

### Pattern 4: Radial / Pie Menu

Appears around controller or hand. 4–8 segments. Selected by angle.

```
SEGMENTS:    4 (90° each) to 8 (45° each). Never more than 8.
SELECTION:   Tilt controller / move hand in direction of segment
ACTIVATION:  Release trigger / pinch release
ICONS:       Large, centered in segment. Text label below.
OPEN:        On button hold (appears) → tilt to select → release to confirm
BEST FOR:    Tool switching, weapon wheels, quick actions.
RESPONSE:    O(1) selection depth — faster than any list or hierarchy.
```

### Pattern 5: 3D Bounding Box Manipulation

Wireframe box around an object with handle affordances.

```
CORNER HANDLES:    Uniform scale (maintain proportions)
EDGE HANDLES:      Single-axis stretch
FACE HANDLES:      Translate along face normal
ROTATION:          Ring gizmo around each axis, or grab-and-twist gesture
HANDLE SIZE:       ≥ 2 cm radius (graspable)
FEEDBACK:          Highlight active handle. Show axis lines during manipulation.
IMPLEMENTATION:    MRTK 3 BoundsControl (Unity). Custom for other engines.
```

### Pattern 6: Gaze-Dwell Button

Activates after sustained gaze (0.8–1.2 s).

```
INDICATOR:   Radial fill (clockwise) around button, progressing with dwell time
CANCEL:      Gaze leaves button → progress resets (with 0.1 s grace period)
USE:         Accessibility fallback ONLY. Not primary input (too slow, fatiguing).
FEEDBACK:    Audio tick at 50% and 100%. Visual pulse on activation.
AVOID:       For destructive actions (too easy to accidentally trigger).
```

### Pattern 7: Tooltip / Spatial Label

Floating text label connected to a 3D object.

```
TRIGGER:     Proximity (hand within 0.5 m) or hover (ray intersects collider)
POSITION:    Slightly above and behind the object (don't occlude it)
ORIENTATION: Billboard toward camera (always faces user)
CONTENT:     3–5 words maximum. No paragraphs.
CONNECTOR:   Thin leader line from label to object attachment point
DISMISS:     Hand moves away or gaze leaves (with 0.3 s delay)
```

### Pattern 8: Confirmation Dialog

For destructive or irreversible actions.

```
POSITION:    1.5 m from user, centered in view
CONTENT:     Clear question: "Delete this model? This cannot be undone."
BUTTONS:     Two large buttons side by side:
               [Cancel] (left/dominant side — the safe default)
               [Confirm] (right, distinct color — e.g., red for delete)
CRITICAL:    Never use gaze-dwell for destructive confirmations.
             Require deliberate pinch/press.
ALTERNATIVE: For high-stakes: hold-to-confirm (press and hold for 1.5 s with progress bar)
```

### Pattern 9: Spatial Notification

Non-intrusive alert that respects immersion.

```
POSITION:    Peripheral vision (±25° from center, slightly above eye line)
ENTRY:       Fade in over 0.3 s + subtle spatial audio chime from notification direction
DURATION:    3–5 s, then fade out (or persist until dismissed)
INTERACTION: Gaze at it to expand details. Pinch to dismiss or take action.
NEVER:       Center of view (breaks flow), modal overlay (blocks interaction)
```

### Pattern 10: Progress / Loading Indicator

Users are wearing a headset. They can't switch to their phone while they wait.

```
POSITION:    1.5 m, centered, slightly below eye line
CONTENT:     Animated indicator (not a static spinner — users think it froze)
             Progress bar with percentage if progress is measurable
             Estimated time if > 5 s ("About 15 seconds remaining")
NEVER:       Black screen with no indicator (user thinks headset crashed)
             Blocking the entire view (let them look around while loading)
BEST:        Progressive loading — show low-detail environment immediately,
             stream in detail while user explores.
```

### Pattern 11: Voice Command Indicator

Visual feedback when voice input is active.

```
POSITION:    Wrist UI or small floating indicator at bottom of view
STATES:      Idle → Listening (pulsing mic icon) → Processing (spinner) → Confirmed (check)
FEEDBACK:    Show recognized text in real-time (like live captions)
ACTIVATION:  Keyword ("Hey [app name]") or button press to start listening
TIMEOUT:     Auto-stop after 5 s of silence
```

### Pattern 12: Passthrough Portal / Window

A window into the real world from within a VR environment (or vice versa).

```
USE CASE:    Let VR users see their keyboard, drink, or surroundings
             without fully exiting VR.
SHAPE:       Circular or rectangular window, world-locked at a useful position
SIZE:        ~0.5 m diameter minimum (large enough to be useful)
EDGE:        Soft feathered edge (no hard cutoff between VR and passthrough)
TRIGGER:     Double-tap controller, look-down gesture, or proximity to guardian edge
PLATFORM:    Quest: OVRPassthroughLayer with custom geometry
```

---

## Locomotion {#locomotion}

### Comparison Table

| Pattern | Comfort | Speed | Precision | Best For |
|---|---|---|---|---|
| **Teleport + snap turn** | ★★★★★ | Medium | Medium | Default for all VR apps |
| **Physical walking** | ★★★★★ | Slow | High | Room-scale (< 10 m²) |
| **Grab-the-world** | ★★★★★ | Fast | High | Model inspection, maps, tabletop |
| **Vehicle/cockpit** | ★★★★☆ | Fast | Low | Driving sims, virtual tours |
| **Smooth locomotion** | ★★☆☆☆ | Fast | High | Experienced VR gamers ONLY |
| **Smooth rotation** | ★★☆☆☆ | — | High | Experienced VR gamers ONLY |

### Implementation Checklist

- [ ] Default: teleportation + snap turn (45°). Works for everyone.
- [ ] Teleport arc: visible, responsive (< 1 frame lag), shows landing indicator
- [ ] Invalid targets: clear red/X indicator (don't silently fail)
- [ ] Snap turn angle: configurable (30°, 45°, 60°, 90°)
- [ ] Smooth locomotion: OFF by default, behind a comfort toggle
- [ ] Smooth locomotion vignette: ON by default when smooth loco is enabled
- [ ] Speed limit: walking speed (1.4 m/s) default, adjustable
- [ ] Seated mode: all locomotion reachable from a seated position
- [ ] Dominant hand: configurable (left-handed users exist!)

---

## Onboarding & First-Time Experience {#onboarding}

First-time XR users don't know how to grab, teleport, or use hand tracking. Experienced users
hate tutorials. Design for both.

### Progressive Disclosure

```
1. ENVIRONMENT FIRST (0–10 s):
   Let the user look around. No instructions. Just presence.
   This is often someone's first time in XR. Give them a moment.

2. BASIC INTERACTION (10–30 s):
   Highlight ONE object with a pulsing glow + spatial audio cue.
   "Reach out and grab this." Wait for success. Celebrate.

3. LOCOMOTION (30–60 s):
   "Point at the floor and press [trigger/pinch] to teleport."
   Show the arc visually before asking them to use it.

4. TASK-SPECIFIC (60+ s):
   Now teach your app's unique interactions, one at a time.
   Never introduce more than one new concept per step.
```

### Comfort Settings Menu

Present early (during onboarding or accessible from hand menu):

```
MOVEMENT:
  [ ] Teleportation (default)
  [ ] Smooth locomotion
  
TURNING:
  [ ] Snap turn: 30° / 45° / 60° / 90°
  [ ] Smooth turning

COMFORT AIDS:
  Vignette intensity:  [slider: 0% ———●——— 100%]

INTERACTION:
  Dominant hand:  [Left] [Right]
  
DISPLAY:
  UI scale:      [80%] [100%] [125%] [150%]
  Subtitle size: [Small] [Medium] [Large]
```

---

## Accessibility {#accessibility}

### Core Requirements (Non-Negotiable)

- **Seated mode:** All content reachable from a seated position. Adjust UI heights accordingly.
- **One-handed operation:** Every action possible with a single hand. No mandatory two-hand gestures.
- **Text scaling:** 100%, 125%, 150% options minimum. Test at 150% for layout breakage.
- **High contrast mode:** UI backgrounds at 85%+ opacity. Text contrast ratio ≥ 4.5:1.
- **Color-blind safe:** Never use color alone to convey meaning. Pair with shape, icon, or text.
  Test with Deuteranopia/Protanopia simulations.
- **Subtitles/captions:** Speaker identification + sound descriptions (e.g., "[alarm blaring]").
  Spatial subtitles: position near speaker but billboard toward user.
- **Haptic alternatives:** Every haptic has a visual AND audio equivalent.

### Additional (Strongly Recommended)

- **Motor impairment:** Gaze+dwell as universal fallback. Button remapping.
- **Cognitive load:** Difficulty/pacing options. Don't require memorization.
  Show active task reminders in wrist UI or persistent tooltip.
- **Photosensitivity:** No rapid flashing (> 3 Hz). "Reduce motion" toggle.
- **Audio descriptions:** For low-vision users, describe key spatial elements via audio.
- **Mono audio option:** Some users are deaf in one ear. Allow L/R balance and mono fold.
- **Adjustable interaction speeds:** Gaze-dwell time, hold-to-confirm duration, animation speeds.

### Testing Protocol

```
TEST EACH FEATURE WITH:
  1. Seated, using dominant hand only
  2. Seated, using non-dominant hand only
  3. Standing, full mobility (baseline)
  4. With high-contrast mode enabled
  5. With subtitles enabled at 150% scale
  6. With comfort settings at maximum (heavy vignette, snap turn only)
  7. With eye tracking disabled (if your app uses it)
  8. On the lowest-spec target device (performance affects accessibility)
```

---

## Design Process {#process}

### Before You Code

1. **Paper prototype** your spatial layout. Sketch the user's view at key moments.
   Where is the UI? Where are they looking? What are they holding?
2. **Blockout in-engine.** Gray boxes at correct scale. Walk through the experience in VR.
   Can you reach everything? Is text readable? Does the space feel right?
3. **Test with a first-time VR user.** Not your team. Someone who's never worn a headset.
   Watch where they struggle. Don't explain — observe.

### XR-Specific Heuristics (Jakob Nielsen, Adapted)

```
1. SPATIAL VISIBILITY OF SYSTEM STATUS
   The user can see their hands, controllers, and body. Use this.
   Show state on the user's wrist, on tools they're holding, in the environment.

2. MATCH BETWEEN SYSTEM AND REAL WORLD
   If it looks like a button, it should push like a button.
   If it looks like a drawer, it should slide. Use physical metaphors.

3. USER CONTROL AND FREEDOM
   Always let users undo, go back, or escape to a safe space.
   "Exit to lobby" must always be accessible (hand menu or guardian double-tap).

4. CONSISTENCY ACROSS SPACE
   Buttons at the same distance should be the same size.
   Interaction patterns should be consistent across the entire experience.

5. ERROR PREVENTION IN 3D
   Snapping, magnetism, and confirmation dialogs prevent spatial errors.
   Undo is harder in 3D than 2D. Prevent errors instead of fixing them.
```
