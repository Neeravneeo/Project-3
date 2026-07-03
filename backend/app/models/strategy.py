from sqlalchemy import Column, String, Boolean, DateTime, text, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from sqlalchemy import UniqueConstraint
from app.core.database import Base

class Strategy(Base):
    __tablename__ = "strategies"

    id = Column(UUID(as_uuid=True), primary_key=True, server_default=text("uuid_generate_v4()"))
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String(100), nullable=False)
    display_name = Column(String(100), nullable=False)
    description = Column(String)
    is_enabled = Column(Boolean, nullable=False, server_default=text('false'))
    parameters = Column(JSONB, nullable=False, server_default=text("'{}'::jsonb"))

    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())

    __table_args__ = (UniqueConstraint('user_id', 'name', name='uq_user_strategy'),)

    user = relationship("User", back_populates="strategies")
    signals = relationship("Signal", back_populates="strategy", cascade="all, delete-orphan")
