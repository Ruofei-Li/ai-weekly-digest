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

    # Diagnostic: print config (mask sensitive fields)
    print(f"[Email] host={config.smtp_host} port={config.smtp_port}")
    print(f"[Email] from={config.email_from} to={config.email_to}")
    print(f"[Email] user={config.smtp_user}")
    masked = config.smtp_password[:4] + "****" if len(config.smtp_password) > 4 else "****"
    print(f"[Email] password={masked}")

    try:
        if config.smtp_port == 465:
            with smtplib.SMTP_SSL(config.smtp_host, config.smtp_port, timeout=30) as server:
                server.set_debuglevel(1)
                server.login(config.smtp_user, config.smtp_password)
                server.sendmail(config.email_from, [config.email_to], msg.as_string())
        else:
            with smtplib.SMTP(config.smtp_host, config.smtp_port, timeout=30) as server:
                server.set_debuglevel(1)
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
