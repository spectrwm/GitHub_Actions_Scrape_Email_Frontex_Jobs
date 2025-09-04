import requests
from bs4 import BeautifulSoup
import json
import smtplib
from email.mime.text import MIMEText
from pathlib import Path
import os

URL = "https://www.frontex.europa.eu/careers/vacancies/open-vacancies/"
DATA_FILE = Path("last_jobs.json")

EMAIL_USER = os.environ["EMAIL_USER"]
EMAIL_PASS = os.environ["EMAIL_PASS"] 
recipients = os.getenv("EMAIL_RECIPIENTS").split(',')

def fetch_jobs():
    response = requests.get(URL)
    soup = BeautifulSoup(response.text, 'html.parser')
    jobs = []

    for item in soup.select(".careers-list-item"):
        title = item.find("h3", class_="title").get_text(strip=True)
        deadline = item.find("dd").get_text(strip=True)
        link = item.find("a")["href"]
        jobs.append({
            "title": title,
            "deadline": deadline,
            "link": link
        })
        print("Page Title:", title)
    print(jobs)
    return jobs

def load_last_jobs():
    if DATA_FILE.exists():
        with open(DATA_FILE, "r") as f:
            return json.load(f)
    return []

def save_jobs(jobs):
    DATA_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(DATA_FILE, "w") as f:
        json.dump(jobs, f, indent=2)

def find_new_jobs(current, previous):
    prev_titles = {job["title"] for job in previous}
    return [job for job in current if job["title"] not in prev_titles]

def send_email(new_jobs):
    if not new_jobs:
        print("No new jobs.")
        return

    subject = "🚨 New Frontex Job Vacancies Posted"
    body = "\n\n".join([f"{j['title']} | Deadline: {j['deadline']}\n{j['link']}" for j in new_jobs])
  
    msg = MIMEText(body)
    msg['Subject'] = subject
    msg['From'] = EMAIL_USER
    msg['To'] = ", ".join(recipients)

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(EMAIL_USER, EMAIL_PASS)
            server.send_message(msg)
        print("Email sent.")
    except Exception as e:
        print("Failed to send email:", e)

def main():
    current_jobs = fetch_jobs()
    print("fetch_jobs() ok")
    previous_jobs = load_last_jobs()
    new_jobs = find_new_jobs(current_jobs, previous_jobs)

    if new_jobs:
        print(f"Found {len(new_jobs)} new jobs.")
        send_email(new_jobs)
        save_jobs(current_jobs)
    else:
        print("No new jobs found.")

if __name__ == "__main__":
    main()
