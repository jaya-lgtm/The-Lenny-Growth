# Design Specification & UI/UX Architecture
## The Lenny Growth Assistant

---

## 1. Design Philosophy & User Experience Principles

The Lenny Growth Assistant is designed for Product Managers, Growth Leads, Founders, and Strategy Operators who need high-signal answers and executive-ready deliverables without prompt engineering friction.

### 1.1 Core Principles

1. **Zero Prompt Fatigue & Deterministic Action**
   - Growth operators should not have to craft complex prompts or guess formatting structures.
   - 7 specialized skill pills allow 1-click generation of distinct artifact archetypes (Growth Action Plans, Ship 30 Essays, Frameworks, Checklists, Experiment Plans, Strategy Docs, and HTML Components).

2. **Grounded Transparency & Citation Co-Presence**
   - AI answers must be visibly backed by evidence. Every factual claim surfaces its source episode, guest name, match confidence score, YouTube timestamp, and verbatim excerpt.
   - Collapsible citation cards give immediate confidence without cluttering the primary narrative.

3. **In-Situ Artifact Workspace (Claude-Style Dual Pane)**
   - Generated deliverables are not trapped in raw markdown text bubbles.
   - A dedicated slide-over Artifact Viewer renders deliverables natively beside the conversation, providing **Formatted View**, **Raw Source View**, and **Evidence & Citations View** with 1-click clipboard copy and file export.

4. **Security by Isolation (Zero-Trust HTML Rendering)**
   - Interactive components and HTML widgets are treated as untrusted third-party code.
   - Rendering occurs exclusively inside sandboxed iframes (`sandbox="allow-scripts"` without `allow-same-origin`), guaranteeing zero access to host cookies, `localStorage`, or the parent DOM.

5. **Clarity, Precision, and Impeccable Typography**
   - Clean, high-contrast visual hierarchy built on Slate/Indigo palettes (`#0F172A`, `#2563EB`, `#F8FAFC`).
   - Generous whitespace, refined micro-interactions, responsive typography, and clear loading/error indicators.

---

## 2. Information Architecture & Layout Structure

The interface uses a 3-tier layout designed for high-density product workflows:

```
┌──────────────────────────────────────────────────────────────────────────────────────────────────┐
│                                   THE LENNY GROWTH ASSISTANT                                     │
├──────────────────────┬───────────────────────────────────────────┬───────────────────────────────┤
│       SIDEBAR        │                 CHAT AREA                 │        ARTIFACT VIEWER        │
│   (Width: 260px)     │             (Flex-1 Container)            │   (Width: 480px–640px / 50%)  │
├──────────────────────┼───────────────────────────────────────────┼───────────────────────────────┤
│ • Brand & Status     │ • Header: Active Session Title & Status   │ • Header: Type Icon, Title    │
│ • "New Session" Button│ • Provider Badge (Ollama/Mock/Cloud)      │ • Tabs:                       │
│ • History List:      │ • Messages Stream:                        │   1. Formatted View           │
│   - Session Title    │   - User message (right-aligned, indigo)  │      (Markdown / Iframe)      │
│   - Time & Item Count│   - Assistant response (left, slate)      │   2. Raw Source View          │
│   - Rename / Delete  │   - Expandable Citation Cards             │      (Line-numbered code)     │
│ • Active Artifacts   │   - Artifact Card with "Open" action      │   3. Evidence & Citations     │
│ • Database & Host    │ • Composer (Bottom-pinned):               │      (Direct episode quotes)  │
│   Health Indicator   │   - 7 Skill Pills Selector                │ • Action Bar:                 │
│                      │   - Auto-expanding Textarea               │   - Copy with feedback        │
│                      │   - Model Selector & Send Button          │   - Export (.md / .html)      │
│                      │                                           │   - Fullscreen & Close (Esc)  │
└──────────────────────┴───────────────────────────────────────────┴───────────────────────────────┘
```

---

## 3. Key Interaction States

