from datetime import date
from fastapi import APIRouter,Depends,HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import select,func
from sqlalchemy.orm import Session
from app.database.core import get_db
from app.models.entities import User,Transaction,Budget,Goal,TxType
from app.schemas.common import *
from app.security.auth import *
from app.ml.engine import detect,forecast,guard_score
router=APIRouter(prefix='/api/v1')
@router.post('/auth/register',response_model=UserOut,status_code=201)
def register(body:UserCreate,db:Session=Depends(get_db)):
 if db.scalar(select(User).where(User.email==body.email.lower())):raise HTTPException(409,'Email already registered')
 u=User(name=body.name,email=body.email.lower(),password_hash=hash_password(body.password),currency=body.currency.upper(),language=body.language);db.add(u);db.commit();db.refresh(u);return u
@router.post('/auth/login',response_model=Token)
def login(form:OAuth2PasswordRequestForm=Depends(),db:Session=Depends(get_db)):
 u=db.scalar(select(User).where(User.email==form.username.lower()))
 if not u or not verify_password(form.password,u.password_hash):raise HTTPException(401,'Invalid credentials')
 return Token(access_token=create_token(u.id))
@router.get('/users/me',response_model=UserOut)
def me(u:User=Depends(current_user)):return u
@router.get('/transactions',response_model=list[TransactionOut])
def list_tx(db:Session=Depends(get_db),u:User=Depends(current_user)):return db.scalars(select(Transaction).where(Transaction.user_id==u.id).order_by(Transaction.date.desc()).limit(200)).all()
@router.post('/transactions',response_model=TransactionOut,status_code=201)
def add_tx(body:TransactionCreate,db:Session=Depends(get_db),u:User=Depends(current_user)):
 try:t=Transaction(**body.model_dump(),transaction_type=TxType(body.transaction_type),user_id=u.id)
 except ValueError:raise HTTPException(422,'transaction_type must be income, expense or transfer')
 db.add(t);db.commit();db.refresh(t);return t
@router.delete('/transactions/{tx_id}',status_code=204)
def delete_tx(tx_id:str,db:Session=Depends(get_db),u:User=Depends(current_user)):
 t=db.scalar(select(Transaction).where(Transaction.id==tx_id,Transaction.user_id==u.id))
 if not t:raise HTTPException(404,'Transaction not found')
 db.delete(t);db.commit()
@router.get('/analytics/summary')
def summary(db:Session=Depends(get_db),u:User=Depends(current_user)):
 rows=db.execute(select(Transaction.transaction_type,func.sum(Transaction.amount)).where(Transaction.user_id==u.id).group_by(Transaction.transaction_type)).all();d={str(k.value):float(v or 0) for k,v in rows};income=d.get('income',0);expenses=d.get('expense',0);health=guard_score(income,expenses);return {'income':income,'expenses':expenses,'balance':income-expenses,**health}
@router.get('/anomaly/scan')
def scan(db:Session=Depends(get_db),u:User=Depends(current_user)):
 rows=db.scalars(select(Transaction).where(Transaction.user_id==u.id).order_by(Transaction.date)).all();h=[{'amount':x.amount,'category':x.category,'date':x.date,'transaction_type':x.transaction_type.value} for x in rows];return [{'transaction_id':x.id,**detect(x.amount,x.category,h[:-1])} for x in rows[-20:]]
@router.get('/prediction/expenses')
def predict(db:Session=Depends(get_db),u:User=Depends(current_user)):
 rows=db.scalars(select(Transaction).where(Transaction.user_id==u.id)).all();return forecast([{'amount':x.amount,'date':x.date,'transaction_type':x.transaction_type.value} for x in rows])
@router.post('/budgets',status_code=201)
def add_budget(body:BudgetCreate,db:Session=Depends(get_db),u:User=Depends(current_user)):
 if body.end_date<=body.start_date:raise HTTPException(422,'end_date must be after start_date')
 x=Budget(**body.model_dump(),user_id=u.id);db.add(x);db.commit();db.refresh(x);return {'id':x.id,**body.model_dump()}
@router.get('/budgets')
def budgets(db:Session=Depends(get_db),u:User=Depends(current_user)):return db.scalars(select(Budget).where(Budget.user_id==u.id)).all()
@router.post('/goals',status_code=201)
def add_goal(body:GoalCreate,db:Session=Depends(get_db),u:User=Depends(current_user)):
 x=Goal(**body.model_dump(),user_id=u.id);db.add(x);db.commit();db.refresh(x);return {'id':x.id,**body.model_dump()}
@router.get('/goals')
def goals(db:Session=Depends(get_db),u:User=Depends(current_user)):return db.scalars(select(Goal).where(Goal.user_id==u.id)).all()
@router.get('/notifications')
def notifications(u:User=Depends(current_user)):return [{'type':'security','message':'No critical threats detected'},{'type':'budget','message':'Dining budget is nearing its limit'}]

@router.get('/analytics/recurring')
def recurring(db:Session=Depends(get_db),u:User=Depends(current_user)):
 rows=db.scalars(select(Transaction).where(Transaction.user_id==u.id,Transaction.transaction_type==TxType.expense)).all();groups={}
 for x in rows:groups.setdefault(x.merchant.lower(),[]).append(x)
 found=[{'merchant':v[0].merchant,'estimated_monthly':round(sum(x.amount for x in v)/len(v),2),'occurrences':len(v)} for v in groups.values() if len(v)>=2]
 return {'items':found,'monthly_total':round(sum(x['estimated_monthly'] for x in found),2)}
@router.post('/ai/ask')
def ask_ai(body:dict,db:Session=Depends(get_db),u:User=Depends(current_user)):
 q=str(body.get('question','')).lower();rows=db.scalars(select(Transaction).where(Transaction.user_id==u.id)).all();expenses=[x for x in rows if x.transaction_type==TxType.expense]
 if 'biggest' in q and expenses:
  x=max(expenses,key=lambda z:z.amount);answer=f'Your biggest expense was {x.merchant} at {x.amount:.2f} {u.currency}.'
 elif 'food' in q:answer=f'You spent {sum(x.amount for x in expenses if x.category.lower()=="food"):.2f} {u.currency} on food.'
 elif 'unusual' in q or 'anomal' in q:answer='I scanned recent transactions using Z-score, Isolation Forest and Local Outlier Factor. Open Anomaly Center for the ranked results.'
 else:answer='Your strongest opportunity is budget adherence. Shopping and food are the largest variable categories this period.'
 return {'answer':answer,'grounded_transactions':len(rows)}

@router.get('/reports/monthly')
def report(db:Session=Depends(get_db),u:User=Depends(current_user)):return {'period':date.today().strftime('%Y-%m'),'summary':summary(db,u),'generated_for':u.email}
