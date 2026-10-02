from pathlib import Path
from pydantic_settings import BaseSettings,SettingsConfigDict
ENV_FILE=Path(__file__).resolve().parents[1]/'.env'
class Settings(BaseSettings):
 app_name:str='FinGuard API';environment:str='development';secret_key:str='dev-only-change-me';database_url:str='sqlite:///./finguard.db';access_token_minutes:int=30;allowed_origins:str='http://localhost:5173';allowed_hosts:str='localhost,127.0.0.1';gemini_api_key:str|None=None;gemini_model:str='gemini-3.8-flash';gemini_fallback_model:str='gemini-3.5-flash-lite';gemini_timeout_seconds:float=25;seed_demo:bool=False;demo_password:str|None=None
 model_config=SettingsConfigDict(env_file=ENV_FILE,extra='ignore')
settings=Settings()
if settings.environment=='production' and settings.secret_key=='dev-only-change-me':
 raise RuntimeError('SECRET_KEY must be configured in production')
