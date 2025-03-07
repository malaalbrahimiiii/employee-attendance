
# هذا الكود يتعامل مع جزء من تطبيق الفاست اي بي اي و يهدف الى اداره الحضور اليوميي للمستخدمين 
# يتمصن رواتي لاسترجاع الحضور اليومي للمستخدمين 
#على حسب صلاحياته الى كان المستخديم يوزر او مشرفا او غير مشرف 



from typing import Any  # استيراد Any من مكتبة typing للسماح باستخدام أنواع متعددة في الأنواع التوضيحية

from fastapi import APIRouter, HTTPException  # استيراد الأدوات الخاصة بـ FastAPI لإنشاء المسارات والتعامل مع الأخطاء
from sqlmodel import func, select  # استيراد الأدوات الخاصة بـ SQLModel للتفاعل مع قاعدة البيانات

from app.api.deps import CurrentUser, SessionDep  # استيراد التبعيات مثل المستخدم الحالي وSession
from app.models import DailyAttendance, DailyAttendancesPublic  # استيراد نماذج الحضور اليومي والمخرجات العامة للحضور اليومي

router = APIRouter(prefix="/daily", tags=["daily"])  # إنشاء مسار جديد في FastAPI مع تعيين البادئة '/daily' والوسم 'daily'

# استرجاع الحضور اليومي
@router.get("/", response_model=DailyAttendancesPublic)
def read_daily_attendances(
    session: SessionDep, current_user: CurrentUser, skip: int = 0, limit: int = 100
) -> Any:
    """
    Retrieve daily attendances.
    """
    # إذا كان المستخدم مشرفًا (superuser)، استرجاع جميع الحضور اليومي
    if current_user.is_superuser:
        count_statement = select(func.count()).select_from(DailyAttendance)  # استعلام لحساب عدد الحضور اليومي
        count = session.exec(count_statement).one()  # تنفيذ الاستعلام للحصول على العدد الإجمالي
        statement = select(DailyAttendance).offset(skip).limit(limit)  # استعلام لاسترجاع الحضور اليومي مع إمكانية تخطي وعرض عدد معين
        daily_attendances = session.exec(statement).all()  # تنفيذ الاستعلام للحصول على جميع الحضور
    else:
        # إذا لم يكن المستخدم مشرفًا، استرجاع الحضور اليومي الخاص بالمستخدم فقط
        count_statement = (
            select(func.count())
            .select_from(DailyAttendance)
            .where(DailyAttendance.user_id == current_user.id)  # تحديد الحضور بناءً على معرف المستخدم الحالي
        )
        count = session.exec(count_statement).one()  # تنفيذ الاستعلام للحصول على العدد الإجمالي
        statement = (
            select(DailyAttendance)
            .where(DailyAttendance.user_id == current_user.id)
            .offset(skip)
            .limit(limit)
        )  # استعلام لاسترجاع الحضور اليومي للمستخدم الحالي فقط
        daily_attendances = session.exec(statement).all()  # تنفيذ الاستعلام للحصول على الحضور اليومي للمستخدم الحالي

    return DailyAttendancesPublic(data=daily_attendances, count=count)  # إرجاع الحضور اليومي مع العدد الإجمالي في نموذج DailyAttendancesPublic

# استرجاع الحضور اليومي حسب المستخدم
@router.get("/{user_id}", response_model=DailyAttendancesPublic)
def read_daily_attendance_by_user(
    session: SessionDep, current_user: CurrentUser, user_id: str, skip: int = 0, limit: int = 100
) -> Any:
    """
    Retrieve daily attendances by user.
    """
    # إذا كان المستخدم مشرفًا (superuser)، استرجاع الحضور اليومي بناءً على user_id
    if current_user.is_superuser:
        count_statement = select(func.count()).select_from(DailyAttendance)  # استعلام لحساب عدد الحضور اليومي
        count = session.exec(count_statement).one()  # تنفيذ الاستعلام للحصول على العدد الإجمالي
        statement = select(DailyAttendance).where(DailyAttendance.user_id == user_id).offset(skip).limit(limit)  # استعلام لاسترجاع الحضور بناءً على معرف المستخدم
        daily_attendances = session.exec(statement).all()  # تنفيذ الاستعلام للحصول على الحضور للمستخدم المحدد
    else:
        # إذا لم يكن المستخدم مشرفًا، إرجاع خطأ 403 (ممنوع)
        raise HTTPException(status_code=403, detail="Forbidden")

    return DailyAttendancesPublic(data=daily_attendances, count=count)  # إرجاع الحضور اليومي للمستخدم المحدد مع العدد الإجمالي في نموذج DailyAttendancesPublic
