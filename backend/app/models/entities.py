import enum,uuid
from datetime import date,datetime
from sqlalchemy import String,Float,Date,DateTime,ForeignKey,Enum,Boolean
from sqlalchemy.orm import Mapped,mapped_column,relationship
from app.database.core import Base
class TxType(str,enum.Enum):income='income';expense='expense';transfer='transfer'
class User(Base):
 __tablename__='users';id:Mapped[str]=mapped_column(String,primary_key=True,default=lambda:str(uuid.uuid4()));name:Mapped[str]=mapped_column(String(120));email:Mapped[str]=mapped_column(String(255),unique=True,index=True);password_hash:Mapped[str]=mapped_column(String(255));phone:Mapped[str|None]=mapped_column(String(40));currency:Mapped[str]=mapped_column(String(3),default='USD');language:Mapped[str]=mapped_column(String(10),default='en');created_at:Mapped[datetime]=mapped_column(DateTime,default=datetime.utcnow);updated_at:Mapped[datetime]=mapped_column(DateTime,default=datetime.utcnow,onupdate=datetime.utcnow)
 transactions=relationship('Transaction',cascade='all,delete-orphan')
class Transaction(Base):
 __tablename__='transactions';id:Mapped[str]=mapped_column(String,primary_key=True,default=lambda:str(uuid.uuid4()));user_id:Mapped[str]=mapped_column(ForeignKey('users.id',ondelete='CASCADE'),index=True);amount:Mapped[float]=mapped_column(Float);transaction_type:Mapped[TxType]=mapped_column(Enum(TxType));category:Mapped[str]=mapped_column(String(80),index=True);merchant:Mapped[str]=mapped_column(String(120));description:Mapped[str|None]=mapped_column(String(500));payment_method:Mapped[str|None]=mapped_column(String(50));date:Mapped[date]=mapped_column(Date,index=True);location:Mapped[str|None]=mapped_column(String(120));created_at:Mapped[datetime]=mapped_column(DateTime,default=datetime.utcnow)
class Budget(Base):
 __tablename__='budgets';id:Mapped[str]=mapped_column(String,primary_key=True,default=lambda:str(uuid.uuid4()));user_id:Mapped[str]=mapped_column(ForeignKey('users.id',ondelete='CASCADE'),index=True);category:Mapped[str]=mapped_column(String(80));limit:Mapped[float]=mapped_column(Float);spent:Mapped[float]=mapped_column(Float,default=0);start_date:Mapped[date]=mapped_column(Date);end_date:Mapped[date]=mapped_column(Date)
class Goal(Base):
 __tablename__='goals';id:Mapped[str]=mapped_column(String,primary_key=True,default=lambda:str(uuid.uuid4()));user_id:Mapped[str]=mapped_column(ForeignKey('users.id',ondelete='CASCADE'),index=True);name:Mapped[str]=mapped_column(String(120));target_amount:Mapped[float]=mapped_column(Float);current_amount:Mapped[float]=mapped_column(Float,default=0);deadline:Mapped[date]=mapped_column(Date);status:Mapped[str]=mapped_column(String(30),default='active')
class Anomaly(Base):
 __tablename__='anomalies';id:Mapped[str]=mapped_column(String,primary_key=True,default=lambda:str(uuid.uuid4()));transaction_id:Mapped[str]=mapped_column(ForeignKey('transactions.id',ondelete='CASCADE'));user_id:Mapped[str]=mapped_column(ForeignKey('users.id',ondelete='CASCADE'),index=True);anomaly_score:Mapped[float]=mapped_column(Float);risk_level:Mapped[str]=mapped_column(String(20));reason:Mapped[str]=mapped_column(String(500));is_resolved:Mapped[bool]=mapped_column(Boolean,default=False);detected_at:Mapped[datetime]=mapped_column(DateTime,default=datetime.utcnow)
