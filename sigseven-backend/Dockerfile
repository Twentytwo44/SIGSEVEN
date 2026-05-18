FROM python:3.11-slim

WORKDIR /app

# 1. ติดตั้งเครื่องมือคอมไพเลอร์พื้นฐาน
RUN apt-get update && apt-get install -y \
    git \
    build-essential \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*

# 2. อัปเดตตัวช่วยบิวด์ของ pip
RUN pip install --no-cache-dir --upgrade pip setuptools wheel

# 🔥 [FIX] ชิงติดตั้งรากฐานข้อมูลล่วงหน้า เพื่อป้องกันสคริปต์ setup.py ของ pandas-ta บิวด์พัง
RUN pip install --no-cache-dir numpy pandas

# 3. ติดตั้งไลบรารีที่เหลือตามรายการปกติ
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# ก๊อปปี้โค้ดหลังบ้านทั้งหมด
COPY . .

EXPOSE 8000

# รัน FastAPI ด้วย uvicorn
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]