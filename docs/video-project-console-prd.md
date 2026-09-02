# Video Project Console PRD

> Status: draft for implementation
>
> Product name: Video Project Console (working title)
>
> Scope: local, single-user, file-system-first video engineering console

## 1. Product Decision

Build the product around `video_spec_gen`, not inside MuseDock.

The console turns the existing video workflow into a visible, recoverable project experience. The user works in one local UI and can see source material, storyboard, Codex activity, generated files, validation, rendering progress, and versioned output.

The console does not replace Codex, the existing skills, or HyperFrames:

```text
Video Project Console     project UI, task control, visibility, recovery
Codex runtime             planning, tool use, file edits, command execution
Video skills              video specification and rendering workflow knowledge
HyperFrames / FFmpeg      preview, checking, rendering, media inspection
File system               the sole source of truth for projects and task state
```

MuseDock is a product-experience reference only. Version 1 must not depend on its database, workflow engine, or source tree.

## 2. Problem Statement

The current workflow can produce editable video artifacts, but its state is distributed across prompts, Markdown, source material, analysis JSON, HyperFrames files, logs, and render outputs. The user cannot use one interface to answer these questions quickly:

- Which project is currently running, and what is Codex doing?
- Which source assets and analysis results were used for this version?
- What is the current storyboard and what files implement each scene?
- Did validation or rendering fail, and can the task continue from a checkpoint?
- Which output version corresponds to which specification and edit?

The product must make those answers visible without replacing the file-based workflow with a database-centric system.

## 3. Users And Primary Scenarios

### Primary user

A single local video creator who uses Codex and the repository skills to create and iterate on video projects. The user values inspectability and recoverability over collaborative editing or cloud synchronization.

### Primary scenarios

1. Create a project, register locally available source assets, describe a video goal in the chat, and start a Codex run.
2. Watch the project progress from source analysis to storyboard, project generation, validation, rendering, and output inspection.
3. Open the storyboard, generated specification, HyperFrames files, logs, and preview without leaving the console.
4. Change a requirement, start a new run, and compare its artifacts and output with the previous version.
5. Resume an interrupted run from its latest valid checkpoint instead of starting the entire workflow again.

## 4. Goals

- Provide a local browser UI for video-project creation, inspection, and task control.
- Keep project state entirely in readable files under this repository.
- Let a project chat start a real Codex runtime in that project's workspace.
- Make skill-driven work observable: stages, logs, edits, artifacts, and failures.
- Preserve editable inputs and generated engineering artifacts, not only the final MP4.
- Reuse the repository's directory boundaries:
  - `assets/<film-slug>/` for user-provided source material;
  - `projects/<project-slug>/` for editable project artifacts;
  - `outputs/<project-slug>/` for versioned playable outputs.
- Ensure new renders never overwrite existing outputs.

## 5. Non-Goals For Version 1

- Multi-user collaboration, accounts, permissions, remote sync, or cloud hosting.
- A relational database, vector store, queue service, or external task scheduler.
- A full non-linear editor: frame-accurate drag editing, multi-track media timeline, keyframe authoring, or direct waveform editing.
- Uploading large video files through the browser. Source files are registered from the local workspace.
- Replacing Codex with MuseDock's existing prompt pipeline or replacing HyperFrames with a new renderer.
- Publishing or distributing videos.

## 6. Product Principles

1. **Files are the source of truth.** The UI is an editor and viewer over files, never the only holder of state.
2. **Every run is inspectable.** A user can trace an output to the run, requirement, spec, assets, and code that produced it.
3. **Every write is recoverable.** A stopped process leaves an event trail and checkpoint instead of an opaque failed job.
4. **Codex executes; the console observes and controls.** Business logic and skill knowledge remain in the runtime and project files.
5. **Local media stays local.** The console references approved source paths and generates local derivatives only when necessary for preview or inspection.
6. **Start narrow.** The first release is an engineering console, not a complete desktop video editor.

## 7. System Boundary And Architecture

```text
Browser UI (localhost)
  - project dashboard, chat, storyboard, files, logs, preview, output history
                 |
Local Console API
  - project discovery, path validation, process control, SSE, file reads
                 |
Project Runner
  - starts/resumes Codex, tracks a run, converts process output to events
                 |
Codex session in projects/<project-slug>/
  - loads the configured video skills, edits files, runs analysis/check/render
                 |
File system
  - assets/, projects/, outputs/ and append-only run records
```

