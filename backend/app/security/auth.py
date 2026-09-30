from datetime import datetime,timedelta,timezone
from fastapi import Depends,HTTPException,status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError,jwt
from passlib.context import CryptContext
from sqlalchemy.orm import Session
from app.config import settings
from app.database.core import get_db
from app.models.entities import User
pwd=CryptContext(schemes=['argon2'],deprecated='auto');oauth=OAuth2PasswordBearer(tokenUrl='/api/v1/auth/login');ALGO='HS256'
def hash_password(v:str)->str:return pwd.hash(v)
def verify_password(raw:str,hashed:str)->bool:return pwd.verify(raw,hashed)
def create_token(uid:str)->str:return jwt.encode({'sub':uid,'exp':datetime.now(timezone.utc)+timedelta(minutes=settings.access_token_minutes)},settings.secret_key,algorithm=ALGO)
def current_user(token:str=Depends(oauth),db:Session=Depends(get_db))->User:
 try:uid=jwt.decode(token,settings.secret_key,algorithms=[ALGO]).get('sub')
 except JWTError:raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,detail='Invalid credentials')
 user=db.get(User,uid) if uid else None
 if not user:raise HTTPException(status_code=401,detail='Invalid credentials')
 return user
