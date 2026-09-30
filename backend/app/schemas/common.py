from datetime import date,datetime
from pydantic import BaseModel,EmailStr,Field,ConfigDict
class UserCreate(BaseModel):name:str=Field(min_length=2,max_length=120);email:EmailStr;password:str=Field(min_length=10,max_length=128);currency:str=Field('USD',min_length=3,max_length=3);language:str='en'
class UserOut(BaseModel):model_config=ConfigDict(from_attributes=True);id:str;name:str;email:EmailStr;currency:str;language:str
class Token(BaseModel):access_token:str;token_type:str='bearer'
class TransactionCreate(BaseModel):amount:float=Field(gt=0,le=1_000_000_000);transaction_type:str;category:str=Field(min_length=2,max_length=80);merchant:str=Field(min_length=1,max_length=120);description:str|None=None;payment_method:str|None=None;date:date;location:str|None=None
class TransactionOut(TransactionCreate):model_config=ConfigDict(from_attributes=True);id:str;created_at:datetime
class BudgetCreate(BaseModel):category:str;limit:float=Field(gt=0);start_date:date;end_date:date
class GoalCreate(BaseModel):name:str;target_amount:float=Field(gt=0);current_amount:float=Field(0,ge=0);deadline:date
