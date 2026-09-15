# Coding Agent Transcript: Milestone 6 — Resilience & Multi-Provider Toggle

## Task Objective
Implement multi-provider LLM support (`mock`, `ollama`, `openai`, `anthropic`), ensure zero silent fallbacks when a selected provider is unavailable, and implement explicit HTTP 503 error envelopes with actionable remediation instructions.

---

## Attempt 1: Silent Fallback to Default Provider
* **Agent Action**: Initial provider manager caught connection errors from Ollama and automatically switched to `mock` or `openai`:
  ```python
  try:
      return ollama_provider.generate(...)
  except Exception:
      logger.warning("Ollama failed, falling back to mock")
      return mock_provider.generate(...)
  ```
* **Issue Encountered**:
  The user or evaluator selected Ollama expecting local private inference, but the system silently responded using Mock without the user knowing Ollama had crashed or was unreachable.
* **Diagnosis**:
  Silent fallback violates transparency and reproducibility requirements for forward-deployed systems. An evaluator must know exactly which model generated the output.
* **Correction & Fix**:
  1. Eliminated all silent fallback logic in `ProviderManager`.
  2. Implemented strict availability checks and explicit HTTP 503 error responses:
     ```python
     if not provider.is_available():
         raise ProviderUnavailableException(
             code="PROVIDER_UNAVAILABLE",
             message=f"Requested provider '{requested_provider}' is not available.",
             details={"remediation": provider.remediation_instructions()}
         )
     ```
  3. Added `/api/config` endpoint so the UI displays live provider status badges (Online vs. Unconfigured).
  4. Added automated test `test_providers.py::test_unavailable_provider_returns_explicit_503`.

---

## Attempt 2: Docker-to-Host Ollama Networking
* **Agent Action**: Backend container attempted to reach Ollama at `http://localhost:11434`.
* **Issue Encountered**:
  FastAPI returned `ConnectionRefusedError: [Errno 111] Connection refused` because `localhost` inside the container resolves to the container itself, not the host machine where Ollama is running.
* **Diagnosis**:
  Docker bridge network requires explicit host gateway resolution.
* **Correction & Fix**:
  1. Configured default `OLLAMA_BASE_URL` in `docker-compose.yml` to:
     ```yaml
     OLLAMA_BASE_URL: http://host.docker.internal:11434
     ```
  2. Ensured host gateway is reachable on Windows/macOS/Linux Docker setups.
  3. Verified `/api/config` correctly detects host Ollama status.
