from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase,sessionmaker
from app.config import settings
url=settings.database_url
if url.startswith('postgres://'):url='postgresql+psycopg://'+url[len('postgres://'):]
elif url.startswith('postgresql://'):url='postgresql+psycopg://'+url[len('postgresql://'):]
kwargs={'check_same_thread':False} if url.startswith('sqlite') else {}
engine=create_engine(url,pool_pre_ping=True,connect_args=kwargs)
SessionLocal=sessionmaker(bind=engine,autoflush=False,autocommit=False)
class Base(DeclarativeBase):pass
def get_db():
 db=SessionLocal()
 try:yield db
 finally:db.close()
