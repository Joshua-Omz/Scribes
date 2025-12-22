"""SQLAlchemy ORM models."""

# Import all models to ensure they are registered with Base.metadata
from app.models.base import BaseModel
from app.models.user_model import User
from app.models.user_profile_model import UserProfile
from app.models.note_model import Note
from app.models.note_chunk_model import NoteChunk
from app.models.circle_model import Circle, CircleMember, CircleNote
from app.models.reminder_model import Reminder
from app.models.refresh_model import RefreshToken
from app.models.annotation_model import Annotation
from app.models.export_job_model import ExportJob
from app.models.notification_model import Notification
from app.models.password_reset_model import PasswordResetToken
from app.models.cross_ref_model import CrossRef
from app.models.background_job_model import BackgroundJob

__all__ = [
    "BaseModel",
    "User",
    "UserProfile",
    "Note",
    "NoteChunk",
    "Circle",
    "CircleMember",
    "CircleNote",
    "Reminder",
    "RefreshToken",
    "Annotation",
    "ExportJob",
    "Notification",
    "PasswordResetToken",
    "CrossRef",
    "BackgroundJob",
]
