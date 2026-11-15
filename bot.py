import json
import os
import time
from pathlib import Path
from urllib.parse import unquote
from instagrapi import Client

# ================== تنظیمات ==================
# این sessionid رو از مرورگر گرفتی
SESSIONID = "16096182361%3AmfLwy6lPFVrwzK%3A14%3AAYmLje3-jYRVorJ_FxQpfABU4ty8tCxgFS8pCzVqGg"

VIDEOS_FILE = "videos.txt"
STATE_FILE = "state.json"
DOWNLOAD_FOLDER = Path("downloaded_videos")
SESSION_FILE = "session.json"
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
    cl.delay_range = [2, 5]

    # اول سعی می‌کنه از فایل session.json بخونه (بهترین حالت)
    if os.path.exists(SESSION_FILE):
        try:
            print("در حال لود سشن از فایل session.json ...")
            cl.load_settings(SESSION_FILE)
            cl.get_timeline_feed()
            user = cl.account_info()
            print(f"✅ لاگین با سشن موفق بود → {user.username}")
            return cl
        except Exception as e:
            print(f"⚠ سشن فایل خراب یا منقضی شده: {e}")

    # اگر فایل نبود، با sessionid لاگین می‌کنه
    try:
        print("در حال لاگین با sessionid ...")
        sid = unquote(SESSIONID)
        cl.login_by_sessionid(sid)
        cl.dump_settings(SESSION_FILE)  # سشن رو ذخیره می‌کنه برای دفعات بعد
        user = cl.account_info()
        print(f"✅ لاگین با sessionid موفق بود → {user.username}")
        return cl
    except Exception as e:
        print(f"❌ خطا در لاگین با sessionid: {e}")
        raise


def post_one_story(cl, url, index):
    print(f"\n📥 در حال پردازش ویدیو شماره {index + 1}: {url}")

    try:
        media_pk = cl.media_pk_from_url(url)
        media = cl.media_info(media_pk)

        # فقط ویدیو رو قبول می‌کنه
        if media.media_type not in [2, 8] and not getattr(media, "video_url", None):
            print("⚠ این پست ویدیو نداره، رد می‌شه")
            return False

        DOWNLOAD_FOLDER.mkdir(exist_ok=True)
        video_path = cl.video_download(media_pk, folder=DOWNLOAD_FOLDER)
        print(f"✅ دانلود شد: {video_path}")

        # آپلود به استوری
        story = cl.video_upload_to_story(video_path)
        print(f"✅ استوری پست شد! Story ID: {story.pk}")

        # پاک کردن فایل موقت
        try:
            os.remove(video_path)
        except Exception:
            pass

        return True

    except Exception as e:
        print(f"❌ خطا در پردازش این ویدیو: {e}")
        return False


def main():
    print("=" * 55)
    print("Instagram Daily Story Bot (Railway Version)")
    print("ریسک بن شدن وجود دارد - با مسئولیت خودت استفاده کن")
    print("=" * 55)

    videos = load_videos()
    if not videos:
        print("لیست ویدیو خالیه. فایل videos.txt رو چک کن.")
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
        print("\n⚠ این ویدیو پست نشد. ایندکس جلو نرفت.")


if __name__ == "__main__":
    main()
