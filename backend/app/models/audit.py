from sqlalchemy import Column, String, Boolean, DateTime, text, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, JSONB, INET
from sqlalchemy.sql import func
from app.core.database import Base

class AuditLog(Base):
    __tablename__ = "audit_log"

    id = Column(UUID(as_uuid=True), primary_key=True, server_default=text("uuid_generate_v4()"))
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    action = Column(String(100), nullable=False, index=True)
    entity_type = Column(String(50))
    entity_id = Column(UUID(as_uuid=True))
    details = Column(JSONB)
    ip_address = Column(INET)

    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), index=True)
