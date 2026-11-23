import requests
import json
import re
from concurrent.futures import ThreadPoolExecutor, as_completed

MY_NAME = "Ahmed Store"

# এখানে আপনার কাস্টম প্লেলিস্টের URL গুলো বসান
# প্রথমে ১ নম্বর প্লেলিস্ট ফিল্টার হবে, এরপর বাকি প্লেলিস্টগুলো ফিল্টার হয়ে কম্বাইন হবে (খালি স্লট অটোমেটিক স্কিপ করবে)
CUSTOM_PLAYLISTS = [
    "https://raw.githubusercontent.com/time2shine/Rokon-IPTV/3463896769491e8492dc7953e7b5315431fed440/playlist.m3u",  # প্লেলিস্ট ১ (প্রধান)
    "https://raw.githubusercontent.com/sm-monirulislam/SM-IPTV/refs/heads/main/Combined_Live_TV.m3u",  # কাস্টম প্লেলিস্ট ২ (উদাহরণ: "https://example.com/playlist2.m3u")
    "https://raw.githubusercontent.com/sarsx3/aladin430/refs/heads/main/playlists/eamin-tv.m3u",  # কাস্টম প্লেলিস্ট ৩
    "",  # কাস্টম প্লেলিস্ট ৪
    "",  # কাস্টম প্লেলিস্ট ৫
    "",  # কাস্টম প্লেলিস্ট ৬
    "",  # কাস্টম প্লেলিস্ট ৭
    "",  # কাস্টম প্লেলিস্ট ৮
    "",  # কাস্টম প্লেলিস্ট ৯
    "",  # কাস্টম প্লেলিস্ট ১০
    "",  # কাস্টম প্লেলিস্ট ১১
]

def clean_channel_name(name):
    cleaned = re.sub(r'[\(\[\{].*?[\)\]\}]', '', name)
    return cleaned.strip()

def normalize_text(text):
    return re.sub(r'[^a-zA-Z0-9]', '', text).lower()

def is_excluded_channel(channel):
    name = channel['name'].lower()
    group = channel['group'].lower()
    
    excluded = [
        'telugu', 'tamil', 'kannada', 'malayalam', 'marathi', 'gujarati', 'punjabi', 'oriya', 'odia',
        'gemini', 'vijay', 'sun tv', 'kalignar', 'etv', 'sakshi', 'test', 'dummy', 'promo', 'sample', 
        'shopping', 'teleshopping', 'home shop', 'local', 'cable', 'radio', 'fm',
        'latin', 'latam', 'brazil', 'mexico', 'spanish', 'portuguese', 'pluto'
    ]
    if any(k in group for k in excluded) or any(k in name for k in excluded):
        return True
    return False

def check_single_stream(item):
    ch_obj, res, p_idx, c_idx = item
    url = ch_obj['stream_url']
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    
    try:
        response = requests.head(url, headers=headers, timeout=8, allow_redirects=True)
        if response.status_code == 200:
            return item
        
        with requests.get(url, headers=headers, timeout=8, stream=True, allow_redirects=True) as get_resp:
            if get_resp.status_code == 200:
                return item
    except Exception:
        pass
    
    return None

