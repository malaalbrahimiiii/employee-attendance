import logging  # استيراد مكتبة logging لتسجيل السجلات
from dataclasses import dataclass  # استيراد dataclass لإنشاء فئة البيانات التي تحتوي على خصائص معينة
from datetime import datetime, timedelta, timezone  # استيراد datetime للعمل مع التواريخ والأوقات
from pathlib import Path  # استيراد Path للتعامل مع مسارات الملفات
from typing import Any  # استيراد Any للسماح بأي نوع بيانات في القوائم أو المعاملات

import emails  # type: ignore  # استيراد مكتبة emails لإرسال رسائل البريد الإلكتروني
import jwt  # استيراد مكتبة jwt للتعامل مع JSON Web Tokens
from jinja2 import Template  # استيراد مكتبة jinja2 لاستخدام القوالب
from jwt.exceptions import InvalidTokenError  # استيراد الاستثناءات الخاصة بمكتبة jwt

from app.core import security  # استيراد الأمان من التطبيق
from app.core.config import settings  # استيراد الإعدادات من ملف الإعدادات الخاص بالتطبيق

logging.basicConfig(level=logging.INFO)  # إعداد مستوى السجلات على INFO
logger = logging.getLogger(__name__)  # إنشاء مسجل لالتقاط السجلات للموديل الحالي

@dataclass  # إنشاء فئة بيانات تحتوي على بيانات البريد الإلكتروني
class EmailData:
    html_content: str  # محتوى البريد الإلكتروني بتنسيق HTML
    subject: str  # موضوع البريد الإلكتروني


def render_email_template(*, template_name: str, context: dict[str, Any]) -> str:
    # دالة لتحميل وتحويل القوالب باستخدام Jinja2
    template_str = (
        Path(__file__).parent / "email-templates" / "build" / template_name
    ).read_text()  # قراءة القالب من المسار المحدد
    html_content = Template(template_str).render(context)  # استخدام Jinja2 لتحويل القالب إلى HTML باستخدام المعطيات
    return html_content


def send_email(
    *,
    email_to: str,
    subject: str = "",
    html_content: str = "",
) -> None:
    # دالة لإرسال البريد الإلكتروني
    assert settings.emails_enabled, "no provided configuration for email variables"  # تأكيد تمكين البريد الإلكتروني في الإعدادات
    message = emails.Message(
        subject=subject,
        html=html_content,
        mail_from=(settings.EMAILS_FROM_NAME, settings.EMAILS_FROM_EMAIL),  # إعداد المرسل
    )
    smtp_options = {"host": settings.SMTP_HOST, "port": settings.SMTP_PORT}  # إعدادات SMTP
    if settings.SMTP_TLS:  # إذا كان يجب استخدام TLS
        smtp_options["tls"] = True
    elif settings.SMTP_SSL:  # إذا كان يجب استخدام SSL
        smtp_options["ssl"] = True
    if settings.SMTP_USER:  # إذا كان هناك اسم مستخدم SMTP
        smtp_options["user"] = settings.SMTP_USER
    if settings.SMTP_PASSWORD:  # إذا كان هناك كلمة مرور SMTP
        smtp_options["password"] = settings.SMTP_PASSWORD
    response = message.send(to=email_to, smtp=smtp_options)  # إرسال الرسالة
    logger.info(f"send email result: {response}")  # تسجيل نتيجة إرسال البريد الإلكتروني


def generate_test_email(email_to: str) -> EmailData:
    # دالة لإنشاء بريد إلكتروني لاختبار الإرسال
    project_name = settings.PROJECT_NAME  # الحصول على اسم المشروع من الإعدادات
    subject = f"{project_name} - Test email"  # إعداد الموضوع
    html_content = render_email_template(
        template_name="test_email.html",  # استخدام قالب البريد الإلكتروني
        context={"project_name": settings.PROJECT_NAME, "email": email_to},  # سياق البيانات التي سيتم تضمينها في القالب
    )
    return EmailData(html_content=html_content, subject=subject)  # إرجاع كائن EmailData يحتوي على المحتوى والموضوع


def generate_reset_password_email(email_to: str, email: str, token: str) -> EmailData:
    # دالة لإنشاء بريد إلكتروني لاستعادة كلمة المرور
    project_name = settings.PROJECT_NAME
    subject = f"{project_name} - Password recovery for user {email}"  # إعداد موضوع البريد
    link = f"{settings.FRONTEND_HOST}/reset-password?token={token}"  # إنشاء الرابط لاستعادة كلمة المرور
    html_content = render_email_template(
        template_name="reset_password.html",  # استخدام القالب المخصص
        context={
            "project_name": settings.PROJECT_NAME,
            "username": email,
            "email": email_to,
            "valid_hours": settings.EMAIL_RESET_TOKEN_EXPIRE_HOURS,
            "link": link,
        },
    )
    return EmailData(html_content=html_content, subject=subject)  # إرجاع بيانات البريد الإلكتروني


def generate_new_account_email(
    email_to: str, username: str, password: str
) -> EmailData:
    # دالة لإنشاء بريد إلكتروني عند إنشاء حساب جديد
    project_name = settings.PROJECT_NAME
    subject = f"{project_name} - New account for user {username}"  # إعداد الموضوع
    html_content = render_email_template(
        template_name="new_account.html",  # استخدام القالب
        context={
            "project_name": settings.PROJECT_NAME,
            "username": username,
            "password": password,
            "email": email_to,
            "link": settings.FRONTEND_HOST,
        },
    )
    return EmailData(html_content=html_content, subject=subject)  # إرجاع بيانات البريد الإلكتروني


def generate_password_reset_token(email: str) -> str:
    # دالة لإنشاء رمز إعادة تعيين كلمة المرور
    delta = timedelta(hours=settings.EMAIL_RESET_TOKEN_EXPIRE_HOURS)  # تحديد مدة صلاحية الرمز
    now = datetime.now(timezone.utc)  # الحصول على الوقت الحالي
    expires = now + delta  # تحديد وقت انتهاء الصلاحية
    exp = expires.timestamp()  # تحويل الوقت إلى طابع زمني
    encoded_jwt = jwt.encode(
        {"exp": exp, "nbf": now, "sub": email},  # البيانات المراد ترميزها في الرمز
        settings.SECRET_KEY,  # المفتاح السري المستخدم في الترميز
        algorithm=security.ALGORITHM,  # الخوارزمية المستخدمة في الترميز
    )
    return encoded_jwt  # إرجاع الرمز المشفر


def verify_password_reset_token(token: str) -> str | None:
    # دالة للتحقق من صحة رمز إعادة تعيين كلمة المرور
    try:
        decoded_token = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[security.ALGORITHM]  # فك الترميز والتحقق من الصلاحية
        )
        return str(decoded_token["sub"])  # إرجاع البريد الإلكتروني من الرمز
    except InvalidTokenError:  # إذا كان الرمز غير صالح
        return None  # إرجاع None في حالة فشل التحقق
