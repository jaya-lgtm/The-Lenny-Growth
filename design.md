# Design Specification & UI/UX Architecture
## The Lenny Growth Assistant

> **Note**: For the full version with diagrams and breakpoints, see [docs/design.md](file:///docs/design.md).

---

## 1. Design Philosophy & User Experience Principles

The Lenny Growth Assistant is designed for Product Managers, Growth Leads, Founders, and Strategy Operators who need high-signal answers and executive-ready deliverables without prompt engineering friction.

### 1.1 Core Principles

1. **Zero Prompt Fatigue & Deterministic Action**:
   - 7 specialized skill pills allow 1-click generation of distinct artifact archetypes (Growth Action Plans, Ship 30 Essays, Frameworks, Checklists, Experiment Plans, Strategy Docs, and HTML Components).
2. **Grounded Transparency & Citation Co-Presence**:
   - Every factual claim surfaces its source episode, guest name, match confidence score, YouTube timestamp, and verbatim excerpt.
3. **In-Situ Artifact Workspace (Claude-Style Dual Pane)**:
   - A dedicated slide-over Artifact Viewer renders deliverables natively beside the conversation, providing Formatted View, Raw Source View, and Evidence & Citations View with 1-click clipboard copy and file export.
4. **Security by Isolation (Zero-Trust HTML Rendering)**:
   - Interactive components and HTML widgets render exclusively inside sandboxed iframes (`sandbox="allow-scripts"` without `allow-same-origin`), guaranteeing zero access to host cookies, `localStorage`, or the parent DOM.
5. **Clarity, Precision, and Impeccable Typography**:
   - High-contrast Slate/Indigo palette (`#0F172A`, `#2563EB`, `#F8FAFC`), generous whitespace, refined micro-interactions, responsive typography, and clear loading/error indicators.

---

## 2. Information Architecture & Layout Structure

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

1. **Empty State**: Welcoming title and 4 quick-start prompt cards targeting activation, onboarding playbooks, retention essays, and interactive loops.
2. **Composer & Skill Pill Selection State**: 8 skill pills above input (Auto Detect, Grounded Q&A, Growth Action Plan, Ship 30 Essay, Framework, Audit Checklist, Experiment Plan, Strategy Doc, HTML Component).
3. **Thinking & Generation State**: Animated pulsing indicator (`Synthesizing from transcript corpus...`), send button transforms to loading, active skill badge rendered.
4. **Grounded Response & Citation Accordion State**: Responses rendered with clean typography and collapsible cards featuring guest name, YouTube timestamp link, match percentage, and verbatim quote excerpt.
5. **Artifact Card State**: Embedded card under assistant message with title, format badge, word count, and primary `Open in Viewer →` button.
6. **Slide-Over Artifact Viewer State**: Side-by-side split view on desktop with 3 tabs: Formatted View (Markdown / sandboxed iframe), Raw Source View (line-numbered code), Evidence & Citations View.
7. **Error & 503 Recovery State**: Zero silent fallback. Explicit HTTP 503 banner with instructions for starting Ollama or switching to Mock provider.

---

## 4. Responsive Behavior & Breakpoints

- **Desktop XL ($\ge 1440\text{px}$)**: 3-column co-presence: Sidebar (260px) + Chat Area (Flex) + Artifact Viewer (580px side-by-side).
- **Desktop MD ($1024\text{px} - 1439\text{px}$)**: Sidebar (240px) + Chat Area (Flex). Artifact Viewer slides over with 50% width and backdrop shadow.
- **Tablet ($768\text{px} - 1023\text{px}$)**: Sidebar collapsable into hamburger drawer. Artifact Viewer occupies 70% width slide-over.
- **Mobile ($< 768\text{px}$)**: Single column. Full-screen modal for Artifact Viewer with sticky header and bottom close button. Touch targets strictly $\ge 44\text{px}$.

---

## 5. Accessibility (a11y) & Inclusive Design

- **WCAG 2.1 AA Compliance**: Contrast ratio $\ge 4.5:1$ for all standard text (Slate-900 `#0F172A` on White `#FFFFFF`; Slate-600 `#475569` on Slate-50 `#F8FAFC`).
- **Keyboard Navigation**: `Tab` order through Sidebar -> Mode Pills -> Textarea -> Send -> Artifact Cards; `Esc` dismisses the Artifact Viewer.
- **ARIA Semantics**: Proper `<nav>`, `<main>`, `<aside>` landmarks, `aria-expanded` on citation cards, and `aria-live="polite"` on generation state.
- **Iframe Sandboxing**: Explicit `title="Rendered Artifact Sandbox"` on the preview frame.

---

## 6. Key Design Decisions & Trade-offs

- **Slide-Over Viewer vs. Modal/New Tab**: Maintains conversation co-presence without obscuring context or breaking workflow continuity.
- **Iframe Isolation vs. React DOM**: Eliminates XSS and CSS bleeding risks while permitting interactive HTML calculators and diagrams.
- **Explicit Skill Pills vs. Prompt Crafting**: Removes prompt fatigue by turning unstructured requests into deterministic deliverables.
- **Immutable Artifacts vs. Overwriting**: Ensures auditability and enables iterative comparison of deliverables within a session.
