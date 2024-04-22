
import logging
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# Configure logging
logging.basicConfig(filename='error.log', level=logging.ERROR,
                    format='%(asctime)s:%(levelname)s:%(message)s')

def log_error(error: dict):
    # This function logs an error message to a log file.
    logging.error(f"Error: {error['message']}")

def send_notification(message: str, recipients: list):
    # This function sends an email notification to a list of recipients. Placeholder values are used.
    sender_email = "erez@mvp-house.com"
    sender_password = "pygd jntb sknd bbbu"
    smtp_server = "smtp.gmail.com"
    port = 587  # For starttls

    # Set up the SMTP server
    server = smtplib.SMTP(smtp_server, port)
    server.starttls()
    try:
        server.login(sender_email, sender_password)
        
        for recipient in recipients:
            msg = MIMEMultipart()
            msg['From'] = sender_email
            msg['To'] = recipient
            msg['Subject'] = "Automated Resume Review System Notification"
            
            msg.attach(MIMEText(message, 'plain'))
            
            server.send_message(msg)
            
            del msg  # Clean up message object for the next recipient
        
        print("Email sent successfully!")
    except Exception as e:
        log_error({'message': str(e)})
    finally:
        server.quit()
