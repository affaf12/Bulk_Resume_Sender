# 📤 Bulk Resume Email Sender

A Streamlit web app to **send personalized emails with resume attachments** to multiple recipients automatically.  
This tool is designed for job applicants, recruiters, or anyone who wants to send bulk emails with attachments using Gmail.

---

## 🚀 Features

- Upload **single or multiple PDF resumes**
- Input **recipients manually** (email and company)
- Write a **custom cold email template** with placeholders (`{company}` and `{email}`)
- Set **email subject** dynamically
- Set **delay between emails** to avoid Gmail throttling
- **Track failures** and download a CSV report of failed emails

---

## 💻 How to Use

1. Clone this repository:

```bash
git clone https://github.com/YOUR_USERNAME/bulk-resume-sender.git
cd bulk-resume-sender



Install required packages:
pip install streamlit pyngrok pandas

Run the Streamlit app:
streamlit run app.py


Upload your resume PDFs, enter recipients, write your cold email, and set Gmail credentials and email subject.

Click Start Sending Emails to send emails in bulk.

📌 Notes

Use a Gmail App Password if 2FA is enabled on your Gmail account.

Be careful with Gmail sending limits to avoid your account being temporarily blocked.

Failures will be saved in failed_emails.csv and can be downloaded directly from the app.

🛠 Requirements

Python 3.7+

Packages: streamlit, pyngrok, pandas

Gmail account with App Password (if 2FA enabled)

🔗 Author

Muhammad Affaf
LinkedIn: https://www.linkedin.com/in/muhammadaffaf/
Email: muhammadaff746@gmail.com
