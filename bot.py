import json
import os
import time
from pathlib import Path
from instagrapi import Client
from instagrapi.exceptions import LoginRequired, ChallengeRequired

# ================== تنظیمات ==================
USERNAME = "radvinhsa"          # یوزرنیم اینستا
PASSWORD = "Radvin.1392"          # فقط برای اولین لاگین
SESSION_FILE = "session.json"
VIDEOS_FILE = "videos.txt"
STATE_FILE = "state.json"
DOWNLOAD_FOLDER = Path("downloaded_videos")
# ============================================

def load_state():
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"index": 0, "posted": []}

def save_state(state):
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(state, f, indent=2, ensure_ascii=False)

def load_videos():
    if not os.path.exists(VIDEOS_FILE):
        print(f"❌ فایل {VIDEOS_FILE} پیدا نشد!")
        return []
    with open(VIDEOS_FILE, "r", encoding="utf-8") as f:
        urls = [line.strip() for line in f if line.strip() and not line.startswith("#")]
    return urls

def login():
    cl = Client()
    cl.delay_range = [1, 3]  # کمی تأخیر برای کاهش ریسک

    if os.path.exists(SESSION_FILE):
        try:
            cl.load_settings(SESSION_FILE)
            cl.login(USERNAME, PASSWORD)  # فقط برای چک کردن سشن
            cl.get_timeline_feed()  # تست لاگین
            print("✅ لاگین با سشن موفق بود")
            return cl
        except Exception as e:
            print(f"⚠ سشن منقضی شده، دوباره لاگین می‌کنم... ({e})")

    # لاگین اولیه
    try:
        cl.login(USERNAME, PASSWORD)
        cl.dump_settings(SESSION_FILE)
        print("✅ لاگین موفق + سشن ذخیره شد")
        return cl
    except ChallengeRequired:
        print("❌ اینستاگرام چالش (کد تأیید) خواسته. دستی لاگین کن و سشن رو ذخیره کن.")
        raise
    except Exception as e:
        print(f"❌ خطا در لاگین: {e}")
        raise

def post_one_story(cl, url, index):
    print(f"\n📥 در حال پردازش ویدیو شماره {index + 1}: {url}")

    try:
        media_pk = cl.media_pk_from_url(url)
        media = cl.media_info(media_pk)

        # فقط ویدیو/ریلز رو قبول کن
        if media.media_type not in [2, 8]:  # 2 = video, 8 = album
            if not getattr(media, "video_url", None):
                print("⚠ این پست ویدیو نداره، رد می‌شه")
                return False

        DOWNLOAD_FOLDER.mkdir(exist_ok=True)
        video_path = cl.video_download(media_pk, folder=DOWNLOAD_FOLDER)
        print(f"✅ دانلود شد: {video_path}")

        # آپلود به استوری
        story = cl.video_upload_to_story(video_path)
        print(f"✅ استوری پست شد! Story ID: {story.pk}")

        # پاک کردن فایل دانلود شده (اختیاری)
        try:
            os.remove(video_path)
        except Exception:
            pass

        return True

    except Exception as e:
        print(f"❌ خطا در پردازش این ویدیو: {e}")
        return False

def main():
    print("=" * 50)
    print("Instagram Daily Story from Reposts Bot")
    print("ریسک بن شدن وجود دارد - با مسئولیت خودت استفاده کن")
    print("=" * 50)

    videos = load_videos()
    if not videos:
        print("لیست ویدیو خالیه. فایل videos.txt رو پر کن.")
        return

    state = load_state()
    current_index = state.get("index", 0)

    if current_index >= len(videos):
        print("✅ همه ویدیوها پست شدن. لیست تموم شده.")
        return

    cl = login()

    url = videos[current_index]
    success = post_one_story(cl, url, current_index)

    if success:
        state["index"] = current_index + 1
        state["posted"].append({
            "url": url,
            "time": time.strftime("%Y-%m-%d %H:%M:%S")
        })
        save_state(state)
        print(f"\n🎯 پیشرفت: {state['index']} از {len(videos)}")
    else:
        print("\n⚠ این ویدیو پست نشد. ایندکس جلو نرفت تا دوباره امتحان کنی.")

if __name__ == "__main__":
    main()
