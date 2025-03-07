# هذا الكود مع السيكو ال مودل 
# يستخدم لانشاء نماذج لتمثيل البيانات الي راح تتخزن في القاعده 
# ويحدد نوع البيانات مثل الوقت والنتقر وغيرها 
# ويوضح العلاقات بين الجدوال والبيانات والحضور 


from datetime import datetime
import uuid

from pydantic import EmailStr
from sqlmodel import Field, Relationship, SQLModel


# تعريف خصائص المستخدم الاسياسية مثل الايميل والاسم وغيرها
class UserBase(SQLModel):
    email: EmailStr = Field(unique=True, index=True, max_length=255)
    is_active: bool = True
    is_superuser: bool = False
    full_name: str | None = Field(default=None, max_length=255)
    attend_id: int = Field(default=0, unique=True)
    weekly_work_hours: int = Field(default=0, nullable=True)


# تعريف للخصائص المستخدم عن الانشاء وكمان تمشل الباسبورد 
class UserCreate(UserBase):
    password: str = Field(min_length=8, max_length=40)

#خصائص استلام البيانات عند التسجيل وتشمل الباسبورد والايميل و الفل نيم 
class UserRegister(SQLModel):
    email: EmailStr = Field(max_length=255)
    password: str = Field(min_length=8, max_length=40)
    full_name: str | None = Field(default=None, max_length=255)


# هذي علشان تصير في تحديث البيانات 
class UserUpdate(UserBase):
    email: EmailStr | None = Field(default=None, max_length=255)  # type: ignore
    password: str | None = Field(default=None, min_length=8, max_length=40)

# تحديق البيانات مثل الايميل والاسم 
class UserUpdateMe(SQLModel):
    full_name: str | None = Field(default=None, max_length=255)
    email: EmailStr | None = Field(default=None, max_length=255)

# تحديق الرقم السري 
class UpdatePassword(SQLModel):
    current_password: str = Field(min_length=8, max_length=40)
    new_password: str = Field(min_length=8, max_length=40)


