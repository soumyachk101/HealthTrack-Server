import base64
import json
import hmac
import hashlib
import time

class InvalidTokenError(Exception):
    pass

class ExpiredSignatureError(InvalidTokenError):
    pass

def base64url_encode(input_bytes):
    return base64.urlsafe_b64encode(input_bytes).decode('utf-8').rstrip('=')

def base64url_decode(input_str):
    rem = len(input_str) % 4
    if rem > 0:
        input_str += '=' * (4 - rem)
    return base64.urlsafe_b64decode(input_str)

def encode(payload, key, algorithm='HS256'):
    header = {"alg": algorithm, "typ": "JWT"}
    header_bytes = base64url_encode(json.dumps(header).encode('utf-8'))
    payload_bytes = base64url_encode(json.dumps(payload, default=str).encode('utf-8'))
    
    signing_input = f"{header_bytes}.{payload_bytes}".encode('utf-8')
    
    if isinstance(key, str):
        key = key.encode('utf-8')
        
    signature = hmac.new(key, signing_input, hashlib.sha256).digest()
    sig_bytes = base64url_encode(signature)
    
    return f"{header_bytes}.{payload_bytes}.{sig_bytes}"

def decode(token, key, algorithms=['HS256']):
    try:
        parts = token.split('.')
        if len(parts) != 3:
            raise InvalidTokenError("Invalid token format")
            
        header_bytes, payload_bytes, signature = parts
        signing_input = f"{header_bytes}.{payload_bytes}".encode('utf-8')
        
        if isinstance(key, str):
            key = key.encode('utf-8')
            
        expected_sig = base64url_encode(hmac.new(key, signing_input, hashlib.sha256).digest())
        
        if not hmac.compare_digest(signature, expected_sig):
            raise InvalidTokenError("Signature verification failed")
            
        payload = json.loads(base64url_decode(payload_bytes).decode('utf-8'))
        
        if 'exp' in payload:
            exp = payload['exp']
            if isinstance(exp, (int, float)):
                if exp < time.time():
                    raise ExpiredSignatureError("Signature has expired")
                
        return payload
    except Exception as e:
        if isinstance(e, InvalidTokenError):
            raise e
        raise InvalidTokenError(str(e))
