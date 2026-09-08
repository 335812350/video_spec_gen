<img width="2172" height="724" alt="ChatGPT Image May 16, 2026, 10_46_58 PM" src="https://github.com/user-attachments/assets/7820d93e-84b6-4e09-904c-9567c6595c57" />

**English** · [中文](README.zh.md)

# video-spec-director

[![License: MIT](https://img.shields.io/badge/License-MIT-brightgreen)](LICENSE) ![Agent Agnostic](https://img.shields.io/badge/Agent-Agnostic-blueviolet) [![skills.sh Compatible](https://img.shields.io/badge/skills.sh-Compatible-brightgreen)](https://skills.sh)

> A skill that works like a video director. You say "I want to make a video," and it grills you with questions until your idea is a script you can actually shoot.

I built this skill after realizing the hard part of making a video isn't the rendering. It's figuring out what you actually want.

You've got a vague idea in your head: a product video, a short for social, a company intro. But it's fuzzy. The moment you try to build it, the details get you — how long each shot runs, what's on screen, what comes first and what comes later. You probably haven't pinned them all down, and you might not even be able to put them into words.

video-spec-director gets you through that part. Once enabled, tell your AI "I want to make a video" inside Codex, and it takes over the conversation. It listens to your brief the way a director would, then keeps asking: Who's this for? How long? What's the one line people should walk away with? Which shot carries the weight? Anywhere you go vague, or skip something, it stops and pushes you to fill it in.

A few rounds of that, and the fuzzy idea becomes a `video-spec.md`: a shot-by-shot script, timed to the second, every shot written out. Hand that to HyperFrames and it renders into a real video.

It won't shoot the video for you, and it won't invent the idea. It does one thing: push you, and stay with you, until the idea is something you can actually build.

## What it helps with

The problem it solves is "I have an idea but I can't explain it." A few situations where it earns its keep:

- You know the feeling you want but can't describe the actual picture. It refuses words like "premium" or "high-impact" and keeps after you until you can describe real shots and real motion.
- You have an idea but never thought parts of it through. Maybe you've got the opening and the ending but not the middle. Maybe it never crossed your mind that a section could use captions, or that visuals can move to the beat of the music. It brings those up.
- You have plenty of raw material but no order to it. A script, selling points, a pile of assets — it helps you cut that into individual shots and put them in sequence.

In the end it writes all of it into a script: what each shot shows, how it's presented, how long it holds, how it cuts to the next one.

There are two ways to use it. With no script yet, it talks you through the whole thing from scratch and produces a `video-spec.md`. With a script already there and just one thing to change, you tell it what you want different; it asks enough to be sure, makes the change, and checks whether it knocked anything else loose.

## The workflow

It's two skills working in sequence. video-spec-director sits upstream and turns your idea into a script. HyperFrames sits downstream and turns the script into video.

```
       You: "I want to make a video"
                │
                ▼
   ┌────────────────────────┐
   │ video-spec-director │ asks, breaks it into shots
   └────────────────────────┘
                │
                ▼
          video-spec.md           shot-by-shot script, timed
                │
                ▼   /hyperframes
   ┌────────────────────────┐
   │       HyperFrames      │   renders from the script
   └────────────────────────┘
                │
                ▼
          finished video
```

Before you start, install this skill and make sure HyperFrames is installed.

## Install

I mostly use this skill in **Codex**. That is the setup it works best in.

This skill is distributed from `coocaa_video/skills/video-spec-director/`. Install it, and make sure HyperFrames (the renderer, downstream) is also installed:

```bash
npx skills add heygen-com/hyperframes
```

Needs Node 22 or newer.

## Using it

### Making a video from scratch

Once it's installed, just talk to your AI in plain language inside Codex:

```
I want to make a 3-minute product demo, posting it on YouTube
```

It takes over and starts asking. You don't need to track its internal steps; it just talks with you. First it pins down the basics: who it's for, where it's going, how long, the core message. Then it takes stock of the material you have. Then it settles the style and pacing, picks a visual theme, and finally uses reference videos and counter-examples to calibrate.

It's a real conversation, not a form to fill in. Answer vaguely and it digs; miss something and it fills it in. When you're done, it writes out `video-spec.md`.
Source footage is shared under assets/<film-slug>/; each independent deliverable gets its own projects/<project-slug>/ and outputs/<project-slug>/, linked through source_film_slug in project.json.

### Changing a video you already have

If there's already a `video-spec.md` in the project, just say what you want:

```
Shot 3 is too fast, slow it down; swap the background music for something quieter
```

It checks what you're after, looks at whether the change touches other shots, then updates the script.

### Rendering it

Once the script is final, hand it to HyperFrames:

```
/hyperframes
```

> In Codex, besides triggering it by talking, you can also call `video-spec-director` directly.

## What HyperFrames can and can't do

Worth spelling this out, because it decides whether your script is worth the paper it's on.

HyperFrames renders video from HTML. That one fact is the root of everything it can and can't do. If HTML, CSS, and code can draw it, HyperFrames can turn it into video. If HTML can't draw it, HyperFrames can't either.

What it's **good at** is text and layout work: title animation, captions, word-by-word highlighting, page layout, transitions, charts, UI mockups, geometric animation. Anything you can draw with code, it handles cleanly.

What it **can't do** — know this before you write the script, because however good the script is, if HyperFrames can't render it, the work is wasted:

- It can't draw illustrations. Hand-drawn characters, painterly visuals, cartoon figures — it can't produce those, and writing code won't get you there. Code draws shapes and charts, not artwork.
- It can't generate live-action footage. A real filmed shot, a person performing — it can't conjure that out of nothing.
- It can't generate photorealistic images.
- It can generate a voiceover with AI (text-to-speech) in a pinch, but AI narration has an obvious machine tone. For real quality, record it yourself or hire someone.
- It won't compose background music for you.

The short version: HyperFrames is an **assembly** tool, not a **creation** tool. It takes the material you've prepared — video clips, images, voiceover, music — cuts and composites it, adds text and motion, and puts together a finished video. Assembly is its job.

So here's the thing worth remembering: how good the video looks comes down to the material you feed it. Good material and HyperFrames assembles it sharply. Weak material and HyperFrames can't save it. Video clips, images, voiceover, music — these are worth preparing carefully up front. They decide the quality, not HyperFrames.

## Visual themes

What a video looks like — colors, fonts, motion, transition style — is decided by a "theme." You either use one of HyperFrames' built-in presets, or write your own.

### The 8 HyperFrames presets

HyperFrames ships 8 themes. Name one and it's yours:

| Theme | Mood | Good for |
|---|---|---|
| Swiss Pulse | Precise, restrained, Swiss type | SaaS, data, dev tools, dashboards |
| Velvet Standard | Premium, timeless | Luxury, enterprise software, keynotes, investor decks |
| Deconstructed | Industrial, raw | Tech launches, security products, anything with a punk edge |
| Maximalist Type | Loud, kinetic | Big launches, milestone announcements, high-energy hype |
| Data Drift | Futuristic, immersive | AI products, ML platforms, frontier tech |
| Soft Signal | Intimate, warm | Wellness brands, personal stories, lifestyle products |
| Folk Frequency | Cultural, vivid | Consumer apps, food, community products |
| Shadow Cut | Dark, cinematic | Security products, dramatic reveals, serious storytelling |

Once you've picked one, write its name into `video-spec.md`.

### Writing your own

If none of the presets fit, write your own. HyperFrames has a few hard rules for custom themes, nothing complicated:

- A theme is a single `design.md` file, placed in the target project's `projects/<project-slug>/` working directory. HyperFrames resolves it within that project's working directory.
- The format is fixed. A block of YAML up top for the design variables: colors, fonts, corner radius, spacing, motion. Below it, a set of fixed sections describing the design rules in prose: Overview, Colors, Typography, Elevation, Components, Do's and Don'ts.
- If your theme uses a font HyperFrames doesn't ship with, put the font's `.woff2` files in the target project's working-directory `fonts/` folder yourself.

Drop a finished `design.md` into `projects/<project-slug>/` and the theme is live for that project.

## What's in this repo

```
video-spec-director/
├── SKILL.md                  the skill's main file — the AI reads this first
├── README.md                 English
├── README.zh.md              中文
├── LICENSE
├── references/               reference docs on questioning, shot breakdown, pacing — loaded as needed
│   ├── workflow-0-1.md
│   ├── workflow-iteration.md
│   ├── question-bank.md
│   ├── scene-breakdown.md
│   ├── components-catalog.md
│   ├── pacing-rules.md
│   ├── spec-rules.md
│   └── dialogue-style.md
├── templates/
│   └── video-spec-template.md    output template for video-spec.md
└── examples/
    └── video-spec-spacex.md      a complete video-spec example
```

## License

MIT
