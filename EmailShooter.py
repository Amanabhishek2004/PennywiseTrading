import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from jinja2 import Environment, FileSystemLoader
import os
from dotenv import load_dotenv 


def send_email(to_email: str, subject: str, context: dict, template_name: str):


    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    TEMPLATE_DIR = os.path.join(BASE_DIR, "templates")
    env = Environment(loader=FileSystemLoader(TEMPLATE_DIR))
    
    try:
        template = env.get_template(template_name)
    except Exception as e:
        print(f"Template '{template_name}' not found. Error: {e}")
        return

    # Render HTML content
    html_body = template.render(context)

    # Email server configuration
    smtp_server = "smtpout.secureserver.net"
    smtp_port = 465
    sender_email = "support@pennywisetrading.in"
    sender_password = 'Abhinav@2009'

    # Build email
    msg = MIMEMultipart("alternative")
    msg["From"] = sender_email
    msg["To"] = to_email
    msg["Subject"] = subject
    msg.attach(MIMEText(html_body, "html"))

    # Send email
    try:
        with smtplib.SMTP_SSL(smtp_server, smtp_port) as server:
            server.login(sender_email, sender_password)
            server.sendmail(sender_email, to_email, msg.as_string())
        print("Email sent successfully!")
    except Exception as e:
        print("Error sending email:", e)