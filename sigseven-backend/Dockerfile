FROM python:3.11-slim

WORKDIR /app

# ติดตั้ง git เพื่อให้ pip ดึง tvdatafeed มาได้
RUN apt-get update && apt-get install -y git && rm -rf /var/lib/apt/lists/*

# อัปเดตเครื่องมือพื้นฐาน
RUN pip install --no-cache-dir --upgrade pip wheel setuptools

# ติดตั้งไลบรารีแบบ Clean รวดเดียวจบ
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# ก๊อปปี้โค้ดหลังบ้านทั้งหมด
COPY . .

EXPOSE 8000

# รัน FastAPI ด้วย uvicorn
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]