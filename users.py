# هذا الكود جزء من تطبيق فاست اي بي اي لاداره المستخدمين مع مجموعه من العمليات 
#المرتبطة بالمستخدمين  مثلا الانشاء والقراء ، الحدف ، بالاضافه التحقق من الادونات 
# والتحكم في الوصول بناء على حاله المستخدم من مثل المشرف 


import uuid  # استيراد uuid لإنشاء معرّفات فريدة للمستخدمين (مثل معرف المستخدم).
from typing import Any  # استيراد Any من مكتبة typing للسماح باستخدام أنواع بيانات مرنة.

from fastapi import APIRouter, Depends, HTTPException  # استيراد APIRouter لإنشاء المسارات و Depends و HTTPException لإدارة التبعيات والاستثناءات.
from sqlmodel import col, delete, func, select  # استيراد الأدوات اللازمة للتعامل مع SQL باستخدام SQLModel.

from app.logger import logger  # استيراد logger لتسجيل الأحداث.
from app import crud  # استيراد crud (عمليات قاعدة البيانات) مثل الحصول على مستخدم أو تحديثه.
from app.api.deps import (
    CurrentUser,  # استيراد التابع الذي يحدد المستخدم الحالي.
    SessionDep,  # استيراد التابع الخاص بالجلسة (session).
    get_current_active_superuser,  # استيراد التابع للتحقق من حالة المستخدم المشرف (superuser).
)
from app.core.config import settings  # استيراد الإعدادات من التطبيق.
from app.core.security import get_password_hash, verify_password  # استيراد وظائف التعامل مع كلمات المرور.
from app.models import (
    Item,  # استيراد نموذج Item (المنتج أو العنصر).
    Message,  # استيراد نموذج Message لإرجاع رسائل بسيطة مثل "تم الحذف بنجاح".
    UpdatePassword,  # استيراد نموذج UpdatePassword لتحديث كلمة المرور.
    User,  # استيراد نموذج User للمستخدمين.
    UserCreate,  # استيراد نموذج UserCreate لإنشاء مستخدم جديد.
    UserPublic,  # استيراد نموذج UserPublic لتمثيل المستخدم في الردود.
    UserRegister,  # استيراد نموذج UserRegister لتمثيل المستخدم عند التسجيل.
    UsersPublic,  # استيراد نموذج UsersPublic لتمثيل قائمة المستخدمين.
    UserUpdate,  # استيراد نموذج UserUpdate لتحديث بيانات المستخدم.
    UserUpdateMe,  # استيراد نموذج UserUpdateMe لتحديث بيانات المستخدم الحالي.
)
from app.utils import generate_new_account_email, send_email  # استيراد وظائف إرسال البريد الإلكتروني وتوليد محتوى البريد.

router = APIRouter(prefix="/users", tags=["users"])  # إنشاء مسار جديد للمستخدمين مع البادئة "/users" والوسم "users" للمسارات.

# مسار لقراءة المستخدمين.
@router.get(
    "/",
    dependencies=[Depends(get_current_active_superuser)],  # فقط المشرفين يمكنهم الوصول إلى هذا المسار.
    response_model=UsersPublic,  # نموذج البيانات الذي سيتم إرجاعه.
)
def read_users(session: SessionDep, skip: int = 0, limit: int = 100) -> Any:
    """
    Retrieve users.
    """
    count_statement = select(func.count()).select_from(User)  # حساب العدد الإجمالي للمستخدمين.
    count = session.exec(count_statement).one()  # تنفيذ الاستعلام للحصول على العدد.

    statement = select(User).offset(skip).limit(limit)  # جلب المستخدمين مع التحديد حسب قيمة skip و limit.
    users = session.exec(statement).all()  # تنفيذ الاستعلام لاسترجاع المستخدمين.

    return UsersPublic(data=users, count=count)  # إرجاع البيانات في نموذج UsersPublic.

