import streamlit as st
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication
import time, traceback, os
import pandas as pd
import datetime
import pytz

# -------------------- PAGE CONFIG --------------------
st.set_page_config(page_title="Bulk Resume Sender", page_icon="📧")
st.title("📤 Bulk Resume Email Sender")

st.markdown("""
Upload your resume PDFs and send personalized emails to multiple recipients.
You can manually enter recipients below (one per line, format: email, company),
or upload a CSV with columns: email, company.
""")

# -------------------- TIMEZONE MAPPING --------------------
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
    "New Zealand": "Pacific/Auckland"
}

# -------------------- UPLOADS --------------------
uploaded_files = st.file_uploader("📂 Upload your resume PDFs", type="pdf", accept_multiple_files=True)
recipients_input = st.text_area("📥 Enter recipients (one per line, format: email, company):")
uploaded_csv = st.file_uploader("📂 Upload recipients CSV (optional)", type="csv")

# -------------------- EMAIL SETTINGS --------------------
email_body_template = st.text_area(
    "✉️ Write your cold email here (use {company} for company name and {email} for your email):"
)
EMAIL_USER = st.text_input("✉️ Your Gmail address")
EMAIL_PASS = st.text_input("🔑 Gmail App Password", type="password")
EMAIL_SUBJECT = st.text_input(
    "📝 Email Subject",
    value="Application for Data Analyst Position at {company} – Onsite / Relocation"
)
SEND_DELAY_SECONDS = st.slider("⏱ Delay between emails (seconds)", 0, 10, 2)

# -------------------- COUNTRY & TIME --------------------
selected_country = st.selectbox("🌍 Select Country (Email sent at local time of this country)", list(COUNTRY_TIMEZONES.keys()))
schedule_date = st.date_input("📅 Select Date (Country Local Date)", datetime.date.today())
schedule_time = st.time_input("⏰ Select Time (Country Local Time)", datetime.time(8, 0))

# -------------------- DAILY LIMIT --------------------
DAILY_EMAIL_LIMIT = st.slider("📊 Daily Email Limit (safe for Gmail)", 50, 300, 100, step=10)

# -------------------- LOG FILE FOR TRACKING --------------------
LOG_FILE = "sent_log.csv"
if os.path.exists(LOG_FILE):
    sent_log = pd.read_csv(LOG_FILE)
else:
    sent_log = pd.DataFrame(columns=["email", "company", "date_sent"])

