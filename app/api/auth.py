from fastapi import APIRouter, HTTPException, status
from app.models.auth import UserLogin, Token
from app.core import security
from app.core.config import settings


router = APIRouter()


@router.post("/login", response_model=Token)
async def login(credentials: UserLogin):
    if (credentials.username == settings.ADMIN_USERNAME and 
        credentials.password == settings.ADMIN_PASSWORD):
        
        token = security.create_access_token(data={"sub": credentials.username})
        return {"access_token": token, "token_type": "bearer"}
    
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid credentials"
    )