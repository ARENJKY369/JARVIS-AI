"""
JARVIS OS - Email Skill
=======================

One-command email:
  "email Mom saying I'll be late"
  "send email to alice@example.com subject Meeting body See you at 5"
  "draft email to Dad about the trip"

Safety model:
  - Default = draft (saved locally + optional Gmail compose URL)
  - Real SMTP send only when JARVIS_EMAIL_ENABLED=true AND credentials set
    AND user confirms (or confirmed=True on API)
"""

from __future__ import annotations

import json
import re
import smtplib
import time
import webbrowser
from datetime import datetime
from email.message import EmailMessage
from pathlib import Path
from urllib.parse import quote

from loguru import logger

from core.config import get_settings
from core.security import Permission
from memory.contacts import get_contact_book
from .base import Skill, SkillContext, SkillResult


_EMAIL_RE = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")


def parse_email_command(text: str) -> dict[str, str | None]:
    """
    Extract to / subject / body from natural language.

    Patterns handled:
      email Mom saying I'll be late
      send email to alice@x.com saying hello
      draft a mail to Dad about the trip: we leave Friday
      email to bob@x.com subject Hello body How are you
    """
    t = (text or "").strip()
    out: dict[str, str | None] = {
        "to": None,
        "subject": None,
        "body": None,
        "mode": "draft",
    }
    low = t.lower()
    if re.search(r"\b(send|dispatch)\b", low):
        out["mode"] = "send"
    if re.search(r"\b(draft|compose|write)\b", low):
        out["mode"] = "draft"

    # Explicit subject/body keys
    m = re.search(
        r"(?:subject|subj)\s*[:=]?\s*(.+?)(?:\s+(?:body|message|saying)\s*[:=]?\s*(.+))?$",
        t,
        re.I,
    )
    if m and ("subject" in low or "subj" in low):
        out["subject"] = m.group(1).strip(" .,\"'")
        if m.group(2):
            out["body"] = m.group(2).strip(" .,\"'")

    m_body = re.search(r"\b(?:body|message)\s*[:=]\s*(.+)$", t, re.I)
    if m_body and not out["body"]:
        out["body"] = m_body.group(1).strip(" .,\"'")

    # "to X"
    m_to = re.search(
        r"\b(?:email|mail|e-mail|message)\s+(?:to\s+)?(.+?)(?:\s+(?:saying|about|subject|body|that|with)\b|$)",
        t,
        re.I,
    )
    if not m_to:
        m_to = re.search(
            r"\b(?:send|draft|compose|write)\s+(?:an?\s+)?(?:email|mail|e-mail)\s+(?:to\s+)?(.+?)(?:\s+(?:saying|about|subject|body|that|with)\b|$)",
            t,
            re.I,
        )
    if m_to:
        candidate = m_to.group(1).strip(" .,\"'")
        # strip leading "to "
        candidate = re.sub(r"^to\s+", "", candidate, flags=re.I)
        out["to"] = candidate

    # Raw email anywhere
    em = _EMAIL_RE.search(t)
    if em and not out["to"]:
        out["to"] = em.group(0)
    elif em and out["to"] and "@" not in (out["to"] or ""):
        # prefer explicit address if name was captured poorly
        pass

    # saying / about → body
    m_say = re.search(r"\b(?:saying|that|about)\s+(.+)$", t, re.I)
    if m_say and not out["body"]:
        body = m_say.group(1).strip(" .,\"'")
        # if "about X: rest" split subject/body
        if ":" in body and not out["subject"]:
            subj, _, rest = body.partition(":")
            out["subject"] = subj.strip()
            out["body"] = rest.strip() or body
        else:
            out["body"] = body
            if not out["subject"]:
                # short subject from body
                out["subject"] = (body[:48] + ("…" if len(body) > 48 else ""))

    if out["to"] and not out["subject"]:
        out["subject"] = "Message from JARVIS"
    if out["to"] and not out["body"]:
        out["body"] = "(No body provided)"

    return out


def _drafts_dir() -> Path:
    settings = get_settings()
    d = settings.base_dir / settings.data_dir / "email_drafts"
    d.mkdir(parents=True, exist_ok=True)
    return d


