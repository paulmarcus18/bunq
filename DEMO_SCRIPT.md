# deBunq · demo video script (3 min target)

A minute-by-minute storyboard for the 2–4 minute Devpost video. Designed to land **all five rubric criteria** without ever feeling like a feature list. Optimised for **screen recording the iPhone** (or a desktop browser sized to phone width if the iPhone tunnel isn't ready by recording time).

If you only have time to record one take, this is it.

---

## Total: 3:00

| Block | Time | Visual | Voiceover |
|---|---|---|---|
| **A. Hook** | 0:00–0:15 | Title card → cut to a real WhatsApp voice-note screenshot | *"Last year, Dutch banks lost over a hundred million euros to scams users authorised themselves. Fake invoices. 'Hi mom' voice notes. Phishing emails with a swapped IBAN. None of it gets refunded — because the user pressed pay. So the only place to stop the scam is **before** the user pays."* |
| **B. Setup** | 0:15–0:25 | Cut to deBunq inbox screen on iPhone | *"Meet deBunq — the scam shield inside the bunq app. Forward a voice note, snap a bill, paste a suspicious email. Multimodal AI scores it before bunq pays anyone."* |
| **C. Scenario 1 — voice scam** | 0:25–1:05 | Tap **Forward voice note** → upload `hi-mom.m4a` → tap analyse | *"Here's a voice note someone forwarded me. 'Hi mom, this is your son, I lost my phone, please send 450 euros urgent, don't tell anyone.' Classic family-emergency scam."* |
|  |  | Indigo transcript card appears, then rose ring `11/100` | *"deBunq transcribes locally — the audio never leaves my phone — then Claude scores it. Eleven out of a hundred. Blocked."* |
|  |  | Scroll to red-flag list | *"Family impersonation. Urgency. Secrecy request. No payment reference. Five concrete reasons, not just a flag."* |
|  |  | Pan to the bottom — bunq pay button greyed out | *"And the bunq API call? It doesn't even leave the server. The block is real."* |
| **D. Scenario 2 — phishing email** | 1:05–1:35 | Hit clear, paste the fake KPN email, tap analyse | *"Same engine on a phishing email. Spoofed sender, two-hour ultimatum, bit-ly link, brand new IBAN."* |
|  |  | Rose ring `13/100` + four sub-score bars all red | *"Thirteen. Blocked again. Notice the four sub-scores: issuer authenticity bottoms out, urgency pressure bottoms out. The score isn't a vibe — it's math."* |
| **E. Scenario 3 — legit invoice** | 1:35–2:25 | Hit clear, tap **Snap a bill** → take photo of a real AON invoice on a second screen | *"Now the moment that matters. Same app, real invoice. I take a photo of my actual AON Student Insurance bill."* |
|  |  | Green ring `96/100` with five ✓ green ticks | *"Ninety-six out of a hundred. Safe. Five green ticks — known issuer, valid IBAN format, complete payment details, no urgency, normal corporate boilerplate."* |
|  |  | Scroll to the **blue bunq pre-flight card** | *"Here's the bunq pre-flight. It shows the exact endpoint deBunq is about to hit — `POST /v1/user/.../monetary-account/.../payment`. Sandbox badge, real API. Nothing mocked."* |
|  |  | Tap **Pay from Joint** | *"I tap pay."* |
|  |  | Green receipt card with bunq id | *"And there's the bunq receipt. Real bunq id three-eight-three-seven-four-nine-two. From my Joint account. Reference preserved. TrustScore reminder. The whole loop closed."* |
| **F. Stack flash** | 2:25–2:45 | Brief montage: terminal showing `uvicorn` log, `boto3` invoking Bedrock, bunq response JSON | *"Under the hood — Claude Sonnet 4.5 on AWS Bedrock. Audio via faster-whisper running locally. bunq calls RSA-signed against the public sandbox API. IBAN mod-97 checked before any call leaves the box. All live."* |
| **G. Close** | 2:45–3:00 | Title card again with a QR code to the live demo URL (or just the title) | *"deBunq. The scam shield, built into the bank where the money lives. Built solo for bunq Hackathon 7.0."* |

---

## Recording tips

- **One take, no editing.** Practice it three times silent first to nail the clicks. Then record once with voice.
- **Phone mirrored to your laptop** if possible (QuickTime on macOS, scrcpy on Linux). Means you can record screen + voice cleanly, no tripod-shake.
- **Voiceover in a quiet room.** A 30-euro USB mic beats your laptop mic by miles, but even built-in is fine if you're not in a café.
- **Don't say "as you can see" or "right now we're".** Replace with present-tense action verbs: *"I tap…", "deBunq returns…", "Notice…"*.
- **Sandbox top-up first.** Before recording, run `curl -X POST http://localhost:8000/bunq/sandbox-topup?amount=200` so the source account has money.
- **Fresh references for the AON scenario.** bunq deduplicates by reference; if you've already paid `497186-04699219`, change to `497186-04699219-VID1`.
- **Have all three demo inputs in a notes file** that you can paste from instantly:
  1. The fake KPN phishing text (in `demo-assets/`).
  2. A pre-recorded `hi-mom.m4a` voice note.
  3. A real AON / TU/e photo on a second device or in your Photos.

---

## Backup script if a scenario breaks live

If the voice scam analysis hangs or Bedrock errors:

> *"Network blip — let me cut to the next scenario. The scam scenarios are deterministic; here's the receipt from when I ran this an hour ago."*

Then show a screenshot of a successful prior run as proof, and continue. Judges will *not* hold a temporary backend hiccup against you if you keep the narrative moving. They *will* hold it against you if you panic.

---

## After recording

1. Trim head/tail silence with QuickTime / Kdenlive / DaVinci Resolve (free).
2. Export at 1080p, MP4, ≤ 200 MB.
3. Upload to **YouTube as Unlisted**. Copy the link.
4. Paste the link in the Devpost submission's "Demo video" field.
5. Done.