The browser must never directly browse arbitrary disk paths. The local API allows reads and commands only within the repository's approved `assets`, `projects`, and `outputs` roots.

## 8. Canonical Workspace Contract

### 8.0 Source film and video project identities

The repository distinguishes the source film from each independently managed video deliverable:

- `film-slug` identifies shared source material under `assets/<film-slug>/`.
- `project-slug` identifies one deliverable with its own brief, spec, composition, runs, QA, and output versions.
- Different video types, platforms, durations, narration strategies, or editorial goals use different top-level `project-slug` directories.
- `variant_id` describes a candidate or experiment inside a batch; it does not create a nested project directory by default.
- A project manifest links the two identities with `source_film_slug`.

### 8.1 Directory layout

```text
assets/<film-slug>/
  source/                         original user-provided media and references

projects/<project-slug>/
  project.json                    project manifest and UI index
  brief.md                        user intent and current requirement
  edit-plan.md                    editable editorial plan
  video-spec.md                   renderable video specification
  storyboard.json                 normalized storyboard for the UI
  codex-session.json              runtime session reference; no secrets
  hyperframes/                    editable composition project
  analysis/                       generated analysis and scene decisions
  runs/<run-id>/
    run.json                       immutable run metadata and current status
    events.jsonl                   append-only structured event log
    artifacts.json                 artifact index for this run
    checkpoints/latest.json        latest resumable stage and command context
    logs/codex.log                 raw runner output
    logs/render.log                renderer output

outputs/<project-slug>/
  render-v001.mp4
  render-v002.mp4
  qa-v001.json
  qa-v001-contact-sheet.jpg
```

`assets/<film-slug>/` contains inputs only. Generated specifications, project files, previews, run state, and rendered outputs must never be written there.

The existing `videos/<film-slug>/` directory remains legacy material. New console projects use top-level `projects/<project-slug>/` and `outputs/<project-slug>/` directories. Shared source material remains under `assets/<film-slug>/`; the project manifest records `source_film_slug`.

The former `projects/annual-meeting/high-energy-90s/` directory has been normalized to the top-level project `projects/annual-meeting-high-energy-90s/`. The migration preserved existing files and updated the project manifest, source path, edit plan, and BGM reference; no source media was copied into `assets/`.

### 8.2 Project manifest

`project.json` is the UI's compact index, not a replacement for the editable source files.

```json
{
  "schema_version": 1,
  "id": "annual-meeting-high-energy-90s",
  "source_film_slug": "annual-meeting",
  "video_type": "high-energy-clip",
  "title": "Annual Meeting High Energy 90s",
  "created_at": "2026-08-30T12:00:00+08:00",
  "updated_at": "2026-08-30T12:20:00+08:00",
  "status": "ready",
  "active_run_id": "run-20260830-120000",
  "skills": ["video-spec-builder-personal", "hyperframes"],
  "assets": [],
  "storyboard_path": "storyboard.json",
  "spec_path": "video-spec.md",
  "composition_path": "hyperframes/",
  "latest_output": "../../outputs/annual-meeting-high-energy-90s/render-v001.mp4"
}
```

The manifest may cache labels and paths for fast project listing. Any content that matters creatively remains in its own editable file.

### 8.3 Run record and event format

Each user request that launches work creates a new `runs/<run-id>/` directory. A run never mutates another run's event history.

`events.jsonl` uses one JSON object per line:

```json
{"seq":17,"time":"2026-08-30T12:04:12+08:00","type":"stage.started","stage":"render","message":"Starting HyperFrames render"}
{"seq":18,"time":"2026-08-30T12:05:03+08:00","type":"progress","stage":"render","percent":42,"message":"Rendering frame 840/2000"}
{"seq":19,"time":"2026-08-30T12:07:55+08:00","type":"artifact.created","path":"../../outputs/annual-meeting-high-energy-90s/render-v001.mp4","kind":"video"}
```

Required event types:

- `run.created`, `run.started`, `run.paused`, `run.completed`, `run.failed`, `run.cancelled`;
- `stage.started`, `stage.completed`, `stage.failed`;
- `progress`;
- `log`;
- `artifact.created`, `artifact.updated`;
- `checkpoint.saved`;
- `user.input_required`.

