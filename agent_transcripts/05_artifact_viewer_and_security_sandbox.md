# Coding Agent Transcript: Milestone 5 — Artifact Viewer & Security Sandbox

## Task Objective
Develop the Claude-style slide-over Artifact Viewer, support Formatted/Raw/Evidence tabs, and implement secure sandboxing and sanitization for rendered HTML/CSS artifacts.

---

## Attempt 1: Insecure React DOM Rendering
* **Agent Action**: Initial prototype rendered HTML artifacts directly in the frontend using `dangerouslySetInnerHTML`:
  ```tsx
  <div dangerouslySetInnerHTML={{ __html: artifact.content }} />
  ```
* **Issue Encountered**:
  Security audit identified immediate XSS vulnerabilities:
  - If a generated snippet contains `<script>window.location = "http://malicious.com"</script>`, the entire host application can be redirected.
  - Styles inside `<style>` tags polluted the host React application CSS, breaking layout styling.
* **Diagnosis**:
  Direct DOM insertion violates zero-trust principles for untrusted AI-generated web content.
* **Correction & Fix**:
  1. Replaced `dangerouslySetInnerHTML` with an isolated `<iframe>`:
     ```tsx
     <iframe
       sandbox="allow-scripts"
       srcDoc={artifact.content}
       title="Rendered Artifact Sandbox"
       className="w-full h-full border-0 rounded-lg bg-white"
     />
     ```
  2. **Strict Security Isolation**: Deliberately omitted `allow-same-origin`. This forces the iframe into a distinct opaque origin, blocking access to host `document.cookie`, `localStorage`, `sessionStorage`, and parent window navigation.
  3. Added server-side sanitization in `sanitize_html_content` stripping external scripts, parent navigation attempts, meta refresh, and form action hijacking.
  4. Added automated test `test_milestone3_artifacts.py::test_html_sanitization_and_isolation`.

---

## Attempt 2: Artifact Mutability vs. Historical Auditability
* **Agent Action**: Initially, requesting a new draft in the same session updated the existing artifact row in PostgreSQL.
* **Issue Encountered**:
  Product managers lost their previous draft iteration when requesting revisions.
* **Diagnosis**:
  Artifacts in forward-deployed environments must represent immutable point-in-time deliverables.
* **Correction & Fix**:
  1. Made artifact generation strictly immutable: every generation assigns a new UUID.
  2. Linked each artifact to the specific `message_id` that produced it.
  3. Active session artifacts list in the sidebar displays historical iterations.
  4. Added test `test_milestone3_artifacts.py::test_artifact_immutability_on_regeneration`.
