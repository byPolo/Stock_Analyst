from pydantic import BaseModel, EmailStr
from typing import Optional

class User(BaseModel):
    username: str
    password: str
    email: EmailStr
    full_name: Optional[str] = None
    is_admin: bool = False
    balance: float = 10000.0


