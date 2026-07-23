"""Settings model for application configuration."""

from sqlalchemy import Column, Integer, String, Text, DateTime, func
from sqlalchemy.orm import relationship

from app.models.base import Base, TimestampMixin


class Setting(Base, TimestampMixin):
    """System setting model.

    Stores key-value configuration settings for the application.
    """

    __tablename__ = "settings"

    id = Column(Integer, primary_key=True, autoincrement=True)
    key = Column(String(255), unique=True, nullable=False, index=True)
    value = Column(Text, nullable=False)
    description = Column(Text, nullable=True)

    # Timestamps are provided by TimestampMixin (created_at, updated_at)