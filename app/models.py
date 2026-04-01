from sqlalchemy import (
    Column, Integer, String, Text, DateTime, Boolean, Float, ForeignKey, Date, Table
)
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from app.database import Base


def utcnow():
    return datetime.now(timezone.utc)


# Association table for Content <-> Label (N:N)
content_labels = Table(
    "content_labels", Base.metadata,
    Column("content_id", Integer, ForeignKey("contents.id", ondelete="CASCADE"), primary_key=True),
    Column("label_id", Integer, ForeignKey("labels.id", ondelete="CASCADE"), primary_key=True),
)


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(80), unique=True, nullable=False, index=True)
    email = Column(String(120), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    full_name = Column(String(150), nullable=False)
    role = Column(String(20), nullable=False, default="editor")
    avatar_color = Column(String(7), default="#6366f1")
    is_active = Column(Boolean, default=True)
    dark_mode = Column(Boolean, default=False)
    created_at = Column(DateTime, default=utcnow)

    contents = relationship("Content", back_populates="responsible", foreign_keys="Content.responsible_id")
    videos = relationship("Video", back_populates="responsible", foreign_keys="Video.responsible_id")
    ideas = relationship("Idea", back_populates="created_by_user", foreign_keys="Idea.created_by")
    comments = relationship("Comment", back_populates="user")


class Content(Base):
    __tablename__ = "contents"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(200), nullable=False)
    description = Column(Text)
    content_type = Column(String(50), nullable=False)
    status = Column(String(50), nullable=False, default="ideia")
    responsible_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    campaign_id = Column(Integer, ForeignKey("campaigns.id"), nullable=True)
    due_date = Column(Date, nullable=True)
    column_order = Column(Integer, default=0)
    priority = Column(String(20), default="media")
    is_favorite = Column(Boolean, default=False)
    is_recurring = Column(Boolean, default=False)
    recurrence_rule = Column(String(100), nullable=True)  # e.g. "weekly:mon,wed" or "daily" or "monthly:1,15"
    created_at = Column(DateTime, default=utcnow)
    updated_at = Column(DateTime, default=utcnow, onupdate=utcnow)

    responsible = relationship("User", back_populates="contents", foreign_keys=[responsible_id])
    campaign = relationship("Campaign", back_populates="contents")
    videos = relationship("Video", back_populates="content", cascade="all, delete-orphan")
    art_requests = relationship("ArtRequest", back_populates="content", cascade="all, delete-orphan")
    checklist_items = relationship("ChecklistItem", back_populates="content", cascade="all, delete-orphan", order_by="ChecklistItem.order")
    comments = relationship("Comment", back_populates="content", cascade="all, delete-orphan", order_by="Comment.created_at")
    attachments = relationship("Attachment", back_populates="content", cascade="all, delete-orphan")
    labels = relationship("Label", secondary=content_labels, back_populates="contents")


class Campaign(Base):
    __tablename__ = "campaigns"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False)
    description = Column(Text)
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)
    budget = Column(Float, default=0)
    status = Column(String(50), default="planejamento")
    color = Column(String(7), default="#6366f1")
    created_at = Column(DateTime, default=utcnow)

    contents = relationship("Content", back_populates="campaign")
    calendar_events = relationship("CalendarEvent", back_populates="campaign")


class Video(Base):
    __tablename__ = "videos"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(200), nullable=False)
    script = Column(Text)
    location = Column(String(200))
    status = Column(String(50), default="roteiro")
    content_id = Column(Integer, ForeignKey("contents.id"), nullable=True)
    responsible_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    due_date = Column(Date, nullable=True)
    notes = Column(Text)
    duration_seconds = Column(Integer)
    created_at = Column(DateTime, default=utcnow)
    updated_at = Column(DateTime, default=utcnow, onupdate=utcnow)

    content = relationship("Content", back_populates="videos")
    responsible = relationship("User", back_populates="videos", foreign_keys=[responsible_id])


class ArtRequest(Base):
    __tablename__ = "art_requests"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=False)
    references = Column(Text)
    deadline = Column(Date, nullable=False)
    status = Column(String(50), default="enviado")
    content_id = Column(Integer, ForeignKey("contents.id"), nullable=True)
    format_type = Column(String(100))
    dimensions = Column(String(50))
    designer_name = Column(String(150))
    feedback = Column(Text)
    image_path = Column(String(500))
    created_at = Column(DateTime, default=utcnow)
    updated_at = Column(DateTime, default=utcnow, onupdate=utcnow)

    content = relationship("Content", back_populates="art_requests")
    comments = relationship("Comment", back_populates="art", cascade="all, delete-orphan", order_by="Comment.created_at")


