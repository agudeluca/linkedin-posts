
from urllib.parse import urlencode
from telegram import Bot, InlineKeyboardMarkup, InlineKeyboardButton, Update
from telegram.error import TelegramError, RetryAfter
from telegram.ext import Application, MessageHandler, filters, ContextTypes
import logging
import re
import asyncio
import time


sources_threads_ids = {
    "emails": "",
    "upwork": "4294967306",
    "freelancer": "4294967305",
    "ziprecruiter": "4294967303",
    "indeed": "4294967302",
    "google": "4294967301",
    "linkedin_jobs": "4294967300",
    "linkedin_post": "4294967300"
}

class TelegramNotifier:
    def __init__(self, bot_token, channel_id):
        """Initialize the bot with the token and channel ID"""
        self.bot_token = bot_token
        self.channel_id = channel_id
        self.bot = Bot(token=bot_token)
        self.application = Application.builder().token(bot_token).build()
        self.application.add_handler(
            MessageHandler(filters.TEXT & ~filters.COMMAND, self.echo)
        )
        # Add rate limiting tracking
        self.last_request_time = 0
        self.min_request_interval = 0.034  # ~30 messages per second max

    async def echo(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Print the received message along with the chat ID"""
        chat_id = update.message.chat_id
        message_text = update.message.text
        print(f"Received message from {chat_id}: {message_text}")

    async def wait_for_rate_limit(self):
        """Ensure we don't exceed rate limits"""
        elapsed = time.time() - self.last_request_time
        if elapsed < self.min_request_interval:
            await asyncio.sleep(self.min_request_interval - elapsed)
        self.last_request_time = time.time()

    async def send_job_offer(self, job_data, max_retries=3):
        """Send a job offer message to the Telegram channel with buttons"""
        message = remove_hashtags(job_data["content"])
        emails = extract_emails(message)

        keyboard = []
        subject = "Job Offer"  # Default subject for the email
        body = f"Hello,\n\nI am reaching out regarding the job post: {job_data['url']}"  # Default body

        for email in emails:
            # Create a Gmail compose link with prefilled subject and body
            email_url = (
                "https://mail.google.com/mail/?view=cm&fs=1&tf=1&" +
                urlencode({
                    "to": email,
                    "su": subject,
                    "body": body
                })
            )
            keyboard.append(
                [InlineKeyboardButton(f"Email: {email}", url=email_url)]
            )

        # Add the "View Post" button
        keyboard.append([InlineKeyboardButton("View Post", url=job_data["url"])])

        reply_markup = InlineKeyboardMarkup(keyboard)
        retry_count = 0

        while retry_count < max_retries:
            try:
                # Wait for rate limit before sending
                await self.wait_for_rate_limit()

                await self.bot.send_message(
                    chat_id=self.channel_id,
                    text=message,
                    reply_markup=reply_markup,
                    parse_mode="Markdown",
                )
                print("Job offer sent successfully with buttons!")
                return True

            except RetryAfter as e:
                # Handle "Too Many Requests" error
                retry_after = e.retry_after
                print(f"Rate limit exceeded. Waiting for {retry_after} seconds...")
                await asyncio.sleep(retry_after)
                retry_count += 1
                continue

            except TelegramError as e:
                if "Too Many Requests" in str(e):
                    # If we get a rate limit error without RetryAfter info
                    wait_time = 5 * (retry_count + 1)  # Exponential backoff
                    print(f"Rate limit hit. Waiting {wait_time} seconds...")
                    await asyncio.sleep(wait_time)
                    retry_count += 1
                    continue
                else:
                    print(f"Error sending job offer to Telegram: {e}")
                    return False

        print("Max retries reached. Failed to send message.")
        return False

    async def send_multiple_jobs(self, jobs_data):
        """Send multiple job offers with rate limiting"""
        for job in jobs_data:
            success = await self.send_job_offer(job)
            if not success:
                print(f"Failed to send job: {job['content'][:50]}...")
            # Add a small delay between messages
            await asyncio.sleep(1)

    def start(self):
        """Start the bot to listen for messages"""
        print("Bot is listening for messages...")
        self.application.run_polling()


# Helper functions remain the same
def remove_hashtags(text):
    text = re.sub(r"#\w+", "", text)
    text = re.sub(r"\bhashtag\b", "", text, flags=re.IGNORECASE)
    return " ".join(text.split())


def extract_emails(text):
    email_pattern = r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}"
    return re.findall(email_pattern, text)


if __name__ == "__main__":
    # API_ID = "21706349"  # Get from https://my.telegram.org/apps
    # API_HASH = "9404b2187fea840579fb8d4f3e1b6b46"
    # USERNAME = "alejocanion"
    # GROUP_ID = "2478023982"  # Your group ID

    # Run the async function
    # asyncio.run(list_groups(API_ID, API_HASH, USERNAME, "AleJobs"))

    # Enable logging
    logging.basicConfig(
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        level=logging.INFO
    )
    logger = logging.getLogger(__name__)

    # Initialize the bot
    notifier = TelegramNotifier(bot_token="8091974785:AAEo54xSwH4XCAUgTxVPkj4S4rNRVPW_EVE", channel_id="-1002268524956")

    # Example usage with multiple jobs
    jobs = [
        {
            "content": "Software Developer position available! Contact us at",
            "url": "https://example.com/job1"
        },
        {
            "content": "Data Scientist needed! Email",
            "url": "https://example.com/job2"
        }
    ]

    for job in jobs:
        asyncio.run(notifier.send_job_offer(job))

    # Run the bot
    # notifier.start()