def save_draft(to: str, subject: str, body: str, meta: dict | None = None) -> Path:
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    path = _drafts_dir() / f"draft_{ts}.json"
    payload = {
        "to": to,
        "subject": subject,
        "body": body,
        "created_at": datetime.now().isoformat(),
        "meta": meta or {},
    }
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    # Also human-readable .eml-ish text
    txt = _drafts_dir() / f"draft_{ts}.txt"
    txt.write_text(
        f"To: {to}\nSubject: {subject}\nDate: {payload['created_at']}\n\n{body}\n",
        encoding="utf-8",
    )
    return path


def open_gmail_compose(to: str, subject: str, body: str) -> str:
    """Open Gmail compose with fields pre-filled (no password needed)."""
    url = (
        "https://mail.google.com/mail/?view=cm&fs=1"
        f"&to={quote(to)}"
        f"&su={quote(subject)}"
        f"&body={quote(body)}"
    )
    try:
        webbrowser.open(url, new=2)
    except Exception as exc:
        logger.warning(f"Could not open browser for Gmail compose: {exc}")
    return url


def smtp_send(to: str, subject: str, body: str) -> tuple[bool, str]:
    settings = get_settings().email
    if not settings.is_configured():
        return False, "SMTP is not configured. Set JARVIS_EMAIL_* in .env"

    msg = EmailMessage()
    from_addr = settings.from_address or settings.smtp_user
    msg["From"] = from_addr
    msg["To"] = to
    msg["Subject"] = subject
    msg.set_content(body)

    try:
        if settings.use_tls:
            with smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=30) as smtp:
                smtp.ehlo()
                smtp.starttls()
                smtp.ehlo()
                smtp.login(settings.smtp_user, settings.smtp_password)
                smtp.send_message(msg)
        else:
            with smtplib.SMTP_SSL(settings.smtp_host, settings.smtp_port, timeout=30) as smtp:
                smtp.login(settings.smtp_user, settings.smtp_password)
                smtp.send_message(msg)
        return True, f"Email sent to {to}"
    except Exception as exc:
        logger.exception("SMTP send failed")
        return False, f"SMTP failed: {exc}"