### 8.4 State and recovery rules

- Status writes use temporary-file-plus-rename semantics to prevent partial JSON corruption.
- Events are append-only. The UI may derive live state by replaying them.
- Only one active run may write to a project at a time; the runner creates a project-scoped lock.
- At startup, the API scans `projects/*/runs/*/run.json`. A run with a stale process record is marked `interrupted`, never silently `failed` or `completed`.
- Resume creates a new run that references the previous run and starts from its latest checkpoint. The old run remains immutable.
- Render output names are selected by scanning existing `render-vNNN.mp4` files and incrementing the version number.

## 9. Functional Requirements

### 9.1 Project management

- The home view lists each top-level directory under `projects/` as an independently managed video project with title, source film, status, latest activity, active stage, and latest output.
- The user can create a project from a kebab-case slug and title.
- Project creation produces the canonical directory structure and a valid `project.json`.
- The user can archive a project only through an explicit UI action; version 1 does not permanently delete projects or source material from the UI.
- A project page shows asset count, current brief/spec status, active run, last checkpoint, and output history.

### 9.2 Source asset registration

- The user can choose an existing file or directory under `assets/<film-slug>/` and register it in the project manifest.
- The console records relative path, media type, byte size, duration/resolution when available, source label, and optional notes.
- The API uses `ffprobe` or equivalent local inspection for video/audio metadata; it does not load the entire media file into memory.
- The console may generate thumbnails, contact sheets, or proxy media under `projects/<project-slug>/`, never beside the source asset.
- Version 1 does not accept browser uploads for video material.

### 9.3 Project chat and Codex execution

- Every project has a chat panel. A user message is stored as a run input and displayed in its conversation history.
- Sending a message creates a Codex-backed run or attaches to the current waiting run after explicit user confirmation.
- The runner launches Codex in the target project workspace and makes the configured skills available.
- The runner provides Codex with the project manifest, approved asset paths, prior relevant artifacts, and the latest checkpoint.
- Codex output is captured as raw logs and normalized events. It must not be treated as successful merely because a process exits; expected artifacts and check results determine completion.
- The UI supports Cancel. Cancel stops the current child process, writes `run.cancelled`, and preserves the checkpoint and logs.
- The console does not expose or persist provider API secrets in project files. Credential handling stays in the local runtime environment.

### 9.4 Storyboard and engineering artifacts

- The project page provides a storyboard view with ordered scenes, purpose, duration, source references, narration/captions, visual treatment, and implementation status.
- The storyboard view reads `storyboard.json` and supports opening the linked editable source file. Version 1 need not provide drag-and-drop scene rearrangement.
- The file panel shows editable and generated project artifacts with type, path, modified time, originating run, and preview action.
- The user can open Markdown, JSON, HTML, text logs, images, audio, and video from the console through sandboxed local routes.
- The UI visibly differentiates source material, editable project files, generated run artifacts, and versioned outputs.

### 9.5 Checks, preview, render, and output

- The user can start `check`, `preview`, `render`, and QA actions from the project page when the required project files exist.
- A preview action reuses the single managed HyperFrames preview lifecycle for that project and exposes its local URL in the UI.
- Render events display stage, progress when available, elapsed time, warnings, command result, and output version path.
- The output panel lists every `render-vNNN.mp4` with linked run, render time, file size, and QA artifacts.
- The UI plays output video through a range-capable local route rather than embedding the source media directly.

### 9.6 Logs, errors, and input requests

- The run panel exposes a chronological event stream and raw log viewer.
- Errors identify the failed stage, command or artifact where possible, and the suggested recovery action.
- When Codex needs a decision, it emits `user.input_required`; the UI presents the request in the chat and leaves the run in `waiting_for_input`.
- The user can retry a failed stage from the latest checkpoint. Retrying never deletes the prior failed run.

## 10. User Interface Requirements

### 10.1 Home: project browser

The first screen is the project browser, not a marketing page. It provides a dense list/grid of projects and a clear new-project command. Each row shows status, active task, latest output thumbnail where available, and last modified time.

### 10.2 Project workspace

The project workspace has four stable areas:

```text
Left:     project identity, asset list, file tree
Center:   chat and active task/event stream
Right:    storyboard / artifacts / logs tabs
Bottom:   preview player, render progress, output versions
```

