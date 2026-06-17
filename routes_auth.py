from fastapi import APIRouter, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from sqlalchemy.orm import Session
from datetime import datetime, timedelta, timezone
import bcrypt
import jwt

from database import SessionLocal, SECRET_KEY
from models import User, CardKey

router = APIRouter(prefix="/api/auth", tags=["auth"])
security = HTTPBearer()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def create_token(user_id: int, username: str, is_admin: bool) -> str:
    payload = {
        "user_id": user_id,
        "username": username,
        "is_admin": is_admin,
        "exp": datetime.now(timezone.utc) + timedelta(days=30),
    }
    return jwt.encode(payload, SECRET_KEY, algorithm="HS256")


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db),
) -> User:
    try:
        payload = jwt.decode(credentials.credentials, SECRET_KEY, algorithms=["HS256"])
        user = db.query(User).get(payload["user_id"])
        if not user or not user.is_active:
            raise HTTPException(status_code=401, detail="用户不存在或已禁用")
        return user
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="登录已过期")
    except Exception:
        raise HTTPException(status_code=401, detail="无效的认证")


class RegisterRequest(BaseModel):
    card_key: str
    username: str
    password: str
    app_phone: str = ""       # 步道乐跑app手机号/学号
    app_password: str = ""    # 步道乐跑app密码


class LoginRequest(BaseModel):
    username: str
    password: str


class UpdateAccountRequest(BaseModel):
    app_phone: str = ""
    app_password: str = ""


@router.post("/register")
def register(req: RegisterRequest, db: Session = Depends(get_db)):
    if len(req.username) < 3:
        raise HTTPException(status_code=400, detail="用户名至少3位")
    if len(req.password) < 6:
        raise HTTPException(status_code=400, detail="密码至少6位")

    card = db.query(CardKey).filter(CardKey.key == req.card_key).first()
    if not card:
        raise HTTPException(status_code=400, detail="卡密无效")
    if card.is_used:
        raise HTTPException(status_code=400, detail="卡密已被使用")
    if card.expires_at and card.expires_at < datetime.now(timezone.utc):
        raise HTTPException(status_code=400, detail="卡密已过期")

    existing = db.query(User).filter(User.username == req.username).first()
    if existing:
        raise HTTPException(status_code=400, detail="用户名已存在")

    user = User(
        username=req.username,
        password_hash=bcrypt.hashpw(req.password.encode(), bcrypt.gensalt()).decode(),
        card_key_id=card.id,
        app_phone=req.app_phone,
        app_password=req.app_password,
    )
    card.is_used = True
    card.used_by = None  # will be set after flush
    db.add(user)
    db.flush()
    card.used_by = user.id
    db.commit()
    db.refresh(user)
    token = create_token(user.id, user.username, user.is_admin)
    return {"token": token, "username": user.username, "is_admin": user.is_admin}


@router.post("/login")
def login(req: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == req.username).first()
    if not user:
        raise HTTPException(status_code=401, detail="用户名或密码错误")
    if not bcrypt.checkpw(req.password.encode(), user.password_hash.encode()):
        raise HTTPException(status_code=401, detail="用户名或密码错误")

    token = create_token(user.id, user.username, user.is_admin)
    return {"token": token, "username": user.username, "is_admin": user.is_admin}


@router.put("/account")
def update_account(req: UpdateAccountRequest, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    user.app_phone = req.app_phone
    user.app_password = req.app_password
    db.commit()
    return {"message": "已更新"}
