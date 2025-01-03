import os
import asyncio
import logging
from datetime import datetime
from typing import List

from dotenv import load_dotenv



# Assuming these are imported from separate modules
from db import DatabaseManager
from providers.linkedin_posts import LinkedInJobScanner
from tg import TelegramNotifier

load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('linkedin_scanner.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)



class JobNotificationService:
    """Handles job storage and notification"""
    def __init__(self, db_manager: DatabaseManager, telegram_client: TelegramNotifier):
        self.db = db_manager
        self.telegram_client = telegram_client

    async def process_new_jobs(self, jobs: List[dict]) -> List[dict]:
        """Process and store new job listings"""
        new_jobs = []
        for job in jobs:
            if not self.db.job_exists(job['job_id']):
                if self.db.add_job(job):
                    await self.telegram_client.send_job_offer(job)
                    new_jobs.append(job)
        
        return new_jobs

class JobScanScheduler:
    """Manages job scanning schedule and execution"""
    def __init__(
        self,
        notification_service: JobNotificationService, 
    ):
        self.notification_service = notification_service

    async def run(self):
        """Main job scanning routine"""
        logger.info(f"Starting job scan at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        services = [LinkedInJobScanner()]  # noqa: F821
        all_new_jobs = []

        for service in services:
            jobs = await service.run()
            new_jobs = await self.notification_service.process_new_jobs(jobs)
            all_new_jobs.extend(new_jobs)

        # Log scan results
        self.notification_service.db.log_scan(len(all_new_jobs))
        
        if all_new_jobs:
            logger.info(f"Found {len(all_new_jobs)} new jobs")
        else:
            logger.info("No new jobs found")



if __name__ == "__main__":
    CHROME_PROFILE_PATH = os.path.join(os.getcwd(), "chrome_profile", "linkedin_profile")

    notification_service = JobNotificationService(DatabaseManager(), TelegramNotifier(os.getenv("BOT_TOKEN"), "-1002478023982"))
    scanner = JobScanScheduler(notification_service)
    asyncio.run(scanner.run())