# -------------------- START BUTTON --------------------
if st.button("🚀 Start Sending Emails"):

    # -------------------- VALIDATION --------------------
    if not uploaded_files:
        st.error("❌ Please upload at least one PDF!")
        st.stop()
    if not EMAIL_USER or not EMAIL_PASS:
        st.error("❌ Enter Gmail credentials!")
        st.stop()
    if not email_body_template.strip():
        st.error("❌ Email body required!")
        st.stop()

    # -------------------- SAVE PDFs --------------------
    filenames = []
    for file in uploaded_files:
        with open(file.name, "wb") as f:
            f.write(file.getbuffer())
        filenames.append(file.name)
    st.success(f"✅ Using resumes: {', '.join(filenames)}")

    # -------------------- PARSE RECIPIENTS --------------------
    recipients = []
    for line in recipients_input.strip().split("\n"):
        if "," in line:
            email, company = line.split(",", 1)
            recipients.append({"email": email.strip(), "company": company.strip()})

    if uploaded_csv:
        try:
            df = pd.read_csv(uploaded_csv)
            for _, row in df.iterrows():
                recipients.append({
                    "email": str(row["email"]).strip(),
                    "company": str(row["company"]).strip()
                })
        except Exception as e:
            st.error(f"❌ Failed to read CSV: {e}")

    if not recipients:
        st.error("❌ No recipients found!")
        st.stop()

    # -------------------- REMOVE ALREADY SENT TODAY --------------------
    today = datetime.date.today()
    sent_today = sent_log[sent_log["date_sent"] == str(today)]
    already_sent_emails = sent_today["email"].tolist()
    recipients = [r for r in recipients if r["email"] not in already_sent_emails]

    if not recipients:
        st.warning("✅ All recipients have already received emails today. Nothing to send.")
        st.stop()

    # -------------------- TIMEZONE LOGIC --------------------
    target_tz = pytz.timezone(COUNTRY_TIMEZONES[selected_country])
    local_tz = pytz.timezone("Asia/Karachi")  # change if needed

    target_datetime = target_tz.localize(datetime.datetime.combine(schedule_date, schedule_time))
    local_send_time = target_datetime.astimezone(local_tz)
    now_local = datetime.datetime.now(local_tz)

    seconds_to_wait = (local_send_time - now_local).total_seconds()
    if seconds_to_wait > 0:
        st.info(
            f"⏳ Emails scheduled for **{schedule_time.strftime('%I:%M %p')} ({selected_country})**\n"
            f"📍 Your local time: {local_send_time.strftime('%Y-%m-%d %H:%M:%S')}"
        )
        time.sleep(seconds_to_wait)
    else:
        st.warning("⚠️ Time already passed. Sending now.")

    # -------------------- CONNECT TO SMTP --------------------
    try:
        smtp = smtplib.SMTP("smtp.gmail.com", 587)
        smtp.starttls()
        smtp.login(EMAIL_USER, EMAIL_PASS)
        st.success("✅ Connected to Gmail")
    except Exception as e:
        st.error(f"❌ SMTP connection failed: {e}")
        st.stop()

    # -------------------- SEND EMAILS --------------------
    progress = st.progress(0)
    failures = []
    emails_sent_today = len(sent_today)

    for i, r in enumerate(recipients, 1):

        # Daily limit check
        if emails_sent_today >= DAILY_EMAIL_LIMIT:
            st.warning(f"🛑 Daily limit reached ({DAILY_EMAIL_LIMIT} emails). Stop now and continue tomorrow.")
            break

        try:
            msg = MIMEMultipart()
            msg["From"] = EMAIL_USER
            msg["To"] = r["email"]
            msg["Subject"] = EMAIL_SUBJECT.format(company=r["company"])
            body = email_body_template.format(company=r["company"], email=EMAIL_USER)
            msg.attach(MIMEText(body, "plain"))

            for file in filenames:
                with open(file, "rb") as f:
                    part = MIMEApplication(f.read(), _subtype="pdf")
                    part.add_header("Content-Disposition", "attachment", filename=file)
                    msg.attach(part)

            smtp.sendmail(EMAIL_USER, r["email"], msg.as_string())
            emails_sent_today += 1

            # -------------------- LOG EMAIL --------------------
            sent_log = pd.concat([sent_log, pd.DataFrame([{
                "email": r["email"],
                "company": r["company"],
                "date_sent": str(today)
            }])], ignore_index=True)
            sent_log.to_csv(LOG_FILE, index=False)

            st.success(f"✅ Sent ({emails_sent_today}/{DAILY_EMAIL_LIMIT}) → {r['email']} ({r['company']})")

        except Exception as e:
            failures.append({"email": r["email"], "error": str(e)})
            st.error(f"❌ Failed → {r['email']}: {e}")
            traceback.print_exc()

        progress.progress(min(emails_sent_today / DAILY_EMAIL_LIMIT, 1.0))
        time.sleep(SEND_DELAY_SECONDS)

    smtp.quit()

    st.info(f"📌 Finished session\n📨 Emails sent: {emails_sent_today}\n❌ Failed: {len(failures)}")

    if failures:
        df_fail = pd.DataFrame(failures)
        df_fail.to_csv("failed_emails.csv", index=False)
        st.download_button("📥 Download Failed Emails", "failed_emails.csv")



# gjlk lcrs qqvc tggz
