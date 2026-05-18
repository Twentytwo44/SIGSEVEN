# app/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.routes import router as api_router # นำเข้ารองเตอร์เข้ามา

app = FastAPI(title="SIGSEVEN Options Engine")

# ปลดล็อก CORS ให้ฝั่ง React ยิงฝั่ง Python ได้สะดวก
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 💥 สำคัญ: ต้องรวมเราเตอร์นี้เข้ามาในระบบหลัก
app.include_router(api_router) 

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)