## 2025-02-20 - Unconditional commits on GET endpoints
**Learning:** Initially tried to remove `await session.commit()` from `get_db()` FastAPI dependency to optimize read-only endpoints. However, this is a dangerous architectural change because all existing data-modifying endpoints rely on this implicit commit, and removing it silently breaks data persistence across the application.
**Action:** Do not remove implicit dependency commits unless doing a full codebase audit of all data-modifying endpoints to add explicit commits.

## 2025-02-20 - FastAPI Native JSON Serialization
**Learning:** Returning a bare `dict` from endpoints bypasses FastAPI's optimized native JSON serialization in versions >=0.115, which serializes directly to bytes using Pydantic.
**Action:** Always define and use a Pydantic `response_model` (e.g. for `/health`) to leverage FastAPI's built-in optimized serialization pipeline instead of custom classes or generic dicts.
