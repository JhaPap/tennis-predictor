import resend
from config import FRONTEND_URL, RESEND_API_KEY, RESEND_FROM_EMAIL


def send_verification_email(to_email: str, username: str, token: str) -> bool:
    if not RESEND_API_KEY:
        print(f"[email] RESEND_API_KEY not set — skipping send (token={token})")
        return False

    resend.api_key = RESEND_API_KEY
    verify_url = f"{FRONTEND_URL}/auth/verify-email?token={token}"

    html = f"""
    <div style="font-family:sans-serif;max-width:480px;margin:auto">
      <h2 style="color:#10b981">Verify your TennisPredictor account</h2>
      <p>Hi <strong>{username}</strong>,</p>
      <p>Click the button below to verify your email address. This link expires in 24 hours.</p>
      <p>
        <a href="{verify_url}"
           style="display:inline-block;padding:12px 24px;background:#10b981;color:#fff;border-radius:6px;text-decoration:none;font-weight:bold">
          Verify Email
        </a>
      </p>
      <p style="color:#6b7280;font-size:13px">Or paste this link in your browser:<br>{verify_url}</p>
    </div>
    """

    try:
        resend.Emails.send({
            "from": RESEND_FROM_EMAIL,
            "to": to_email,
            "subject": "Verify your TennisPredictor account",
            "html": html,
        })
        return True
    except Exception as exc:
        print(f"[email] Failed to send verification email: {exc}")
        return False
