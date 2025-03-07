# الكود هوا جزء من التطبيق الفاست اي بي اي يتفاعل مع القاعده البيانات ويتحقق من الحضور الاسبوعي للمستخدمين 




from typing import Any  # استيراد Any من مكتبة typing لتحديد أن الدالة قد تُرجع أي نوع من البيانات.

from fastapi import APIRouter, HTTPException  # استيراد APIRouter من FastAPI لإنشاء المسارات (routes)، و HTTPException لإثارة الاستثناءات (مثل الخطأ 404 أو 403).

from sqlmodel import func, select  # استيراد func و select من SQLModel. `func` يستخدم للوصول إلى دوال SQL مثل العد، و `select` لتنفيذ استعلامات SQL.

from app.api.deps import CurrentUser, SessionDep  # استيراد CurrentUser (لتحديد المستخدم الحالي) و SessionDep (لإدارة الجلسات مع قاعدة البيانات) من ملف التبعيات.

from app.models import WeeklyAttendance, WeeklyAttendancesPublic  # استيراد النماذج: WeeklyAttendance لتمثيل بيانات الحضور الأسبوعي، و WeeklyAttendancesPublic لتمثيل البيانات التي سيتم إرسالها في الاستجابة.

router = APIRouter(prefix="/weekly", tags=["weekly"])  # تعريف APIRouter جديد باستخدام البادئة "/weekly"، مما يعني أن جميع المسارات التي سيتم تعريفها ستكون تحت هذا العنوان. الوسم "weekly" يتم إضافته لتحديد تصنيف المسار.

# تعريف مسار GET لقراءة الحضور الأسبوعي للمستخدمين مع استجابة من نوع WeeklyAttendancesPublic.
@router.get("/", response_model=WeeklyAttendancesPublic)  
def read_weekly_attendances(
    session: SessionDep, current_user: CurrentUser, skip: int = 0, limit: int = 100
) -> Any:
    """
    Retrieve weekly attendances.  # تعليق يوضح أن هذه الدالة ستسترجع الحضور الأسبوعي.
    """
    if current_user.is_superuser:  # تحقق مما إذا كان المستخدم الحالي هو مشرف النظام.
        count_statement = select(func.count()).select_from(WeeklyAttendance)  # بناء استعلام لحساب عدد السجلات في جدول WeeklyAttendance.
        count = session.exec(count_statement).one()  # تنفيذ الاستعلام للحصول على العدد الإجمالي للحضور الأسبوعي في قاعدة البيانات.
        statement = select(WeeklyAttendance).offset(skip).limit(limit)  # بناء استعلام لاختيار الحضور الأسبوعي مع تطبيق التصفية باستخدام offset (تخطي بعض السجلات) و limit (تحديد عدد السجلات المسترجعة).
        weekly_attendances = session.exec(statement).all()  # تنفيذ الاستعلام واسترجاع جميع سجلات الحضور الأسبوعي.
    else:  # إذا لم يكن المستخدم مشرفًا.
        count_statement = (  # بناء استعلام لحساب عدد الحضور الأسبوعي للمستخدم الحالي فقط.
            select(func.count())
            .select_from(WeeklyAttendance)
            .where(WeeklyAttendance.user_id == current_user.id)  # تحديد شرط لاختيار الحضور الأسبوعي فقط للمستخدم الحالي.
        )
        count = session.exec(count_statement).one()  # تنفيذ الاستعلام للحصول على العدد الإجمالي لحضور هذا المستخدم فقط.
        statement = (  # بناء استعلام لاختيار سجلات الحضور الأسبوعي للمستخدم الحالي.
            select(WeeklyAttendance)
            .where(WeeklyAttendance.user_id == current_user.id)  # اختيار الحضور الأسبوعي فقط للمستخدم الحالي.
            .offset(skip)
            .limit(limit)  # تطبيق التصفية باستخدام offset و limit لتحديد البيانات التي سيتم إرجاعها.
        )
        weekly_attendances = session.exec(statement).all()  # تنفيذ الاستعلام واسترجاع جميع السجلات للمستخدم الحالي.

    return WeeklyAttendancesPublic(data=weekly_attendances, count=count)  # إرجاع بيانات الحضور الأسبوعي مع العدد الإجمالي للمستخدمين.

# تعريف مسار GET لقراءة الحضور الأسبوعي لمستخدم معين بناءً على معرف المستخدم user_id.
@router.get("/{user_id}", response_model=WeeklyAttendancesPublic)  
def read_weekly_attendance_by_user(
    session: SessionDep, current_user: CurrentUser, user_id: str, skip: int = 0, limit: int = 100
) -> Any:
    """
    Retrieve weekly attendances by user.  # تعليق يوضح أن هذه الدالة ستسترجع الحضور الأسبوعي لمستخدم معين.
    """
    if current_user.is_superuser:  # إذا كان المستخدم الحالي هو مشرف النظام.
        count_statement = select(func.count()).select_from(WeeklyAttendance)  # بناء استعلام لحساب العدد الإجمالي للحضور الأسبوعي.
        count = session.exec(count_statement).one()  # تنفيذ الاستعلام للحصول على العدد الإجمالي.
        statement = select(WeeklyAttendance).where(WeeklyAttendance.user_id == user_id).offset(skip).limit(limit)  # بناء استعلام لاختيار الحضور الأسبوعي لمستخدم معين بناءً على user_id مع تطبيق التصفية باستخدام offset و limit.
        weekly_attendances = session.exec(statement).all()  # تنفيذ الاستعلام واسترجاع سجلات الحضور الأسبوعي للمستخدم المحدد.
    else:  # إذا لم يكن المستخدم مشرفًا.
        raise HTTPException(status_code=403, detail="Forbidden")  # إذا كان المستخدم ليس مشرفًا، يتم إرجاع خطأ 403 (ممنوع) لأنه لا يملك الصلاحيات.

    return WeeklyAttendancesPublic(data=weekly_attendances, count=count)  # إرجاع بيانات الحضور الأسبوعي للمستخدم المحدد مع العدد الإجمالي.