### 3.1 Empty State (First Load / New Session)
- **Visual Presentation**: High-contrast Lenny Growth Assistant avatar, welcoming title, and 4 quick-start prompt cards.
- **Card Actions**:
  - *“Three components of user activation”* (Triggers Grounded Q&A).
  - *“Draft a 30-60-90 day onboarding growth plan”* (Triggers Growth Action Plan).
  - *“Why retention is the silent killer of startups”* (Triggers Ship 30 Essay).
  - *“Build an interactive growth loops simulator”* (Triggers HTML/CSS Component).
- **Behavior**: Clicking any card populates the composer, auto-selects the corresponding mode pill, and initiates generation.

### 3.2 Composer & Skill Pill Selection State
- **Pill Selector**: Horizontally scrollable row above the input field featuring 8 options:
  - ⚡ `Auto Detect`: Heuristic intent routing.
  - 💬 `Grounded Q&A`: Strict factual Q&A with episode citations.
  - 🚀 `Growth Action Plan`: Phased 30-60-90 day tactical playbooks.
  - 📝 `Ship 30 Essay`: 1,000–1,500 word structured essays with hook, 3 parts, and takeaways.
  - 🎯 `Framework`: Decision matrices and mental models.
  - ✅ `Audit Checklist`: Verification criteria and PMF readiness audits.
  - 🧪 `Experiment Plan`: Hypotheses, metrics, guardrails, and sample sizes.
  - 🧭 `Strategy Doc`: Vision, moats, and roadmaps.
  - 💻 `HTML Component`: Interactive sandboxed widgets and calculators.
- **Active State**: Selected pill highlights with `bg-blue-600 text-white font-medium shadow-sm`.
- **Keyboard Shortcut**: `Enter` submits; `Shift + Enter` inserts a newline.

### 3.3 Thinking & Generation State
- **Visual Feedback**:
  - Send button transforms into an active loading state.
  - Assistant message bubble displays an animated pulsing indicator (`Synthesizing from transcript corpus...`).
  - Active skill badge renders on the response bubble (e.g., `⚡ Ship 30 Content Skill Active`).
- **Resilience**: Client enforces timeout boundaries and displays explicit failure banners if Ollama or the backend drops connection.

### 3.4 Grounded Response & Citation Accordion State
- **Formatting**: Assistant responses are rendered with clean typography, bulleted lists, bold highlights, and structured subheadings.
- **Citation Badges**: Every cited chunk displays:
  - Guest name and episode title.
  - YouTube icon with deep-link timestamp.
  - Match confidence percentage badge (e.g., `92% match`).
  - Expandable excerpt showing the exact verbatim quote from the transcript.

### 3.5 Artifact Card State
- When an artifact is produced, an interactive card renders directly below the assistant message:
  - Artifact icon, title, format (`MARKDOWN` or `HTML`), and word/byte count.
  - High-visibility primary action button: `Open in Viewer →`.
  - Clicking automatically slides out the Artifact Viewer on the right side of the screen.

### 3.6 Slide-Over Artifact Viewer State
- **Side-by-Side Co-Presence**: Slides in from the right edge with a smooth CSS translation (`translate-x-0`). On desktop ($\ge 1280\text{px}$), the chat area shrinks slightly, allowing concurrent reading of the chat and artifact.
- **3 Dynamic Tabs**:
  1. **Formatted View**: Rich typography rendering for Markdown; isolated `<iframe>` for HTML/CSS.
  2. **Raw Source**: Monospace code view with syntax styling and byte counters.
  3. **Evidence & Citations**: Direct list of all podcast transcripts and quotes used to construct this specific deliverable.
- **Action Bar**:
  - `Copy`: Copies formatted content to system clipboard with 2-second “Copied!” checkmark confirmation.
  - `Download`: Exports artifact as `.md` or `.html` file named according to the artifact title.
  - `Close`: Closes viewer via button or pressing `Esc`.