def categorize_and_prioritize(channel):
    name = channel['name'].lower()
    norm_name = normalize_text(name)

    # শুধুমাত্র নিচের কিওয়ার্ডগুলো ম্যাচ করলে ফিল্টার হবে, বাকি সব বাদ পড়বে

    # ১. Bangladeshi TV
    bd_keywords = [
        'somoy', 'jamuna', 'ekattor', 'independent', 'channel 24', 'channel24',
        'dbc news', 'news 24', 'news24', 'ekushey', 'ntv', 'rtv', 'atn bangla',
        'atn news', 'banglavision', 'boishakhi', 'desh tv', 'maasranga', 'channel i',
        'deepto', 'btv', 'bangladesh television', 'nagorik', 'mohona', 'asian tv',
        'sa tv', 'satv', 'bijoy tv', 'ananda tv', 'nexus tv', 'duronto', 'mytv',
        'gaan bangla', 'global tv', 'ekhon', 'green tv', 'channel s', 'channel 9',
        'bangla tv', 'sangbad'
    ]
    if any(normalize_text(bd) in norm_name for bd in bd_keywords):
        return (1, 0, "Bangladeshi TV")

    # ২. Sports Channels
    sports_keywords = [
        't sports', 'tsports', 'gazi tv', 'gtv', 'star sports', 'sony sports', 
        'sony ten', 'ten sports', 'sports18', 'sports 18', 'willow', 'ptv sports', 
        'dd sports', 'astrosports', 'bein sports', 'supersport', 'sky sports', 'eurosport'
    ]
    unwanted_sports = ['golf', 'racing', 'poker', 'outdoor', 'hunt', 'fight', 'ufc', 'billiards', 'darts']
    
    if not any(un_sp in norm_name for un_sp in unwanted_sports):
        if any(normalize_text(sp) in norm_name for sp in sports_keywords):
            return (2, 0, "Sports Channels")

    # ৩. Islamic TV
    islamic_keywords = ['islam', 'quran', 'madani', 'peace tv', 'makkah', 'madinah', 'sunnah', 'alhuda', 'iqra']
    if any(normalize_text(k) in norm_name for k in islamic_keywords):
        return (3, 0, "Islamic TV")

    # ৪. Indian Movie Channels
    indian_movies = [
        'star gold', 'sony max', 'zee cinema', 'and pictures', '&pictures',
        'goldmines', 'b4u movies', 'colors cineplex', 'zee classic', 'zee action',
        'rishtey cineplex'
    ]
    if any(normalize_text(m) in norm_name for m in indian_movies):
        return (4, 0, "Indian Movie Channels")

    # ৫. English Movie Channels
    english_movies = [
        'hbo', 'star movies', 'sony pix', 'movies now', '&flix', 'andflix',
        'mnx', 'wb', 'paramount', 'cinemax', 'sky cinema', 'film4', 'amc'
    ]
    if any(normalize_text(em) in norm_name for em in english_movies):
        return (5, 0, "English Movie Channels")

    # ৬. Kolkata Bangla
    kolkata_popular = [
        'star jalsha', 'star jalsha movies', 'zee bangla', 'zee bangla cinema', 'colors bangla', 
        'abp ananda', 'sony aath', 'sangeet bangla', 'zee 24 ghanta', 'enterr10 bangla', 
        'news18 bangla', 'tv9 bangla', 'aakash aath'
    ]
    if any(normalize_text(k) in norm_name for k in kolkata_popular):
        return (6, 0, "Kolkata Bangla")

    # ৭. Kids Channels
    kids_keywords = ['hungama', 'super hungama', 'pogo', 'cartoon network', 'cartoonnetwork', 'sonic', 'nickelodeon', 'nick', 'disney']
    if any(normalize_text(k) in norm_name for k in kids_keywords):
        return (7, 0, "Kids Channels")

    # ৮. Documentary & Info
    doc_popular_keywords = [
        'discovery', 'national geographic', 'nat geo', 'natgeo', 
        'animal planet', 'history tv', 'history channel', 'planet earth'
    ]
    if any(normalize_text(k) in norm_name for k in doc_popular_keywords):
        return (8, 0, "Documentary & Info")

    # ৯. Music Channels
    music_keywords = ['mnet', 'mtv', '9xm', 'zoom', 'b4u music', 'sangeet bangla']
    if any(normalize_text(k) in norm_name for k in music_keywords):
        return (9, 0, "Music Channels")

    # ১০. International News
    global_news = [
        'bbc news', 'bbc world news', 'cnn', 'cnn international', 'al jazeera', 
        'al jazeera english', 'aaj tak', 'ndtv india', 'ndtv 24x7', 'india today', 'dw news', 'france 24'
    ]
    if any(normalize_text(news) in norm_name for news in global_news):
        return (10, 0, "International News")

    return None

