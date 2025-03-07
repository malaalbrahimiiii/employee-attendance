import logging  # استيراد مكتبة logging لتسجيل السجلات

# تكوين إعدادات تسجيل السجلات
logging.basicConfig(
    filename='backend.log',  # تحديد اسم ملف السجل
    encoding='utf-8',  # تعيين ترميز الملف
    level=logging.DEBUG,  # تحديد مستوى السجلات ليكون DEBUG (أي تسجيل جميع الرسائل)
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',  # تنسيق السجلات
    datefmt='%Y-%m-%d %H:%M:%S'  # تنسيق التاريخ والوقت في السجلات
)

# إنشاء كائن logger الذي سيتم استخدامه لتسجيل السجلات
logger = logging.getLogger(__name__)  # تعيين اسم وحدة التسجيل بناءً على الملف الحالي
