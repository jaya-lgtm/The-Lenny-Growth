# Demo Video Guide & Recording Script (2–3 Minutes)
## The Lenny Growth Assistant

This document provides a timed, camera-on recording script and screen walkthrough designed to fulfill **Deliverable 8** of the Forward Deployed Engineer Take-Home Assignment.

---

## 1. Video Recording Setup & Checklist

* **Target Length**: 2 minutes 30 seconds to 2 minutes 55 seconds (strictly $< 3$ minutes).
* **Format**: Camera enabled (picture-in-picture talking head in corner, e.g. via Loom, OBS, or QuickTime).
* **Audio**: Clear microphone without echo.
* **Pre-Recording State**:
  1. Docker containers running: `docker compose up -d`.
  2. Local Ollama running: `ollama serve` with `llama3.2:3b` pulled.
  3. Browser open to `http://localhost:5173` with a clean session.
  4. Second tab open to `http://localhost:8000/docs` (Swagger UI).
  5. Terminal open showing `docker compose ps` and `pytest tests/`.

---

## 2. Timed Talk Track & Screen Actions

### [0:00 – 0:30] Scene 1: Problem & FDE Discovery Framing
* **Camera Focus**: Speaker full-screen or prominent talking head.
* **Talk Track**:
  > *"Hi everyone, I'm presenting The Lenny Growth Assistant. Growth teams and product managers face a persistent challenge: Lenny's Podcast and Newsletter contain over 300 episodes of world-class wisdom, but turning that fragmented knowledge into actionable product deliverables usually requires hours of manual searching, complex prompt engineering, and leaves teams worried about LLM hallucinations.*
  > *As a Forward Deployed Engineer, my goal was to build a system that delivers grounded answers, structured artifacts, and executive-ready deliverables without the user ever needing to engineer a prompt or manage infrastructure."*

---

### [0:30 – 1:15] Scene 2: Live Product Tour & Evidence-Grounded Q&A
* **Screen Action**: Switch to browser at `http://localhost:5173`.
* **Action**:
  1. Point out the clean UI, independent conversation sessions in the sidebar, and the 7 specialized skill pills above the input box.
  2. Select the **"💬 Grounded Q&A"** mode pill.
  3. Submit: *"What are the three components of activation according to Lenny's guests?"*
* **Talk Track**:
  > *"Here is the application running locally on Docker. At the bottom, users have access to 7 dedicated growth skills. Let's ask a grounded product question about user activation.*
  > *Notice that every claim in the response is synthesized strictly from our indexed ChatPRD transcript corpus in PostgreSQL with pgvector. Below the answer, we have interactive citation cards detailing the guest name, episode title, match confidence score, and deep-linked YouTube timestamps so operators can verify the source in one click."*

---

### [1:15 – 1:50] Scene 3: Specialized Growth Skills & Sandboxed Artifact Viewer
* **Screen Action**:
  1. Click the **"📝 Ship 30 Essay"** mode pill.
  2. Click the starter prompt card or enter: *"Write a Ship 30 essay on why retention is the silent killer of startups."*
  3. Once generated, point out the **Artifact Card** and click **"Open in Viewer →"**.
  4. Show the side-by-side slide-over panel.
  5. Toggle to the **"Raw Source"** tab, then the **"Evidence & Citations"** tab.
  6. Click **"Copy"** (shows "Copied!" checkmark), then show the **"Download"** button.
* **Talk Track**:
  > *"Next, let's look at the Ship 30 for 30 content skill. Rather than a generic prompt, this skill encodes Dickie Bush and Nicolas Cole's core writing principles: an irresistible hook, three structured sub-arguments, selective bolding, and an actionable takeaway, falling strictly between 1,000 and 1,500 words.*
  > *Clicking 'Open in Viewer' slides out our Claude-style Artifact Viewer right beside the chat. We can inspect the formatted essay, view the raw source markdown, review the underlying episode quotes, copy it to our clipboard, or download it as a standalone file."*

---

### [1:50 – 2:25] Scene 4: Local Ollama Demonstration & Provider Resilience
* **Screen Action**:
  1. In the composer dropdown, show the provider menu: `mock`, `ollama:llama3.2:3b`, `openai`, and `anthropic`.
  2. Select **"ollama (llama3.2:3b)"**.
  3. Submit: *"Draft a 30-day activation experiment plan."*
  4. Show the generation running locally on Ollama without any cloud APIs.
* **Talk Track**:
  > *"A critical requirement for this forward deployment is local model execution. In the provider toggle, we can seamlessly switch between our deterministic offline mock, local Ollama running llama3.2:3b on my machine, and cloud providers.*
  > *Here, the agent is executing 100% locally on my machine via Ollama. Furthermore, we enforce a strict 'zero silent fallback' policy: if an evaluator selects Ollama and the daemon is down, the system returns an explicit HTTP 503 with troubleshooting steps rather than secretly routing data to a cloud provider."*

---

### [2:25 – 2:55] Scene 5: Critical Technical Trade-Off & Conclusion
* **Screen Action**: Switch briefly to terminal / architecture diagram or back to talking head.
* **Talk Track**:
  > *"To wrap up, let's discuss one key technical trade-off: Artifact Security Isolation versus Interactivity.*
  > *When generating interactive HTML/CSS components, rendering them in the React DOM with 'dangerouslySetInnerHTML' introduces severe XSS risks and CSS collisions. We chose to isolate all rendered components inside a sandboxed iframe with 'sandbox=\"allow-scripts\"' while strictly omitting 'allow-same-origin'. This prevents the rendered artifact from accessing host cookies, localStorage, or parent windows, while still allowing dynamic JavaScript calculators and visualizers to run smoothly.*
  > *The system is fully reproducible with one Docker command, includes 64 automated tests, and is ready for evaluator handoff. Thank you!"*

---

## 3. Post-Recording Submission Steps

1. Upload the recorded video to YouTube:
   - **Visibility**: `Unlisted` (or `Public`).
   - **Title**: *The Lenny Growth Assistant — Forward Deployed Engineer Demo*
2. Copy the video URL.
3. Paste the URL into the submission form: [https://forms.gle/LgotDHNVxW1mbzNE7](https://forms.gle/LgotDHNVxW1mbzNE7).
