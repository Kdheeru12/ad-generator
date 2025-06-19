from sqlalchemy import Column, Integer, String, DateTime, func
from database import Base


class Video(Base):
    """SQLAlchemy model for storing video metadata."""

    __tablename__ = "videos"

    id = Column(Integer, primary_key=True, index=True)
    original_url = Column(String, index=True)
    product_title = Column(String, index=True)
    video_filename = Column(String, unique=True, index=True)
    status = Column(String, default="processing")  # e.g., "processing", "completed", "failed"
    created_at = Column(DateTime, server_default=func.now())  # Automatically set timestamp on creation
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())  # Automatically update timestamp

    def __repr__(self):
        return f"<Video(title='{self.product_title}', filename='{self.video_filename}', status='{self.status}')>"
