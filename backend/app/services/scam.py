import re
from urllib.parse import urlparse,unquote

CATEGORY_PATTERNS={
 'banking_scam':['bank','account blocked','net banking','debit card','credit card'],
 'upi_scam':['upi','collect request','payment request','qr code','paytm','phonepe'],
 'investment_scam':['guaranteed return','double your money','crypto profit','investment opportunity'],
 'job_scam':['job offer','registration fee','work from home','interview fee'],
 'delivery_scam':['parcel','delivery fee','courier','package held'],
 'kyc_scam':['kyc','verify account','update identity','account suspended'],
 'lottery_scam':['lottery','prize','winner','claim reward'],
 'romance_scam':['love you','emergency money','gift card','military officer'],
 'tech_support_scam':['remote access','anydesk','teamviewer','virus detected','tech support'],
 'loan_scam':['instant loan','processing fee','loan approved','credit fee']}
URGENCY=['immediately','urgent','today','now','within 24 hours','final warning','act fast']
THREATS=['blocked','suspended','legal action','arrest','penalty','closed']
SENSITIVE=['otp','pin','password','cvv','private key','login credentials']
MONEY=['send money','transfer','pay now','processing fee','payment request','gift card']
SUSPICIOUS_TLDS={'zip','click','top','xyz','work','support','loan','live'}

def analyze_url(raw:str|None)->dict:
 if not raw:return {'risk_score':0,'risk_level':'LOW','signals':[],'explanation':'No URL was supplied.'}
 candidate=raw.strip()
 if not re.match(r'^https?://',candidate,re.I):candidate='http://'+candidate
 signals=[];score=0
 try:
  p=urlparse(candidate);host=(p.hostname or '').lower();decoded=unquote(candidate).lower()
  if p.scheme!='https':signals.append('Connection is not HTTPS');score+=18
  if re.fullmatch(r'\d{1,3}(\.\d{1,3}){3}',host):signals.append('IP address used instead of a domain');score+=28
  if host.count('.')>=3:signals.append('Excessive subdomains');score+=14
  if len(candidate)>120:signals.append('Unusually long URL');score+=12
  if '%' in raw or '@' in raw:signals.append('Encoded or misleading URL characters');score+=15
  if host.split('.')[-1] in SUSPICIOUS_TLDS:signals.append('Higher-risk top-level domain pattern');score+=15
  if any(x in decoded for x in ['verify','secure-login','kyc','account-update','claim','reward','wallet']):signals.append('Suspicious financial or verification keyword');score+=16
  if host.startswith('xn--'):signals.append('Internationalized look-alike domain');score+=22
  level='HIGH' if score>=55 else 'MEDIUM' if score>=25 else 'LOW'
  text='No obvious indicators detected by FinGuard current checks.' if not signals else f'{len(signals)} URL risk indicator(s) detected. This is model-assisted analysis, not definitive proof.'
  return {'risk_score':min(score,100),'risk_level':level,'signals':signals,'explanation':text,'normalized_url':candidate,'host':host}
 except Exception:return {'risk_score':65,'risk_level':'HIGH','signals':['URL could not be parsed reliably'],'explanation':'The URL format is invalid or intentionally obfuscated.'}

def analyze_message(text:str,url:str|None=None)->dict:
 clean=' '.join(text.lower().split());signals=[];score=5
 def hit(words,label,weight):
  nonlocal score
  if any(w in clean for w in words):signals.append(label);score+=weight
 hit(URGENCY,'Urgency language',18);hit(THREATS,'Threat or account-pressure language',16);hit(SENSITIVE,'Sensitive information requested',28);hit(MONEY,'Request for money or payment',20)
 if any(x in clean for x in ['bank','police','government','income tax','rbi','support team']):signals.append('Possible institutional impersonation');score+=17
 if any(x in clean for x in ['prize','lottery','guaranteed return','double your money']):signals.append('Unrealistic reward or return claim');score+=22
 url_result=analyze_url(url or (re.search(r'https?://\S+',text,re.I).group(0) if re.search(r'https?://\S+',text,re.I) else None))
 if url_result['risk_score']>=25:signals.extend(url_result['signals']);score+=round(url_result['risk_score']*.45)
 category='other';best=0
 for name,words in CATEGORY_PATTERNS.items():
  n=sum(w in clean for w in words)
  if n>best:best=n;category=name
 score=min(99,score);level='CRITICAL' if score>=85 else 'HIGH' if score>=65 else 'MEDIUM' if score>=35 else 'LOW';classification='Potential Scam' if score>=65 else 'Suspicious' if score>=35 else 'Likely Legitimate'
 actions=['Do not click links or send additional money.','Verify the sender using contact information from an official website or statement.','Preserve the message, URL, phone number and payment details as evidence.']
 if score>=65:actions+=['Contact the relevant bank or payment provider through its official channel.','Use the appropriate official cybercrime or law-enforcement reporting channel for your location.']
 return {'risk_score':score,'risk_level':level,'classification':classification,'category':category,'signals':list(dict.fromkeys(signals)) or ['No strong scam indicator detected by current checks'],'explanation':f'FinGuard found {len(set(signals))} explainable signal(s). This AI-assisted result should be independently verified.','recommended_actions':actions,'url_analysis':url_result,'confidence':round(.55+min(score,90)/250,2)}

def recovery_checklist(scam_type:str,description:str)->list[dict]:
 return [
  {'title':'Stop contact and additional payments','urgent':True},
  {'title':'Contact the relevant bank/payment provider using an official channel','urgent':True},
  {'title':'Report the transaction through the appropriate official reporting mechanism','urgent':True},
  {'title':'Preserve screenshots, messages, URLs, phone numbers and transaction IDs','urgent':False},
  {'title':'Change exposed credentials from a trusted device; never share an OTP, PIN or CVV','urgent':False},
  {'title':'Monitor accounts for additional unauthorized activity','urgent':False}]