On smaller screens, these become switchable views rather than overlapping panels. The player, file tree, and progress controls keep stable dimensions while work is running.

### 10.3 Essential visible states

- Idle: project has no active run and shows next meaningful actions.
- Planning: Codex is inspecting assets or writing the brief/spec.
- Building: Codex is editing project files or the HyperFrames composition.
- Checking: validation is running.
- Rendering: progress, elapsed time, and cancel control are visible.
- Waiting: Codex requires user input.
- Interrupted/failed: checkpoint and retry action are visible.
- Completed: latest output and the originating run are visible.

### 10.4 MuseDock UI Reference

MuseDock's existing creative UI is the reference for information architecture and interaction patterns, not a code dependency. The console should borrow its strongest product decisions while adapting them to file-backed Codex runs.

| MuseDock pattern | Console adaptation |
| --- | --- |
| `CreativeEditorPage`: project title, settings, and return action in a compact header | Keep a stable project header with film slug, active run, settings, and a clear return-to-projects action. |
| `CreativeWorkflowStepper`: horizontal stage rail with active, completed, queued, and failed states | Use a data-driven Codex stage rail. Stages come from the run record and may be `analysis`, `storyboard`, `spec`, `composition`, `check`, `render`, or `inspect`; they must not be hard-coded to MuseDock's ten-stage image workflow. |
| `CreativeProgressPanel`: current message, percentage, and expandable event details | Show one concise current-progress block, then reveal event sequence, command, elapsed time, and checkpoint details on demand. |
| `CreativeTaskDetail`: summary, progress, assets, warnings, retry, and preview in one task view | Use the same progressive disclosure: project summary, current run, source assets, storyboard, artifacts, warnings/recovery, and output preview. |
| `CreativeVideoPreview`: dark framed video player with native controls | Make the preview/output player a first-class workspace area with metadata and the originating run beside it. |

The visual language should stay quiet and work-focused: restrained surfaces, clear status color, compact cards for repeated items, and responsive overflow for the stage rail. The console must not copy MuseDock branding, fixed stage assumptions, or its image-first upload behavior.

### 10.5 Console-specific interaction rules

- The chat, run status, and preview remain visible together on desktop so the user can connect an instruction to its result.
- Selecting a storyboard scene filters the artifact list and highlights the linked composition/source files.
- Selecting an artifact shows its path, originating run, modification time, and a preview or text viewer when supported.
- The active run always exposes Cancel, and interrupted or failed runs always expose Resume/Retry with the checkpoint stage.
- Progress is event-driven through SSE. The UI may refresh project metadata after events, but must not rely on full-directory polling for live state.
- Every status has a text label in addition to color, so failed, waiting, and active states remain understandable without visual color cues.

## 11. Local API Requirements

The console backend is a local-only API and SSE service. It may be implemented in the repository's most practical runtime, but must expose these capabilities:

- discover, create, read, and update projects;
- register and inspect approved local assets;
- list and read sandboxed artifacts;
- start, cancel, resume, and inspect runs;
- stream run events through SSE;
- serve preview and output media with range requests;
- invoke the local Codex runner and HyperFrames commands.

The API must bind to localhost by default. It must reject absolute paths, traversal sequences, and symbolic-link escapes outside the approved workspace roots.

## 12. Acceptance Criteria For Version 1

1. A user can create `projects/<project-slug>/` from the console without manually creating project metadata.
2. A user can register a local source video from `assets/<film-slug>/` and see its metadata in the project.
3. A project chat message starts a Codex-backed run in the correct workspace with the configured skills.
4. During a run, the UI receives live stage, log, progress, and artifact events without polling the entire project directory.
5. The user can inspect the current storyboard, `video-spec.md`, composition files, and raw run logs from the project page.
6. A render creates the next available `outputs/<project-slug>/render-vNNN.mp4` and never overwrites a previous output.
7. A stopped run retains `events.jsonl`, logs, and a checkpoint; after restart, the project displays it as interrupted and offers a resume path.
8. No project state requires a database or remote service to open and inspect.
9. The legacy `videos/` directory is not used as the default destination for new projects or renders.
10. The UI does not expose arbitrary disk files or secrets outside the approved workspace roots.

## 13. Delivery Sequence

### Milestone 1: File-backed project shell

