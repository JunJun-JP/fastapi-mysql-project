import pymysql
pymysql.install_as_MySQLdb()

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv
import os

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL") or os.getenv("MYSQL_PUBLIC_URL") or ""

# 内部ホスト (.railway.internal) は接続不安定なため PUBLIC URL を優先
if ".railway.internal" in DATABASE_URL:
    public = os.getenv("MYSQL_PUBLIC_URL") or os.getenv("MYSQL_URL") or ""
    if public:
        DATABASE_URL = public

# mysql:// / mysql+mysqldb:// を mysql+pymysql:// に統一
for _prefix in ("mysql+mysqldb://", "mysql://"):
    if DATABASE_URL.startswith(_prefix):
        DATABASE_URL = "mysql+pymysql://" + DATABASE_URL[len(_prefix):]
        break

engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,       # 接続が切れていたら自動再接続
    pool_recycle=280,         # 接続を 280 秒ごとに更新（Railway の idle timeout 対策）
    pool_size=5,
    max_overflow=10,
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
