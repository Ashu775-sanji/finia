from datetime import date,timedelta
from sqlalchemy import select,func
from app.database.core import SessionLocal
from app.models.entities import User,Transaction,Budget,Goal,TxType
from app.security.auth import hash_password

def seed_demo_data():
    """Create fictional portfolio data. No record represents a real person or bank feed."""
    db=SessionLocal()
    try:
        user=db.scalar(select(User).where(User.email=='demo@finguard.app'))
        if not user:
            user=User(name='Demo User',email='demo@finguard.app',password_hash=hash_password('FinGuard@2026'),currency='INR',language='en')
            db.add(user);db.flush()
        today=date.today()
        existing=db.scalar(select(func.count()).select_from(Transaction).where(Transaction.user_id==user.id)) or 0
        if existing<20:
            db.query(Transaction).filter(Transaction.user_id==user.id).delete()
            templates=[
                ('Salary deposit',62000,TxType.income,'Income',3),('Apartment rent',18000,TxType.expense,'Bills',5),
                ('Fresh Market',4200,TxType.expense,'Food',8),('Metro Mobility',1240,TxType.expense,'Transport',11),
                ('Netflix',649,TxType.expense,'Subscriptions',14),('Pharmacy',980,TxType.expense,'Healthcare',17),
                ('Book Store',1650,TxType.expense,'Education',20),('Amazon Marketplace',8500,TxType.expense,'Shopping',23),
            ]
            for month in range(6):
                anchor=today-timedelta(days=30*month)
                for idx,(merchant,amount,kind,category,day) in enumerate(templates):
                    variation=1+(((month+idx)%5)-2)*.025
                    value=amount if kind==TxType.income else round(amount*variation,2)
                    db.add(Transaction(user_id=user.id,amount=value,transaction_type=kind,category=category,merchant=merchant,date=anchor-timedelta(days=day%24),description='SAMPLE DATA — fictional transaction',payment_method='Demo'))
            db.add(Transaction(user_id=user.id,amount=48500,transaction_type=TxType.expense,category='Other',merchant='Unknown recipient',date=today-timedelta(days=1),description='SAMPLE DATA — unusual UPI payment',payment_method='UPI'))
            for _ in range(4):
                db.add(Transaction(user_id=user.id,amount=499,transaction_type=TxType.expense,category='Other',merchant='Repeated micro-charge',date=today-timedelta(days=2),description='SAMPLE DATA — repeated small transaction',payment_method='Card'))
        if not db.scalar(select(Budget).where(Budget.user_id==user.id)):
            db.add(Budget(user_id=user.id,category='Food',limit=8000,spent=6450,start_date=today.replace(day=1),end_date=today+timedelta(days=30)))
        if not db.scalar(select(Goal).where(Goal.user_id==user.id)):
            db.add(Goal(user_id=user.id,name='Emergency fund',target_amount=120000,current_amount=42000,deadline=today+timedelta(days=180)))
        db.commit()
    finally:db.close()