class EmailSkill(Skill):
    name = "email.send"
    description = (
        "Draft or send an email. Default is safe draft + Gmail compose. "
        "SMTP send requires config and confirmation."
    )
    # Browser used for Gmail compose; SMTP network checked inside run()
    permissions = [Permission.AUTOMATION_BROWSER]
    examples = [
        "send email",
        "email mom saying",
        "draft email to",
        "mail dad about",
        "compose email",
        "write an email to",
    ]
    require_confirmation = False  # confirmation only for SMTP path inside run()

    def matches(self, text: str) -> float:
        t = (text or "").lower()
        # Don't steal contact management
        if re.search(r"\b(add|save|remember)\s+contact\b", t) or re.search(
            r"\bset\s+email\s+for\b", t
        ):
            return 0.05
        # "help me write an email" → ChatGPT work skill, not send-email
        if re.search(r"\bhelp me (write|draft|create)\b", t):
            return 0.05
        if re.search(r"\b(write|draft)\s+(a|an|the)?\s*(professional\s+)?email\b", t) and not re.search(
            r"\b(to\s+\S+|saying|subject)\b", t
        ):
            return 0.2
        # Don't steal plain "open gmail"
        if re.search(r"\bopen\s+(gmail|mail|email)\b", t) and not re.search(
            r"\b(send|draft|saying|to\s+\S+@)\b", t
        ):
            return 0.1
        if re.search(
            r"\b(send\s+(an?\s+)?(email|mail|e-mail)|email\s+\w+|draft\s+(an?\s+)?(email|mail)|"
            r"compose\s+(an?\s+)?(email|mail)|write\s+(an?\s+)?(email|mail)|mail\s+\w+\s+(saying|about))\b",
            t,
        ):
            return 0.97
        if re.search(r"\b(email|e-mail)\b", t) and re.search(
            r"\b(to|saying|about|subject)\b", t
        ):
            return 0.93
        return super().matches(text)

    async def run(self, ctx: SkillContext) -> SkillResult:
        settings = get_settings()
        parsed = parse_email_command(ctx.user_text)
        # params override
        to_raw = ctx.params.get("to") or parsed["to"]
        subject = ctx.params.get("subject") or parsed["subject"] or "Message from JARVIS"
        body = ctx.params.get("body") or parsed["body"] or ""
        mode = ctx.params.get("mode") or parsed["mode"] or settings.email.default_mode
        confirmed = bool(ctx.params.get("confirmed", False))

        if not to_raw:
            return SkillResult(
                success=False,
                message=(
                    "Who should I email, sir? Try: email Mom saying I'll be late — "
                    "or add contacts in data/contacts.json."
                ),
                skill=self.name,
                error="MISSING_TO",
            )

        book = get_contact_book()
        display, email_addr = book.resolve_email(str(to_raw))

        if not email_addr:
            # Save draft with unresolved name + help user
            draft_path = save_draft(
                to=str(display or to_raw),
                subject=str(subject),
                body=str(body),
                meta={"unresolved": True, "hint": "Add email in data/contacts.json"},
            )
            return SkillResult(
                success=False,
                message=(
                    f"I don't have an email address for {display or to_raw}, sir. "
                    f"Add it to data/contacts.json. Draft saved at {draft_path.name}."
                ),
                skill=self.name,
                error="UNKNOWN_CONTACT",
                data={
                    "to_name": display or to_raw,
                    "draft_path": str(draft_path),
                    "contacts_file": str(book.path),
                },
            )

        # Always save a draft first
        draft_path = save_draft(
            to=email_addr,
            subject=str(subject),
            body=str(body),
            meta={"display": display, "mode": mode},
        )

        # Dry run
        if ctx.dry_run:
            return SkillResult(
                success=True,
                message=f"Would {mode} email to {display} <{email_addr}>: {subject}",
                skill=self.name,
                data={
                    "to": email_addr,
                    "subject": subject,
                    "body": body,
                    "mode": mode,
                    "draft_path": str(draft_path),
                    "dry_run": True,
                },
            )

        # Prefer safe draft + Gmail compose unless explicit send + config + confirm
        want_send = str(mode).lower() == "send"
        can_smtp = settings.email.is_configured()

        if want_send and can_smtp:
            if settings.email.require_confirmation and not confirmed:
                return SkillResult(
                    success=False,
                    message=(
                        f"Ready to SEND email to {display} <{email_addr}> "
                        f"subject '{subject}'. Say 'confirm send email' to dispatch, sir."
                    ),
                    skill=self.name,
                    needs_confirmation=True,
                    error="NEEDS_CONFIRMATION",
                    data={
                        "to": email_addr,
                        "subject": subject,
                        "body": body,
                        "draft_path": str(draft_path),
                    },
                )
            # Network permission for real send
            from core.security import get_permission_manager

            pm = get_permission_manager()
            if not pm.has_permission(Permission.NETWORK_ACCESS):
                if settings.environment == "development":
                    pm.grant(Permission.NETWORK_ACCESS, reason="email send")
                else:
                    return SkillResult(
                        success=False,
                        message="NETWORK_ACCESS permission required to send email.",
                        skill=self.name,
                        error="PERMISSION_DENIED",
                    )

            ok, msg = smtp_send(email_addr, str(subject), str(body))
            return SkillResult(
                success=ok,
                message=msg if ok else msg,
                skill=self.name,
                error=None if ok else "SMTP_FAILED",
                data={
                    "to": email_addr,
                    "subject": subject,
                    "sent": ok,
                    "draft_path": str(draft_path),
                },
            )

        # Default safe path: draft + open Gmail compose
        url = open_gmail_compose(email_addr, str(subject), str(body))
        hint = ""
        if want_send and not can_smtp:
            hint = (
                " SMTP is not configured yet — opened Gmail compose instead. "
                "Set JARVIS_EMAIL_ENABLED=true and SMTP credentials in .env for direct send."
            )
        return SkillResult(
            success=True,
            message=(
                f"Draft prepared for {display} <{email_addr}>. "
                f"Subject: {subject}. Opened Gmail compose and saved "
                f"{draft_path.name}.{hint}"
            ),
            skill=self.name,
            data={
                "to": email_addr,
                "display": display,
                "subject": subject,
                "body": body,
                "draft_path": str(draft_path),
                "gmail_compose_url": url,
                "mode": "draft",
            },
        )


