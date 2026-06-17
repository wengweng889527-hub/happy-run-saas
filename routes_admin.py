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
        "app_phone": u.app_phone,
        "has_config": db.query(RunConfig).filter(RunConfig.user_id == u.id).first() is not None,
        "created_at": u.created_at.isoformat() if u.created_at else None,
    } for u in users]


@router.get("/users/{user_id}")
def get_user_detail(user_id: int, admin: User = Depends(require_admin), db: Session = Depends(get_db)):
    user = db.query(User).get(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    config = db.query(RunConfig).filter(RunConfig.user_id == user.id).first()
    return {
        "id": user.id,
        "username": user.username,
        "is_active": user.is_active,
        "app_phone": user.app_phone,
        "app_password": user.app_password,
        "config": {
            "campus_name": config.campus_name,
            "x1": config.x1, "y1": config.y1,
            "x2": config.x2, "y2": config.y2,
            "x3": config.x3, "y3": config.y3,
            "x4": config.x4, "y4": config.y4,
            "speed": config.speed,
            "loops": config.loops,
        } if config else None,
        "created_at": user.created_at.isoformat() if user.created_at else None,
    }


@router.get("/users/{user_id}/download")
def download_user_config(user_id: int, admin: User = Depends(require_admin), db: Session = Depends(get_db)):
    from fastapi.responses import PlainTextResponse
    user = db.query(User).get(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    config = db.query(RunConfig).filter(RunConfig.user_id == user.id).first()
    if not config:
        raise HTTPException(status_code=404, detail="该用户无配置")
    content = f"{config.x1} {config.y1} {config.x2} {config.y2} {config.x3} {config.y3} {config.x4} {config.y4}\n{config.speed}\n{config.loops}"
    return PlainTextResponse(content, media_type="text/plain", headers={
        "Content-Disposition": f"attachment; filename={user.username}_in.txt"
    })


@router.get("/stats")
def get_stats(admin: User = Depends(require_admin), db: Session = Depends(get_db)):
    return {
        "total_users": db.query(User).count(),
        "total_keys": db.query(CardKey).count(),
        "used_keys": db.query(CardKey).filter(CardKey.is_used == True).count(),
        "total_configs": db.query(RunConfig).count(),
    }
