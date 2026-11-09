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

# DrissionPage Options (JS runtime error fix ke sath)
co = ChromiumOptions()
co.set_argument('--no-sandbox')
co.set_argument('--disable-dev-shm-usage')
co.set_argument('--disable-gpu')
co.set_argument('--remote-debugging-port=9222')
co.set_argument('--disable-software-rasterizer')
co.set_argument('--disable-blink-features=AutomationControlled')
co.auto_port()

# Browser start karein
page = ChromiumPage(addr_or_opts=co)

try:
    print("🌐 Website load ho rahi hai (bypassing Cloudflare)...")
    page.get(url)

    # Page load hone ke liye 5 seconds ka wait
    time.sleep(5)

    # 🛡️ SMART CLOUDFLARE TURNSTILE CLICKING LOGIC
    print("🛡️ Cloudflare verification check ki ja rahi hai...")
    clicked = False
    
    for attempt in range(3):
        try:
            # 1. Main page par checkbox ya text dhoondein
            cb = page.ele('text:Verify you are human', timeout=2) or page.ele('.cf-turnstile', timeout=2)
            if cb:
                print("⚡ Main page par Cloudflare checkbox mila, click kar rahe hain...")
                cb.click()
                clicked = True
                break
            
            # 2. Agar main page par na ho, toh sabhi iframes ke andar dhoondein
            frames = page.get_frames()
            for f in frames:
                try:
                    inner_cb = f.ele('text:Verify you are human', timeout=1) or f.ele('input[type="checkbox"]', timeout=1) or f.ele('.cf-turnstile-wrapper', timeout=1)
                    if inner_cb:
                        print("⚡ Iframe ke andar Cloudflare checkbox mila, click kar rahe hain...")
                        inner_cb.click()
                        clicked = True
                        break
                except:
                    pass
            
            if clicked:
                break
                
            print(f"⏳ Attempt {attempt+1}: Checkbox abhi load nahi hua, 3 seconds mazeed wait kar rahe hain...")
            time.sleep(3)
        except Exception as e:
            print(f"⚠️ Attempt error: {e}")
            time.sleep(2)

    if clicked:
        print("✅ Cloudflare checkbox par click ho gaya! Verify hone ka wait kar rahe hain...")
        time.sleep(6) # Verify hone ke liye waqfa
    else:
        print("ℹ️ Cloudflare checkbox nahi mila ya khud-ba-khud bypass ho gaya hai.")

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
