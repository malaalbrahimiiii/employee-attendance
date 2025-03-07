# هذا الكود قدمته جزء من اي بي اي من فاست اي بي اي وسيكوال ،يختص باداره العناصر التيم 
# يتيح هذا الكود من انشاء قراده وتحديث وحذف 


import uuid  # استيراد مكتبة UUID لتوليد معرّفات فريدة.
from typing import Any  # استيراد Any من مكتبة typing للسماح باستخدام أنواع متعددة في الأنواع التوضيحية.

from fastapi import APIRouter, HTTPException  # استيراد الأدوات الخاصة بـ FastAPI لإنشاء المسارات والتعامل مع الأخطاء.
from sqlmodel import func, select  # استيراد الأدوات الخاصة بـ SQLModel للتفاعل مع قاعدة البيانات.

from app.api.deps import CurrentUser, SessionDep  # استيراد التبعيات مثل المستخدم الحالي و Session.
from app.models import Item, ItemCreate, ItemPublic, ItemsPublic, ItemUpdate, Message  # استيراد نماذج العناصر مثل Item و ItemCreate و ItemUpdate وغيرها.

router = APIRouter(prefix="/items", tags=["items"])  # إنشاء مسار جديد في FastAPI مع تعيين البادئة '/items' والوسم 'items'.

# قراءة جميع العناصر (GET /items)
@router.get("/", response_model=ItemsPublic)
def read_items(
    session: SessionDep, current_user: CurrentUser, skip: int = 0, limit: int = 100
) -> Any:
    """
    Retrieve items.
    """
    # إذا كان المستخدم مشرفًا، استرجاع جميع العناصر.
    if current_user.is_superuser:
        count_statement = select(func.count()).select_from(Item)  # استعلام لحساب عدد العناصر في قاعدة البيانات.
        count = session.exec(count_statement).one()  # تنفيذ الاستعلام للحصول على العدد الإجمالي.
        statement = select(Item).offset(skip).limit(limit)  # استعلام لاسترجاع العناصر مع إمكانية التخطي وعرض عدد معين من السجلات.
        items = session.exec(statement).all()  # تنفيذ الاستعلام للحصول على جميع العناصر.
    else:
        # إذا لم يكن المستخدم مشرفًا، استرجاع العناصر التي يملكها فقط.
        count_statement = (
            select(func.count())
            .select_from(Item)
            .where(Item.owner_id == current_user.id)  # استعلام لحساب عدد العناصر التي يملكها المستخدم الحالي.
        )
        count = session.exec(count_statement).one()  # تنفيذ الاستعلام للحصول على العدد الإجمالي.
        statement = (
            select(Item)
            .where(Item.owner_id == current_user.id)
            .offset(skip)
            .limit(limit)
        )  # استعلام لاسترجاع العناصر التي يملكها المستخدم.
        items = session.exec(statement).all()  # تنفيذ الاستعلام للحصول على العناصر.

    return ItemsPublic(data=items, count=count)  # إرجاع العناصر مع العدد الإجمالي في نموذج ItemsPublic.

# قراءة عنصر معين (GET /items/{id})
@router.get("/{id}", response_model=ItemPublic)
def read_item(session: SessionDep, current_user: CurrentUser, id: uuid.UUID) -> Any:
    """
    Get item by ID.
    """
    item = session.get(Item, id)  # استرجاع العنصر من قاعدة البيانات بناءً على المعرف.
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")  # إذا لم يتم العثور على العنصر، إرجاع خطأ 404.
    if not current_user.is_superuser and (item.owner_id != current_user.id):
        raise HTTPException(status_code=400, detail="Not enough permissions")  # إذا لم يكن المستخدم مشرفًا وكان العنصر لا يخصه، إرجاع خطأ 400.
    return item  # إرجاع العنصر.

# إنشاء عنصر جديد (POST /items)
@router.post("/", response_model=ItemPublic)
def create_item(
    *, session: SessionDep, current_user: CurrentUser, item_in: ItemCreate
) -> Any:
    """
    Create new item.
    """
    item = Item.model_validate(item_in, update={"owner_id": current_user.id})  # إنشاء العنصر باستخدام البيانات المدخلة وتحديث owner_id ليكون هو المستخدم الحالي.
    session.add(item)  # إضافة العنصر إلى الجلسة.
    session.commit()  # تنفيذ العملية في قاعدة البيانات (إضافة العنصر).
    session.refresh(item)  # تحديث العنصر بعد إضافته للحصول على البيانات المحدثة.
    return item  # إرجاع العنصر الذي تم إنشاؤه.

# تحديث عنصر (PUT /items/{id})
@router.put("/{id}", response_model=ItemPublic)
def update_item(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    id: uuid.UUID,
    item_in: ItemUpdate,
) -> Any:
    """
    Update an item.
    """
    item = session.get(Item, id)  # استرجاع العنصر من قاعدة البيانات باستخدام المعرف.
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")  # إذا لم يتم العثور على العنصر، إرجاع خطأ 404.
    if not current_user.is_superuser and (item.owner_id != current_user.id):
        raise HTTPException(status_code=400, detail="Not enough permissions")  # إذا لم يكن المستخدم مشرفًا وكان العنصر لا يخصه، إرجاع خطأ 400.
    update_dict = item_in.model_dump(exclude_unset=True)  # استخراج البيانات المحدثة من الـ ItemUpdate.
    item.sqlmodel_update(update_dict)  # تحديث العنصر باستخدام البيانات المدخلة.
    session.add(item)  # إضافة العنصر المحدث إلى الجلسة.
    session.commit()  # تنفيذ العملية في قاعدة البيانات (تحديث العنصر).
    session.refresh(item)  # تحديث العنصر بعد التحديث للحصول على البيانات المحدثة.
    return item  # إرجاع العنصر بعد التحديث.

# حذف عنصر (DELETE /items/{id})
@router.delete("/{id}")
def delete_item(
    session: SessionDep, current_user: CurrentUser, id: uuid.UUID
) -> Message:
    """
    Delete an item.
    """
    item = session.get(Item, id)  # استرجاع العنصر من قاعدة البيانات باستخدام المعرف.
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")  # إذا لم يتم العثور على العنصر، إرجاع خطأ 404.
    if not current_user.is_superuser and (item.owner_id != current_user.id):
        raise HTTPException(status_code=400, detail="Not enough permissions")  # إذا لم يكن المستخدم مشرفًا وكان العنصر لا يخصه، إرجاع خطأ 400.
    session.delete(item)  # حذف العنصر من قاعدة البيانات.
    session.commit()  # تنفيذ عملية الحذف في قاعدة البيانات.
    return Message(message="Item deleted successfully")  # إرجاع رسالة تؤكد الحذف الناجح.
