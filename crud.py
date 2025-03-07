#الكود يحتوي على عدة دوال للتعامل مع الكيانات المختلفة في قاعدة البيانات مثل المستخدمين والعناصر وحضور المستخدمين سواء يوميًا أو أسبوعيًا.

import calendar  # استيراد مكتبة calendar للعمل مع تواريخ وتقويمات معينة
import uuid  # استيراد مكتبة uuid لإنشاء معرفات فريدة
from typing import Any  # استيراد Any من مكتبة typing لتحديد أنواع البيانات العامة
from datetime import datetime, time, timedelta  # استيراد datetime وtime وtimedelta للعمل مع التواريخ والأوقات
from sqlmodel import Session, select, func  # استيراد الأدوات اللازمة للتعامل مع قاعدة البيانات باستخدام SQLModel

from app.core.security import get_password_hash, verify_password  # استيراد دوال للتشفير والتحقق من كلمات المرور
from app.models import Item, ItemCreate, User, UserCreate, UserUpdate, DailyAttendance, Attendance, WeeklyAttendance  # استيراد النماذج التي تمثل الكيانات في قاعدة البيانات
from app.logger import logger  # استيراد logger لتسجيل السجلات

def create_user(*, session: Session, user_create: UserCreate) -> User:
    db_obj = User.model_validate(
        user_create, update={"hashed_password": get_password_hash(user_create.password)}
    )  # إنشاء كائن مستخدم جديد باستخدام المدخلات وتشفير كلمة المرور
    session.add(db_obj)  # إضافة المستخدم إلى الجلسة
    session.commit()  # حفظ التغييرات في قاعدة البيانات
    session.refresh(db_obj)  # تحديث الكائن المضاف بالبيانات المحفوظة
    logger.info(f"User created: {db_obj.email}")  # تسجيل المعلومات حول المستخدم المنشأ
    return db_obj  # إرجاع الكائن المستخدم الذي تم إنشاؤه

def update_user(*, session: Session, db_user: User, user_in: UserUpdate) -> Any:
    user_data = user_in.model_dump(exclude_unset=True)  # استخراج البيانات المدخلة من نموذج التحديث
    extra_data = {}  # تخزين البيانات الإضافية التي ستتم إضافتها
    if "password" in user_data:  # إذا كانت كلمة المرور موجودة في البيانات
        password = user_data["password"]
        hashed_password = get_password_hash(password)  # تشفير كلمة المرور الجديدة
        extra_data["hashed_password"] = hashed_password  # إضافة كلمة المرور المشفرة إلى البيانات الإضافية
    db_user.sqlmodel_update(user_data, update=extra_data)  # تحديث المستخدم في قاعدة البيانات
    session.add(db_user)  # إضافة التحديثات إلى الجلسة
    session.commit()  # حفظ التغييرات
    session.refresh(db_user)  # تحديث الكائن بالبيانات الجديدة
    logger.info(f"User updated: {db_user.email}")  # تسجيل تحديث المستخدم
    return db_user  # إرجاع الكائن المستخدم المحدث

def get_user_by_email(*, session: Session, email: str) -> User | None:
    statement = select(User).where(User.email == email)  # بناء استعلام للبحث عن المستخدم بناءً على البريد الإلكتروني
    session_user = session.exec(statement).first()  # تنفيذ الاستعلام واسترجاع أول مستخدم مطابق
    logger.info(f"User found: {email}")  # تسجيل العثور على المستخدم
    return session_user  # إرجاع المستخدم الموجود أو None إذا لم يتم العثور عليه

def authenticate(*, session: Session, email: str, password: str) -> User | None:
    db_user = get_user_by_email(session=session, email=email)  # استرجاع المستخدم باستخدام البريد الإلكتروني
    if not db_user:  # إذا لم يتم العثور على المستخدم
        return None
    if not verify_password(password, db_user.hashed_password):  # التحقق من تطابق كلمة المرور المدخلة مع المشفرة
        return None
    logger.info(f"User authenticated: {db_user.email}")  # تسجيل أن المستخدم تم توثيقه
    return db_user  # إرجاع المستخدم بعد التحقق من كلمة المرور

