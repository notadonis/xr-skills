#!/usr/bin/env python3
"""
xr_lint.py - Static checks for known XR anti-patterns.

Part of the xr-development skill. Scans Unity C#, Unity scenes/prefabs,
package manifests, and WebXR JS/TS for the mistakes listed in SKILL.md's
"Common Mistakes That Ship Broken Products" table.

Zero dependencies. Python 3.8+.

Usage:
    python3 xr_lint.py <project-path> [--json] [--strict]

Exit codes:
    0  no BLOCK findings (warnings allowed unless --strict)
    1  BLOCK findings present (or any findings with --strict)
    2  usage / path error

Severity:
    BLOCK  ships a broken or sickness-inducing product; must fix or justify
    WARN   likely problem; verify by hand

These are heuristics. A clean run does not prove comfort or framerate;
it proves the absence of the detectable classics. Profile on device.
"""

import argparse
import json
import os
import re
import sys

SKIP_DIRS = {
    ".git", "Library", "Temp", "Obj", "obj", "bin", "Build", "Builds",
    "Logs", "UserSettings", "node_modules", "PackageCache", "dist",
    ".vs", ".idea", "__pycache__",
}

CS_EXT = {".cs"}
YAML_EXT = {".unity", ".prefab"}
JS_EXT = {".js", ".jsx", ".ts", ".tsx"}

# Struct constructions that do not allocate on the GC heap.
NON_ALLOC_TYPES = (
    "Vector2", "Vector3", "Vector4", "Quaternion", "Color", "Color32",
    "Rect", "Ray", "Ray2D", "Bounds", "Matrix4x4", "Pose", "Plane",
    "WaitForSeconds",  # allocates, but cached idiom is common; handled below
)


class Finding:
    def __init__(self, check_id, severity, path, line, message, fix):
        self.check_id = check_id
        self.severity = severity
        self.path = path
        self.line = line
        self.message = message
        self.fix = fix

    def to_dict(self):
        return {
            "id": self.check_id, "severity": self.severity, "file": self.path,
            "line": self.line, "message": self.message, "fix": self.fix,
        }


def iter_files(root):
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]
        for name in filenames:
            yield os.path.join(dirpath, name)


def read_text(path):
    try:
        with open(path, "r", encoding="utf-8", errors="replace") as f:
            return f.read()
    except OSError:
        return None


def line_of(text, index):
    return text.count("\n", 0, index) + 1


# ---------------------------------------------------------------- C# checks

RE_TIMESCALE = re.compile(r"Time\.timeScale\s*=\s*0(?:\.0*)?f?\s*;")
RE_CAMERA_WRITE = re.compile(
    r"Camera\.main\.transform\.(?:position|rotation|localPosition|localRotation|eulerAngles)\s*="
)
RE_WWW = re.compile(r"\bnew\s+WWW\s*\(")
RE_BUSY_WAIT = re.compile(r"while\s*\(\s*!\s*\w+\.isDone\s*\)")
RE_IPD = re.compile(r"(?i)\b(?:ipd|interpupillary\w*)\s*=\s*\d")
RE_TARGET_FPS = re.compile(r"Application\.targetFrameRate\s*=\s*(\d+)")
RE_UPDATE_METHOD = re.compile(r"\bvoid\s+(Update|LateUpdate|FixedUpdate)\s*\(\s*\)")
RE_CONTINUOUS_TURN = re.compile(r"\bContinuousTurnProvider\b")
RE_SNAP_TURN = re.compile(r"\bSnapTurnProvider\b")

RE_UPDATE_ALLOC = re.compile(r"\bnew\s+([A-Z][\w.]*)\s*(?:<[^<>]*>)?\s*[\(\[{]")
RE_UPDATE_FIND = re.compile(
    r"\b(GameObject\.Find|FindObjectOfType|FindObjectsOfType|"
    r"FindFirstObjectByType|FindAnyObjectByType)\s*[<\(]"
)
RE_UPDATE_GETCOMP = re.compile(r"\bGetComponent(?:s|InChildren|InParent)?\s*<")
RE_UPDATE_LINQ = re.compile(r"\.(Where|Select|OrderBy|ToList|ToArray|First(?:OrDefault)?)\s*\(")
RE_UPDATE_INSTANTIATE = re.compile(r"\bInstantiate\s*[\(<]")
RE_UPDATE_STRCAT = re.compile(r"\+\s*\"|\"\s*\+")


def extract_method_body(text, start_index):
    """Return (body, body_start_index) for the brace block after start_index."""
    brace = text.find("{", start_index)
    if brace == -1:
        return None, None
    depth = 0
    for i in range(brace, len(text)):
        c = text[i]
        if c == "{":
            depth += 1
        elif c == "}":
            depth -= 1
            if depth == 0:
                return text[brace:i + 1], brace
    return None, None


