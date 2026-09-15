# UI Manual Test Plan
## The Lenny Growth Assistant

This test plan provides step-by-step instructions for an evaluator or QA engineer to manually verify the full frontend, backend, agent engine, and security sandbox workflows of **The Lenny Growth Assistant**.

---

## Prerequisites
1. Stack running via Docker Compose:
   ```bash
   docker compose up -d
   ```
2. Frontend accessible at `http://localhost:5173`.
3. Backend accessible at `http://localhost:8000`.

---

## Test Scenarios

### Test 1: Session Lifecycle & Context Isolation
* **Goal**: Verify independent conversation contexts and clean session management.
* **Steps**:
  1. Open `http://localhost:5173`. Notice the default active session.
  2. In the input box, type: *"We are designing a B2B onboarding flow for enterprise accountants."* and send.
  3. Wait for the response.
  4. Click the **"+ New Session"** button in the sidebar.
  5. Confirm the chat area clears to the empty state with welcome starter cards.
  6. In the new session, ask: *"Who did I say our target audience was?"*
  7. Confirm the assistant states that it does not know or has no prior mention in this session (verifying zero context bleeding).
  8. In the sidebar, click the pencil icon next to the first session, rename it to *"Accountants Onboarding"*, and confirm the title updates.
  9. Click the trash icon to delete the session. Confirm the session disappears and its messages/artifacts are removed.

---

### Test 2: Provider Toggling & Zero Silent Fallback (Resilience)
* **Goal**: Verify provider switching and strict error handling when a provider is unavailable.
* **Steps**:
  1. Look at the provider selector dropdown in the composer (bottom right of input area).
  2. Select **"mock (mock-growth-v1)"**.
  3. Submit any prompt (e.g., *"What is activation?"*). Confirm fast deterministic response.
  4. Select **"ollama (llama3.2:3b)"** (or the model configured on your machine).
  5. Ensure your local Ollama daemon is running (`ollama serve`). Submit a prompt: *"What are the three components of activation according to Lenny's guests?"*.
  6. Confirm the assistant responds with streaming/thinking indicator and completes successfully using the local model.
  7. **Negative Resilience Test**: Stop your local Ollama daemon or change model name to a non-existent one in settings.
  8. Submit a question.
  9. Confirm the UI displays an explicit **HTTP 503 Provider Unavailable** banner explaining that Ollama is unreachable with remediation steps.
  10. Confirm the system **never silently falls back** to a different model without user consent.

---

### Test 3: Grounded Conversational Q&A & Evidence Citations
* **Goal**: Validate natural conversational interaction for greetings and strict transcript evidence grounding for substantive product questions.
* **Steps**:
  1. **Conversational Greeting Test**: Send *"hi"* or *"hello"*.
     - Confirm the assistant responds naturally and warmly like a friendly, expert product colleague.
     - Confirm it briefly introduces its capabilities without citing random podcast chunks.
     - Confirm **zero citation drawers** appear for casual greetings.
  2. In the mode selector above the composer, select **"💬 Grounded Q&A"**.
  3. Submit a substantive question: *"What does Casey Winters say about activation and retention loops?"*
  4. Verify the generated response contains specific quotes from Casey Winters.
  4. Look below the assistant message: confirm the **Citations Accordion** is present (e.g., *"2 sources cited"*).
  5. Click to expand the citation cards.
  6. Verify:
     - Guest name: `Casey Winters`.
     - Episode title.
     - YouTube icon with deep-link timestamp. Click the link to verify it opens YouTube in a new tab.
     - Match score percentage badge (e.g., `89% match`).
     - Verbatim excerpt from the transcript.
  7. **Negative Test (Unsupported Query)**: Ask: *"What is the secret recipe for French sourdough bread?"*
  8. Confirm the assistant explicitly acknowledges: *"I cannot find evidence for this in the available Lenny's Podcast transcripts"* rather than hallucinating an answer.

---

### Test 4: Specialized Skills & Ship 30 for 30 Essay Generation
* **Goal**: Validate the Ship 30 for 30 essay skill (~1,250 words, hook, 3 parts, takeaway, citations).
* **Steps**:
  1. Click the **"📝 Ship 30 Essay"** mode pill above the input box.
  2. Click the starter prompt card or enter: *"Write a Ship 30 essay on why retention is the silent killer of startups."*
  3. Watch the assistant response stream. Confirm an **Artifact Card** appears below the response with:
     - Title: *"Why Retention Is the Silent Killer of Startups"*.
     - Type badge: `SHIP 30 ESSAY`.
     - Format: `MARKDOWN`.
     - Word count indicator (~1,100–1,400 words).
  4. Click the **"Open in Viewer →"** button on the card.
  5. Verify the slide-over Artifact Viewer opens on the right side of the screen.
  6. Inspect the essay structure:
     - Clear narrative hook in the opening section.
     - 3 distinct core parts with subheadings and bold emphasis.
     - Specific, useful takeaway section at the end.
     - Grounded transcript quotes and citations.

---

### Test 5: Slide-Over Artifact Viewer Navigation & Actions
* **Goal**: Verify tab switching, raw source view, evidence tab, copy, and export.
* **Steps**:
  1. With the Artifact Viewer open:
  2. In the viewer header, click the **"Raw Source"** tab. Confirm the raw markdown source is rendered with line numbers and character/byte count.
  3. Click the **"Evidence & Citations"** tab. Confirm the direct list of podcast episodes and quote excerpts used to build the essay are displayed.
  4. Click the **"Copy"** button in the action bar. Confirm the button displays a checkmark and *"Copied!"* badge. Paste into a text editor to verify the clipboard contents.
  5. Click the **"Download"** button. Confirm a `.md` file downloads to your browser's download folder named after the artifact.
  6. Press the `Esc` key on your keyboard. Confirm the Artifact Viewer closes smoothly.

---

### Test 6: Security Sandbox & Iframe Isolation (HTML/CSS Artifacts)
* **Goal**: Verify untrusted HTML/CSS artifacts are strictly sandboxed and cannot access host DOM, cookies, or storage.
* **Steps**:
  1. Select the **"💻 HTML Component"** mode pill.
  2. Enter: *"Generate an interactive growth loops visualizer component with sliders."*
  3. Wait for generation to complete and click **"Open in Viewer →"** on the generated artifact card.
  4. In the viewer, observe the rendered interactive HTML widget (sliders, dynamic calculations).
  5. Open Chrome DevTools (`F12`) and inspect the DOM element containing the widget.
  6. Verify:
     - The component renders inside an `<iframe>`.
     - The `iframe` attributes are: `sandbox="allow-scripts"` and **strictly omit** `allow-same-origin`.
     - Right-click the iframe -> Inspect Console: run `window.parent.document.cookie`. Confirm an `Uncaught DOMException: Blocked a frame with origin "null" from accessing a cross-origin frame` error is thrown.
  7. Confirm that host cookies and localStorage are completely unreachable from the rendered artifact.

---

### Test 7: Mobile & Responsive Layout
* **Goal**: Verify usability across mobile, tablet, and desktop viewports.
* **Steps**:
  1. In Chrome DevTools, toggle Device Toolbar (`Ctrl + Shift + M`) and select **iPhone 14 / Pixel 7** (390px width).
  2. Confirm:
     - Sidebar collapses into a top hamburger menu.
     - Composer and mode pills scroll horizontally without breaking screen width.
     - Touch targets are large and accessible ($\ge 44\text{px}$).
  3. Open an artifact. Confirm the Artifact Viewer opens as a full-screen sheet with a sticky header and accessible close button.
