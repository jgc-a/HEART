# Video Script — 60 seconds

> Format: voiceover + on-screen action. Cap at 60s total.
> Voice: warm, paused, Rosewood-fitting (Charlotte voice on ElevenLabs works).
> Recording: screen recording of the demo + cuts to the Telegram phone.

---

## Timeline

| t | Voiceover (English) | On screen |
|---|---|---|
| **0:00** | *"In 2030, you won't convince humans to choose your hotel."* | Hero card: cream background, serif "Agents are the new SEO." typewriting in |
| **0:04** | *"You'll convince their agents."* | Same card, line 2 fades in |
| **0:08** | *"Agents are the new SEO. And Rosewood is where agents bring their humans."* | Bronze underline appears under "Rosewood" |
| **0:14** | *"Today, hotels send you an app. By 2030, they send your Claude a plugin."* | Cut to `/install` page — HAP plugin sitting next to Google Drive, GitHub, Calendar in the marketplace mockup |
| **0:20** | *"One click installs it. A scope-bounded session opens for the length of your stay."* | Click animation on "Connect HAP to my Claude" button → "Installed" badge flips on |
| **0:26** | *"From there, your agent and ours speak HAP — Hospitality Agent Protocol."* | Cut to `/hap-console` — the three Phase pills animate green: PHASE 1 → 2 → 3 |
| **0:32** | *"Three phases: you authorize the scope, the agents negotiate within it, you confirm the outcome."* | A2AConversation panel — bubbles cascade from Guest Agent → HEART → Guest Agent |
| **0:38** | *"And they actually talk."* | Phone shot: Telegram group with both bots posting voice messages, audio waveform visible |
| **0:42** | *"Voice by ElevenLabs. Reasoning by Claude. Audit hash-chained on every step."* | Audit Log panel scrolling SHA-256 hashes in real time |
| **0:48** | *"At checkout, the plugin auto-disconnects. The hotel returns your memory to your agent. Nothing is kept."* | Cut to `/checkout` Telegram → invoice preview with Bleisure split → confirm → "🔌 Disconnected" appears on dashboard |
| **0:54** | *"This is the agentic era of hospitality. Open protocol. Reference implementation. Rosewood defines the category."* | Final card: cream, bronze underline. URL: `github.com/jgc-a/HEART` |
| **0:60** | *(silent — 1 second hold)* | "HAP" mark · "AISociety × Rosewood" small at the bottom |

## Word count check

Spoken segment runs ~150 words at 150 wpm = 60 seconds. Land it under 155.
Current count: 138 words across 11 lines. 18s of room for breath + transitions.

## Recording checklist

- [ ] Screen recording at 1920×1080, 30fps minimum
- [ ] Run the actual demo end-to-end before recording, so the dashboard already has live data
- [ ] Phone shot in landscape with good lighting
- [ ] Voiceover separate, ElevenLabs Charlotte voice (XB0fDUnXU5powFXDhCwa)
- [ ] Background: silence or a faint piano motif under -22dB
- [ ] Export H.264, 1080p, ≤50MB

## Voice generation snippet (ElevenLabs)

```bash
# Generates the full 60-second voiceover as a single MP3 you can drop into Premiere/CapCut
curl -X POST "https://api.elevenlabs.io/v1/text-to-speech/XB0fDUnXU5powFXDhCwa" \
  -H "xi-api-key: $ELEVENLABS_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "text": "In 2030, you won'\''t convince humans to choose your hotel. You'\''ll convince their agents. Agents are the new SEO — and Rosewood is where agents bring their humans. Today, hotels send you an app. By 2030, they send your Claude a plugin. One click installs it. A scope-bounded session opens for the length of your stay. From there, your agent and ours speak HAP — Hospitality Agent Protocol. Three phases: you authorize the scope, the agents negotiate within it, you confirm the outcome. And they actually talk. Voice by ElevenLabs. Reasoning by Claude. Audit hash-chained on every step. At checkout, the plugin auto-disconnects. The hotel returns your memory to your agent. Nothing is kept. This is the agentic era of hospitality. Open protocol. Reference implementation. Rosewood defines the category.",
    "model_id": "eleven_turbo_v2_5",
    "voice_settings": {"stability": 0.55, "similarity_boost": 0.75, "style": 0.30, "use_speaker_boost": true}
  }' --output voiceover.mp3
```
