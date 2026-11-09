import os
import time
import subprocess
from DrissionPage import ChromiumPage, ChromiumOptions

# GitHub YAML inputs se data lena
url = os.getenv('TARGET_URL', 'https://playsza.st/player.php?id=willow')
stream_key = os.getenv('FB_STREAM_KEY')
duration_minutes = int(os.getenv('DURATION', '30'))

if not stream_key:
    print("❌ Error: Facebook Stream Key missing hai!")
    exit(1)

print(f"🚀 Target URL: {url}")

# DrissionPage Options
co = ChromiumOptions()
co.set_argument('--no-sandbox')
co.set_argument('--disable-dev-shm-usage')
co.set_argument('--disable-gpu')
co.set_argument('--remote-debugging-port=9222')
co.set_argument('--disable-software-rasterizer')
co.set_argument('--disable-blink-features=AutomationControlled')
co.auto_port()

# Browser start karein (yeh JS runtime error ko khatam kar dega)
page = ChromiumPage(addr_or_opts=co)

try:
    print("🌐 Website load ho rahi hai (bypassing Cloudflare)...")
    page.get(url)

    # Cloudflare ko verify karne ke liye wait
    time.sleep(6)

    # Cloudflare checkbox click logic
    try:
        cf_frame = page.get_frame('@title=Widget containing a Cloudflare security challenge')
        if cf_frame:
            print("🛡️ Cloudflare box mila, click kar rahe hain...")
            checkbox = cf_frame.ele('.cf-turnstile-wrapper')
            if checkbox:
                checkbox.click()
                time.sleep(3)
    except Exception as e:
        print(f"ℹ️ Cloudflare check skipped/passed: {e}")

    print("\n✅ Page load ho gaya. Iframes scan ho rahe hain...\n")

    # Iframes scan logic
    outer_frames = page.get_frames()
    print(f"Total Level 1 Iframes Found: {len(outer_frames)}\n")

    for i, f1 in enumerate(outer_frames):
        id1 = f1.attr('id') or '-'
        src1 = f1.attr('src') or '-'
        if len(src1) > 60: src1 = src1[:60] + "..."
        print(f"[{i+1}] Outer Iframe ─ ID: {id1} | URL: {src1}")
        
        inner_frames = f1.get_frames()
        for j, f2 in enumerate(inner_frames):
            id2 = f2.attr('id') or '-'
            src2 = f2.attr('src') or '-'
            if len(src2) > 60: src2 = src2[:60] + "..."
            print(f"    ↳ Inner Iframe ─ ID: {id2} | URL: {src2}")

    print("\n✅ Scanning mukammal! Facebook Live stream shuru ki ja rahi hai...")

    # FFmpeg streaming process start karna (Screen + Dummy Audio for Facebook)
    rtmp_url = f"rtmps://live-api-s.facebook.com:443/rtmp/{stream_key}"
    display_id = os.getenv('DISPLAY', ':99')

    ffmpeg_cmd = [
        'ffmpeg',
        '-y',
        '-f', 'x11grab',
        '-video_size', '1280x720',
        '-framerate', '30',
        '-i', display_id,
        # Facebook ke liye mandatory dummy audio track
        '-f', 'lavfi',
        '-i', 'anullsrc=channel_layout=stereo:sample_rate=44100',
        '-c:a', 'aac',
        '-b:a', '128k',
        '-c:v', 'libx264',
        '-preset', 'veryfast',
        '-b:v', '2500k',
        '-maxrate', '2500k',
        '-bufsize', '5000k',
        '-pix_fmt', 'yuv420p',
        '-g', '60',
        '-f', 'flv',
        rtmp_url
    ]

    print(f"[+] FFmpeg stream process spawn ho raha hai...")
    ffmpeg_process = subprocess.Popen(ffmpeg_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    # Required duration tak stream chalne dein
    total_seconds = duration_minutes * 60
    print(f"[+] Stream chalu hai! Yeh script {duration_minutes} minutes tak chalegi...")
    
    time.sleep(total_seconds)

    print("[+] Waqt poora ho gaya, stream band ki ja rahi hai...")
    ffmpeg_process.terminate()

except Exception as ex:
    print(f"❌ Error aagaya: {ex}")

finally:
    page.quit()
    print("👋 Browser closed successfully.")
