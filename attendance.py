# هذا الكود عباره مجموعه من الدوال الخاصه بحضور باستخدام الفاست اي بي اي 
# يتعامل مه تسجيل الحضور للمستخدمين مثل تسجيل الخروج ، تسجيل الحضور 
# ويشمل علميات اخرى مثل استرجاع حضور وتحديثه 

import uuid  # استيراد مكتبة UUID لإنشاء معرفات فريدة
from datetime import datetime, time  # استيراد مكتبات للتعامل مع التاريخ والوقت
from typing import Any  # استيراد Any للسماح بأنواع البيانات المتعددة في الأنواع التوضيحية

from app.logger import logger  # استيراد وحدة التسجيل (logging) من app.logger لكتابة السجلات

from fastapi import APIRouter, HTTPException  # استيراد الأدوات الخاصة بـ FastAPI لإنشاء المسارات والتعامل مع الأخطاء
from sqlmodel import func, select  # استيراد الأدوات الخاصة بـ SQLModel للتفاعل مع قاعدة البيانات

from app.crud import create_daily_attendance, create_weekly_attendance_or_update  # استيراد الوظائف الخاصة بإضافة الحضور اليومي والأسبوعي
from app.api.deps import CurrentUser, SessionDep  # استيراد التبعيات (dependencies) مثل المستخدم الحالي وSession
from app.models import (
    Attendance,  # استيراد نموذج الحضور
    AttendancePublic,  # استيراد نموذج الحضور الذي سيتم إرجاعه للمستخدم
    AttendancesPublic,  # استيراد نموذج قائمة الحضور
    AttendanceUpdate,  # استيراد نموذج لتحديث الحضور
    Message,  # استيراد نموذج الرسالة لإرجاعها للمستخدم
    User,  # استيراد نموذج المستخدم
)

router = APIRouter(prefix="/attend", tags=["attend"])  # إنشاء مسار جديد في FastAPI مع تعيين البادئة '/attend' والوسم 'attend'

# استرجاع الحضور
@router.get("/", response_model=AttendancesPublic)
def read_attends(
    session: SessionDep, current_user: CurrentUser, skip: int = 0, limit: int = 100
) -> Any:
    """
    Retrieve attendances.
    """
    # تحقق من ما إذا كان المستخدم هو مشرف (superuser)
    if current_user.is_superuser:
        count_statement = select(func.count()).select_from(Attendance)  # حساب عدد الحضور في قاعدة البيانات
        count = session.exec(count_statement).one()  # تنفيذ الاستعلام للحصول على العدد الإجمالي
        statement = select(Attendance).offset(skip).limit(limit)  # استعلام للحصول على الحضور مع إمكانية تخطي وعرض عدد معين من الحضور
        attendances = session.exec(statement).all()  # تنفيذ الاستعلام للحصول على جميع الحضور
        logger.info(f"Attendances retrieved: {len(attendances)}")  # تسجيل عدد الحضور المسترجع
    else:
        # في حال لم يكن المستخدم مشرفًا، احصل على الحضور الخاص بالمستخدم فقط
        count_statement = (
            select(func.count())
            .select_from(Attendance)
            .where(Attendance.user_id == current_user.id)  # تحديد الحضور بناءً على معرف المستخدم
        )
        count = session.exec(count_statement).one()  # تنفيذ الاستعلام للحصول على العدد الإجمالي
        statement = (
            select(Attendance)
            .where(Attendance.user_id == current_user.id)
            .offset(skip)
            .limit(limit)
        )  # استعلام للحصول على الحضور للمستخدم الحالي فقط
        attendances = session.exec(statement).all()  # تنفيذ الاستعلام للحصول على الحضور للمستخدم الحالي
        logger.info(f"Attendances retrieved: {len(attendances)}")  # تسجيل عدد الحضور المسترجع
    return AttendancesPublic(data=attendances, count=count)  # إرجاع الحضور مع العدد الإجمالي في نموذج AttendancesPublic

