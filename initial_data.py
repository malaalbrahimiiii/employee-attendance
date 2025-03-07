
# هذا الكود بانشاء الاتصال بقاعده البيانات ثم يهيي البيانات الاوليه من خلال داله انتال دف 
# تسجيل كل خطوه في سجل باستخدما لوقيرر 

import logging

from sqlmodel import Session

from app.core.db import engine, init_db

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
# هنا افتح جلسه مع قاعده البيانات علشان انشاء بيانات اوليه 

def init() -> None:
    with Session(engine) as session:
        init_db(session)
# وهنا اهئيي البيانات الواليه للبرنامج 


def main() -> None:
    logger.info("Creating initial data") 
    init()
    logger.info("Initial data created")


if __name__ == "__main__":
    main()
