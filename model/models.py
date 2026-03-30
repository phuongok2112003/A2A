from datetime import datetime
from sqlalchemy import String, Text, Boolean, Integer, TIMESTAMP, Enum
from sqlalchemy.orm import Mapped, mapped_column
from typing import Optional
from schemas.base import ScheduleType, TypeConfigConversation

from model.model_base import BareBaseModel


class ScheduledJob(BareBaseModel):
    
    # business data
    task_prompt: Mapped[str] = mapped_column(Text, nullable=False)

    # schedule config
    schedule_type: Mapped[ScheduleType] = mapped_column(
        Enum(ScheduleType), nullable=False
    )

    cron_expression: Mapped[Optional[str]] = mapped_column(
        String(100), nullable=True
    )

    type_config_conversation: Mapped[TypeConfigConversation] = mapped_column(
        Enum(TypeConfigConversation), nullable= False
    )
    external_user_id: Mapped[str] = mapped_column(String(50))

    run_at: Mapped[Optional[datetime]] = mapped_column(
        TIMESTAMP(timezone=True),
        nullable=True,
    )

    timezone: Mapped[str] = mapped_column(
        String(100), default="Asia/Ho_Chi_Minh"
    )

    # execution tracking
    next_run_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True),
        index=True,
        nullable=False,
    )

    last_run_at: Mapped[Optional[datetime]] = mapped_column(
        TIMESTAMP(timezone=True),
        nullable=True,
    )

    # control
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        index=True,
    )

    failure_count: Mapped[int] = mapped_column(
        Integer,
        default=0,
    )