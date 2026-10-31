FROM python:3.10-slim

# Tizimga FFmpeg ni o'rnatish (video tahrirlash va watermark uchun)
RUN apt-get update && apt-get install -y ffmpeg && rm -rf /var/lib/apt/lists/*

# Ishchi katalogni belgilash
WORKDIR /app

# Kutubxonalarni o'rnatish
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Barcha kodlarni ko'chirish
COPY . .

# Asosiy skriptni ishga tushirish
CMD ["python", "main.py"]