# إنشاء الحضور (check-in / check-out)
@router.post("/{attend_id}", response_model=Message)
def create_attend(*, session: SessionDep, attend_id: int) -> Any:
    """
    Create attendance.
    """
    time_now = datetime.now().time()  # الحصول على الوقت الحالي
    today = datetime.today()  # الحصول على التاريخ الحالي
    if time_now < time(8, 0, 0):  # إذا كان الوقت قبل الساعة 8 صباحًا
        return Message(message="Attendance is not allowed before 8:00 AM")  # إرجاع رسالة تمنع تسجيل الحضور قبل الساعة 8 صباحًا
    
    db_user_statement = select(User).where(User.attend_id == attend_id)  # استعلام للبحث عن المستخدم بناءً على attend_id
    db_user = session.exec(db_user_statement).one()  # تنفيذ الاستعلام للحصول على المستخدم
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")  # إذا لم يتم العثور على المستخدم، إرجاع خطأ 404
    
    db_attendance_statement = (select(Attendance)
    .where(Attendance.user_id == db_user.id)
    .where(func.date(Attendance.created_at) == today.date()))  # استعلام للتحقق إذا كان المستخدم قد سجل الحضور اليوم
    db_attendance = session.exec(db_attendance_statement).all()  # تنفيذ الاستعلام للحصول على الحضور اليومي للمستخدم

    # إذا لم يكن هناك أي سجل حضور لهذا المستخدم اليوم
    if len(db_attendance) == 0:
        if time_now < time(8, 30, 0):  # إذا كان الوقت قبل الساعة 8:30 صباحًا
            record_attendance = Attendance(user_id=db_user.id, status=True, type_attendance="check-in", reason="", 
                                           full_name=db_user.full_name, attend_id=db_user.attend_id)  # إنشاء سجل حضور جديد
            session.add(record_attendance)  # إضافة السجل إلى الجلسة
            session.commit()  # تأكيد التغييرات في قاعدة البيانات
            session.refresh(record_attendance)  # تحديث السجل
            logger.info(f"Attendance check-in created successfully: {record_attendance.user_id}")  # تسجيل رسالة بنجاح إنشاء الحضور
            return Message(message="Attendance check-in created successfully")  # إرجاع رسالة نجاح
        else:  # إذا كان الوقت بعد الساعة 8:30 صباحًا
            record_attendance = Attendance(user_id=db_user.id, status=False, type_attendance="check-in", reason="", 
                                           full_name=db_user.full_name, attend_id=db_user.attend_id)  # سجل الحضور مع التأخير
            session.add(record_attendance)  # إضافة السجل إلى الجلسة
            session.commit()  # تأكيد التغييرات في قاعدة البيانات
            session.refresh(record_attendance)  # تحديث السجل
            logger.info(f"Attendance check-in created successfully but late: {record_attendance.user_id}")  # تسجيل رسالة عن التأخير
            return Message(message="Attendance check-in created successfully but late")  # إرجاع رسالة تأكيد الحضور لكن متأخر
    if len(db_attendance) == 1:  # إذا كان هناك سجل واحد (أي تم تسجيل الحضور لهذا المستخدم في الصباح)
        if time_now > time(15, 0, 0):  # إذا كان الوقت بعد الساعة 3 مساءً
            record_attendance = Attendance(user_id=db_user.id, status=True, type_attendance="check-out", reason="", 
                                           full_name=db_user.full_name, attend_id=db_user.attend_id)  # إنشاء سجل خروج
            session.add(record_attendance)  # إضافة السجل إلى الجلسة
            session.commit()  # تأكيد التغييرات في قاعدة البيانات
            session.refresh(record_attendance)  # تحديث السجل
            db_daily_attendance = create_daily_attendance(
                session=session, user_id=db_user.id, full_name=db_user.full_name, attend_id=db_user.attend_id, date=today)  # إنشاء سجل الحضور اليومي
            db_weekly_attendance = create_weekly_attendance_or_update(session=session, 
                                                                      user_id=db_user.id, 
                                                                      daily_attendance_hours=db_daily_attendance.daily_attendance_hours,
                                                                      date=today)  # إنشاء أو تحديث الحضور الأسبوعي
            logger.info(f"Attendance check-out created successfully: {record_attendance.user_id}")  # تسجيل رسالة نجاح الخروج
            return Message(message="Attendance check-out created successfully")  # إرجاع رسالة نجاح الخروج
        else:  # إذا كان الوقت قبل الساعة 3 مساءً
            record_attendance = Attendance(user_id=db_user.id, status=False, type_attendance="check-out", reason="", 
                                           full_name=db_user.full_name, attend_id=db_user.attend_id)  # سجل خروج مبكر
            session.add(record_attendance)  # إضافة السجل إلى الجلسة
            session.commit()  # تأكيد التغييرات في قاعدة البيانات
            session.refresh(record_attendance)  # تحديث السجل
            db_daily_attendance = create_daily_attendance(
                session=session, user_id=db_user.id, 
                full_name=db_user.full_name, attend_id=db_user.attend_id, date=today)  # إنشاء سجل الحضور اليومي
            db_weekly_attendance = create_weekly_attendance_or_update(session=session, 
                                                                      user_id=db_user.id, 
                                                                      daily_attendance_hours=db_daily_attendance.daily_attendance_hours,
                                                                      date=today)  # إنشاء أو تحديث الحضور الأسبوعي
            logger.info(f"Attendance check-out created successfully but early: {record_attendance.user_id}")  # تسجيل رسالة عن الخروج المبكر
            return Message(message="Attendance check-out created successfully but early")  # إرجاع رسالة عن الخروج المبكر
    return Message(message="The user has already checked in today")  # إذا كان المستخدم قد سجل الحضور مسبقًا اليوم، إرجاع رسالة

# تحديث الحضور
@router.put("/{id}", response_model=AttendancePublic)
def update_attendance(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    id: uuid.UUID,
    attendance_in: AttendanceUpdate,
) -> Any:
    """
    Update an Attendance.
    """
    attendance = session.get(Attendance, id)  # الحصول على سجل الحضور بناءً على معرف الحضور
    if not attendance:
        raise HTTPException(status_code=404, detail="Attendance not found")  # إذا لم يتم العثور على الحضور، إرجاع خطأ 404
    if not current_user.is_superuser and (attendance.user_id != current_user.id):  # إذا لم يكن المستخدم مشرفًا أو صاحب الحضور
        raise HTTPException(status_code=400, detail="Not enough permissions")  # إرجاع خطأ 400 إذا لم يكن للمستخدم الصلاحية
    update_dict = attendance_in.model_dump(exclude_unset=True)  # تحويل النموذج المدخل إلى قاموس مع استبعاد القيم غير المحددة
    attendance.sqlmodel_update(update_dict)  # تحديث الحضور في قاعدة البيانات
    session.add(attendance)  # إضافة التحديث إلى الجلسة
    session.commit()  # تأكيد التغييرات
    session.refresh(attendance)  # تحديث السجل
    logger.info(f"Attendance updated: {attendance.user_id}")  # تسجيل رسالة بنجاح التحديث
    return attendance  # إرجاع السجل المحدث للمستخدم
