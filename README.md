# 🥽 XR Development Skill

**Full-stack AR/VR/MR/XR expertise for AI coding agents.**

An open [agent skill](https://skills.sh) that gives Claude Code, Cursor, Copilot, Windsurf, and other AI agents deep, production-tested knowledge of spatial computing — from GPU-level rendering optimization to spatial UX patterns to backend multiplayer architecture.

## Install

```bash
npx skills add notadonis/xr-skills
```

Works with: Claude Code, Cursor, Windsurf, Copilot, Cline, Goose, Roo, AMP, and [all agents supported by skills.sh](https://skills.sh).

## What's Inside

| File | Lines | Covers |
|---|---|---|
| **SKILL.md** | ~170 | Decision frameworks, non-negotiable rules, terminology, routing logic |
| **references/platform-specs.md** | ~220 | Device specs (Quest 3, Vision Pro, PCVR, HoloLens 2, phone AR), performance budgets, OpenXR extensions, cross-platform strategy |
| **references/frontend-engines.md** | ~370 | Unity (packages, project structure, XRI architecture, shaders, physics, audio), Unreal Engine, WebXR (Three.js, React Three Fiber), native visionOS (SwiftUI + RealityKit) |
| **references/backend-infrastructure.md** | ~320 | Multiplayer networking (bandwidth math, pose compression, framework comparison), spatial anchor persistence, cloud rendering, CDN/asset delivery, analytics, API design, XR authentication |
| **references/spatial-ux-design.md** | ~340 | Comfort science (exact measurements), 12 spatial UI patterns with specs, locomotion, onboarding flow, accessibility requirements |
| **references/quality-and-security.md** | ~280 | Testing pyramid, profiling workflows, CI/CD pipelines, biometric privacy law (GDPR/BIPA), PR review checklist |

## What It Teaches Agents

After loading this skill, an AI agent can:

- **Choose the right engine** for a given XR project (Unity vs. Unreal vs. WebXR vs. native visionOS)
- **Write performant XR code** that hits framerate on Quest 3 (draw call budgets, shader rules, physics config)
- **Design spatial interfaces** that don't cause nausea (comfort zones, text sizing, locomotion patterns)
- **Architect multiplayer** with pose compression, spatial voice, IK avatars, and shared anchors
- **Handle biometric privacy** correctly (eye tracking ≠ just another analytics signal)
- **Review XR pull requests** against a comprehensive checklist (comfort, performance, accessibility, privacy)
- **Scaffold projects** with correct package setup for Unity OpenXR, WebXR, or visionOS

## Supported Platforms

The skill covers development for:

- **Meta Quest 2 / 3 / 3S** (standalone & PC Link)
- **Apple Vision Pro** (native SwiftUI + RealityKit)
- **PC VR** (Valve Index, HTC Vive Pro 2, Bigscreen Beyond)
- **HoloLens 2** (MRTK, enterprise AR)
- **Magic Leap 2** (enterprise AR)
- **Phone AR** (ARKit / ARCore)
- **WebXR** (browser-based, all devices)

## Design Principles

1. **Opinionated over encyclopedic.** This skill tells agents what to do, not every possible option. When there's a best practice, it states it directly.

2. **Comfort is non-negotiable.** XR is the only software domain where bad code can make users physically sick. The skill treats comfort rules as hard constraints, not suggestions.

3. **Progressive disclosure.** The SKILL.md is kept under 500 lines. Detailed references load only when needed, keeping agent context windows efficient.

4. **Real-world grounded.** Patterns come from shipping products, not documentation. The skill covers what actually goes wrong (thermal throttling after 15 minutes, GC spikes during physics), not just what's theoretically correct.

## Contributing

Issues and PRs welcome. If you've shipped an XR product and something in here is wrong or missing, please contribute. Especially welcome:

- Corrections to SDK versions or API changes
- New device coverage (e.g., Android XR, Snapdragon XR)
- Additional spatial UI patterns from production apps
- Accessibility improvements
- Non-English localization of the skill

## License

MIT
