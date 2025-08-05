import random
import string
import aiosmtplib
from email.message import EmailMessage
from datetime import datetime, timedelta
from app.utils.email_config import settings

# In-memory store for OTPs: {email: (otp, expiry_time)}
otp_store = {}

def generate_otp(email: str, expiry_minutes: int = 10) -> str:
    """
    Generate a 6-character alphanumeric OTP and store it with an expiry time.
    """
    otp = ''.join(random.choices(string.ascii_letters + string.digits, k=6))
    expiry = datetime.utcnow() + timedelta(minutes=expiry_minutes)
    otp_store[email] = (otp, expiry)
    print(f"[OTP] Generated for {email}: {otp} (expires at {expiry})")
    return otp

async def send_otp_email(to_email: str, otp: str, username: str = "User"):
    """
    Send OTP to user's email with a formatted message.
    """
    message = EmailMessage()
    message["From"] = settings.EMAIL_FROM
    message["To"] = to_email
    message["Subject"] = "Your One-Time Password (OTP) for Verification"

    email_body = f"""
Hello {username},

Your One-Time Password (OTP) for verification is:

{otp}

This OTP is valid for the next 10 minutes. Please do not share this code with anyone for security reasons.

If you did not request this code, please ignore this email or contact our support team.

Thank you,  
CCT Team
    """.strip()

    message.set_content(email_body)

    await aiosmtplib.send(
        message,
        hostname=settings.SMTP_SERVER,
        port=settings.SMTP_PORT,
        start_tls=True,
        username=settings.SMTP_USERNAME,
        password=settings.SMTP_PASSWORD
    )

def verify_otp(email: str, otp: str) -> bool:
    """
    Verify the OTP associated with a given email address.
    """
    entry = otp_store.get(email)
    if not entry:
        print(f"[OTP] No OTP entry for {email}")
        return False

    stored_otp, expiry = entry
    if datetime.utcnow() > expiry:
        print(f"[OTP] Expired for {email}")
        del otp_store[email]
        return False

    if stored_otp == otp:
        print(f"[OTP] Verified for {email}")
        del otp_store[email]
        return True

    print(f"[OTP]  Invalid OTP for {email}")
    return False