- Create the local API and browser UI shell.
- Bootstrap the frontend with React + Vite, Tailwind CSS, and shadcn/ui. Use the official shadcn/ui components for common controls and keep the console browser-first.
- Implement project discovery/creation and the canonical manifest.
- Implement asset registration, file tree, Markdown/JSON viewers, and local media playback.

### Milestone 2: Observable Codex runs

- Implement the Codex runner interface, run directories, JSONL events, logs, checkpoints, cancellation, and SSE.
- Add project chat and live task status.

### Milestone 3: Video engineering views

- Generate/read `storyboard.json`.
- Add artifact provenance, validation results, HyperFrames preview control, and output history.

### Milestone 4: Controlled editing improvements

- Add structured storyboard edits and rerun from selected checkpoints.
- Evaluate a lightweight scene/clip timeline only after the file contract is stable. This remains outside Version 1.

## 14. Open Implementation Decisions

- The frontend stack is fixed as React + Vite + Tailwind CSS + shadcn/ui. Select the local server runtime based on the repository's existing tooling and the easiest reliable Codex process integration; the product contract must stay independent of that backend choice.
- Define the exact Codex runner command/session protocol during Milestone 2; the runner must expose session ID, workspace, child-process status, and normalized events.
- Define the initial `storyboard.json` schema by mapping existing analysis outputs and `video-spec.md` into one UI-friendly structure.
- Decide whether generated preview proxies are always created or created only when source formats cannot be played by the local browser.

## 15. Explicit Decisions

- The product starts as a local web application. A desktop wrapper is optional later, not a Version 1 dependency.
- The file system, not a database, is authoritative.
- `projects/<project-slug>/project.json` is the compact project index.
- Each Codex request produces an immutable run directory and append-only event history.
- Codex and the two existing skills are the execution engine; the console does not reimplement their domain logic.
- MuseDock is not a runtime dependency for Version 1.
- The shared frontend component and style baseline is React + Vite + Tailwind CSS + shadcn/ui; Electron is a later wrapper around the same build.

## 16. Frontend UI And Style System

The console adopts MuseDock's information architecture while using a small, explicit frontend design system.

### 16.1 Technology baseline

- React + Vite for the browser UI.
- Tailwind CSS utility classes for layout, spacing, responsive behavior, and ordinary visual states.
- shadcn/ui as the default component system for buttons, inputs, selects, dialogs, tabs, badges, tooltips, tables, checkboxes, switches, and progress indicators.
- Lucide icons through the project's installed icon package for icon-only actions.
- Electron is a later packaging target for the same built frontend; it must not create a second UI implementation.

### 16.2 Component and CSS rules

- Reuse an existing shadcn/ui component before creating a new generic control.
- When a new component is required, keep its API and source boundary clear and retain the underlying shadcn/ui behavior where practical.
- Do not grow a page-wide global stylesheet for one screen. New styles belong in Tailwind classes or a narrowly scoped component stylesheet.
- A complex video editor or preview surface may retain local CSS for canvas, timeline, media, and rendering-specific layout. Common controls inside it still use shadcn/ui.
- Migrate legacy handwritten CSS incrementally. A migration must remove obsolete selectors as each page is converted; a complete one-shot rewrite is not required.
- All interactive controls must have visible focus states, keyboard access, and text labels or tooltips. Status must not rely on color alone.
- Use stable dimensions for the player, stage rail, progress bars, file rows, and icon buttons so live events cannot cause layout shifts.

### 16.3 Visual direction

- Work-focused and dense, with clear hierarchy rather than marketing-style hero sections or decorative card stacks.
- Project identity and active run status are visible in the first viewport.
- The preview player is a real media surface, not a decorative placeholder.
- Repeated artifacts, scenes, and runs may use compact cards or rows; avoid nesting cards inside cards.
- Responsive layouts turn the desktop workspace's panels into tabs or stacked regions on narrow screens without overlapping text or controls.

### 16.4 UI acceptance checks

- The home page, project header, progress panel, stage rail, artifact list, retry controls, and preview player use the shared tokens and component primitives.
- A new common control cannot introduce an ad-hoc visual language when an equivalent shadcn/ui component exists.
- The console remains usable at desktop and mobile widths, with no clipped labels, overlapping panels, or unstable media dimensions during a running task.
