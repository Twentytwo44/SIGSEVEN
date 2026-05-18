FROM python:3.11-slim

WORKDIR /app

# ติดตั้งไลบรารีที่จำเป็น
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# ก๊อปปี้โค้ดหลังบ้านทั้งหมด
COPY . .

EXPOSE 8000

# รัน FastAPI ด้วย uvicorn
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]