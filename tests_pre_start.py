import logging  # استيراد مكتبة logging لتسجيل السجلات (Logs)

from sqlalchemy import Engine  # استيراد نوع Engine من SQLAlchemy للعمل مع قاعدة البيانات
from sqlmodel import Session, select  # استيراد Session و select من sqlmodel للعمل مع قاعدة البيانات
from tenacity import after_log, before_log, retry, stop_after_attempt, wait_fixed  # استيراد مكتبة Tenacity لتنفيذ المحاولات المتكررة

from app.core.db import engine  # استيراد المحرك (engine) من ملف db في التطبيق

logging.basicConfig(level=logging.INFO)  # إعداد السجلات على مستوى INFO
logger = logging.getLogger(__name__)  # إنشاء مسجل خاص للموديل الحالي (تسمية السجلات بناءً على اسم الموديل)

max_tries = 60 * 5  # 5 minutes  # تحديد الحد الأقصى لعدد المحاولات (5 دقائق)
wait_seconds = 1  # تحديد وقت الانتظار بين كل محاولة وأخرى (1 ثانية)


@retry(
    stop=stop_after_attempt(max_tries),  # التوقف بعد عدد معين من المحاولات
    wait=wait_fixed(wait_seconds),  # تحديد وقت الانتظار الثابت بين المحاولات
    before=before_log(logger, logging.INFO),  # تسجيل رسالة قبل المحاولة في مستوى INFO
    after=after_log(logger, logging.WARN),  # تسجيل رسالة بعد المحاولة في مستوى WARN
)
def init(db_engine: Engine) -> None:  # دالة لتفعيل المحاولة المتكررة للاتصال بقاعدة البيانات
    try:
        # Try to create session to check if DB is awake  # محاولة إنشاء جلسة للتحقق من ما إذا كانت قاعدة البيانات نشطة
        with Session(db_engine) as session:  # فتح جلسة باستخدام المحرك (engine) المرسل
            session.exec(select(1))  # تنفيذ استعلام بسيط لاختبار الاتصال بقاعدة البيانات
    except Exception as e:  # إذا حدث استثناء أثناء محاولة الاتصال
        logger.error(e)  # تسجيل الخطأ في السجلات
        raise e  # رفع الاستثناء مرة أخرى ليتم معالجته لاحقًا


def main() -> None:  # الدالة الرئيسية لتنفيذ التطبيق
    logger.info("Initializing service")  # تسجيل رسالة عند بدء تهيئة الخدمة
    init(engine)  # استدعاء دالة init لتهيئة الاتصال بقاعدة البيانات
    logger.info("Service finished initializing")  # تسجيل رسالة عند الانتهاء من تهيئة الخدمة


if __name__ == "__main__":  # إذا تم تشغيل الملف كبرنامج رئيسي
    main()  # استدعاء الدالة الرئيسية
