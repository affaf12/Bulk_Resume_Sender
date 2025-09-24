import streamlit as st
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication
import time, traceback

st.set_page_config(page_title="Bulk Resume Sender", page_icon="📧")
st.title("📤 Bulk Resume Email Sender")

# Upload resume
uploaded_file = st.file_uploader("📂 Upload your resume PDF", type="pdf")

# Manual recipients input
recipients_input = st.text_area(
    "📥 Enter recipients (one per line, format: email, company):"
)

# Cold email input
email_body_template = st.text_area(
    "✉️ Write your cold email here (use {company} for company name and {email} for your email):"
)

EMAIL_USER = st.text_input("✉️ Your Gmail address")
EMAIL_PASS = st.text_input("🔑 Gmail App Password", type="password")
SEND_DELAY_SECONDS = st.slider("⏱ Delay between emails (seconds)", 0, 10, 2)

if st.button("🚀 Start Sending Emails"):
    if not uploaded_file:
        st.error("❌ Please upload a PDF file first!")
    elif not EMAIL_USER or not EMAIL_PASS:
        st.error("❌ Please enter your Gmail credentials!")
    else:
        filename = uploaded_file.name
        with open(filename, "wb") as f:
            f.write(uploaded_file.getbuffer())

        recipients = []
        for line in recipients_input.strip().split("\\n"):
            parts = line.split(",", 1)
            if len(parts) == 2:
                email, company = parts
                recipients.append({"email": email.strip(), "company": company.strip()})

        failures = []
        progress_bar = st.progress(0)
        try:
            smtp = smtplib.SMTP("smtp.gmail.com", 587)
            smtp.starttls()
            smtp.login(EMAIL_USER, EMAIL_PASS)
        except Exception as e:
            st.error(f"❌ SMTP connection failed: {e}")
            st.stop()

        for i, recipient in enumerate(recipients, 1):
            email = recipient["email"]
            company = recipient["company"]
            try:
                msg = MIMEMultipart()
                msg["From"] = EMAIL_USER
                msg["To"] = email
                msg["Subject"] = "Application"

                body = email_body_template.format(company=company, email=EMAIL_USER)
                msg.attach(MIMEText(body, "plain"))

                with open(filename, "rb") as f:
                    pdf_part = MIMEApplication(f.read(), _subtype="pdf")
                    pdf_part.add_header("Content-Disposition", "attachment", filename=filename)
                    msg.attach(pdf_part)

                smtp.sendmail(EMAIL_USER, email, msg.as_string())
            except Exception as e:
                failures.append({"recipient": email, "error": str(e)})

            progress_bar.progress(i / len(recipients))
            time.sleep(SEND_DELAY_SECONDS)

        smtp.quit()
        st.success(f"Finished sending emails. Failures: {len(failures)}")
        if failures:
            st.json(failures)