def check_csharp(path, text, findings):
    for m in RE_TIMESCALE.finditer(text):
        findings.append(Finding(
            "XR001", "BLOCK", path, line_of(text, m.start()),
            "Time.timeScale = 0 used for pause. Freezes animation/physics context "
            "and makes the world feel stuck to the head.",
            "Pause game logic with your own flag. Never freeze the sim clock in XR."))
    for m in RE_CAMERA_WRITE.finditer(text):
        findings.append(Finding(
            "XR002", "BLOCK", path, line_of(text, m.start()),
            "Direct write to the camera transform. Programmatic camera movement "
            "causes vestibular mismatch and nausea.",
            "Move the XR Origin / rig root for locomotion. The camera belongs to "
            "the user's head."))
    for m in RE_WWW.finditer(text):
        findings.append(Finding(
            "XR003", "WARN", path, line_of(text, m.start()),
            "Deprecated WWW class. Risk of main-thread stalls and it is removed "
            "in current Unity versions.",
            "UnityWebRequest with async/await or coroutines."))
    for m in RE_BUSY_WAIT.finditer(text):
        findings.append(Finding(
            "XR004", "BLOCK", path, line_of(text, m.start()),
            "Busy-wait on request.isDone blocks the main thread. Frame hitch, "
            "reprojection artifact, nausea chain.",
            "await request.SendWebRequest() or yield in a coroutine."))
    for m in RE_IPD.finditer(text):
        findings.append(Finding(
            "XR005", "BLOCK", path, line_of(text, m.start()),
            "Hardcoded IPD value. Stereo mismatch gives everyone else a headache.",
            "Use the OS-reported IPD. Never a literal."))
    for m in RE_TARGET_FPS.finditer(text):
        try:
            fps = int(m.group(1))
        except ValueError:
            continue
        if 0 < fps < 72:
            findings.append(Finding(
                "XR006", "BLOCK", path, line_of(text, m.start()),
                f"Application.targetFrameRate = {fps}. Below the 72 Hz XR floor.",
                "72 minimum, 90 preferred. Better: let the XR runtime own the rate."))

    # Per-frame hot-path checks inside Update/LateUpdate/FixedUpdate bodies.
    for m in RE_UPDATE_METHOD.finditer(text):
        body, body_start = extract_method_body(text, m.end())
        if not body:
            continue
        method = m.group(1)

        def rep(check_id, sev, rx, msg, fix, skip_types=False):
            for hit in rx.finditer(body):
                if skip_types:
                    t = hit.group(1).rsplit(".", 1)[-1]
                    if t in NON_ALLOC_TYPES:
                        continue
                findings.append(Finding(
                    check_id, sev, path, line_of(text, body_start + hit.start()),
                    f"{msg} (inside {method}())", fix))

        rep("XR010", "WARN", RE_UPDATE_ALLOC,
            "Heap allocation in a per-frame method. GC spikes = frame drops = nausea",
            "Allocate once, cache, or object-pool.", skip_types=True)
        rep("XR011", "WARN", RE_UPDATE_FIND,
            "Scene search in a per-frame method",
            "Cache the reference in Awake/Start.")
        rep("XR012", "WARN", RE_UPDATE_GETCOMP,
            "GetComponent in a per-frame method",
            "Cache the component in Awake/Start.")
        rep("XR013", "WARN", RE_UPDATE_LINQ,
            "LINQ in a per-frame method allocates",
            "Plain loops in hot paths.")
        rep("XR014", "WARN", RE_UPDATE_INSTANTIATE,
            "Instantiate in a per-frame method",
            "Object pool. Pre-warm at load time.")
        rep("XR015", "WARN", RE_UPDATE_STRCAT,
            "String concatenation in a per-frame method allocates",
            "Cache strings, or StringBuilder updated only on change.")


def check_csharp_project_level(cs_texts, findings):
    """Checks that need the whole project's C# in view."""
    has_continuous = None
    has_snap = False
    for path, text in cs_texts:
        if has_continuous is None:
            m = RE_CONTINUOUS_TURN.search(text)
            if m:
                has_continuous = (path, line_of(text, m.start()))
        if RE_SNAP_TURN.search(text):
            has_snap = True
    if has_continuous and not has_snap:
        path, line = has_continuous
        findings.append(Finding(
            "XR020", "WARN", path, line,
            "ContinuousTurnProvider referenced with no SnapTurnProvider anywhere "
            "in the project. Smooth rotation is the second-strongest nausea "
            "trigger and must not be the only option.",
            "Snap turn as default. Smooth turn opt-in, with vignette."))


# ------------------------------------------------------- Unity YAML checks

RE_RENDERMODE = re.compile(r"m_RenderMode:\s*([01])\b")
RE_SHADOW_BLOCK = re.compile(r"m_Shadows:\s*\n\s*m_Type:\s*([12])\b")


