import re
import os
import asyncio
import logging
import schedule
from datetime import datetime
from typing import List, Optional, Dict

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.remote.webelement import WebElement
from selenium.common.exceptions import TimeoutException, WebDriverException
from webdriver_manager.chrome import ChromeDriverManager as ChromeDriverManager2
from selenium.webdriver.chrome.service import Service

from filters.ai_formatter import DeepSeekAIFormatter

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

DEEPSEEK_API_URL=os.getenv("DEEPSEEK_API_URL", "")
DEEPSEEK_API_TOKEN=os.getenv("DEEPSEEK_API_TOKEN")

class LinkedInAuthenticator:
    """Handles LinkedIn authentication and login verification"""
    def __init__(self, driver: webdriver.Chrome):
        self.driver = driver
        self.wait = WebDriverWait(self.driver, 10)

    async def check_login_status(self) -> bool:
        """Verify LinkedIn login status"""
        try:
            self.driver.get('https://www.linkedin.com/feed/')
            self.wait.until(
                EC.presence_of_element_located((By.CLASS_NAME, "feed-identity-module"))
            )
            logger.info("Successfully logged into LinkedIn")
            return True
        except TimeoutException:
            logger.error("Not logged in to LinkedIn")
            return False

    def manual_login_prompt(self):
        """Prompt user to manually log in if needed"""
        logger.warning("Please log in to LinkedIn manually in the browser window")
        self.driver.get("https://www.linkedin.com/checkpoint/rm/sign-in-another-account")
        input("Press Enter after logging in...")

    def login_to_linkedin(self, driver, username, password):
        """
        Automates the LinkedIn login process.
        
        Args:
            driver: Selenium WebDriver instance.
            username (str): LinkedIn username (email or phone number).
            password (str): LinkedIn password.
        """
        try:
            # Open the LinkedIn login page
            driver.get("https://www.linkedin.com/checkpoint/rm/sign-in-another-account")

            # Locate the username field and enter the username
            username_field = driver.find_element(By.ID, "username")
            username_field.clear()
            username_field.send_keys(username)

            # Locate the password field and enter the password
            password_field = driver.find_element(By.ID, "password")
            password_field.clear()
            password_field.send_keys(password)

            # Submit the login form
            password_field.send_keys(Keys.RETURN)

            # Wait for the login to complete and check for errors
            driver.implicitly_wait(5)
            if "feed" in driver.current_url:
                logger.info("Successfully logged in to LinkedIn.")
            else:
                logger.error("Login failed. Check username and password.")

        except Exception as e:
            logger.error(f"An error occurred during LinkedIn login: {e}")
            raise

class LinkedInPostFetcher:
    """Handles fetching job posts from LinkedIn"""
    def __init__(self, driver: webdriver.Chrome):
        self.driver = driver
        self.wait = WebDriverWait(self.driver, 10)

    async def extract_job_details(self, job_card: WebElement) -> Optional[dict]:
        """Extract job details from a job card with improved error handling"""
        try:
            job_id = job_card.find_element(By.CLASS_NAME, "feed-shared-update-v2").get_attribute("data-urn")
            title = ""
            content = job_card.find_element(By.CLASS_NAME, "break-words").get_attribute("innerText").strip()
            url = f"https://www.linkedin.com/feed/update/{job_id}"

            email_match = re.search(r'\b[\w.-]+?@\w+?\.\w+?\b', content)
            email = email_match.group(0) if email_match else None

            return {
                'job_id': job_id,
                'title': title,
                'content': content,
                'url': url,
                'email': email,
                'found_at': datetime.now(),
                'source': "linkedin_post"
            }
        except Exception as e:
            logger.error(f"Error extracting job details: {str(e)}")
            return None

    async def scan_page(self, url: str) -> List[dict]:
        """Scan a single LinkedIn page for job listings"""
        try:
            self.driver.get(url)
            await self._scroll_to_load_jobs()

            job_cards = self.wait.until(
                EC.presence_of_all_elements_located((By.CSS_SELECTOR, "li.artdeco-card"))
            )

            jobs = []
            for card in job_cards:
                if job_data := await self.extract_job_details(card):
                    jobs.append(job_data)

            return jobs

        except TimeoutException:
            logger.error("Timeout while loading job listings")
            return []
        except WebDriverException as e:
            logger.error(f"WebDriver error during scan: {str(e)}")
            return []

    async def _scroll_to_load_jobs(self, max_jobs: int = 50):
        """Scroll page to load more job listings"""
        while len(self.driver.find_elements(By.CSS_SELECTOR, "li.artdeco-card")) < max_jobs:
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            await asyncio.sleep(2)

