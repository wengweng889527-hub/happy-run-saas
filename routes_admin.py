from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session
import secrets
import string

from database import SessionLocal
from models import CardKey, User, RunConfig
from routes_auth import get_current_user

router = APIRouter(prefix="/api/admin", tags=["admin"])


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def require_admin(user: User = Depends(get_current_user)):
    if not user.is_admin:
        raise HTTPException(status_code=403, detail="无管理员权限")
    return user


class GenerateKeysRequest(BaseModel):
    count: int = 1
    prefix: str = ""


@router.post("/keys")
def generate_keys(req: GenerateKeysRequest, admin: User = Depends(require_admin), db: Session = Depends(get_db)):
    keys = []
    for _ in range(req.count):
        code = req.prefix + "-" + "".join(secrets.choice(string.ascii_uppercase + string.digits) for _ in range(8))
        key = CardKey(key=code)
        db.add(key)
        keys.append(code)
    db.commit()
    return {"keys": keys, "count": len(keys)}


@router.get("/keys")
def list_keys(admin: User = Depends(require_admin), db: Session = Depends(get_db)):
    keys = db.query(CardKey).order_by(CardKey.id.desc()).limit(50).all()
    return [{"id": k.id, "key": k.key, "is_used": k.is_used, "created_at": k.created_at.isoformat() if k.created_at else None} for k in keys]


@router.get("/users")
def list_users(admin: User = Depends(require_admin), db: Session = Depends(get_db)):
    users = db.query(User).order_by(User.id.desc()).all()
    return [{
        "id": u.id,
        "username": u.username,
        "is_active": u.is_active,
        "has_config": db.query(RunConfig).filter(RunConfig.user_id == u.id).first() is not None,
        "created_at": u.created_at.isoformat() if u.created_at else None,
    } for u in users]


@router.get("/stats")
def get_stats(admin: User = Depends(require_admin), db: Session = Depends(get_db)):
    return {
        "total_users": db.query(User).count(),
        "total_keys": db.query(CardKey).count(),
        "used_keys": db.query(CardKey).filter(CardKey.is_used == True).count(),
        "total_configs": db.query(RunConfig).count(),
    }