### 3.7 Error & 503 Recovery State
- **Zero Silent Fallback**: If the user selects a local Ollama model and Ollama is stopped, the app never silently switches to another model.
- **Actionable Error Banner**: Surfaces an explicit error box:
  - Error title: `Provider Unavailable (HTTP 503)`.
  - Remediation instructions: `Ensure Ollama is running ('ollama serve') and model 'llama3.2:3b' is pulled ('ollama run llama3.2:3b').`
  - Quick action to switch to the offline `Mock` provider for instant evaluation.

---

## 4. Responsive Behavior & Breakpoints

| Breakpoint | Viewport Width | Layout Behavior |
| :--- | :---: | :--- |
| **Desktop XL** | $\ge 1440\text{px}$ | 3-column co-presence: Sidebar (260px) + Chat Area (Flex) + Artifact Viewer (580px side-by-side). |
| **Desktop MD** | $1024\text{px} - 1439\text{px}$ | Sidebar (240px) + Chat Area (Flex). Artifact Viewer slides over with 50% width and backdrop shadow. |
| **Tablet** | $768\text{px} - 1023\text{px}$ | Sidebar collapsable into hamburger drawer. Artifact Viewer occupies 70% width slide-over. |
| **Mobile** | $< 768\text{px}$ | Single column. Full-screen modal for Artifact Viewer with sticky header and bottom close button. Touch targets strictly $\ge 44\text{px}$. |

---

## 5. Accessibility (a11y) & Inclusive Design

1. **WCAG 2.1 AA Compliance**:
   - Color contrast ratio exceeds $4.5:1$ for all standard text (Slate-900 `#0F172A` on White `#FFFFFF`; Slate-600 `#475569` on Slate-50 `#F8FAFC`).
   - Interactive focus rings use 2px solid blue offset (`focus-visible:ring-2 focus-visible:ring-blue-500 focus-visible:ring-offset-2`).

2. **Keyboard Navigation**:
   - `Tab` navigates logically through Sidebar -> Mode Pills -> Input Textarea -> Send Button -> Artifact Cards.
   - `Escape` key dismisses the Artifact Viewer and returns focus to the triggering button.
   - `Enter` in composer submits; `Shift + Enter` allows multi-line input.

3. **Screen Readers & ARIA Semantics**:
   - Landmarks: `<nav>` for sidebar sessions, `<main>` for chat conversation, `<aside>` for the artifact viewer.
   - `aria-expanded` and `aria-controls` for citation cards and mobile menus.
   - `role="status"` and `aria-live="polite"` on thinking/loading states.

4. **Iframe Isolation Accessibility**:
   - The sandboxed preview iframe includes a descriptive `title` attribute: `title="Rendered Artifact Sandbox"`.

---

## 6. Key Design Decisions & Trade-offs

| Decision | Alternative Considered | Rationale & Trade-off |
| :--- | :--- | :--- |
| **Side-by-Side Slide-Over Viewer** | Modal dialog or new browser tab | Modals obscure conversation context; new tabs break workflow continuity. Slide-over allows cross-referencing chat instructions while reviewing artifacts. |
| **Iframe Sandbox for HTML** | React `dangerouslySetInnerHTML` | `dangerouslySetInnerHTML` exposes the application to CSS pollution and XSS/DOM hijacking. Sandboxed iframes without `allow-same-origin` provide ironclad origin isolation. |
| **Explicit Skill Pills above Input** | Hidden prompt engineering / Slash commands | Slash commands require user memorization. Skill pills visually educate the user on system capabilities and eliminate prompt-crafting friction. |
| **Collapsible Citations in Message** | Inline footnotes or separate page | Footnotes disrupt executive reading; separate pages lose context. Collapsible cards provide immediate verification without visual noise. |
| **Immutable Artifact Versioning** | In-place artifact mutation | Overwriting deliverables destroys conversation history. Assigning unique UUIDs per generation preserves auditability and iterative refinement. |
