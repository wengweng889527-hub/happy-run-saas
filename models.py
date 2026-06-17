from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Float
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from database import Base


class CardKey(Base):
    __tablename__ = "card_keys"
    id = Column(Integer, primary_key=True, index=True)
    key = Column(String(64), unique=True, index=True, nullable=False)
    is_used = Column(Boolean, default=False)
    used_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    expires_at = Column(DateTime, nullable=True)


class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    card_key_id = Column(Integer, ForeignKey("card_keys.id"), nullable=True)
    is_active = Column(Boolean, default=True)
    is_admin = Column(Boolean, default=False)
    app_phone = Column(String(50), nullable=True)      # 步道乐跑app手机号/学号
    app_password = Column(String(100), nullable=True)   # 步道乐跑app密码
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    configs = relationship("RunConfig", back_populates="user", cascade="all, delete-orphan")


class RunConfig(Base):
    __tablename__ = "run_configs"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    campus_name = Column(String(100), default="")
    # 四个顶点坐标
    x1 = Column(Float, default=0)
    y1 = Column(Float, default=0)
    x2 = Column(Float, default=0)
    y2 = Column(Float, default=0)
    x3 = Column(Float, default=0)
    y3 = Column(Float, default=0)
    x4 = Column(Float, default=0)
    y4 = Column(Float, default=0)
    # 速度和循环次数
    speed = Column(Float, default=1.0)  # t: 越大越慢
    loops = Column(Integer, default=1)   # k: 循环圈数
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    user = relationship("User", back_populates="configs")
