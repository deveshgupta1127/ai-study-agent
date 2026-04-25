import jwt
from jwt.exceptions import InvalidTokenError
from pwdlib import PasswordHash
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any
from backend.config import get_settings

settings=get_settings()

password_hash=PasswordHash.recommended()

def hash_password(password:str)->str:
    return password_hash.hash(password)

def verify_password(plain:str, hashed:str)->bool:
    return password_hash.verify(plain, hashed)

def create_access_token(
        data:dict[str, Any],
        expires_delta:Optional[timedelta]=None
)->str:
    to_encode=data.copy()

    expire=datetime.now(timezone.utc)+(expires_delta or timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({
        "exp":expire,
        "type":"access"
    })

    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm="HS256")

def create_refresh_token(data:dict)->str:
    to_encode=data.copy()

    expire=datetime.now(timezone.utc)+timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)

    to_encode.update({
        "exp":expire,
        "type":"refresh"
    })

    return jwt.encode(to_encode,settings.SECRET_KEY, algorithm="HS256")

def decode_token(token:str)->dict|None:
    try:
        payload=jwt.decode(token,settings.SECRET_KEY,algorithms=["HS256"])
        return payload
    except InvalidTokenError:
        return None
    