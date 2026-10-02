from datetime import date
from collections import defaultdict
from fastapi import APIRouter,Depends,HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import select,func
from sqlalchemy.orm import Session
from app.database.core import get_db
from app.models.entities import User,Transaction,Budget,Goal,TxType
from app.schemas.common import *
from app.security.auth import *
from app.ml.engine import detect,forecast,guard_score
from app.services.gemini import generate_financial_answer
from app.config import settings
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
@router.post('/auth/change-password',status_code=204)
def change_password(body:PasswordChange,db:Session=Depends(get_db),u:User=Depends(current_user)):
 if not verify_password(body.current_password,u.password_hash):raise HTTPException(400,'Current password is incorrect')
 if body.current_password==body.new_password:raise HTTPException(422,'New password must be different')
 u.password_hash=hash_password(body.new_password);db.commit()
@router.get('/transactions',response_model=list[TransactionOut])
def list_tx(db:Session=Depends(get_db),u:User=Depends(current_user)):return db.scalars(select(Transaction).where(Transaction.user_id==u.id).order_by(Transaction.date.desc()).limit(200)).all()
@router.post('/transactions',response_model=TransactionOut,status_code=201)
def add_tx(body:TransactionCreate,db:Session=Depends(get_db),u:User=Depends(current_user)):
 data=body.model_dump();raw_type=data.pop('transaction_type')
 try:t=Transaction(**data,transaction_type=TxType(raw_type),user_id=u.id)
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
 rows=list(db.scalars(select(Transaction).where(Transaction.user_id==u.id).order_by(Transaction.date,Transaction.created_at)).all());out=[]
 for idx,x in enumerate(rows[-20:],start=max(0,len(rows)-20)):
  history=[{'amount':y.amount,'category':y.category,'date':y.date,'transaction_type':y.transaction_type.value} for y in rows[:idx]]
  out.append({'transaction_id':x.id,'merchant':x.merchant,'amount':x.amount,'category':x.category,'date':x.date,**detect(x.amount,x.category,history)})
 return out
@router.post('/anomaly/evaluate')
def evaluate_transaction(body:TransactionRiskRequest,db:Session=Depends(get_db),u:User=Depends(current_user)):
 rows=list(db.scalars(select(Transaction).where(Transaction.user_id==u.id).order_by(Transaction.date)).all())
 history=[{'amount':x.amount,'category':x.category,'date':x.date,'transaction_type':x.transaction_type.value} for x in rows]
 result=detect(body.amount,body.category,history)
 label='Potentially suspicious transaction' if result['risk_level']=='high' else 'Unusual transaction' if result['risk_level']=='medium' else 'Normal transaction pattern'
 action='Pause and independently verify the recipient before paying.' if result['risk_level']=='high' else 'Review the details and confirm they match your intent.' if result['risk_level']=='medium' else 'No unusual pattern was detected by the current checks.'
 return {**body.model_dump(),'classification':label,'recommended_action':action,**result,'verified_fraud':False}
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
@router.post('/ai/ask',response_model=AIAnswer)
async def ask_ai(body:AIAsk,db:Session=Depends(get_db),u:User=Depends(current_user)):
 rows=list(db.scalars(select(Transaction).where(Transaction.user_id==u.id).order_by(Transaction.date.desc()).limit(250)).all())
 income=sum(float(x.amount) for x in rows if x.transaction_type==TxType.income)
 expenses=sum(float(x.amount) for x in rows if x.transaction_type==TxType.expense)
 categories=defaultdict(float);merchants=defaultdict(float)
 for x in rows:
  if x.transaction_type==TxType.expense:
   categories[x.category]+=float(x.amount);merchants[x.merchant]+=float(x.amount)
 top_categories=sorted(categories.items(),key=lambda x:x[1],reverse=True)[:6]
 top_merchants=sorted(merchants.items(),key=lambda x:x[1],reverse=True)[:6]
 recent=[f'{x.date}: {x.merchant} | {x.category} | {x.transaction_type.value} | {x.amount:.2f}' for x in rows[:12]]
 budgets=list(db.scalars(select(Budget).where(Budget.user_id==u.id)).all())
 goals=list(db.scalars(select(Goal).where(Goal.user_id==u.id)).all())
 safety=list(db.scalars(select(ScamAnalysis).where(ScamAnalysis.user_id==u.id).order_by(ScamAnalysis.created_at.desc()).limit(5)).all())
 incidents=list(db.scalars(select(Incident).where(Incident.user_id==u.id).order_by(Incident.created_at.desc()).limit(5)).all())
 health=guard_score(income,expenses)
 context='\n'.join([
  f'Currency: {u.currency}',f'Income total: {income:.2f}',f'Expense total: {expenses:.2f}',f'Balance: {income-expenses:.2f}',
  f'Guard score: {health["guard_score"]}; savings rate: {health["savings_rate"]}%',
  'Top expense categories: '+(', '.join(f'{k}: {v:.2f}' for k,v in top_categories) or 'none'),
  'Top merchants: '+(', '.join(f'{k}: {v:.2f}' for k,v in top_merchants) or 'none'),
  'Budgets: '+(', '.join(f'{x.category} limit {x.limit:.2f}, spent {x.spent:.2f}' for x in budgets[:8]) or 'none'),
  'Goals: '+(', '.join(f'{x.name} {x.current_amount:.2f}/{x.target_amount:.2f}, deadline {x.deadline}' for x in goals[:8]) or 'none'),
  'Recent scam analyses: '+(', '.join(f'{x.category} risk {x.risk_level} score {x.risk_score:.0f}' for x in safety) or 'none'),
  'Open incidents: '+(', '.join(f'{x.incident_code} {x.scam_type} {x.status} amount {x.amount:.2f}' for x in incidents if x.status!="RESOLVED") or 'none'),
  'Recent transactions:',*recent
 ])
 sources=['transaction summary','category totals','merchant totals','Guard Score']
 if budgets:sources.append('budgets')
 if goals:sources.append('financial goals')
 if safety:sources.append('scam analyses')
 if incidents:sources.append('incident records')
 try:
  answer,model=await generate_financial_answer(body.question,context,[x.model_dump() for x in body.history])
 except Exception:
  q=body.question.lower()
  if 'biggest' in q and top_merchants:answer=f'Your largest merchant total is {top_merchants[0][0]} at {top_merchants[0][1]:.2f} {u.currency}.'
  elif 'food' in q:answer=f'Your recorded Food spending is {categories.get("Food",0):.2f} {u.currency}.'
  elif 'spending' in q or 'expense' in q:answer=f'Your recorded expenses total {expenses:.2f} {u.currency}. Your largest category is {top_categories[0][0] if top_categories else "not available"}.'
  else:answer='I could not reach the AI model. Your financial summary is still available from the retrieved records.'
  model='grounded-fallback'
 return AIAnswer(answer=answer,sources=sources,grounded_transactions=len(rows),model=model)

