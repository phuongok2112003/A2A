from datetime import datetime
from zoneinfo import ZoneInfo
from croniter import croniter
from config.db_postgres import AsyncSessionLocal
from sqlalchemy import select
from config.scheduler import scheduler
from schemas.base import ScheduleRequest
from model.models import ScheduledJob
from config.scheduler import setup_scheduler
from typing import List
class SchedulerService:

    @staticmethod
    async def create_schedule(
    schedule_request : ScheduleRequest
    ) -> ScheduledJob:

        async with AsyncSessionLocal() as db:

            now = datetime.now(ZoneInfo(schedule_request.timezone))
            cron = croniter(schedule_request.cron_expression, now)
            next_run = cron.get_next(datetime)

            job = ScheduledJob(
                external_user_id = schedule_request.external_user_id,
                task_prompt=schedule_request.task_prompt,
                cron_expression=schedule_request.cron_expression,
                timezone=schedule_request.timezone,
                schedule_type=schedule_request.schedule_type,
                next_run_at=next_run,
                type_config_conversation= schedule_request.type_config_conversation
            )

            db.add(job)
            await db.commit()
            await db.refresh(job)

            return job
    @staticmethod
    async def load_schedules():
        async with AsyncSessionLocal() as db:

            result = await db.execute(
                select(ScheduledJob).where(ScheduledJob.is_active == True)
            )
          
            jobs = result.scalars().all()

            for job in jobs:
                try:
                    await setup_scheduler(
                        ScheduleRequest(
                            external_user_id=job.external_user_id,
                            task_prompt=job.task_prompt,
                            cron_expression=job.cron_expression,
                            run_at=job.run_at,
                            schedule_type=job.schedule_type,
                            timezone=job.timezone,
                            type_config_conversation=job.type_config_conversation,
                        )
                    )
                except Exception as e:
                    print(f"[Load Scheduler Error] job_id={job.id}, error={e}")
            
        