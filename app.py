import streamlit as st
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication
import time, traceback
import pandas as pd
import os
import datetime
import pytz

st.set_page_config(page_title="Bulk Resume Sender", page_icon="📧")
st.title("📤 Bulk Resume Email Sender")

st.markdown("""
Upload your resume PDFs and send personalized emails to multiple recipients.
You can manually enter recipients below (one per line, format: email, company),
or upload a CSV with columns: email, company.
""")

# ---------------- TIMEZONE MAPPING ----------------
COUNTRY_TIMEZONES = {
    "Pakistan": "Asia/Karachi",
    "Australia": "Australia/Sydney",
    "India": "Asia/Kolkata",
    "United Kingdom": "Europe/London",
    "USA (EST)": "US/Eastern",
    "USA (CST)": "US/Central",
    "USA (PST)": "US/Pacific",
    "Canada": "Canada/Eastern",
    "Germany": "Europe/Berlin",
    "UAE": "Asia/Dubai"
}

# Upload resumes
uploaded_files = st.file_uploader("📂 Upload your resume PDFs", type="pdf", accept_multiple_files=True)

# Manual recipients
recipients_input = st.text_area(
    "📥 Enter recipients (one per line, format: email, company):"
)

# CSV upload
uploaded_csv = st.file_uploader("📂 Upload recipients CSV (optional)", type="csv")

# Email body
email_body_template = st.text_area(
    "✉️ Write your cold email here (use {company} for company name and {email} for your email):"
)

# Gmail credentials
EMAIL_USER = st.text_input("✉️ Your Gmail address")
EMAIL_PASS = st.text_input("🔑 Gmail App Password", type="password")

# Subject
EMAIL_SUBJECT = st.text_input(
    "📝 Email Subject",
    value="Application for Data Analyst Position at {company} – Onsite / Relocation"
)

SEND_DELAY_SECONDS = st.slider("⏱ Delay between emails (seconds)", 0, 10, 2)

# ---------------- COUNTRY & TIME ----------------
selected_country = st.selectbox(
    "🌍 Select Country (Email sent at local time of this country)",
    list(COUNTRY_TIMEZONES.keys())
)

schedule_date = st.date_input(
    "📅 Select Date (Country Local Date)",
    datetime.date.today()
)

schedule_time = st.time_input(
    "⏰ Select Time (Country Local Time)",
    datetime.time(8, 0)
)

# ---------------- SEND BUTTON ----------------
if st.button("🚀 Start Sending Emails"):

    if not uploaded_files:
        st.error("❌ Please upload at least one PDF!")
        st.stop()

    if not EMAIL_USER or not EMAIL_PASS:
        st.error("❌ Enter Gmail credentials!")
        st.stop()

    if not email_body_template.strip():
        st.error("❌ Email body required!")
        st.stop()

    # Save PDFs
    filenames = []
    for file in uploaded_files:
        with open(file.name, "wb") as f:
            f.write(file.getbuffer())
        filenames.append(file.name)

    st.success(f"✅ Using resumes: {', '.join(filenames)}")

    # Parse recipients
    recipients = []

    for line in recipients_input.strip().split("\n"):
        if "," in line:
            email, company = line.split(",", 1)
            recipients.append({"email": email.strip(), "company": company.strip()})

    if uploaded_csv:
        df = pd.read_csv(uploaded_csv)
        for _, row in df.iterrows():
            recipients.append({
                "email": str(row["email"]).strip(),
                "company": str(row["company"]).strip()
            })

    if not recipients:
        st.error("❌ No recipients found!")
        st.stop()

    # ---------------- TIMEZONE LOGIC ----------------
    target_tz = pytz.timezone(COUNTRY_TIMEZONES[selected_country])
    local_tz = pytz.timezone("Asia/Karachi")  # change if needed

    target_datetime = target_tz.localize(
        datetime.datetime.combine(schedule_date, schedule_time)
    )

    local_send_time = target_datetime.astimezone(local_tz)
    now_local = datetime.datetime.now(local_tz)

    seconds_to_wait = (local_send_time - now_local).total_seconds()

    if seconds_to_wait > 0:
        st.info(
            f"⏳ Emails scheduled for **{schedule_time.strftime('%I:%M %p')} ({selected_country})**\n\n"
            f"📍 Your local time: {local_send_time.strftime('%Y-%m-%d %H:%M:%S')}"
        )
        time.sleep(seconds_to_wait)
    else:
        st.warning("⚠️ Time already passed. Sending now.")

    # ---------------- SMTP ----------------
    smtp = smtplib.SMTP("smtp.gmail.com", 587)
    smtp.starttls()
    smtp.login(EMAIL_USER, EMAIL_PASS)
    st.success("✅ Connected to Gmail")

    # ---------------- SEND EMAILS ----------------
    progress = st.progress(0)
    failures = []

    for i, r in enumerate(recipients, 1):
        try:
            msg = MIMEMultipart()
            msg["From"] = EMAIL_USER
            msg["To"] = r["email"]
            msg["Subject"] = EMAIL_SUBJECT.format(company=r["company"])

            body = email_body_template.format(
                company=r["company"],
                email=EMAIL_USER
            )
            msg.attach(MIMEText(body, "plain"))

            for file in filenames:
                with open(file, "rb") as f:
                    part = MIMEApplication(f.read(), _subtype="pdf")
                    part.add_header("Content-Disposition", "attachment", filename=file)
                    msg.attach(part)

            smtp.sendmail(EMAIL_USER, r["email"], msg.as_string())
            st.success(f"✅ Sent to {r['email']} ({r['company']})")

        except Exception as e:
            failures.append({"email": r["email"], "error": str(e)})

        progress.progress(i / len(recipients))
        time.sleep(SEND_DELAY_SECONDS)

    smtp.quit()

    st.info(f"📌 Done. Failed: {len(failures)}")

    if failures:
        df_fail = pd.DataFrame(failures)
        df_fail.to_csv("failed_emails.csv", index=False)
        st.download_button("📥 Download Failed Emails", "failed_emails.csv")