@router.get('/reports/monthly')
def report(db:Session=Depends(get_db),u:User=Depends(current_user)):return {'period':date.today().strftime('%Y-%m'),'summary':summary(db,u),'generated_for':u.email}

# Financial safety and incident-response APIs
from fastapi import UploadFile,File
from app.models.entities import ScamAnalysis,Incident,Evidence,Alert,ModelPrediction
from app.services.scam import analyze_message,analyze_url,recovery_checklist
import csv,io,json

@router.post('/scam/analyze')
async def scam_analyze(body:ScamRequest,db:Session=Depends(get_db),u:User=Depends(current_user)):
 result=analyze_message(body.text,body.url)
 row=ScamAnalysis(user_id=u.id,text=body.text,url=body.url,risk_score=result['risk_score'],risk_level=result['risk_level'],category=result['category'],signals=json.dumps(result['signals']),explanation=result['explanation']);db.add(row)
 db.add(ModelPrediction(user_id=u.id,model_name='FinGuard Explainable Scam Baseline',prediction_type='scam_message',score=result['risk_score']/100,label=result['category'],explanation=result['explanation']))
 if result['risk_level'] in ('HIGH','CRITICAL'):db.add(Alert(user_id=u.id,title='Potential scam detected',risk_level=result['risk_level'],details=result['explanation']))
 db.commit();return {'analysis_id':row.id,**result,'verified':False}

@router.post('/url/analyze')
def url_analyze(body:URLRequest,u:User=Depends(current_user)):return {**analyze_url(body.url),'verified':False}

@router.post('/transactions/upload')
async def upload_transactions(file:UploadFile=File(...),db:Session=Depends(get_db),u:User=Depends(current_user)):
 if not file.filename or not file.filename.lower().endswith('.csv'):raise HTTPException(422,'Upload a CSV file')
 raw=await file.read(2_000_001)
 if len(raw)>2_000_000:raise HTTPException(413,'CSV must be 2 MB or smaller')
 try:
  reader=csv.DictReader(io.StringIO(raw.decode('utf-8-sig')));required={'date','amount','merchant','category','payment_method'}
  if not reader.fieldnames or not required.issubset(set(reader.fieldnames)):raise HTTPException(422,f'Missing required columns: {sorted(required-set(reader.fieldnames or []))}')
  created=[]
  for i,row in enumerate(reader):
   if i>=1000:break
   try:
    t=Transaction(user_id=u.id,date=date.fromisoformat(row['date']),amount=abs(float(row['amount'])),merchant=row['merchant'][:120],category=row['category'][:80],payment_method=row.get('payment_method','')[:50],location=row.get('location','')[:120],description=f"Imported reference: {row.get('transaction_id','')[:100]}",transaction_type=TxType.expense);db.add(t);created.append(t)
   except (ValueError,TypeError):continue
  db.commit();return {'imported':len(created),'skipped':max(0,(i+1 if 'i' in locals() else 0)-len(created)),'message':'Imported records are user-provided data, not live bank transactions.'}
 except UnicodeDecodeError:raise HTTPException(422,'CSV must use UTF-8 encoding')