class ChromeDriverManager:
    def __init__(self, profile_path: str):
        self.profile_path = profile_path
        self.driver = None

    def setup(self, debug_port=9222) -> webdriver.Chrome:
        """Initialize and configure Chrome WebDriver"""
        initial_path = os.path.dirname(self.profile_path)
        profile_dir = os.path.basename(self.profile_path)
        os.makedirs(self.profile_path, exist_ok=True)

        options = webdriver.ChromeOptions()
        options.add_argument('--disable-gpu')
        options.add_argument('--no-sandbox')
        # Configure Chrome options
        # options.add_argument('--headless=new')
        options.add_argument('--user-data-dir=' + initial_path)
        options.add_argument('--profile-directory=' + profile_dir)
        options.add_argument("--remote-debugging-port={}".format(debug_port))  # Enable remote debugging
        self.driver = webdriver.Chrome(service=Service(ChromeDriverManager2().install()), options=options)
        self.driver.get("https://www.google.com")
        return self.driver

    def cleanup(self):
        """Clean up Chrome driver resources"""
        if self.driver:
            self.driver.quit()

class LinkedInJobScanner:
    SEARCH_URLS = [
        "https://www.linkedin.com/search/results/content/?keywords=(%22react%22%20OR%20%22javascript%22%20OR%20%22node%22%20OR%20%22python%22)%20developer%20latam&origin=GLOBAL_SEARCH_HEADER&sid=rfF&sortBy=%22date_posted%22",
        "https://www.linkedin.com/search/results/content/?keywords=%22react%22%20%22developer%22%20%22latam%22&origin=GLOBAL_SEARCH_HEADER&sid=YBw&sortBy=%22date_posted%22"
    ]

    def __init__(self, message_formatters=None):
        CHROME_PROFILE_PATH = os.path.join(os.getcwd(), "chrome_profile", "linkedin_profile")
        self.driver_manager = ChromeDriverManager(CHROME_PROFILE_PATH)
        self.driver = None
        self.authenticator = None
        self.post_fetcher = None
        self.job_scanner = None
        self.message_formatters = self.message_formatters

    async def run(self):
        """Main execution loop"""
        try:
            # Setup driver and components
            self.driver = self.driver_manager.setup()

            self.authenticator = LinkedInAuthenticator(self.driver)
            while not await self.authenticator.check_login_status():
                self.authenticator.manual_login_prompt()

            self.post_fetcher = LinkedInPostFetcher(self.driver)

            new_jobs = await self.scan_jobs(message_formatters=self.message_formatters)

            return new_jobs

        except KeyboardInterrupt:
            logger.info("Stopping job scanner...")
        except Exception as e:
            logger.error(f"Unexpected error: {str(e)}")
        finally:
            self.cleanup()

    async def scan_jobs(self, message_formatters=None):
        """Scan job posts from predefined URLs"""
        jobs = []
        for url in self.SEARCH_URLS:
            page_jobs = await self.post_fetcher.scan_page(url)
            jobs.extend(page_jobs)

                    
        for job in formatted_jobs:
            logger.info(f"Found Job: {job['title']} - URL: {job['url']}")

        # Print or process jobs as needed
        formatted_jobs = [message_formatter.apply_to_messages(jobs) for message_formatter in message_formatters if message_formatters]

        return formatted_jobs

    def cleanup(self):
        """Clean up all resources"""
        self.driver_manager.cleanup()

# Optional: Main entry point for running the scanner
async def main():
    scanner = LinkedInJobScanner(message_formatters=[DeepSeekAIFormatter(deepseek_api_url=DEEPSEEK_API_URL, deepseek_api_token=DEEPSEEK_API_TOKEN)])
    await scanner.run()

if __name__ == "__main__":
    asyncio.run(main())
