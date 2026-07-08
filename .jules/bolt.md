## 2026-07-08 - [Pydantic schema setup & Backend Linting]
**Learning:** When generating schema files, breaking down monolithic files (`__init__.py`) into domain-specific files (`user.py`, `portfolio.py`, etc.) and correctly aggregating them back in `__init__.py` with `__all__` is best practice. It simplifies maintenance while keeping the API stable.
**Action:** Next time when dealing with multiple models/schemas, create modular files early to prevent bloated `__init__.py` files and ensure `__all__` is used to expose them.
