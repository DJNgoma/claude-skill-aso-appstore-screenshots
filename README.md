# ASO App Store Screenshots

A Claude Code skill that generates high-converting App Store screenshots for your iOS app. It analyzes your codebase, identifies core benefits, and creates professional screenshot images using AI.

## What It Does

1. **Benefit Discovery** — Analyzes your app's codebase to identify the 3-5 core benefits that drive downloads
2. **Screenshot Pairing** — Reviews your simulator screenshots, rates them, and pairs each with the best benefit
3. **Generation** — Creates polished App Store screenshots in two layers: a deterministic Pillow scaffold (compose.py) plus an optional pop-out / breakout pass (enhance.py or OpenAI Image v2). The local-only path produces App Store-ready images with zero external dependencies; AI polish is opt-in.
4. **Showcase** — Generates a preview image with all screenshots side-by-side

## Installation

### 1. Add the skill to Claude Code

```bash
claude install-skill github.com/adamlyttleapps/claude-skill-aso-appstore-screenshots
```

### 2. Install Python dependencies

```bash
pip install Pillow
```

### 3. Font requirement

The skill uses **SF Pro Display Black** for headline text. On macOS, install it from [Apple's developer fonts](https://developer.apple.com/fonts/). The expected path is:

```
/Library/Fonts/SF-Pro-Display-Black.otf
```

### 4. Optional — OpenAI Image v2 for AI polish

The default generation path is local-only (compose.py + enhance.py, both Pillow). For AI-enhanced photorealistic device frames or generative breakouts, configure an OpenAI Image v2-capable tool (`gpt-image-2`). When unavailable the skill falls back to the local-only path automatically.

### 5. Optional — non-Latin script support

For headlines in Hangul, CJK, Cyrillic, Arabic, etc., compose.py auto-falls-back from SF Pro Display Black to a script-appropriate font that ships with macOS (Apple SD Gothic Neo Heavy for Hangul; PingFang Heavy for CJK). No setup required on macOS.

## Usage

From within your app's project directory, run:

```
/aso-appstore-screenshots
```

The skill will guide you through each phase interactively. Progress is saved to Claude Code's memory system, so you can resume across conversations.

## How It Works

### Scaffold → Enhance Pipeline

Rather than generating screenshots from scratch (which produces inconsistent results), the skill uses a layered approach:

1. **compose.py** creates a deterministic scaffold with exact text positioning, device frame, and your simulator screenshot composited inside. Auto-detects non-Latin scripts (Hangul, CJK, Cyrillic, Arabic, etc.) and switches fonts accordingly.
2. **enhance.py** (local) or **OpenAI Image v2** (optional, AI) adds the breakout pop-out polish — extracting a UI panel from the screenshot, scaling it up, and floating it over the device frame with a soft drop shadow.

The local path produces App Store-ready images with no external services. AI polish is opt-in.

### Output

Screenshots are saved to a `screenshots/` directory in your project:

```
screenshots/
  01-benefit-slug/          ← working versions
    scaffold.png            ← deterministic compose.py output
    v1.png, v2.png, v3.png  ← AI-enhanced versions
    v1-resized.png, ...     ← cropped to App Store dimensions
  final/                    ← approved screenshots, ready to upload
    01-benefit-slug.png
    02-benefit-slug.png
  showcase.png              ← preview image with all screenshots
```

The `final/` folder contains App Store-ready screenshots at exact Apple dimensions (default: 1290×2796px for iPhone 6.7").

## Files

| File | Purpose |
|------|---------|
| `SKILL.md` | The skill prompt — defines the multi-phase workflow |
| `compose.py` | Deterministic scaffold generator (Pillow-based) — supports non-Latin scripts via Unicode-range font fallback |
| `enhance.py` | Local breakout/pop-out enhancer (Pillow-based) — no external services |
| `generate_frame.py` | Generates the device frame template |
| `showcase.py` | Generates the side-by-side showcase image |
| `assets/device_frame.png` | Pre-rendered iPhone device frame template |

## License

MIT