# هذا نموذج الاساسي لتمثيل البيانات المستخدم في قاعده البيانات ويتحتوي على الخصائص مثل الاي دي وغيرها 
class User(UserBase, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    hashed_password: str
    items: list["Item"] = Relationship(back_populates="owner", cascade_delete=True)
    attendance: list["Attendance"] = Relationship(back_populates="user", cascade_delete=True)
    daily_attendance: list["DailyAttendance"] = Relationship(back_populates="user", cascade_delete=True)
    weekly_attendance: list["WeeklyAttendance"] = Relationship(back_populates="user", cascade_delete=True)


# هنا راح ستعرض الخصائص 
class UserPublic(UserBase):
    id: uuid.UUID

#يحتوي على مجموعة من اليرو ببلك وعدد المستخدمين 
class UsersPublic(SQLModel):
    data: list[UserPublic]
    count: int

#خصائص الاساس مثل التاتل والدسكربشن 
class ItemBase(SQLModel):
    title: str = Field(min_length=1, max_length=255)
    description: str | None = Field(default=None, max_length=255)


#خصائص استلام البيانات لإنشاء عنصر جديد.
class ItemCreate(ItemBase):
    pass


#خصائص استلام البيانات لتحديث العنصر، تشمل title.
class ItemUpdate(ItemBase):
    title: str | None = Field(default=None, min_length=1, max_length=255)  # type: ignore

#نموذج العنصرفي قاعده اليبيانات يحتوي علس الاي دي والتاولت مع ربط المستخدم 
class Item(ItemBase, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    title: str = Field(max_length=255)
    owner_id: uuid.UUID = Field(
        foreign_key="user.id", nullable=False, ondelete="CASCADE"
    )
    owner: User | None = Relationship(back_populates="items")


#يحتوي على مجموعة من الـ ItemPublic وعدد العناصر.
class ItemPublic(ItemBase):
    id: uuid.UUID
    owner_id: uuid.UUID


class ItemsPublic(SQLModel):
    data: list[ItemPublic]
    count: int


# Generic message
class Message(SQLModel):
    message: str


# JSON payload containing access token
class Token(SQLModel):
    access_token: str
    token_type: str = "bearer"


#يحتوي على رمز الوصول access_token ونوعه.
class TokenPayload(SQLModel):
    sub: str | None = None

#يحتوي على token و new_password لتحديث كلمة المرور.

class NewPassword(SQLModel):
    token: str
    new_password: str = Field(min_length=8, max_length=40)

class AttendanceBase(SQLModel):
    status: bool = Field(default=False)
    reason: str | None = Field(default=None)
    type_attendance: str = Field(default="")
    full_name: str | None = Field(default=None)
    attend_id: int | None = Field(default=None)

# خصائص الأساس لحضور الموظفين مثل الايوزر والاي دي 
class Attendance(AttendanceBase, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    user_id: uuid.UUID = Field(foreign_key="user.id", nullable=False, ondelete="CASCADE")
    user: User | None = Relationship(back_populates="attendance")
    created_at: datetime = Field(default_factory=datetime.now)


#نموذج الحضور في قاعدة البيانات، يحتوي على 
class AttendancePublic(AttendanceBase):
    id: uuid.UUID
    user_id: uuid.UUID
    created_at: datetime

#خصائص الحضور التي ستُعرض عبر API، تشمل
class AttendancesPublic(SQLModel):
    data: list[AttendancePublic]
    count: int
# يتحتوي علي رويشن لتحديث الحضور 
class AttendanceUpdate(SQLModel):
    reason: str | None = Field(default=None)

#خصائص الأساس لحضور يومي مثل
class DailyAttendanceBase(SQLModel):
    daily_attendance_hours: int = Field(default=0)
    full_name: str | None = Field(default=None)
    attend_id: int | None = Field(default=None)

class DailyAttendance(DailyAttendanceBase, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    user_id: uuid.UUID = Field(foreign_key="user.id", nullable=False, ondelete="CASCADE")
    user: User | None = Relationship(back_populates="daily_attendance")
    created_at: datetime = Field(default_factory=datetime.now)

#خصائص الحضور اليومي التي ستُعرض عبر API.
class DailyAttendancePublic(DailyAttendanceBase):
    id: uuid.UUID
    user_id: uuid.UUID
    created_at: datetime
#يحتوي على مجموعة من الـ DailyAttendancePublic وعدد الحضور اليومي.
class DailyAttendancesPublic(SQLModel):
    data: list[DailyAttendancePublic]
    count: int

#خصائص استلام البيانات لإنشاء حضور يومي.
class DailyAttendanceCreate(SQLModel):
    daily_attendance_hours: int = Field(default=0)
    full_name: str | None = Field(default=None)
    attend_id: int | None = Field(default=None)
#خصائص استلام البيانات لتحديث الحضور اليومي.
class DailyAttendanceUpdate(SQLModel):
    daily_attendance_hours: int = Field(default=0)
    full_name: str | None = Field(default=None)
    attend_id: int | None = Field(default=None)

#خصائص الأساس لحضور أسبوعي مثل
class WeeklyAttendanceBase(SQLModel):
    weekly_attendance_hours: int = Field(default=0)
    start_date: datetime = Field(default_factory=datetime.now)
    end_date: datetime = Field(default_factory=datetime.now)
    full_name: str | None = Field(default=None)
    attend_id: int | None = Field(default=None)

#نموذج الحضور الأسبوعي في قاعدة البيانات، يحتوي على id, user_id, created_at.
class WeeklyAttendance(WeeklyAttendanceBase, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    user_id: uuid.UUID = Field(foreign_key="user.id", nullable=False, ondelete="CASCADE")
    user: User | None = Relationship(back_populates="weekly_attendance")
    created_at: datetime = Field(default_factory=datetime.now)

#خصائص الحضور الأسبوعي التي ستُعرض عبر API.
class WeeklyAttendancePublic(WeeklyAttendanceBase):
    id: uuid.UUID
    user_id: uuid.UUID
    created_at: datetime

class WeeklyAttendancesPublic(SQLModel):
    data: list[WeeklyAttendancePublic]
    count: int

#خصائص استلام البيانات لإنشاء حضور أسبوعي.
class WeeklyAttendanceCreate(SQLModel):
    weekly_attendance_hours: int = Field(default=0)
    start_date: datetime = Field(default_factory=datetime.now)
    end_date: datetime = Field(default_factory=datetime.now)
    full_name: str | None = Field(default=None)
    attend_id: int | None = Field(default=None)

#خصائص استلام البيانات لتحديث الحضور الأسبوعي.
class WeeklyAttendanceUpdate(SQLModel):
    weekly_attendance_hours: int = Field(default=0)
    start_date: datetime = Field(default_factory=datetime.now)
    end_date: datetime = Field(default_factory=datetime.now)
    full_name: str | None = Field(default=None)
    attend_id: int | None = Field(default=None)
