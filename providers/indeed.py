from jobspy import scrape_jobs
import pandas as pd
from io import StringIO

class IndeedService:
    def __init__(self) -> None:
        pass

    def run(self):
        # Scrape jobs and convert to CSV string
        csv_data = scrape_jobs(
            site_name=["indeed"],
            search_term="full stack latam",
            location="Remote",
            country_indeed='USA'
        ).to_csv(index=False)  # Avoid including the index in the CSV

        # Read the CSV string into a DataFrame
        df = pd.read_csv(StringIO(csv_data))

        # Convert the DataFrame to JSON format
        json_data = df.to_json(orient="records", indent=4)

        return json_data

if __name__ == "__main__":
    service = IndeedService()
    jobs = service.run()

    print(jobs)
