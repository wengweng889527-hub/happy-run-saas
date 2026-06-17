import os
import bcrypt
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

from database import engine, Base, SessionLocal, SERVER_PORT
from models import User, CardKey, RunConfig

Base.metadata.create_all(bind=engine)

# 数据库迁移：添加新字段
from sqlalchemy import text
with engine.connect() as conn:
    try:
        conn.execute(text("ALTER TABLE users ADD COLUMN app_phone VARCHAR(50)"))
        conn.commit()
    except Exception:
        pass  # 字段已存在
    try:
        conn.execute(text("ALTER TABLE users ADD COLUMN app_password VARCHAR(100)"))
        conn.commit()
    except Exception:
        pass

# 创建默认管理员
db = SessionLocal()
try:
    admin = db.query(User).filter(User.username == "admin").first()
    if not admin:
        admin = User(
            username="admin",
            password_hash=bcrypt.hashpw("admin123".encode(), bcrypt.gensalt()).decode(),
            is_admin=True,
        )
        db.add(admin)
        db.commit()
finally:
    db.close()

app = FastAPI(title="步道乐跑", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

from routes_auth import router as auth_router
from routes_config import router as config_router
from routes_admin import router as admin_router

app.include_router(auth_router)
app.include_router(config_router)
app.include_router(admin_router)

STATIC_DIR = os.path.join(os.path.dirname(__file__), "static")
if os.path.exists(STATIC_DIR):
    @app.get("/")
    async def index():
        return FileResponse(os.path.join(STATIC_DIR, "index.html"))

    @app.get("/dashboard")
    async def dashboard():
        return FileResponse(os.path.join(STATIC_DIR, "dashboard.html"))

    @app.get("/admin")
    async def admin_page():
        return FileResponse(os.path.join(STATIC_DIR, "admin.html"))

if __name__ == "__main__":
    public_url = os.getenv("RAILWAY_PUBLIC_DOMAIN", "")
    base = f"https://{public_url}" if public_url else f"http://localhost:{SERVER_PORT}"
    print(f"\n 步道乐跑 v1.0")
    print(f" 地址: {base}")
    print(f" 管理后台: {base}/admin")
    print(f" 管理员: admin / admin123\n")
    uvicorn.run(app, host="0.0.0.0", port=SERVER_PORT, log_level="info")