@router.get('/transactions/anomalies')
def transaction_anomalies(db:Session=Depends(get_db),u:User=Depends(current_user)):return scan(db,u)

@router.post('/incidents',status_code=201)
def create_incident(body:IncidentCreate,db:Session=Depends(get_db),u:User=Depends(current_user)):
 n=(db.scalar(select(func.count()).select_from(Incident).where(Incident.user_id==u.id)) or 0)+1;code=f'FG-{date.today().year}-{n:05d}';analysis=analyze_message(body.description,body.url)
 row=Incident(**body.model_dump(),incident_code=code,user_id=u.id,risk_level=analysis['risk_level'],status='DOCUMENTING');db.add(row);db.commit();db.refresh(row);return {'id':row.id,'incident_code':row.incident_code,'risk_level':row.risk_level,'status':row.status}

@router.get('/incidents')
def list_incidents(db:Session=Depends(get_db),u:User=Depends(current_user)):return db.scalars(select(Incident).where(Incident.user_id==u.id).order_by(Incident.created_at.desc())).all()

def owned_incident(iid:str,db:Session,u:User):
 row=db.scalar(select(Incident).where(Incident.id==iid,Incident.user_id==u.id))
 if not row:raise HTTPException(404,'Incident not found')
 return row

@router.get('/incidents/{incident_id}')
def get_incident(incident_id:str,db:Session=Depends(get_db),u:User=Depends(current_user)):
 row=owned_incident(incident_id,db,u);ev=db.scalars(select(Evidence).where(Evidence.incident_id==row.id,Evidence.user_id==u.id).order_by(Evidence.occurred_at,Evidence.created_at)).all();return {'incident':row,'evidence':ev,'checklist':recovery_checklist(row.scam_type,row.description),'notice':'FinGuard cannot recover funds directly. Recovery depends on the relevant institution and authorities.'}

@router.patch('/incidents/{incident_id}')
def update_incident(incident_id:str,body:IncidentUpdate,db:Session=Depends(get_db),u:User=Depends(current_user)):
 row=owned_incident(incident_id,db,u);row.status=body.status;db.commit();return {'id':row.id,'status':row.status}

@router.post('/incidents/{incident_id}/evidence',status_code=201)
def add_evidence(incident_id:str,body:EvidenceCreate,db:Session=Depends(get_db),u:User=Depends(current_user)):
 row=owned_incident(incident_id,db,u);ev=Evidence(**body.model_dump(),incident_id=row.id,user_id=u.id);db.add(ev);db.commit();db.refresh(ev);return ev

@router.get('/incidents/{incident_id}/report')
def incident_report(incident_id:str,db:Session=Depends(get_db),u:User=Depends(current_user)):
 data=get_incident(incident_id,db,u);row=data['incident'];return {'generated_by':'FinGuard','verification_notice':'AI-generated analysis should be independently verified.','recovery_notice':'FinGuard cannot recover funds directly.','incident':row,'evidence':data['evidence'],'recommended_actions':data['checklist']}

@router.get('/dashboard')
def safety_dashboard(db:Session=Depends(get_db),u:User=Depends(current_user)):
 tx=list(db.scalars(select(Transaction).where(Transaction.user_id==u.id)).all());analyses=list(db.scalars(select(ScamAnalysis).where(ScamAnalysis.user_id==u.id)).all());incidents=list(db.scalars(select(Incident).where(Incident.user_id==u.id)).all());expense=sum(x.amount for x in tx if x.transaction_type==TxType.expense)
 return {'total_transactions':len(tx),'suspicious_transactions':len([x for x in scan(db,u) if x['risk_level'] in ('high','medium')]),'scam_alerts':len([x for x in analyses if x.risk_level in ('HIGH','CRITICAL')]),'total_spending':expense,'detected_anomalies':len(scan(db,u)),'open_incidents':len([x for x in incidents if x.status!='RESOLVED']),'simulation':True}

@router.get('/financial-insights')
def financial_insights(db:Session=Depends(get_db),u:User=Depends(current_user)):return {'summary':summary(db,u),'forecast':predict(db,u),'notice':'Forecasts are estimates based on available historical activity.'}
