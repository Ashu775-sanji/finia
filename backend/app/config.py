from pydantic_settings import BaseSettings,SettingsConfigDict
class Settings(BaseSettings):
 app_name:str='FinGuard API';environment:str='development';secret_key:str='dev-only-change-me';database_url:str='sqlite:///./finguard.db';access_token_minutes:int=30;allowed_origins:str='http://localhost:5173'
 model_config=SettingsConfigDict(env_file='.env',extra='ignore')
settings=Settings()
