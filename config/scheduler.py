from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.date import DateTrigger
from zoneinfo import ZoneInfo
from uuid import uuid4
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from schemas.base import ScheduleRequest, ConfigConversation, TypeConfigConversation, ScheduleType
from services.chat_service import ChatService
from config.logger import log
# Đặt timezone Việt Nam để 8h sáng chạy đúng giờ
tz = ZoneInfo("Asia/Ho_Chi_Minh")
scheduler = AsyncIOScheduler(timezone=tz)

async def process_task(schedule_request: ScheduleRequest):
    try:
        log.info("Running process_task")
        chat_service = ChatService()
        await chat_service.init(status_access_agent_urls=False)

        config = ConfigConversation(
            user_id=schedule_request.external_user_id,
            context_id=f'_{schedule_request.external_user_id}',
            type_config_conversation=TypeConfigConversation.ZALO_BOT
        )

        await chat_service.process_chat(
            config=config,
            user_input_text=schedule_request.task_prompt
        )

    except Exception as e:
        print(f"[Scheduler Error] {e}")


async def setup_scheduler(schedule_request: ScheduleRequest):
    tz = ZoneInfo(schedule_request.timezone)

    # unique job id (tránh trùng)
    job_id = f"{schedule_request.external_user_id}_{uuid4().hex}"

    if schedule_request.schedule_type == ScheduleType.CRON:
        # validate cron
        try:
            minute, hour, day, month, day_of_week = schedule_request.cron_expression.split()
        except ValueError:
            raise ValueError("Invalid cron expression. Expected format: 'm h dom mon dow'")

        trigger = CronTrigger(
            minute=minute,
            hour=hour,
            day=day,
            month=month,
            day_of_week=day_of_week,
            timezone=tz,
        )

    elif schedule_request.schedule_type == ScheduleType.ONE_TIME:
        if not schedule_request.run_at:
            raise ValueError("run_at is required for ONE_TIME")

        run_at = schedule_request.run_at

        # đảm bảo timezone-aware
        if run_at.tzinfo is None:
            run_at = run_at.replace(tzinfo=tz)

        trigger = DateTrigger(
            run_date=run_at,
            timezone=tz,
        )

    else:
        raise ValueError("Unsupported schedule type")

    # add job vào scheduler
    scheduler.add_job(
        process_task,
        trigger=trigger,
        args=[schedule_request],
        id=job_id,
        replace_existing=False,
        misfire_grace_time=300,  # tolerate delay 5 phút
        coalesce=True,
        max_instances=1,
    )