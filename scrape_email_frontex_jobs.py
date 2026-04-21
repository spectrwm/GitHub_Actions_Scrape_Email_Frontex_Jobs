import requests
from bs4 import BeautifulSoup
import json
import smtplib
from email.mime.text import MIMEText
from pathlib import Path
import os

URL = "https://www.frontex.europa.eu/careers/vacancies/open-vacancies/"
DATA_FILE = Path("last_jobs.json")

# create empty file if it doesn't exist
DATA_FILE.parent.mkdir(parents=True, exist_ok=True)
DATA_FILE.touch(exist_ok=True)

EMAIL_USER = os.getenv("EMAIL_USER")
EMAIL_PASS = os.getenv("EMAIL_PASS") 
recipients = os.getenv("EMAIL_RECIPIENTS").split(',')
recipients = [r.strip() for r in recipients if r.strip()]
if not EMAIL_USER or not EMAIL_PASS or not recipients:
    raise ValueError("Missing EMAIL_USER or EMAIL_PASS or recipients")

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

    return jobs

def load_last_jobs():
    if DATA_FILE.exists():
        try:
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except json.JSONDecodeError:
            return []  # corrupted or empty file
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
    previous_jobs = load_last_jobs()
    new_jobs = find_new_jobs(current_jobs, previous_jobs)
    
    if new_jobs:
        print(f"Found {len(new_jobs)} new jobs.")
        send_email(new_jobs)
    else:
        print("No new jobs found.")

    save_jobs(current_jobs)

if __name__ == "__main__":
    main()
