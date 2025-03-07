import sentry_sdk  # استيراد مكتبة Sentry لإدارة الأخطاء والتتبع
from fastapi import FastAPI  # استيراد FastAPI لإنشاء تطبيق API
from fastapi.routing import APIRoute  # استيراد APIRoute لتخصيص هوية المسارات
from starlette.middleware.cors import CORSMiddleware  # استيراد CORSMiddleware لإدارة CORS

from app.api.main import api_router  # استيراد الرواتر الأساسي من تطبيقك
from app.core.config import settings  # استيراد الإعدادات من ملف التكوين


def custom_generate_unique_id(route: APIRoute) -> str:
    """توليد هوية فريدة للمسارات باستخدام العلامات (tags) وأسمائها."""
    return f"{route.tags[0]}-{route.name}"


# تهيئة Sentry إذا تم توفير DSN ولا يوجد في البيئة المحلية
if settings.SENTRY_DSN and settings.ENVIRONMENT != "local":
    sentry_sdk.init(dsn=str(settings.SENTRY_DSN), enable_tracing=True)

# إنشاء تطبيق FastAPI مع تخصيص بعض الإعدادات
app = FastAPI(
    title=settings.PROJECT_NAME,  # عنوان المشروع
    openapi_url=f"{settings.API_V1_STR}/openapi.json",  # تحديد رابط OpenAPI
    generate_unique_id_function=custom_generate_unique_id,  # تخصيص طريقة توليد الهوية الفريدة للمسارات
)

# إضافة middleware لإعداد CORS (Cross-Origin Resource Sharing)
if settings.all_cors_origins:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.all_cors_origins,  # السماح بالأصول المصرح بها
        allow_credentials=True,  # السماح بالتحقق من الهوية
        allow_methods=["*"],  # السماح بجميع الطرق (GET، POST، إلخ)
        allow_headers=["*"],  # السماح بجميع الرؤوس
    )

# تضمين الرواتر الأساسي للمسارات
app.include_router(api_router, prefix=settings.API_V1_STR)
