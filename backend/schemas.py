from pydantic import BaseModel, HttpUrl  # HttpUrl for strict URL validation
from datetime import datetime


# Schema for the incoming request to generate a video
class URLInput(BaseModel):
    url: HttpUrl  # Use HttpUrl for Pydantic's built-in URL validation


# Base schema for Video attributes
class VideoBase(BaseModel):
    original_url: HttpUrl
    product_title: str
    video_filename: str
    status: str


class VideoCreate(VideoBase):
    pass


# Schema for reading/returning a Video entry (includes ID and timestamps)
class Video(VideoBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# Schema for listing videos
class VideoList(BaseModel):
    id: int
    product_title: str
    status: str
    video_filename: str
    created_at: datetime

    class Config:
        from_attributes = True
