# ai-sdr
An AI Sales Development Representative


## Architecture

- DuckDB at the database: Further reading at https://mode.com/blog/how-we-switched-in-memory-data-engine-to-duck-db-to-boost-visual-data-exploration-speed
- ruff for linting
- uv for package management
- FastAPI for API serving
- Jinja2 for templating
- xAI / Grok as the key AI model for lead generation, evaluation, and message templating
- Streamlit for the frontend UI

## Evaluation

Consistency: 50% success rate. Lead qualification shows scoring consistency (78 across 5 trials) but priority assignment inconsistency. Message personalization fully consistent.
Edge Cases: Handled 6 low-priority leads correctly (scores 0-35).
Recommendations: Fix priority assignment logic. Model performs better than expected in failure scenarios.

### Lead Management
Scoring Variations: Three approaches tested (aggressive/conservative/balanced). Enterprise leads consistently high-scored (91-95), startup/mid-level leads vary by approach (45-65).
- Often cases where the startup founder was rated lower than expected
