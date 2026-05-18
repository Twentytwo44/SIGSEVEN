FROM python:3.11-slim

WORKDIR /app

# 🔥 [FIX] ติดตั้ง git, gcc, build-essential และ python3-dev เพื่อรองรับการบิวด์ Lib จาก GitHub
RUN apt-get update && apt-get install -y \
    git \
    build-essential \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*

# อัปเดตเครื่องมือช่วยบิวด์ของ pip ให้เป็นเวอร์ชันล่าสุดก่อน
RUN pip install --no-cache-dir --upgrade pip setuptools wheel

# ติดตั้งไลบรารีที่จำเป็น
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# ก๊อปปี้โค้ดหลังบ้านทั้งหมด
COPY . .

EXPOSE 8000

# รัน FastAPI ด้วย uvicorn
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]