class ConfirmEmailSkill(Skill):
    """Confirm a pending send: 'confirm send email'."""

    name = "email.confirm"
    description = "Confirm and send the last drafted email via SMTP."
    permissions = [Permission.NETWORK_ACCESS]
    examples = ["confirm send email", "confirm email", "yes send it", "confirm send"]
    require_confirmation = False

    def matches(self, text: str) -> float:
        t = (text or "").lower()
        if re.search(r"\bconfirm\s+(send\s+)?(email|mail|it)\b", t):
            return 0.99
        if t.strip() in ("confirm", "yes send it", "send it"):
            return 0.7
        return 0.0

    async def run(self, ctx: SkillContext) -> SkillResult:
        # Find latest draft
        drafts = sorted(_drafts_dir().glob("draft_*.json"), reverse=True)
        if not drafts:
            return SkillResult(
                success=False,
                message="No email draft to confirm, sir.",
                skill=self.name,
                error="NO_DRAFT",
            )
        data = json.loads(drafts[0].read_text(encoding="utf-8"))
        settings = get_settings()
        if not settings.email.is_configured():
            url = open_gmail_compose(data["to"], data["subject"], data["body"])
            return SkillResult(
                success=True,
                message=(
                    "SMTP not configured — reopened Gmail compose for the latest draft. "
                    "Configure JARVIS_EMAIL_* to send directly."
                ),
                skill=self.name,
                data={"gmail_compose_url": url, "draft": str(drafts[0])},
            )

        from core.security import get_permission_manager

        pm = get_permission_manager()
        if not pm.has_permission(Permission.NETWORK_ACCESS):
            pm.grant(Permission.NETWORK_ACCESS, reason="confirm email send")

        ok, msg = smtp_send(data["to"], data["subject"], data["body"])
        return SkillResult(
            success=ok,
            message=msg,
            skill=self.name,
            data={"to": data["to"], "subject": data["subject"], "sent": ok},
            error=None if ok else "SMTP_FAILED",
        )


class AddContactSkill(Skill):
    name = "contacts.add"
    description = "Save a contact email: add contact Mom email mom@example.com"
    permissions = [Permission.MEMORY_WRITE]
    examples = [
        "add contact",
        "save contact",
        "remember contact",
        "set email for",
    ]

    def matches(self, text: str) -> float:
        t = (text or "").lower()
        if re.search(r"\b(add|save|remember)\s+contact\b", t):
            return 0.95
        if re.search(r"\bset\s+email\s+for\b", t):
            return 0.95
        return super().matches(text)

    async def run(self, ctx: SkillContext) -> SkillResult:
        text = ctx.user_text or ""
        email_m = _EMAIL_RE.search(text)
        if not email_m:
            return SkillResult(
                success=False,
                message="I need an email address, sir. Example: add contact Mom email mom@gmail.com",
                skill=self.name,
                error="MISSING_EMAIL",
            )
        email = email_m.group(0)
        # name: after contact / for
        name = None
        m = re.search(
            r"(?:contact|for)\s+([A-Za-z][A-Za-z0-9 .'-]{0,40}?)\s+(?:email|=|:)",
            text,
            re.I,
        )
        if m:
            name = m.group(1).strip()
        if not name:
            m2 = re.search(r"add\s+contact\s+([A-Za-z][A-Za-z0-9 .'-]+)", text, re.I)
            if m2:
                name = m2.group(1).replace(email, "").strip()
        if not name:
            name = email.split("@")[0]

        book = get_contact_book()
        c = book.upsert(name, email=email)
        return SkillResult(
            success=True,
            message=f"Contact saved: {c.name} → {c.email}, sir.",
            skill=self.name,
            data={"name": c.name, "email": c.email},
        )
