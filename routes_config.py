from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import PlainTextResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session

from database import SessionLocal
from models import RunConfig, User
from routes_auth import get_current_user

router = APIRouter(prefix="/api/config", tags=["config"])


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


class RunConfigCreate(BaseModel):
    campus_name: str = ""
    x1: float = 0
    y1: float = 0
    x2: float = 0
    y2: float = 0
    x3: float = 0
    y3: float = 0
    x4: float = 0
    y4: float = 0
    speed: float = 1.0
    loops: int = 1
    randomize: bool = False  # 随机扰动


@router.get("/")
def get_config(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    config = db.query(RunConfig).filter(RunConfig.user_id == user.id).first()
    if not config:
        return None
    return {
        "id": config.id,
        "campus_name": config.campus_name,
        "x1": config.x1, "y1": config.y1,
        "x2": config.x2, "y2": config.y2,
        "x3": config.x3, "y3": config.y3,
        "x4": config.x4, "y4": config.y4,
        "speed": config.speed,
        "loops": config.loops,
        "randomize": config.randomize,
    }


@router.post("/")
def create_config(req: RunConfigCreate, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    existing = db.query(RunConfig).filter(RunConfig.user_id == user.id).first()
    if existing:
        raise HTTPException(status_code=400, detail="已有配置，请先删除")

    config = RunConfig(
        user_id=user.id,
        campus_name=req.campus_name,
        x1=req.x1, y1=req.y1,
        x2=req.x2, y2=req.y2,
        x3=req.x3, y3=req.y3,
        x4=req.x4, y4=req.y4,
        speed=req.speed,
        loops=req.loops,
        randomize=req.randomize,
    )
    db.add(config)
    db.commit()
    db.refresh(config)
    return {"id": config.id, "message": "配置已保存"}


@router.put("/")
def update_config(req: RunConfigCreate, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    config = db.query(RunConfig).filter(RunConfig.user_id == user.id).first()
    if not config:
        raise HTTPException(status_code=404, detail="配置不存在")

    config.campus_name = req.campus_name
    config.x1 = req.x1; config.y1 = req.y1
    config.x2 = req.x2; config.y2 = req.y2
    config.x3 = req.x3; config.y3 = req.y3
    config.x4 = req.x4; config.y4 = req.y4
    config.speed = req.speed
    config.loops = req.loops
    config.randomize = req.randomize
    db.commit()
    return {"message": "配置已更新"}


@router.get("/download")
def download_config(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    config = db.query(RunConfig).filter(RunConfig.user_id == user.id).first()
    if not config:
        raise HTTPException(status_code=404, detail="配置不存在")

    import random as _rnd
    def perturb(v):
        """给坐标加随机 GPS 漂移，范围 ±0.0003 度（约 ±30 米）"""
        return round(v + _rnd.uniform(-0.0003, 0.0003), 6)

    if config.randomize:
        x1, y1 = perturb(config.x1), perturb(config.y1)
        x2, y2 = perturb(config.x2), perturb(config.y2)
        x3, y3 = perturb(config.x3), perturb(config.y3)
        x4, y4 = perturb(config.x4), perturb(config.y4)
        speed = round(config.speed * _rnd.uniform(0.85, 1.15), 1)
    else:
        x1, y1 = config.x1, config.y1
        x2, y2 = config.x2, config.y2
        x3, y3 = config.x3, config.y3
        x4, y4 = config.x4, config.y4
        speed = config.speed

    content = f"{x1} {y1} {x2} {y2} {x3} {y3} {x4} {y4}\n{speed}\n{config.loops}"
    return PlainTextResponse(content, media_type="text/plain", headers={
        "Content-Disposition": "attachment; filename=in.txt"
    })


@router.delete("/")
def delete_config(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    config = db.query(RunConfig).filter(RunConfig.user_id == user.id).first()
    if not config:
        raise HTTPException(status_code=404, detail="配置不存在")
    db.delete(config)
    db.commit()
    return {"message": "配置已删除"}
