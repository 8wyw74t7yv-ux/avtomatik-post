import os
import json
import time
import random
import datetime
import requests
import subprocess
from google import genai
from zoneinfo import ZoneInfo

# --- SOZLAMALAR VA ENVIRONMENT O'ZGARUVCHILARI ---
LEONARDO_API_KEY = os.environ.get("LEONARDO_API_KEY")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
IG_USER_ID = os.environ.get("IG_USER_ID")
IG_ACCESS_TOKEN = os.environ.get("IG_ACCESS_TOKEN")

# 📌 USERNAME JOYI (O'z userneymingizni shu yerga yozing)
INSTAGRAM_USERNAME = os.environ.get("INSTAGRAM_USERNAME", "@YOUR_INSTAGRAM_USERNAME_HERE")

UZB_TIMEZONE = ZoneInfo("Asia/Tashkent")
LEONARDO_BASE_URL = "https://cloud.ai.leonardo.ai/api/rest/v1"

# Gemini klienta
client = genai.Client(api_key=GEMINI_API_KEY)


def get_next_idea():
    """10,000 talik bazadan (ideas.json) navbatdagi g'oyani oladi"""
    if not os.path.exists("ideas.json"):
        return "satisfying liquid glowing metallic substance loop"
    
    with open("ideas.json", "r", encoding="utf-8") as f:
        data = json.load(f)
        ideas = data.get("ideas", [])
    
    if not ideas:
        return "satisfying glowing metallic substance loop"
    
    # Hozircha birinchisini olamiz (keyinchalik o'qilganini o'chirib borish mumkin)
    idea = ideas[0]
    return idea


def enhance_prompt_with_gemini(raw_idea):
    """Gemini yordamida Leonardo AI uchun clickbait, loop, matnsiz ASMR prompt yaratish"""
    system_instruction = (
        "You are an expert prompt engineer for AI video generation (Leonardo AI). "
        "Create a hyper-realistic, visually stunning, clickbait, weirdly satisfying, "
        "seamless loop ASMR prompt based on the user's idea. "
        "CRITICAL: The prompt must result in a video with NO TEXT, pure mesmerizing visual physics, "
        "macro lens, unreal engine 5, 4k, smooth infinite loop motion."
    )
    
    response = client.models.generate_content(
        model='gemini-2.5-flash',
        contents=f"Idea: {raw_idea}",
        config={
            'system_instruction': system_instruction,
            'temperature': 0.7,
        }
    )
    return response.text.strip()


def generate_video_leonardo(prompt):
    """Leonardo AI API orqali 9:16 formatda 10 soniyali video generatsiya qilish"""
    headers = {
        "accept": "application/json",
        "content-type": "application/json",
        "authorization": f"Bearer {LEONARDO_API_KEY}"
    }
    
    payload = {
        "prompt": prompt,
        "modelId": "b824ea91-2453-4492-938e-0925e2f31448", # Motion/Creative model
        "width": 576,
        "height": 1024,
        "num_images": 1,
        "promptMagic": True
    }
    
    res = requests.post(f"{LEONARDO_BASE_URL}/generations", json=payload, headers=headers)
    if res.status_code != 200:
        print(f"❌ Leonardo xatosi: {res.text}")
        return None
        
    data = res.json()
    gen_id = data.get("sdGenerationJob", {}).get("generationId")
    print(f"⏳ Generatsiya boshlandi (ID: {gen_id}). Kutilmoqda...")
    
    # Generatsiya tayyor bo'lishini kutamiz (Polling)
    time.sleep(30)
    
    status_res = requests.get(f"{LEONARDO_BASE_URL}/generations/{gen_id}", headers=headers)
    status_data = status_res.json()
    
    try:
        images = status_data.get("generations_by_pk", {}).get("generated_images", [])
        if images:
            video_url = images[0].get("motionMP4URL") or images[0].get("url")
            return video_url
    except Exception as e:
        print(f"❌ Videoni olishda xatolik: {e}")
        
    return None


def process_video_ffmpeg(input_path, output_path):
    """FFmpeg yordamida pastki chap burchakka logotip va username qo'shish (1GB RAM tejamkor)"""
    # Agar repo ichida 'ig_logo.png' bo'lsa uni qo'shamiz, bo'lmasa faqat matn yozamiz
    logo_path = "ig_logo.png"
    
    if os.path.exists(logo_path):
        # Logotip va matnni pastki chap burchakka qo'yish (overlay)
        filter_complex = (
            f"[1:v]scale=40:40[logo];"
            f"[0:v][logo]overlay=15:H-h-15[bg];"
            f"[bg]drawtext=text='{INSTAGRAM_USERNAME}':fontcolor=white:fontsize=22:"
            f"box=1:boxcolor=black@0.5:boxborderw=5:x=65:y=H-h-20[out]"
        )
        cmd = [
            "ffmpeg", "-y", "-i", input_path, "-i", logo_path,
            "-filter_complex", filter_complex, "-map", "[out]",
            "-map", "0:a?", "-c:v", "libx264", "-crf", "23", "-preset", "ultrafast", output_path
        ]
    else:
        # Faqat matnli watermark (agar logo fayl yuklanmagan bo'lsa)
        cmd = [
            "ffmpeg", "-y", "-i", input_path,
            "-vf", f"drawtext=text='{INSTAGRAM_USERNAME}':fontcolor=white:fontsize=24:"
                   f"box=1:boxcolor=black@0.5:boxborderw=5:x=15:y=H-h-35",
            "-c:v", "libx264", "-crf", "23", "-preset", "ultrafast", output_path
        ]
        
    subprocess.run(cmd, check=True)


