"""
api/email_service.py — Envío de emails transaccionales.

Configurar en producción vía env vars:
  SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASSWORD, SMTP_FROM
  FRONTEND_URL  (para los enlaces incluidos en los emails)

Si SMTP_HOST no está definido, el email se loguea en stdout (modo desarrollo).
"""
import logging
import os
import smtplib
from email.message import EmailMessage

logger = logging.getLogger(__name__)

SMTP_HOST = os.getenv("SMTP_HOST")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USER = os.getenv("SMTP_USER")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")
SMTP_FROM = os.getenv("SMTP_FROM", "Komparo <noreply@komparo.app>")
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:3000").rstrip("/")
APP_NAME = "Komparo"


def send_email(to: str, subject: str, body_text: str) -> bool:
    """Envía un email. Devuelve True si se envió (o se logueó en dev)."""
    if not SMTP_HOST:
        logger.warning(
            "📧 [DEV] Email a %s | Asunto: %s\n%s",
            to, subject, body_text,
        )
        return True

    msg = EmailMessage()
    msg["From"] = SMTP_FROM
    msg["To"] = to
    msg["Subject"] = subject
    msg.set_content(body_text)

    try:
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=15) as server:
            server.starttls()
            if SMTP_USER and SMTP_PASSWORD:
                server.login(SMTP_USER, SMTP_PASSWORD)
            server.send_message(msg)
        logger.info(f"📧 Email enviado a {to}: {subject}")
        return True
    except Exception as e:
        logger.error(f"❌ Fallo enviando email a {to}: {e}")
        return False


def send_verification_email(to: str, name: str, token: str) -> bool:
    link = f"{FRONTEND_URL}/verify-email?token={token}"
    body = (
        f"Hola {name},\n\n"
        f"Gracias por registrarte en {APP_NAME}.\n\n"
        f"Confirma tu correo abriendo este enlace (válido 24 horas):\n{link}\n\n"
        f"Si no fuiste tú, ignora este mensaje.\n\n"
        f"— Equipo {APP_NAME}"
    )
    return send_email(to, f"Confirma tu cuenta en {APP_NAME}", body)


def send_password_reset_email(to: str, name: str, token: str) -> bool:
    link = f"{FRONTEND_URL}/reset-password?token={token}"
    body = (
        f"Hola {name},\n\n"
        f"Recibimos una solicitud para restablecer tu contraseña en {APP_NAME}.\n\n"
        f"Para crear una nueva contraseña, abre este enlace (válido 1 hora):\n{link}\n\n"
        f"Si no fuiste tú, ignora este email; tu contraseña seguirá igual.\n\n"
        f"— Equipo {APP_NAME}"
    )
    return send_email(to, f"Restablece tu contraseña en {APP_NAME}", body)
