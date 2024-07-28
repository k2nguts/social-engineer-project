from dynaconf import Dynaconf
import logging
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.image import MIMEImage

logging.basicConfig(level=logging.INFO)

# Initialize Dynaconf with settings from settings.toml
try:
    settings = Dynaconf(settings_files=["settings.toml"])
except Exception as e:
    logging.error(f"Failed to load settings from settings.toml: {e}")
    raise

async def send_email(receiver_email, EMAIL_SUBJECT, EMAIL_MESSAGE_BODY, token, name_surname, img_paths):
    try:
        sender_email = settings.email.sender_email
        sender_password = settings.email.sender_password
        smtp_server = settings.email.smtp_server
        smtp_port = settings.email.smtp_port

        msg = MIMEMultipart('related')
        msg['From'] = sender_email
        msg['To'] = receiver_email
        msg['Subject'] = EMAIL_SUBJECT

        # Replace placeholders in the HTML body with CID references
        message_body = EMAIL_MESSAGE_BODY.format(name_surname=name_surname, token=token)
        for idx in range(len(img_paths)):
            message_body = message_body.replace(f'{{img{idx}}}', f'cid:image{idx}')

        # Add HTML part with UTF-8 encoding
        msg_alternative = MIMEMultipart('alternative')
        msg.attach(msg_alternative)
        msg_text = MIMEText(message_body, 'html', 'utf-8')
        msg_alternative.attach(msg_text)

        # Add images with CID
        for idx, img_path in enumerate(img_paths):
            with open(img_path, 'rb') as img_file:
                img_data = img_file.read()
            image = MIMEImage(img_data)
            image.add_header('Content-ID', f'<image{idx}>')
            image.add_header('Content-Disposition', 'inline', filename=f'image{idx}.png')
            msg.attach(image)

        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls()
            server.login(sender_email, sender_password)
            server.sendmail(sender_email, receiver_email, msg.as_string())
            logging.info(f"Email sent successfully to {receiver_email}")

    except Exception as e:
        logging.error(f"Failed to send email to {receiver_email}. Error: {str(e)}")
