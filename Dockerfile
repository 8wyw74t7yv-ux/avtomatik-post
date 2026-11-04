# Python rasmiy yengil versiyasidan foydalanamiz
FROM python:3.11-slim

# Ishchi katalogni yaratish
WORKDIR /app

# Tizim paketlarini va FFmpeg'ni o'rnatish (Audio effektlar va vizualizator uchun shart!)
RUN apt-get update && apt-get install -y \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# Talab qilinadigan kutubxona ro'yxatini ko'chirish
COPY requirements.txt .

# Python kutubxonalarini o'rnatish
RUN pip install --no-cache-dir -r requirements.txt

# Loyihaning qolgan barcha fayllarini ko'chirish
COPY . .

# Botni ishga tushirish buyrug'i
CMD ["python", "main.py"]