def check_unity_yaml(path, text, findings):
    for m in RE_RENDERMODE.finditer(text):
        mode = "ScreenSpaceOverlay" if m.group(1) == "0" else "ScreenSpaceCamera"
        findings.append(Finding(
            "XR101", "BLOCK", path, line_of(text, m.start()),
            f"Canvas render mode is {mode}. Screen-space UI rigidly follows the "
            "head in XR: nausea, broken presence.",
            "World Space canvas. Lazy-follow with heavy damping at most."))
    for m in RE_SHADOW_BLOCK.finditer(text):
        kind = "Hard" if m.group(1) == "1" else "Soft"
        findings.append(Finding(
            "XR102", "WARN", path, line_of(text, m.start()),
            f"Light with real-time {kind} shadows in scene/prefab. Standalone XR "
            "cannot afford real-time shadows.",
            "Bake lightmaps. Blob shadows for dynamic objects. (Ignore if this "
            "scene only targets PC VR.)"))


# --------------------------------------------------------- manifest checks

def check_manifest(path, text, findings):
    try:
        data = json.loads(text)
    except ValueError:
        return
    deps = data.get("dependencies", {})
    if "com.unity.postprocessing" in deps:
        findings.append(Finding(
            "XR201", "WARN", path, 1,
            "Post-processing stack in manifest. Real-time post-processing does "
            "not fit the standalone XR frame budget.",
            "Remove for Quest-class targets, or gate to PC-only quality tiers."))
    if "com.unity.xr.interaction.toolkit" in deps and "com.unity.xr.openxr" not in deps:
        findings.append(Finding(
            "XR202", "WARN", path, 1,
            "XRI present without com.unity.xr.openxr. Vendor-specific backends "
            "limit portability.",
            "Add the OpenXR package as the runtime backend."))


# ------------------------------------------------------------- JS/TS checks

RE_XR_SIGNAL = re.compile(r"navigator\.xr|isSessionSupported|renderer\.xr|XRButton|VRButton")
RE_RAF = re.compile(r"\brequestAnimationFrame\s*\(")


def check_js(path, text, findings):
    if not RE_XR_SIGNAL.search(text):
        return
    for m in RE_RAF.finditer(text):
        # session.requestAnimationFrame is the correct in-session call.
        prefix = text[max(0, m.start() - 40):m.start()]
        if re.search(r"(session|xrSession|glSession)\s*\.\s*$", prefix):
            continue
        findings.append(Finding(
            "XR301", "BLOCK", path, line_of(text, m.start()),
            "window.requestAnimationFrame in a WebXR file. It does not fire "
            "during an immersive session: the scene freezes when XR starts.",
            "renderer.setAnimationLoop(fn) in Three.js, or "
            "xrSession.requestAnimationFrame inside the session."))


# ------------------------------------------------------------------- main

def scan(root):
    findings = []
    cs_texts = []
    for path in iter_files(root):
        ext = os.path.splitext(path)[1].lower()
        base = os.path.basename(path)
        if ext in CS_EXT:
            text = read_text(path)
            if text is None:
                continue
            cs_texts.append((path, text))
            check_csharp(path, text, findings)
        elif ext in YAML_EXT:
            text = read_text(path)
            if text is not None:
                check_unity_yaml(path, text, findings)
        elif base == "manifest.json" and os.path.basename(
                os.path.dirname(path)) == "Packages":
            text = read_text(path)
            if text is not None:
                check_manifest(path, text, findings)
        elif ext in JS_EXT:
            text = read_text(path)
            if text is not None:
                check_js(path, text, findings)
    check_csharp_project_level(cs_texts, findings)
    return findings


def main():
    ap = argparse.ArgumentParser(description="Static checks for XR anti-patterns.")
    ap.add_argument("path", help="Project root to scan")
    ap.add_argument("--json", action="store_true", help="Machine-readable output")
    ap.add_argument("--strict", action="store_true", help="Exit 1 on WARN too")
    args = ap.parse_args()

    if not os.path.isdir(args.path):
        print(f"error: not a directory: {args.path}", file=sys.stderr)
        return 2

    findings = scan(args.path)
    blocks = [f for f in findings if f.severity == "BLOCK"]
    warns = [f for f in findings if f.severity == "WARN"]

    if args.json:
        print(json.dumps({
            "block_count": len(blocks), "warn_count": len(warns),
            "findings": [f.to_dict() for f in findings],
        }, indent=2))
    else:
        for f in sorted(findings, key=lambda x: (x.severity != "BLOCK", x.path, x.line)):
            rel = os.path.relpath(f.path, args.path)
            print(f"[{f.severity}] {f.check_id} {rel}:{f.line}")
            print(f"    {f.message}")
            print(f"    fix: {f.fix}")
        print(f"\n{len(blocks)} BLOCK, {len(warns)} WARN "
              f"({'FAIL' if blocks or (args.strict and warns) else 'PASS'})")
        if not findings:
            print("Clean. Reminder: this proves the absence of detectable "
                  "classics, not comfort or framerate. Profile on device.")

    if blocks or (args.strict and warns):
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
