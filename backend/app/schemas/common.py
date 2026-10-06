from datetime import date,datetime
from pydantic import BaseModel,EmailStr,Field,ConfigDict,field_validator
class UserCreate(BaseModel):
 name:str=Field(min_length=2,max_length=120)
 email:EmailStr
 password:str=Field(min_length=10,max_length=128)
 currency:str=Field('INR',pattern='^(INR|USD|GBP|EUR)$')
 language:str=Field('en',min_length=2,max_length=10)
 @field_validator('currency',mode='before')
 @classmethod
 def normalize_currency(cls,value):
  return str(value or 'INR').upper()
class UserOut(BaseModel):model_config=ConfigDict(from_attributes=True);id:str;name:str;email:EmailStr;currency:str;language:str
class Token(BaseModel):access_token:str;token_type:str='bearer'
class TransactionCreate(BaseModel):amount:float=Field(gt=0,le=1_000_000_000);transaction_type:str;category:str=Field(min_length=2,max_length=80);merchant:str=Field(min_length=1,max_length=120);description:str|None=None;payment_method:str|None=None;date:date;location:str|None=None
class TransactionOut(TransactionCreate):model_config=ConfigDict(from_attributes=True);id:str;created_at:datetime
class BudgetCreate(BaseModel):category:str;limit:float=Field(gt=0);start_date:date;end_date:date
class GoalCreate(BaseModel):name:str;target_amount:float=Field(gt=0);current_amount:float=Field(0,ge=0);deadline:date
class AIHistoryItem(BaseModel):
 role:str=Field(pattern='^(user|assistant)$');content:str=Field(min_length=1,max_length=2000)
class AIAsk(BaseModel):
 question:str=Field(min_length=2,max_length=1000);history:list[AIHistoryItem]=Field(default_factory=list,max_length=12)
class AIAnswer(BaseModel):
 answer:str;sources:list[str];grounded_transactions:int;model:str
class ScamRequest(BaseModel):text:str=Field(min_length=3,max_length=6000);url:str|None=Field(None,max_length=2000)
class URLRequest(BaseModel):url:str=Field(min_length=4,max_length=2000)
class IncidentCreate(BaseModel):title:str=Field(min_length=3,max_length=180);occurred_at:datetime;scam_type:str=Field(min_length=2,max_length=60);amount:float=Field(0,ge=0,le=1_000_000_000);payment_method:str|None=None;transaction_reference:str|None=None;phone_number:str|None=None;url:str|None=None;description:str=Field(min_length=10,max_length=6000)
class IncidentUpdate(BaseModel):status:str=Field(pattern='^(NEW|DOCUMENTING|REPORTED|UNDER_REVIEW|RESOLVED)$')
class EvidenceCreate(BaseModel):evidence_type:str=Field(min_length=2,max_length=60);label:str=Field(min_length=2,max_length=180);content:str=Field(min_length=1,max_length=6000);occurred_at:datetime|None=None
class PasswordChange(BaseModel):
 current_password:str=Field(min_length=10,max_length=128)
 new_password:str=Field(min_length=10,max_length=128)
class TransactionRiskRequest(BaseModel):
 amount:float=Field(gt=0,le=1_000_000_000)
 category:str=Field(min_length=2,max_length=80)
 merchant:str=Field(min_length=1,max_length=120)
 payment_method:str|None=Field(None,max_length=50)
 description:str|None=Field(None,max_length=500)
