## 2024-07-08 - Fast JSON Serialization with FastAPI 0.115+
**Learning:** In FastAPI >=0.115, returning a Pydantic model with a defined `response_model` allows FastAPI to use Pydantic's highly optimized, native Rust-based serialization directly to JSON bytes. This completely bypasses the slower generic `jsonable_encoder`. Do not use custom JSON response classes like `ORJSONResponse` for optimization.
**Action:** Always ensure endpoints have proper Pydantic response models defined (and avoid bare dicts) to leverage native serialization for optimal read performance.