def publish_to_instagram(video_url, caption):
    """Meta Graph API orqali Instagram Reels joylash"""
    # 1. Konteyner yaratish
    container_url = f"https://graph.facebook.com/v18.0/{IG_USER_ID}/media"
    payload = {
        "media_type": "REELS",
        "video_url": video_url,
        "caption": caption,
        "access_token": IG_ACCESS_TOKEN
    }
    res = requests.post(container_url, data=payload)
    res_data = res.json()
    creation_id = res_data.get("id")
    
    if not creation_id:
        print(f"❌ Instagram konteyner xatosi: {res.text}")
        return False
        
    print(f"⏳ Reels yuklanmoqda... ID: {creation_id}")
    time.sleep(20) # Serverga yuklanishini kutamiz
    
    # 2. Nashr qilish (Publish)
    publish_url = f"https://graph.facebook.com/v18.0/{IG_USER_ID}/media_publish"
    publish_payload = {
        "creation_id": creation_id,
        "access_token": IG_ACCESS_TOKEN
    }
    pub_res = requests.post(publish_url, data=publish_payload)
    if pub_res.status_code == 200:
        print("✅ Reels muvaffaqiyatli e'lon qilindi!")
        return True
    else:
        print(f"❌ Nashr qilishda xatolik: {pub_res.text}")
        return False


def run_pipeline():
    print("🚀 Kontent quvuri ishga tushdi...")
    try:
        # 1. G'oya va Gemini prompt
        raw_idea = get_next_idea()
        print(f"💡 Tanlangan g'oya: {raw_idea}")
        
        prompt = enhance_prompt_with_gemini(raw_idea)
        print(f"✨ Gemini prompt yaratdi: {prompt}")
        
        # 2. Leonardo AI dan video olish
        raw_video_url = generate_video_leonardo(prompt)
        if not raw_video_url:
            print("❌ Video olinmadi, jarayon to'xtatildi.")
            return
            
        # Videoni vaqtincha yuklab olish
        temp_input = "temp_raw.mp4"
        temp_output = "temp_final.mp4"
        
        with open(temp_input, "wb") as f:
            f.write(requests.get(raw_video_url).content)
            
        # 3. FFmpeg bilan tahrirlash (Watermark)
        print("🎬 FFmpeg yordamida watermark qo'shilmoqda...")
        process_video_ffmpeg(temp_input, temp_output)
        
        # 4. Instagram uchun caption yaratish (Gemini orqali)
        caption_res = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=f"Write a short, engaging Instagram Reels caption and 3-4 trending ASMR/satisfying hashtags for this idea: {raw_idea}. NO TEXT IN VIDEO."
        )
        caption = caption_res.text.strip()
        
        # (Eslatma: Haqiqiy production muhitda video_url ochiq internetda turishi kerak, 
        # fly.io da vaqtincha public saqlash yoki to'g'ridan-to'g'ri binary yuborish ishlatiladi)
        # Hozircha raw_video_url ni beramiz yoki serverdan public link qilamiz.
        publish_to_instagram(raw_video_url, caption)
        
    except Exception as e:
        print(f"❌ Xatolik yuz berdi: {e}")
        
    finally:
        # 🧹 1GB RAMni tozalash (Cleanup)
        for f in ["temp_raw.mp4", "temp_final.mp4"]:
            if os.path.exists(f):
                os.remove(f)
        print("🧹 Xotira tozalandi.")


def schedule_loop():
    """Belgilangan vaqtlar bo'yicha random rejalashtiruvchi"""
    target_hours = [9, 11, 13, 15, 17, 19]
    
    while True:
        now = datetime.datetime.now(UZB_TIMEZONE)
        today_times = []
        
        for h in target_hours:
            # Har bir soatga tasodifiy minut qo'shamiz (masalan, 09:14, 11:42 va h.k.)
            m = random.randint(0, 55)
            t = now.replace(hour=h, minute=m, second=0, microsecond=0)
            if t > now:
                today_times.append(t)
                
        if not today_times:
            # Agar bugungi vaqtlar o'tib ketgan bo'lsa, ertangi kunning birinchi vaqtini olamiz
            tomorrow = now + datetime.timedelta(days=1)
            next_run = tomorrow.replace(hour=target_hours[0], minute=random.randint(0, 55), second=0)
        else:
            next_run = min(today_times)
            
        sleep_seconds = (next_run - now).total_seconds()
        print(f"⏰ Keyingi video chiqarish vaqti: {next_run.strftime('%Y-%m-%d %H:%M')} (Ushbu vaqtgacha uxlaydi)")
        
        time.sleep(sleep_seconds)
        run_pipeline()


if __name__ == "__main__":
    # SHART: Birinchi video darhol (hozirning o'zida) ishga tushadi!
    print("🔥 Birinchi video hozir ishga tushirilmoqda...")
    run_pipeline()
    
    # Keyingilari esa random vaqtlar bo'yicha davom etadi
    schedule_loop()
