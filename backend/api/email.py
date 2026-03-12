import resend
from config import FRONTEND_URL, RESEND_API_KEY, RESEND_FROM_EMAIL


def send_password_reset_email(to_email: str, username: str, token: str) -> bool:
    if not RESEND_API_KEY:
        print(f"[email] RESEND_API_KEY not set — skipping send (token={token})")
        return False

    resend.api_key = RESEND_API_KEY
    reset_url = f"{FRONTEND_URL}/auth/reset-password?token={token}"

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width,initial-scale=1.0">
  <title>Reset your TennisPredictor password</title>
</head>
<body style="margin:0;padding:0;background-color:#0f172a;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,Helvetica,Arial,sans-serif;">
  <table width="100%" cellpadding="0" cellspacing="0" role="presentation" style="background-color:#0f172a;">
    <tr>
      <td align="center" style="padding:48px 16px;">
        <table width="480" cellpadding="0" cellspacing="0" role="presentation" style="max-width:480px;width:100%;background-color:#1e293b;border-radius:12px;border:1px solid #334155;">
          <tr>
            <td style="padding:40px 40px 32px;">
              <table width="100%" cellpadding="0" cellspacing="0" role="presentation">
                <tr>
                  <td align="center" style="padding-bottom:20px;">
                    <table cellpadding="0" cellspacing="0" role="presentation">
                      <tr>
                        <td align="center" style="width:52px;height:52px;background-color:#1e1b4b;border-radius:10px;">
                          <img src="https://em-content.zobj.net/source/noto-emoji/386/locked_1f512.png"
                               width="28" height="28" alt=""
                               style="display:block;margin:12px auto;" />
                        </td>
                      </tr>
                    </table>
                  </td>
                </tr>
                <tr>
                  <td align="center" style="padding-bottom:6px;">
                    <span style="font-size:22px;font-weight:700;color:#f1f5f9;letter-spacing:-0.02em;">Tennis</span><span style="font-size:22px;font-weight:700;color:#10b981;letter-spacing:-0.02em;">Predictor</span>
                  </td>
                </tr>
                <tr>
                  <td align="center" style="padding-bottom:32px;">
                    <span style="font-size:13px;color:#64748b;letter-spacing:0.04em;text-transform:uppercase;">Password Reset</span>
                  </td>
                </tr>
              </table>
              <table width="100%" cellpadding="0" cellspacing="0" role="presentation">
                <tr><td style="border-top:1px solid #334155;padding-bottom:28px;"></td></tr>
              </table>
              <p style="margin:0 0 10px;font-size:15px;color:#cbd5e1;">
                Hi <strong style="color:#f1f5f9;">{username}</strong>,
              </p>
              <p style="margin:0 0 28px;font-size:14px;color:#94a3b8;line-height:1.7;">
                We received a request to reset your password. Click the button below to choose a new one. This link expires in&nbsp;<strong style="color:#f1f5f9;">1&nbsp;hour</strong>.
              </p>
              <table width="100%" cellpadding="0" cellspacing="0" role="presentation">
                <tr>
                  <td align="center" style="padding-bottom:32px;">
                    <a href="{reset_url}"
                       style="display:inline-block;padding:13px 36px;background-color:#10b981;color:#ffffff;border-radius:8px;text-decoration:none;font-size:15px;font-weight:600;letter-spacing:0.01em;">
                      Reset Password
                    </a>
                  </td>
                </tr>
              </table>
              <table width="100%" cellpadding="0" cellspacing="0" role="presentation">
                <tr><td style="border-top:1px solid #334155;padding-bottom:20px;"></td></tr>
              </table>
              <p style="margin:0 0 4px;font-size:12px;color:#475569;">
                Button not working? Paste this link into your browser:
              </p>
              <p style="margin:0;font-size:12px;line-height:1.6;word-break:break-all;">
                <a href="{reset_url}" style="color:#10b981;text-decoration:none;">{reset_url}</a>
              </p>
            </td>
          </tr>
          <tr>
            <td style="padding:18px 40px;border-top:1px solid #334155;background-color:#162032;border-radius:0 0 12px 12px;">
              <p style="margin:0;font-size:12px;color:#475569;text-align:center;line-height:1.6;">
                If you didn&rsquo;t request a password reset, you can safely ignore this email. Your password won&rsquo;t change.
              </p>
            </td>
          </tr>
        </table>
      </td>
    </tr>
  </table>