# مسار لإنشاء مستخدم جديد.
@router.post(
    "/", dependencies=[Depends(get_current_active_superuser)], response_model=UserPublic
)
def create_user(*, session: SessionDep, user_in: UserCreate) -> Any:
    """
    Create new user.
    """
    user = crud.get_user_by_email(session=session, email=user_in.email)  # التحقق مما إذا كان المستخدم موجودًا بالفعل.
    if user:
        raise HTTPException(
            status_code=400,
            detail="The user with this email already exists in the system.",
        )  # إذا كان المستخدم موجودًا، إرجاع خطأ.

    user = crud.create_user(session=session, user_create=user_in)  # إنشاء المستخدم في قاعدة البيانات.
    if settings.emails_enabled and user_in.email:  # إذا كانت إعدادات البريد الإلكتروني مفعلّة.
        email_data = generate_new_account_email(
            email_to=user_in.email, username=user_in.email, password=user_in.password
        )  # توليد محتوى البريد الإلكتروني.
        send_email(
            email_to=user_in.email,
            subject=email_data.subject,
            html_content=email_data.html_content,
        )  # إرسال البريد الإلكتروني للمستخدم.

    return user  # إرجاع المستخدم الجديد.

# مسار لتحديث بيانات المستخدم الحالي.
@router.patch("/me", response_model=UserPublic)
def update_user_me(
    *, session: SessionDep, user_in: UserUpdateMe, current_user: CurrentUser
) -> Any:
    """
    Update own user.
    """
    if user_in.email:  # التحقق من إذا كان المستخدم يريد تغيير بريده الإلكتروني.
        existing_user = crud.get_user_by_email(session=session, email=user_in.email)
        if existing_user and existing_user.id != current_user.id:
            raise HTTPException(
                status_code=409, detail="User with this email already exists"
            )  # إذا كان البريد الإلكتروني موجودًا بالفعل.

    user_data = user_in.model_dump(exclude_unset=True)  # تحويل البيانات المدخلة إلى قاموس.
    current_user.sqlmodel_update(user_data)  # تحديث المستخدم.
    session.add(current_user)  # إضافة التغييرات إلى الجلسة.
    session.commit()  # تنفيذ التغييرات في قاعدة البيانات.
    session.refresh(current_user)  # تحديث الكائن في الذاكرة.

    logger.info(f"User updated: {current_user.email}")  # تسجيل الحدث.
    return current_user  # إرجاع المستخدم المحدث.

# مسار لتحديث كلمة مرور المستخدم الحالي.
@router.patch("/me/password", response_model=Message)
def update_password_me(
    *, session: SessionDep, body: UpdatePassword, current_user: CurrentUser
) -> Any:
    """
    Update own password.
    """
    if not verify_password(body.current_password, current_user.hashed_password):
        raise HTTPException(status_code=400, detail="Incorrect password")  # التحقق من كلمة المرور الحالية.
    if body.current_password == body.new_password:
        raise HTTPException(
            status_code=400, detail="New password cannot be the same as the current one"
        )  # التأكد من أن كلمة المرور الجديدة ليست نفسها القديمة.

    hashed_password = get_password_hash(body.new_password)  # توليد هاش لكلمة المرور الجديدة.
    current_user.hashed_password = hashed_password  # تحديث كلمة المرور في الكائن.
    session.add(current_user)  # إضافة التغييرات إلى الجلسة.
    session.commit()  # تنفيذ التغييرات في قاعدة البيانات.

    logger.info(f"Password updated: {current_user.email}")  # تسجيل الحدث.
    return Message(message="Password updated successfully")  # إرجاع رسالة نجاح.

# مسار لقراءة بيانات المستخدم الحالي.
@router.get("/me", response_model=UserPublic)
def read_user_me(current_user: CurrentUser) -> Any:
    """
    Get current user.
    """
    return current_user  # إرجاع بيانات المستخدم الحالي.

# مسار لحذف المستخدم الحالي.
@router.delete("/me", response_model=Message)
def delete_user_me(session: SessionDep, current_user: CurrentUser) -> Any:
    """
    Delete own user.
    """
    if current_user.is_superuser:
        raise HTTPException(
            status_code=403, detail="Super users are not allowed to delete themselves"
        )  # منع المشرفين من حذف أنفسهم.

    session.delete(current_user)  # حذف المستخدم من قاعدة البيانات.
    session.commit()  # تنفيذ التغييرات في قاعدة البيانات.

    logger.info(f"User deleted: {current_user.email}")  # تسجيل الحدث.
    return Message(message="User deleted successfully")  # إرجاع رسالة نجاح.

