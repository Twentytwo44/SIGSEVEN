# app/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.routes import router as api_router # นำเข้ารองเตอร์เข้ามา

app = FastAPI(title="SIGSEVEN Options Engine")

# ปลดล็อก CORS ให้ฝั่ง React ยิงฝั่ง Python ได้สะดวก
origins = [
    "https://sigseven.vercel.app",  # เว็บหน้าบ้านบน Vercel ของจริง
    "http://localhost:3000",        # เผื่อรันเทสหน้าบ้านในเครื่องด้วย React
    "http://localhost:5173",        # เผื่อรันเทสหน้าบ้านในเครื่องด้วย Vite
]

# 🔥 3. ติดตั้ง Middleware ให้ FastAPI รับแขก
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],  # อนุญาตทุกคำสั่ง (GET, POST, PUT, DELETE)
    allow_headers=["*"],  # อนุญาตทุก Header
)

# 💥 สำคัญ: ต้องรวมเราเตอร์นี้เข้ามาในระบบหลัก
app.include_router(api_router) 

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)