</body>
</html>"""

    try:
        resend.Emails.send({
            "from": RESEND_FROM_EMAIL,
            "to": to_email,
            "subject": "Reset your TennisPredictor password",
            "html": html,
        })
        return True
    except Exception as exc:
        print(f"[email] Failed to send password reset email: {exc}")
        return False


def send_verification_email(to_email: str, username: str, token: str) -> bool:
    if not RESEND_API_KEY:
        print(f"[email] RESEND_API_KEY not set — skipping send (token={token})")
        return False

    resend.api_key = RESEND_API_KEY
    verify_url = f"{FRONTEND_URL}/auth/verify-email?token={token}"

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width,initial-scale=1.0">
  <title>Verify your TennisPredictor account</title>
</head>
<body style="margin:0;padding:0;background-color:#0f172a;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,Helvetica,Arial,sans-serif;">
  <table width="100%" cellpadding="0" cellspacing="0" role="presentation" style="background-color:#0f172a;">
    <tr>
      <td align="center" style="padding:48px 16px;">

        <!-- Card -->
        <table width="480" cellpadding="0" cellspacing="0" role="presentation" style="max-width:480px;width:100%;background-color:#1e293b;border-radius:12px;border:1px solid #334155;">

          <!-- Card body -->
          <tr>
            <td style="padding:40px 40px 32px;">

              <!-- Logo row -->
              <table width="100%" cellpadding="0" cellspacing="0" role="presentation">
                <tr>
                  <td align="center" style="padding-bottom:20px;">
                    <!-- Icon badge -->
                    <table cellpadding="0" cellspacing="0" role="presentation">
                      <tr>
                        <td align="center" style="width:52px;height:52px;background-color:#064e3b;border-radius:10px;">
                          <img src="https://em-content.zobj.net/source/noto-emoji/386/bar-chart_1f4ca.png"
                               width="28" height="28" alt=""
                               style="display:block;margin:12px auto;" />
                        </td>
                      </tr>
                    </table>
                  </td>
                </tr>
                <tr>
                  <td align="center" style="padding-bottom:6px;">
                    <span style="font-size:22px;font-weight:700;color:#f1f5f9;letter-spacing:-0.02em;">Tennis</span><span style="font-size:22px;font-weight:700;color:#10b981;letter-spacing:-0.02em;">Predictor</span>
                  </td>
                </tr>
                <tr>
                  <td align="center" style="padding-bottom:32px;">
                    <span style="font-size:13px;color:#64748b;letter-spacing:0.04em;text-transform:uppercase;">Email Verification</span>
                  </td>
                </tr>
              </table>

              <!-- Divider -->
              <table width="100%" cellpadding="0" cellspacing="0" role="presentation">
                <tr><td style="border-top:1px solid #334155;padding-bottom:28px;"></td></tr>
              </table>

              <!-- Greeting & body text -->
              <p style="margin:0 0 10px;font-size:15px;color:#cbd5e1;">
                Hi <strong style="color:#f1f5f9;">{username}</strong>,
              </p>
              <p style="margin:0 0 28px;font-size:14px;color:#94a3b8;line-height:1.7;">
                Thanks for creating your account. Click the button below to verify your email address and get access to match predictions, ELO ratings, and historical stats. This link expires in&nbsp;<strong style="color:#f1f5f9;">24&nbsp;hours</strong>.
              </p>

              <!-- CTA button -->
              <table width="100%" cellpadding="0" cellspacing="0" role="presentation">
                <tr>
                  <td align="center" style="padding-bottom:32px;">
                    <a href="{verify_url}"
                       style="display:inline-block;padding:13px 36px;background-color:#10b981;color:#ffffff;border-radius:8px;text-decoration:none;font-size:15px;font-weight:600;letter-spacing:0.01em;">
                      Verify Email Address
                    </a>
                  </td>
                </tr>
              </table>

              <!-- Divider -->
              <table width="100%" cellpadding="0" cellspacing="0" role="presentation">
                <tr><td style="border-top:1px solid #334155;padding-bottom:20px;"></td></tr>
              </table>

              <!-- Fallback URL -->
              <p style="margin:0 0 4px;font-size:12px;color:#475569;">
                Button not working? Paste this link into your browser:
              </p>
              <p style="margin:0;font-size:12px;line-height:1.6;word-break:break-all;">
                <a href="{verify_url}" style="color:#10b981;text-decoration:none;">{verify_url}</a>
              </p>

            </td>
          </tr>

          <!-- Footer -->
          <tr>
            <td style="padding:18px 40px;border-top:1px solid #334155;background-color:#162032;border-radius:0 0 12px 12px;">
              <p style="margin:0;font-size:12px;color:#475569;text-align:center;line-height:1.6;">
                If you didn&rsquo;t create a TennisPredictor account, you can safely ignore this email.
              </p>
            </td>
          </tr>

        </table>
        <!-- /Card -->

      </td>
    </tr>
  </table>
</body>
</html>"""

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
