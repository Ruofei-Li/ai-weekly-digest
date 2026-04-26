import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from src.config import Config


def send(config: Config, subject: str, html_body: str) -> None:
    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = config.email_from
    msg["To"] = config.email_to

    msg.attach(MIMEText(html_body, "html", "utf-8"))

    try:
        if config.smtp_port == 465:
            # SSL (阿里云邮件推送, QQ邮箱 等)
            with smtplib.SMTP_SSL(config.smtp_host, config.smtp_port, timeout=30) as server:
                server.login(config.smtp_user, config.smtp_password)
                server.sendmail(config.email_from, [config.email_to], msg.as_string())
        else:
            # STARTTLS (默认 587)
            with smtplib.SMTP(config.smtp_host, config.smtp_port, timeout=30) as server:
                server.starttls()
                server.login(config.smtp_user, config.smtp_password)
                server.sendmail(config.email_from, [config.email_to], msg.as_string())
        print(f"[Email] sent successfully to {config.email_to}")
    except smtplib.SMTPAuthenticationError:
        print("[Email] SMTP authentication failed — check SMTP_USER / SMTP_PASSWORD")
        raise
    except smtplib.SMTPException as e:
        print(f"[Email] SMTP error: {e}")
        raise
