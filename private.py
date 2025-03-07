# هذا الكود عباره عن لادراه انشاء المستخدمين الجدد ويتم من خلاله انشاء نموذج بيانات للمستخدم 
# اضافه المستخدمين الجدد الى قاعده البيانات 


from typing import Any  # استيراد Any من مكتبة typing للسماح بمرونة في تحديد نوع البيانات.

from fastapi import APIRouter  # استيراد APIRouter من FastAPI لإنشاء المسارات.
from pydantic import BaseModel  # استيراد BaseModel من Pydantic لإنشاء النماذج التي تمثل البيانات المدخلة من قبل المستخدم.

from app.api.deps import SessionDep  # استيراد SessionDep من app.api.deps للوصول إلى الجلسات (sessions) في قاعدة البيانات.
from app.core.security import get_password_hash  # استيراد دالة get_password_hash من app.core.security لتوليد هاش لكلمة المرور.
from app.models import (  # استيراد النماذج المطلوبة من app.models.
    User,  # نموذج User لتمثيل المستخدمين في قاعدة البيانات.
    UserPublic,  # نموذج UserPublic لتمثيل البيانات التي سيتم إرجاعها للمستخدم في الرد.
)

router = APIRouter(tags=["private"], prefix="/private")  # إنشاء مسار جديد في FastAPI مع تعيين الوسم 'private' و تفعيل البادئة "/private".

# تعريف نموذج البيانات المدخلة لإنشاء مستخدم جديد (Pydantic model).
class PrivateUserCreate(BaseModel):  # هذا النموذج يستخدم للتحقق من البيانات المدخلة من قبل المستخدم.
    email: str  # البريد الإلكتروني للمستخدم.
    password: str  # كلمة المرور الخاصة بالمستخدم.
    full_name: str  # الاسم الكامل للمستخدم.
    is_verified: bool = False  # حالة التحقق من المستخدم (افتراضيًا False).

# مسار لإنشاء مستخدم جديد في قاعدة البيانات.
@router.post("/users/", response_model=UserPublic)  # المسار هو POST ويقبل بيانات لإنشاء مستخدم جديد.
def create_user(user_in: PrivateUserCreate, session: SessionDep) -> Any:
    """
    Create a new user.
    """
    # إنشاء مستخدم جديد باستخدام البيانات المدخلة.
    user = User(
        email=user_in.email,  # تعيين البريد الإلكتروني.
        full_name=user_in.full_name,  # تعيين الاسم الكامل.
        hashed_password=get_password_hash(user_in.password),  # توليد هاش لكلمة المرور.
    )

    # إضافة المستخدم الجديد إلى الجلسة.
    session.add(user)
    # تنفيذ التغييرات (أي إضافة المستخدم الجديد) في قاعدة البيانات.
    session.commit()

    return user  # إرجاع المستخدم الذي تم إنشاؤه في قاعدة البيانات.