def fetch_channels_by_group():
    # শুধুমাত্র CUSTOM_PLAYLISTS থেকেই সোর্স নেওয়া হবে (ক্রমানুসারে ১ নম্বর থেকে শুরু করে বাকিগুলো)
    sources = []
    for idx, custom_url in enumerate(CUSTOM_PLAYLISTS, start=1):
        clean_url = custom_url.strip()
        if clean_url and clean_url.startswith(("http://", "https://")):
            sources.append((clean_url, idx))

    if not sources:
        print("⚠️ কোনো বৈধ কাস্টম প্লেলিস্ট URL পাওয়া যায়নি!")
        return

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }

    print(f"🔄 মোট {len(sources)} টি কাস্টম প্লেলিস্ট থেকে কিওয়ার্ড অনুযায়ী চ্যানেল ফিল্টার করা হচ্ছে...")

    candidate_channels = []
    seen_urls = set()  # শুধুমাত্র ডুপ্লিকেট stream_url আটকাবে, একই নামের ভিন্ন URL রাখবে

    for url, playlist_idx in sources:
        try:
            response = requests.get(url, headers=headers, timeout=15)
            if response.status_code != 200:
                print(f"⚠️ প্লেলিস্ট #{playlist_idx} লোড হয়নি (Status: {response.status_code})")
                continue
            raw_data = response.text
        except Exception as e:
            print(f"⚠️ প্লেলিস্ট #{playlist_idx} এরর: {e}")
            continue

        lines = raw_data.splitlines()
        i = 0
        channel_order = 0
        while i < len(lines):
            line = lines[i].strip()
            if line.startswith("#EXTINF:"):
                info_line = line
                stream_url = ""

                j = i + 1
                while j < len(lines):
                    next_line = lines[j].strip()
                    if not next_line:
                        j += 1
                        continue
                    if next_line.startswith("#EXTINF:"):
                        break
                    if not next_line.startswith("#"):
                        stream_url = next_line
                        i = j
                        break
                    j += 1

                # একই stream_url দুইবার না আসার জন্য seen_urls চেক (নাম এক হলেও URL ভিন্ন হলে নেবে)
                if stream_url and stream_url not in seen_urls:
                    raw_name = info_line.split(",")[-1].strip() if "," in info_line else "Unknown Channel"
                    clean_name = clean_channel_name(raw_name)

                    logo_match = re.search(r'tvg-logo="([^"]*)"', info_line)
                    logo = logo_match.group(1) if logo_match else ""

                    group_match = re.search(r'group-title="([^"]*)"', info_line)
                    group = group_match.group(1) if group_match else "General"

                    ch_obj = {
                        "name": clean_name if clean_name else raw_name,
                        "logo": logo,
                        "group": group,
                        "stream_url": stream_url
                    }

                    if not is_excluded_channel(ch_obj):
                        res = categorize_and_prioritize(ch_obj)
                        if res is not None:
                            channel_order += 1
                            candidate_channels.append((ch_obj, res, playlist_idx, channel_order))
                            seen_urls.add(stream_url)
            i += 1

    print(f"⚡ {len(candidate_channels)} টি কিওয়ার্ড-ম্যাচড চ্যানেল পাওয়া গেছে। স্ট্রিম টেস্ট চলছে...")

    working_channels = []
    
    with ThreadPoolExecutor(max_workers=80) as executor:
        futures = [executor.submit(check_single_stream, item) for item in candidate_channels]
        for future in as_completed(futures):
            result = future.result()
            if result:
                working_channels.append(result)

    # ক্যাটাগরি ও নাম অনুযায়ী সাজানো (একই নামের চ্যানেলের ক্ষেত্রে ১ নম্বর প্লেলিস্টের লিংক আগে থাকবে)
    working_channels.sort(key=lambda x: (x[1][0], x[0]['name'].lower(), x[2], x[3]))

    # কোনো MAX লিমিট নেই — সবগুলো কার্যকর চ্যানেলই রাখা হবে
    final_selected_channels = working_channels
    total_count = len(final_selected_channels)

    m3u_header = f'#EXTM3U name="{MY_NAME} IPTV | Total Channels: {total_count}"\n\n'
    m3u_lines = [m3u_header]
    json_channels = []

    for ch, res, _, _ in final_selected_channels:
        p, sub_p, display_group = res

        m3u_lines.append(f'#EXTINF:-1 tvg-logo="{ch["logo"]}" group-title="{display_group}",{ch["name"]}\n{ch["stream_url"]}\n')
        
        json_channels.append({
            "name": ch["name"],
            "logo": ch["logo"],
            "group": display_group,
            "stream_url": ch["stream_url"]
        })

    json_data = {
        "playlist_name": MY_NAME,
        "total_channels": total_count,
        "status": "success",
        "channels": json_channels
    }

    with open("playlist.json", "w", encoding="utf-8") as jf:
        json.dump(json_data, jf, indent=4, ensure_ascii=False)

    with open("playlist.m3u", "w", encoding="utf-8") as mf:
        mf.writelines(m3u_lines)

    print(f"\n✅ প্লেলিস্ট ফিল্টারিং ও ফাইল জেনারেট সম্পন্ন!")
    print(f"📌 মোট কার্যকর চ্যানেল: {total_count} টি")

if __name__ == "__main__":
    fetch_channels_by_group()
