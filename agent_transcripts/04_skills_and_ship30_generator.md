# Coding Agent Transcript: Milestone 4 — Skills & Ship 30 for 30 Content Generator

## Task Objective
Implement specialized growth skills, including the Ship 30 for 30 essay generator adhering strictly to writing principles (~1,250 words, strong hook, narrative progression, 3 parts, bolding, actionable takeaway, and grounded citations).

---

## Attempt 1: Word Count Under-Generation in Ship 30 Essays
* **Agent Action**: Initial prompt asked the model to *"Write a Ship 30 essay of approximately 1,250 words"*.
* **Issue Encountered**:
  The resulting output had only ~450 words. The test suite failed:
  ```text
  AssertionError: assert 462 >= 1000
  Ship 30 essay word count must be >= 1000 words.
  ```
* **Diagnosis**:
  LLMs naturally tend toward brevity when generating markdown unless provided with structural section minimums and detailed expansion guidance.
* **Correction & Fix**:
  1. Updated the Ship 30 generator prompt and heuristic template with explicit multi-tier length enforcement:
     - Section 1: The Counterintuitive Hook & Context (~250 words).
     - Section 2: Principle 1 Breakdown with Transcript Quotes (~300 words).
     - Section 3: Principle 2 Breakdown with Real Examples (~300 words).
     - Section 4: Principle 3 Tactical Implementation (~300 words).
     - Section 5: The Executive Takeaway & Action Checklist (~150 words).
  2. Implemented `_expand_ship30_essay` in `generators.py` to ensure comprehensive depth, citations, and bolded highlights.
  3. Added automated test `test_milestone3_artifacts.py::test_ship30_essay_word_count_and_structure` verifying word count strictly in the 1,000–1,500 word range.

---

## Attempt 2: Intent Classification Collision
* **Agent Action**: Used a simple keyword dictionary to detect user intent when mode was set to `auto`.
* **Issue Encountered**:
  A prompt like *"Create a checklist to test our onboarding experiment"* triggered `checklist` instead of `experiment_plan`, because "checklist" appeared first in the keyword scan.
* **Diagnosis**:
  Flat keyword matching lacked contextual weighting between broad container words ("checklist", "document") and specialized growth domains ("experiment", "retention", "essay").
* **Correction & Fix**:
  1. Implemented weighted intent scoring in `SkillRouter`:
     - Specific intents (`ship30_essay`, `experiment_plan`, `growth_action_plan`, `html_css`) have higher priority weights.
     - Mode pill selector in UI allows users to bypass heuristic classification with 100% deterministic routing.
  2. Verified with `test_milestone3_artifacts.py::test_intent_routing`.
