FROM python:3.11-slim

WORKDIR /app

# 1. ติดตั้งเครื่องมือคอมไพเลอร์พื้นฐาน
RUN apt-get update && apt-get install -y \
    git \
    build-essential \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*

# 2. อัปเดต pip และล็อกเวอร์ชัน setuptools รุ่นที่เป็นมิตรกับโครงสร้าง pandas-ta
RUN pip install --no-cache-dir --upgrade pip "setuptools<69.0.0" wheel

# 3. ติดตั้งไลบรารีตามรายการ requirements.txt
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# ก๊อปปี้โค้ดหลังบ้านทั้งหมด
COPY . .

EXPOSE 8000

# รัน FastAPI ด้วย uvicorn
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]