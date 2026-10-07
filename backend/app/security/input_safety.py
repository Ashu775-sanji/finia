"""Reject supplied credential values without echoing or persisting them."""
import re
from urllib.parse import urlparse
_SECRET_VALUE=re.compile(r'\b(?:otp|(?:upi\s*)?pin|cvv|verification\s*code)\s*(?:is|[:=]|-)?\s*\d{3,8}\b|\b(?:bank(?:ing)?\s+)?password\s*(?:is|[:=])\s*\S+|-----BEGIN (?:RSA |EC )?PRIVATE KEY-----',re.I)
def reject_secret_values(value):
 if isinstance(value,str) and _SECRET_VALUE.search(value):
  raise ValueError('Remove secret values such as OTPs, PINs, CVVs, UPI PINs or banking passwords before submitting financial content')
 return value

def validate_analysis_url(value):
 if not value:return value
 raw=str(value).strip()
 if re.match(r'^[a-z][a-z0-9+.-]*:',raw,re.I) and not re.match(r'^https?://',raw,re.I):
  raise ValueError('Use an HTTP or HTTPS URL')
 parsed=urlparse(raw if re.match(r'^https?://',raw,re.I) else 'https://'+raw)
 if parsed.scheme not in {'http','https'} or not parsed.hostname or parsed.username or parsed.password:
  raise ValueError('Use an HTTP or HTTPS URL without embedded login credentials')
 return value
