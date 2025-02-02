import os
import asyncio
import logging
from datetime import datetime
from typing import List

from dotenv import load_dotenv



# Assuming these are imported from separate modules
from db import DatabaseManager
from filters.ai_formatter import OpenAIFormatter
from providers.linkedin_posts import LinkedInJobScanner
from providers.scanners import ScannerService
from tg import TelegramNotifier

load_dotenv()

DEEPSEEK_API_URL=os.getenv("DEEPSEEK_API_URL", "")
DEEPSEEK_API_TOKEN=os.getenv("DEEPSEEK_API_TOKEN")

OPENAI_API_URL=os.getenv("OPENAI_API_URL")
OPENAI_API_TOKEN=os.getenv("OPENAI_API_TOKEN")
OPENAI_PROJECT_ID=os.getenv("OPENAI_PROJECT_ID")
OPENAI_ORG_ID=os.getenv("OPENAI_ORG_ID")

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
        scanner_services: List[ScannerService]
    ):
        self.notification_service = notification_service
        self.services = scanner_services

    async def run(self):
        """Main job scanning routine"""
        logger.info(f"Starting job scan at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        all_new_jobs = []

        for service in self.services:
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
    scanner_services = [LinkedInJobScanner(message_formatters=[OpenAIFormatter(api_url=OPENAI_API_URL, api_token=OPENAI_API_TOKEN, openai_project_id=OPENAI_PROJECT_ID, openai_org_id=OPENAI_ORG_ID)])]
    notification_service = JobNotificationService(DatabaseManager(), TelegramNotifier(os.getenv("BOT_TOKEN"), "-1002478023982"))
    scanner = JobScanScheduler(notification_service, scanner_services)
    asyncio.run(scanner.run())