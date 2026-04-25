import pymysql
pymysql.install_as_MySQLdb()

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv
import os

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL") or os.getenv("MYSQL_PUBLIC_URL") or ""

# 内部ホスト (.railway.internal) は Railway 外から到達不可 → PUBLIC URL にフォールバック
if ".railway.internal" in DATABASE_URL:
    DATABASE_URL = os.getenv("MYSQL_PUBLIC_URL") or DATABASE_URL

# mysql:// / mysql+mysqldb:// を mysql+pymysql:// に統一
for _prefix in ("mysql+mysqldb://", "mysql://"):
    if DATABASE_URL.startswith(_prefix):
        DATABASE_URL = "mysql+pymysql://" + DATABASE_URL[len(_prefix):]
        break

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