class Idea(Base):
    __tablename__ = "ideas"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(200), nullable=False)
    description = Column(Text)
    tags = Column(String(500))
    created_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    is_converted = Column(Boolean, default=False)
    converted_content_id = Column(Integer, ForeignKey("contents.id"), nullable=True)
    created_at = Column(DateTime, default=utcnow)

    created_by_user = relationship("User", back_populates="ideas", foreign_keys=[created_by])


class CalendarEvent(Base):
    __tablename__ = "calendar_events"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(200), nullable=False)
    event_type = Column(String(50), nullable=False)
    date = Column(Date, nullable=False)
    time = Column(String(5), nullable=True)
    description = Column(Text)
    color = Column(String(7), default="#6366f1")
    content_id = Column(Integer, ForeignKey("contents.id"), nullable=True)
    campaign_id = Column(Integer, ForeignKey("campaigns.id"), nullable=True)
    source = Column(String(50), default="manual")
    created_at = Column(DateTime, default=utcnow)

    campaign = relationship("Campaign", back_populates="calendar_events")


# ==========================================
# NEW MODELS
# ==========================================

class ChecklistItem(Base):
    __tablename__ = "checklist_items"

    id = Column(Integer, primary_key=True, index=True)
    content_id = Column(Integer, ForeignKey("contents.id", ondelete="CASCADE"), nullable=False)
    text = Column(String(300), nullable=False)
    is_done = Column(Boolean, default=False)
    order = Column(Integer, default=0)
    created_at = Column(DateTime, default=utcnow)

    content = relationship("Content", back_populates="checklist_items")


class Comment(Base):
    __tablename__ = "comments"

    id = Column(Integer, primary_key=True, index=True)
    content_id = Column(Integer, ForeignKey("contents.id", ondelete="CASCADE"), nullable=True)
    art_id = Column(Integer, ForeignKey("art_requests.id", ondelete="CASCADE"), nullable=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    text = Column(Text, nullable=False)
    created_at = Column(DateTime, default=utcnow)

    content = relationship("Content", back_populates="comments")
    art = relationship("ArtRequest", back_populates="comments")
    user = relationship("User", back_populates="comments")


class Attachment(Base):
    __tablename__ = "attachments"

    id = Column(Integer, primary_key=True, index=True)
    content_id = Column(Integer, ForeignKey("contents.id", ondelete="CASCADE"), nullable=False)
    filename = Column(String(300), nullable=False)
    file_path = Column(String(500), nullable=False)
    file_size = Column(Integer, default=0)
    file_type = Column(String(50))
    created_at = Column(DateTime, default=utcnow)

    content = relationship("Content", back_populates="attachments")


class Label(Base):
    __tablename__ = "labels"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50), nullable=False, unique=True)
    color = Column(String(7), nullable=False, default="#6366f1")
    created_at = Column(DateTime, default=utcnow)

    contents = relationship("Content", secondary=content_labels, back_populates="labels")


class AutomationRule(Base):
    __tablename__ = "automation_rules"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False)
    trigger_model = Column(String(50), nullable=False)  # conteudo, video, arte
    trigger_field = Column(String(50), nullable=False)   # status
    trigger_value = Column(String(100), nullable=False)  # aprovado, finalizado, etc
    action_model = Column(String(50), nullable=False)    # conteudo, video, arte
    action_field = Column(String(50), nullable=False)    # status
    action_value = Column(String(100), nullable=False)   # finalizado, postado, etc
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=utcnow)


class CampaignTemplate(Base):
    __tablename__ = "campaign_templates"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False)
    description = Column(Text)
    template_data = Column(Text, nullable=False)  # JSON with campaign structure + content types
    created_at = Column(DateTime, default=utcnow)


class Inspiration(Base):
    __tablename__ = "inspirations"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(200), nullable=False)
    url = Column(String(500))
    description = Column(Text)
    found_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    tags = Column(String(500))
    created_at = Column(DateTime, default=utcnow)

    found_by_user = relationship("User")
