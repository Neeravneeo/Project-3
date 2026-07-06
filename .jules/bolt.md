## 2026-07-06 - [Rejected] ORJSONResponse optimization
**Learning:** In newer versions of FastAPI (>=0.115), using `ORJSONResponse` or custom JSON serializers is deprecated for performance reasons. FastAPI now natively serializes data directly to JSON bytes via Pydantic when a return type or response model is set, which is faster and doesn't require a custom response class.
**Action:** Do not use `ORJSONResponse` or `UJSONResponse` for optimizing JSON serialization in this codebase. Rely on FastAPI's native Pydantic integration by ensuring endpoints have proper response models defined.
