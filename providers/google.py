from jobspy import scrape_jobs
import pandas as pd
from io import StringIO

class GoogleService:
    def __init__(self) -> None:
        pass

    def run(self):
        # Scrape jobs and convert to CSV string
        csv_data = scrape_jobs(
            site_name=["google"],
            results_wanted=100,
            search_term='("python" OR "javascript" OR "react") "remote" "latam" site:jobs.lever.co OR site:boards.greenhouse.io OR site:jobs.ashbyhq.com OR site:jobs.jobvite.com OR site:myworkdayjobs.com OR site:careers.jobscore.com OR site:ats.comparably.com -"remote in the US"',
            google_search_term='("python" OR "javascript" OR "react") "remote" "latam" site:jobs.lever.co OR site:boards.greenhouse.io OR site:jobs.ashbyhq.com OR site:jobs.jobvite.com OR site:myworkdayjobs.com OR site:careers.jobscore.com OR site:ats.comparably.com -"remote in the US"'
        ).to_csv(index=False)  # Avoid including the index in the CSV

        # Read the CSV string into a DataFrame
        df = pd.read_csv(StringIO(csv_data))

        # Convert the DataFrame to JSON format
        json_data = df.to_json(orient="records", indent=4)

        return json_data

if __name__ == "__main__":
    service = GoogleService()
    jobs = service.run()

    print(jobs)
