# 🎀 Puromputan — User Manual

---

## What is Puromputan?

**A companion for your AI chats that turns the scenes you talk about into illustrations, automatically.**
When the AI describes "the scene right now" during a conversation or roleplay, Puromputan generates that scene with Stable Diffusion (Forge) — so you can read along and see it.

It's simple: have the AI write its prompt in the special format (the "📋 Rules"), and a browser userscript detects it → Puromputan receives it and sends it to SD for automatic generation. **No more "ask the AI for a prompt → copy → paste into SD".** Stay in the chat, and the scenes keep turning into pictures.

> It started from the idea "what if I could also output the scenes of my AI chat as images" — an AI-chat support tool. Currently works with Claude, ChatGPT, Gemini, Grok, Copilot and more.

---

## Starting the App

1. Double-click `起動する.bat`
2. Wait for the port indicator to show `🎀 Port 787x`
3. Make sure Stable Diffusion (Forge) is also running. The dot turns 🟢 when connected.

---

## Tampermonkey Scripts

Two browser scripts are needed.

### sd_monitor.user.js (required)
Monitors AI chat pages and auto-detects/sends prompts.

**Supported services:** Claude, ChatGPT, Gemini, Grok, Copilot

> 💡 **Using a local chat UI like OpenWebUI?** Add your own URL to the `@match` lines at the top of `sd_monitor.user.js` (e.g. `// @match http://localhost:8080/*`).

**Install:** Open Tampermonkey → New script → Paste the contents of `sd_monitor.user.js` → Save.

### forge_sync.user.js (optional)
Connects the Forge page and Puromputan in both directions. After installing, buttons appear at the bottom-right of the Forge page.

- **📤 Send settings** … Sync Forge generation settings (Steps, CFG, resolution, sampler) to Puromputan with one click
- **📥 Pull prompt** … Fill Forge's prompt fields with the positive/negative Puromputan received, with one click
- **🪄 Auto-fill** … With the toggle ON, every new prompt is automatically filled into Forge's fields (default ON)

---

## AI Prompt Rules

Ask the AI to format prompts using special markers.  
Press the **「📋 お約束」button** to copy the rules to your clipboard and paste them into the AI chat.

### Format

Positive prompt: starts with 🔴, ends with 🟥  
Negative prompt: starts with 🔵, ends with 🟦

```
🔴
masterpiece, best quality, 1girl, ...
🟥

🔵
worst quality, low quality, bad anatomy, ...
🟦
```

---

## Interface Overview

![Puromputan main window](docs/img/screenshot_main.png)

### Status Card (top-right)
| Display | Meaning |
|---|---|
| ✓ SD connected (green) | Connected to SD |
| ○ SD offline (red) | SD not found (check it's running / URL) |
| ⚡ Auto | Generates immediately on receipt |
| 👀 Manual | Waits for you to press Generate |
| ✨ Generating (pulsing) | A picture is being made — the chip glows softly |
| Timestamps | P = pos received, N = neg received, ✨ = last generated |

### Pos / Neg Boxes

The small pill next to each field shows its state:

| Pill | Meaning |
|---|---|
| ○ Waiting (gray) | Nothing yet |
| ✓ Received (green/red) | A prompt arrived (appears the moment it arrives) |
| ✓ Manual | You typed or edited the content yourself |
| ✓ Generated (purple) | This content has been turned into a picture (a new arrival resets it to Received) |

The fields are fully editable — see "Manual Input" below.

### Preview & History

- Switch the preview size with **S / M / L**. Press **Hide** to hide the picture, history and filename all at once (quick privacy 🙈)
- The strip at the bottom is the history carousel. Use **‹ ›** to step one thumbnail at a time; click one to view it large
- When generation finishes, **the pink selection frame automatically moves to the newest picture**

---

## ✍️ Manual Input

The pos/neg fields accept **direct input** too!

- Type or paste into a field → the Generate button lights up → press it
- **Tweaking a received prompt works as-is** (the pill switches to "Manual" when you edit)
- If the purple spice text is still displayed in the field, it is automatically removed the moment you start editing (prevents double-spicing — spices are still merged in at generation time)

---

## ✨ Pos Spice

Automatically appends extra text to the positive prompt at generation time.

1. Open ⚙️ Settings → Fill in Spice slots 1–9 → Save
2. Click the numbered pill buttons (1–9) on the main screen to toggle ON (purple)
3. Multiple spices can be active — they're appended with commas

---

## 💪 Neg Boost

Appends anatomical correction text (hands, fingers, feet) to the negative prompt.  
Toggle the checkbox next to "💪 ネガ補強" on the right panel.  
Edit the boost template in ⚙️ Settings.

---

## Generation Modes

| Mode | Behavior |
|---|---|
| ⚡ Auto | Generates immediately when pos+neg arrive. Pos-only waits 5s then generates. |
| 👀 Manual | Prompts are received but generation waits for the button press. |

---

## 📌 Mini Mode

Press the **Mini** button (top-right) to transform into a small polaroid-style window. Park it next to your chat and watch the pictures arrive while you talk.

![Mini mode (polaroid style)](docs/img/screenshot_mini.png)

- Always on top, picture first (title bar and panels are hidden)
- Resize the window and the picture follows (position and size are remembered)
- Return with the ↗ button at the bottom-right

### Mini Lamps

| Lamp | Meaning |
|---|---|
| P / N blink rapidly, then stay lit | A new prompt just arrived! |
| GEN pulsing orange | Generating right now |
| GEN green check | Generation finished |
| P / N fade to a dim check | That delivery has been turned into a picture (they light up again on the next arrival) |

Note: Mini mode locks generation to Auto.

---

## Quality Presets

| Preset | Steps | Sampler |
|---|---|---|
| ⚡ Fast | 12 | Euler a |
| ✨ Normal | 28 | DPM++ 2M Karras |
| 💎 High Quality | 45 | DPM++ 2M Karras |
| 🔄 Forge Sync | From Forge | Same |

---

## ⚙️ Settings

Click the gear icon (top-right) to open.

| Setting | Description |
|---|---|
| SD Connection | Stable Diffusion URL (default: http://127.0.0.1:7860) |
| Forge | Import settings from Forge |
| Save Folder | Where generated images are saved |
| CFG / Width / Height | Generation parameters |
| Detection Markers | The emoji markers wrapping prompts |
| Spice Content 1–9 | Text for each spice slot |
| Neg Boost Template | Text appended when boost is enabled |

---

## Button Reference

| Button | Function |
|---|---|
| 🖼️ Open Image | Opens the last generated image |
| 📁 Open Folder | Opens the save folder in Explorer |
| 📖 Manual | Opens this manual in your browser |
| 📋 お約束 | Copies the AI prompt rules to clipboard |

---

## FAQ

**Q. Prompts aren't being received**  
→ Check that sd_monitor.user.js is installed and Puromputan is running.

**Q. SD won't connect**  
→ Make sure Stable Diffusion / Forge is running and the URL in Settings is correct.

**Q. Same prompt sent again — nothing happens**  
→ This is by design, to avoid duplicate auto-generations. An orange message says "Same prompt — skipped (button remakes it!)". **Press the Generate button to make as many as you like** (the seed is random every time, so each picture is different).

**Q. A new prompt arrived while generating**  
→ In Auto mode, the new prompt is queued and generation starts automatically when the current one finishes.

---

*Puromputan 🎀*
