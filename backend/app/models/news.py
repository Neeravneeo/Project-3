from sqlalchemy import Column, String, Boolean, DateTime, text, Numeric
from sqlalchemy.dialects.postgresql import UUID, ARRAY
from sqlalchemy.sql import func
from app.core.database import Base

class NewsItem(Base):
    __tablename__ = "news_items"

    id = Column(UUID(as_uuid=True), primary_key=True, server_default=text("uuid_generate_v4()"))
    headline = Column(String, nullable=False)
    source = Column(String(100))
    url = Column(String)
    symbols = Column(ARRAY(String))
    published_at = Column(DateTime(timezone=True), index=True)
    sentiment_label = Column(String(20))
    sentiment_score = Column(Numeric(5, 4))

    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
