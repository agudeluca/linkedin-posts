# Job Scanner

This application scans LinkedIn job postings, processes new job listings, and sends notifications via Telegram. It uses OpenAI for message formatting and a database for job tracking.

## Prerequisites

Ensure you have the following installed:
- Google Chrome (required for LinkedIn scanning)

Ensure you have the following installed:
- Python 3.9+
- `pip` package manager
- `venv` for virtual environments (optional but recommended)

## Setup Instructions

### 1. Clone the Repository
```bash
git clone <repository_url>
cd <repository_folder>
```

### 2. Create and Activate a Virtual Environment (Optional but Recommended)
```bash
python -m venv venv
source venv/bin/activate  # On macOS/Linux
venv\Scripts\activate    # On Windows
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Set Up Environment Variables

Create a `.env` file in the project root and define the required environment variables:

```
DEEPSEEK_API_URL=<your_deepseek_api_url>
DEEPSEEK_API_TOKEN=<your_deepseek_api_token>

OPENAI_API_URL=<your_openai_api_url>
OPENAI_API_TOKEN=<your_openai_api_token>
OPENAI_PROJECT_ID=<your_openai_project_id>
OPENAI_ORG_ID=<your_openai_org_id>

BOT_TOKEN=<your_telegram_bot_token>
CHANNEL_ID=<your_telegram_channel_id>
```

### 5. Configure Chrome Profile for LinkedIn Scanning

Ensure you have Google Chrome installed.

A new LinkedIn account should be used for scanning. The first time you run the application, you will be prompted to log in to LinkedIn. Your login session will be saved, so subsequent logins will not be necessary.

Ensure you have a valid Chrome profile directory:
```bash
mkdir -p chrome_profile/linkedin_profile
```

### 6. Run the Application

Execute the main script:
```bash
python main.py
```

## How It Works

1. The application scans LinkedIn job posts using `LinkedInJobScanner`.
2. It checks if jobs are new and stores them in the database.
3. New jobs are sent as Telegram notifications.
4. The results of each scan are logged.

## Logging

Logs are stored in `linkedin_scanner.log` and displayed in the console.

## Troubleshooting

- Ensure all environment variables are correctly set in `.env`.
- Check that required dependencies are installed.
- If LinkedIn scanning fails, verify the Chrome profile path is correct.

## License

This project is licensed under the **Proprietary License**. Unauthorized use, distribution, or modification of this software is strictly prohibited.

