from fastapi import FastAPI,Request
from fastapi.responses import JSONResponse
from collections import defaultdict,deque
import time
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from app.config import settings
from app.database.core import Base,engine
from app.api.routes import router
from app.database.seed import seed_demo_data
Base.metadata.create_all(bind=engine)
if settings.seed_demo:seed_demo_data()
app=FastAPI(title=settings.app_name,version='1.0.0',docs_url='/docs' if settings.environment!='production' else None)
app.add_middleware(CORSMiddleware,allow_origins=[x.strip() for x in settings.allowed_origins.split(',')],allow_credentials=True,allow_methods=['*'],allow_headers=['Authorization','Content-Type'])
app.add_middleware(TrustedHostMiddleware,allowed_hosts=['*'] if settings.environment!='production' else [x.strip() for x in settings.allowed_hosts.split(',')])
_limits=defaultdict(deque)
@app.middleware('http')
async def rate_limit(request:Request,call_next):
 if request.method=='POST' and request.url.path in {'/api/v1/ai/ask','/api/v1/scam/analyze','/api/v1/url/analyze','/api/v1/auth/login','/api/v1/auth/register','/api/v1/auth/change-password'}:
  key=f'{request.client.host if request.client else "unknown"}:{request.url.path}';now=time.time();q=_limits[key]
  while q and q[0]<now-60:q.popleft()
  limit=10 if '/auth/' in request.url.path else 30
  if len(q)>=limit:return JSONResponse({'detail':'Too many requests. Try again shortly.'},status_code=429)
  q.append(now)
 return await call_next(request)

@app.middleware('http')
async def secure_headers(request:Request,call_next):
 r=await call_next(request);r.headers['X-Content-Type-Options']='nosniff';r.headers['X-Frame-Options']='DENY';r.headers['Referrer-Policy']='strict-origin-when-cross-origin';r.headers['Permissions-Policy']='camera=(), microphone=(), geolocation=()';return r
@app.get('/health')
def health():return {'status':'healthy','service':'finguard-api'}
app.include_router(router)