def create_item(*, session: Session, item_in: ItemCreate, owner_id: uuid.UUID) -> Item:
    db_item = Item.model_validate(item_in, update={"owner_id": owner_id})  # إنشاء عنصر جديد باستخدام البيانات المدخلة
    session.add(db_item)  # إضافة العنصر إلى الجلسة
    session.commit()  # حفظ التغييرات في قاعدة البيانات
    session.refresh(db_item)  # تحديث العنصر بالبيانات المحفوظة
    return db_item  # إرجاع العنصر الذي تم إنشاؤه

def create_daily_attendance(
        *, session: Session, 
        user_id: uuid.UUID, 
        full_name: str,
        attend_id: int,
        date: datetime) -> DailyAttendance:
    db_attendance_statement = (select(Attendance)
    .where(Attendance.user_id == user_id)
    .where(func.date(Attendance.created_at) == date.date()))  # استعلام للتحقق من حضور المستخدم في اليوم المحدد
    db_attendance = session.exec(db_attendance_statement).all()  # تنفيذ الاستعلام واسترجاع الحضور
    if len(db_attendance) < 2:  # التحقق من وجود سجلين على الأقل (دخول وخروج)
        raise ValueError("Insufficient attendance records for today")  # إذا لم يكن هناك سجلات كافية
    check_in_time = db_attendance[0].created_at  # الوقت الذي سجل فيه الدخول
    check_out_time = db_attendance[1].created_at  # الوقت الذي سجل فيه الخروج
    daily_attendance_hours = (check_out_time - check_in_time).total_seconds() / 3600  # حساب عدد ساعات الحضور
    db_daily_attendance = DailyAttendance(daily_attendance_hours=daily_attendance_hours, user_id=user_id,
                                          full_name=full_name, attend_id=attend_id)  # إنشاء سجل حضور يومي
    session.add(db_daily_attendance)  # إضافة السجل إلى الجلسة
    session.commit()  # حفظ التغييرات
    session.refresh(db_daily_attendance)  # تحديث السجل بالبيانات المحفوظة
    logger.info(f"Daily attendance created: {db_daily_attendance.user_id}")  # تسجيل إنشاء السجل
    return db_daily_attendance  # إرجاع السجل الذي تم إنشاؤه

def create_weekly_attendance_or_update(
        *, session: Session,                        
        user_id: uuid.UUID,
        full_name: str,
        attend_id: int,
        daily_attendance_hours: int, 
        date: datetime
        ) -> WeeklyAttendance:
    today = date  # استخدام التاريخ الحالي
    start_date = today - timedelta(days=today.weekday())  # بداية الأسبوع (يوم الإثنين)
    end_date = start_date + timedelta(days=6)  # نهاية الأسبوع (يوم الأحد)
    db_weekly_attendance_statement = (select(WeeklyAttendance)
    .where(WeeklyAttendance.user_id == user_id)
    .where(func.date(WeeklyAttendance.start_date) <= date.date())
    .where(func.date(WeeklyAttendance.end_date) >= date.date()))  # استعلام للتحقق من سجل الحضور الأسبوعي
    db_weekly_attendance = session.exec(db_weekly_attendance_statement).first()  # استرجاع سجل الحضور الأسبوعي إذا وجد
    if db_weekly_attendance:
        db_weekly_attendance.weekly_attendance_hours += daily_attendance_hours  # تحديث ساعات الحضور الأسبوعية
    else:
        db_weekly_attendance = WeeklyAttendance(
            user_id=user_id, 
            start_date=start_date, 
            end_date=end_date, 
            weekly_attendance_hours=daily_attendance_hours,
            full_name=full_name,
            attend_id=attend_id)  # إنشاء سجل جديد لحضور أسبوعي
    session.add(db_weekly_attendance)  # إضافة السجل إلى الجلسة
    session.commit()  # حفظ التغييرات
    session.refresh(db_weekly_attendance)  # تحديث السجل بالبيانات المحفوظة
    logger.info(f"Weekly attendance created: {db_weekly_attendance.user_id}")  # تسجيل إنشاء السجل
    return db_weekly_attendance  # إرجاع السجل الذي تم إنشاؤه أو تحديثه
