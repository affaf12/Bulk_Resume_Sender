import streamlit as st
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication
import time, traceback
import pandas as pd
import os

st.set_page_config(page_title="Bulk Resume Sender", page_icon="📧")
st.title("📤 Bulk Resume Email Sender")

st.markdown("""
Upload your resume PDFs and send personalized emails to multiple recipients.
You can manually enter recipients below (one per line, format: email, company).
""")

# Upload resumes (multiple)
uploaded_files = st.file_uploader("📂 Upload your resume PDFs", type="pdf", accept_multiple_files=True)

# Manual recipients input
recipients_input = st.text_area(
    "📥 Enter recipients (one per line, format: email, company):"
)

# Cold email input
email_body_template = st.text_area(
    "✉️ Write your cold email here (use {company} for company name and {email} for your email):"
)

# Gmail credentials
EMAIL_USER = st.text_input("✉️ Your Gmail address")
EMAIL_PASS = st.text_input("🔑 Gmail App Password", type="password", help="Use Gmail App Password if 2FA is enabled")

# Email subject input
EMAIL_SUBJECT = st.text_input(
    "📝 Email Subject",
    value="Application for Data Analyst Position – Onsite / Relocation"
)

SEND_DELAY_SECONDS = st.slider("⏱ Delay between emails (seconds)", 0, 10, 2)

if st.button("🚀 Start Sending Emails"):
    if not uploaded_files:
        st.error("❌ Please upload at least one PDF file!")
    elif not EMAIL_USER or not EMAIL_PASS:
        st.error("❌ Please enter your Gmail credentials!")
    elif not EMAIL_SUBJECT.strip():
        st.error("❌ Please enter an email subject!")
    else:
        # Save uploaded files
        filenames = []
        for uploaded_file in uploaded_files:
            filename = uploaded_file.name
            with open(filename, "wb") as f:
                f.write(uploaded_file.getbuffer())
            filenames.append(filename)
        st.success(f"✅ Using uploaded files: {', '.join(filenames)}")

        # Parse recipients input
        recipients = []
        for line in recipients_input.strip().split("\n"):
            parts = line.split(",", 1)
            if len(parts) == 2:
                email, company = parts
                recipients.append({"email": email.strip(), "company": company.strip()})
            else:
                st.warning(f"Skipping invalid line: {line}")

        if not recipients:
            st.error("❌ No valid recipients provided.")
            st.stop()

        # Connect to SMTP
        try:
            smtp = smtplib.SMTP("smtp.gmail.com", 587)
            smtp.ehlo()
            smtp.starttls()
            smtp.login(EMAIL_USER, EMAIL_PASS)
            st.success("✅ Connected to Gmail SMTP server successfully.")
        except Exception as e:
            st.error(f"❌ SMTP connection failed: {e}")
            st.stop()

        # Send emails
        failures = []
        progress_bar = st.progress(0)

        for i, recipient in enumerate(recipients, 1):
            email = recipient["email"]
            company = recipient.get("company", "Team")
            try:
                msg = MIMEMultipart()
                msg["From"] = EMAIL_USER
                msg["To"] = email
                msg["Subject"] = EMAIL_SUBJECT

                body = email_body_template.format(company=company, email=EMAIL_USER)
                msg.attach(MIMEText(body, "plain"))

                # Attach all uploaded PDFs
                for filename in filenames:
                    with open(filename, "rb") as f:
                        pdf_part = MIMEApplication(f.read(), _subtype="pdf")
                        pdf_part.add_header("Content-Disposition", "attachment", filename=filename)
                        msg.attach(pdf_part)

                smtp.sendmail(EMAIL_USER, email, msg.as_string())
                st.success(f"✅ Email sent to {email} ({company})")
            except Exception as e:
                st.error(f"❌ Failed to send to {email}: {e}")
                failures.append({"recipient": email, "company": company, "error": str(e)})
                traceback.print_exc()

            progress_bar.progress(i / len(recipients))
            time.sleep(SEND_DELAY_SECONDS)

        smtp.quit()
        st.info(f"📌 Finished sending emails. Failures: {len(failures)}")

        if failures:
            st.json(failures)
            # Save failures to CSV
            df_failures = pd.DataFrame(failures)
            df_failures.to_csv("failed_emails.csv", index=False)
            st.download_button("📥 Download Failed Emails CSV", "failed_emails.csv")