# مسار لتسجيل مستخدم جديد.
@router.post("/signup", response_model=UserPublic)
def register_user(session: SessionDep, user_in: UserRegister) -> Any:
    """
    Create new user without the need to be logged in.
    """
    user = crud.get_user_by_email(session=session, email=user_in.email)  # التحقق مما إذا كان المستخدم موجودًا بالفعل.
    if user:
        raise HTTPException(
            status_code=400,
            detail="The user with this email already exists in the system",
        )  # إذا كان المستخدم موجودًا بالفعل.

    user_create = UserCreate.model_validate(user_in)  # تحويل البيانات المدخلة إلى نموذج UserCreate.
    user = crud.create_user(session=session, user_create=user_create)  # إنشاء المستخدم في قاعدة البيانات.

    logger.info(f"User created: {user.email}")  # تسجيل الحدث.
    return user  # إرجاع المستخدم الجديد.

# مسار لقراءة بيانات مستخدم بناءً على معرّف المستخدم.
@router.get("/{user_id}", response_model=UserPublic)
def read_user_by_id(
    user_id: uuid.UUID, session: SessionDep, current_user: CurrentUser
) -> Any:
    """
    Get a specific user by id.
    """
    user = session.get(User, user_id)  # استرجاع المستخدم من قاعدة البيانات باستخدام المعرّف.
    if user == current_user:
        return user  # إذا كان المستخدم هو نفسه المستخدم الحالي، إرجاع بياناته.
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=403,
            detail="The user doesn't have enough privileges",
        )  # إذا لم يكن المستخدم مشرفًا، إرجاع خطأ.
    
    logger.info(f"User retrieved: {user.email}")  # تسجيل الحدث.
    return user  # إرجاع بيانات المستخدم.

# مسار لتحديث بيانات مستخدم باستخدام معرّف المستخدم.
@router.patch(
    "/{user_id}",
    dependencies=[Depends(get_current_active_superuser)],
    response_model=UserPublic,
)
def update_user(
    *,
    session: SessionDep,
    user_id: uuid.UUID,
    user_in: UserUpdate,
) -> Any:
    """
    Update a user.
    """
    db_user = session.get(User, user_id)  # استرجاع المستخدم من قاعدة البيانات.
    if not db_user:
        raise HTTPException(
            status_code=404,
            detail="The user with this id does not exist in the system",
        )  # إذا لم يتم العثور على المستخدم، إرجاع خطأ.

    if user_in.email:
        existing_user = crud.get_user_by_email(session=session, email=user_in.email)
        if existing_user and existing_user.id != user_id:
            raise HTTPException(
                status_code=409, detail="User with this email already exists"
            )  # التحقق من عدم وجود مستخدم آخر بنفس البريد الإلكتروني.

    logger.info(f"User updated: {db_user.email}")  # تسجيل الحدث.
    db_user = crud.update_user(session=session, db_user=db_user, user_in=user_in)  # تحديث بيانات المستخدم.
    return db_user  # إرجاع المستخدم المحدث.

# مسار لحذف مستخدم باستخدام معرّف المستخدم.
@router.delete("/{user_id}", dependencies=[Depends(get_current_active_superuser)])
def delete_user(
    session: SessionDep, current_user: CurrentUser, user_id: uuid.UUID
) -> Message:
    """
    Delete a user.
    """
    user = session.get(User, user_id)  # استرجاع المستخدم باستخدام معرّف المستخدم.
    if not user:
        raise HTTPException(status_code=404, detail="User not found")  # إرجاع خطأ إذا لم يتم العثور على المستخدم.

    if user == current_user:
        raise HTTPException(
            status_code=403, detail="Super users are not allowed to delete themselves"
        )  # منع المشرفين من حذف أنفسهم.

    statement = delete(Item).where(col(Item.owner_id) == user_id)  # حذف العناصر المرتبطة بالمستخدم.
    session.exec(statement)  # تنفيذ استعلام الحذف.

    session.delete(user)  # حذف المستخدم.
    session.commit()  # تنفيذ التغييرات في قاعدة البيانات.

    logger.info(f"User deleted: {user.email}")  # تسجيل الحدث.
    return Message(message="User deleted successfully")  # إرجاع رسالة نجاح.
