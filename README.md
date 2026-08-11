# 🥽 XR Development Skill

**Full-stack AR/VR/MR/XR expertise for AI coding agents — built for low-oversight execution.**

An open [agent skill](https://skills.sh) that gives Claude Code, Cursor, Copilot, Windsurf,
and other AI agents deep, production-tested knowledge of spatial computing: GPU-level
rendering optimization, spatial UX patterns, backend multiplayer architecture, and an
executable linter that catches the mistakes that make users physically sick.

## Install

```
npx skills add notadonis/xr-skills
```

Works with: Claude Code, Cursor, Windsurf, Copilot, Cline, Goose, Roo, AMP, and
[all agents supported by skills.sh](https://skills.sh).

## What's Inside

| File | Covers |
|---|---|
| **SKILL.md** | Operating mode (default & declare), routing, terminology, decision frameworks, non-negotiable rules, the exit gate, freshness protocol |
| **references/platform-specs.md** | Device specs (Quest 3/3S, Vision Pro, Galaxy XR, PCVR, HoloLens 2, phone AR), performance budgets (canonical source), OpenXR, cross-platform strategy |
| **references/frontend-engines.md** | Unity 6 (packages, structure, XRI, shaders, physics, audio), Unreal, WebXR (Three.js, R3F), native visionOS |
| **references/backend-infrastructure.md** | Multiplayer networking (bandwidth math, pose compression, framework comparison), anchor persistence, cloud rendering, CDN, analytics, XR auth |
| **references/spatial-ux-design.md** | Comfort science with exact measurements, 12 spatial UI patterns, locomotion, onboarding, accessibility |
| **references/quality-and-security.md** | Testing pyramid, profiling, CI/CD, biometric privacy law (GDPR/BIPA), store submission requirements, PR review checklist |
| **references/task-recipes.md** | End-to-end procedures: scaffold a Quest project, scaffold WebXR, run a ship-readiness audit |
| **scripts/xr_lint.py** | Executable static checks for XR anti-patterns. Zero dependencies. |

## The Linter

Prose rules get skimmed. Exit codes get obeyed.

```
python3 scripts/xr_lint.py <project-path> [--json] [--strict]
```

Scans Unity C#, scenes/prefabs, package manifests, and WebXR JS/TS for the classics:
screen-space canvases, camera transform writes, `Time.timeScale = 0` pauses, hardcoded
IPD, per-frame allocations, busy-waits, `requestAnimationFrame` in WebXR files, real-time
shadows, sub-72 framerate caps, smooth-turn-only locomotion. BLOCK findings fail the run.
Agents using this skill run it before declaring any task done.

## What It Teaches Agents

- **Act without asking.** Sane defaults (Quest 3 + Unity 6 + XRI), declared assumptions, escalation only for expensive-to-reverse decisions
- **Choose the right engine** (Unity vs. Unreal vs. WebXR vs. visionOS vs. Android XR vs. Godot)
- **Write performant XR code** that hits framerate on standalone hardware
- **Design spatial interfaces** that don't cause nausea
- **Architect multiplayer** with pose compression, spatial voice, IK avatars, shared anchors
- **Handle biometric privacy** correctly (eye tracking ≠ just another analytics signal)
- **Verify their own work** against an exit gate and an executable linter before finishing
- **Pass store review** (Meta VRCs, visionOS, Play/Android XR)

## Supported Platforms

- **Meta Quest 2 / 3 / 3S** (standalone & PC Link)
- **Apple Vision Pro** (native SwiftUI + RealityKit)
- **Samsung Galaxy XR / Android XR** (Jetpack XR, Unity OpenXR)
- **PC VR** (Valve Index, HTC Vive Pro 2, Bigscreen Beyond)
- **HoloLens 2** / **Magic Leap 2** (enterprise AR)
- **Phone AR** (ARKit / ARCore)
- **WebXR** (browser-based, all devices)

## Design Principles

1. **Opinionated over encyclopedic.** The skill tells agents what to do, not every option.
2. **Comfort is non-negotiable.** XR is the only software domain where bad code makes users physically sick. Comfort rules are hard constraints.
3. **Default and declare.** Agents assume a sane stack, state the assumption, and proceed. They ask only when a decision is expensive to reverse.
4. **Executable over prose.** Rules that can be checked mechanically live in `scripts/xr_lint.py`. Agents follow exit codes better than paragraphs.
5. **Progressive disclosure.** SKILL.md stays lean; references load on demand.
6. **Honest about decay.** Every reference carries a `Last verified` date. Physiology is stable; SDK versions are defaults to confirm, not facts to repeat.

## Contributing

Issues and PRs welcome. Especially:
- Corrections to SDK versions or API changes (bump the `Last verified` date with your fix)
- New linter checks with a test fixture
- New device coverage
- Additional spatial UI patterns from production apps
- Accessibility improvements

## License

MIT
