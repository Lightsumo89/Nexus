import httpx

from app.config import settings


def send(to: str, subject: str, body: str) -> None:
    if not settings.brevo_api_key:
        print(
            f"\n--- email to {to} ---\n{subject}\n{body}\n---------------------\n",
            flush=True,
        )
        return

    if not settings.brevo_sender_email:
        raise RuntimeError("BREVO_SENDER_EMAIL is not configured.")

    response = httpx.post(
        "https://api.brevo.com/v3/smtp/email",
        headers={
            "accept": "application/json",
            "api-key": settings.brevo_api_key,
            "content-type": "application/json",
        },
        json={
            "sender": {
                "name": settings.brevo_sender_name,
                "email": settings.brevo_sender_email,
            },
            "to": [{"email": to}],
            "subject": subject,
            "textContent": body,
        },
        timeout=15.0,
    )

    if response.is_error:
        raise RuntimeError(
            f"Brevo email sending failed ({response.status_code}): {response.text}"
        )
