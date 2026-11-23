import requests
import json
import re
from concurrent.futures import ThreadPoolExecutor, as_completed

MY_NAME = "Ahmed Store"

# ==============================================================================
# ১. কাস্টম প্লেলিস্টের URL গুলো এখানে বসান (খালি স্লট অটোমেটিক স্কিপ করবে)
#    ১ নম্বর থেকে শুরু করে সব প্লেলিস্ট থেকেই চ্যানেল কালেক্ট করে কম্বাইন করা হবে
# ==============================================================================
CUSTOM_PLAYLISTS = [
    "https://raw.githubusercontent.com/time2shine/Rokon-IPTV/3463896769491e8492dc7953e7b5315431fed440/playlist.m3u",  # প্লেলিস্ট ১
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

# ==============================================================================
# ২. যে শব্দগুলো চ্যানেলের নাম বা গ্রুপে থাকলে চ্যানেলটি বাদ যাবে (চাইলে পরিবর্তন করতে পারেন)
# ==============================================================================
EXCLUDED_WORDS = [
    'telugu', 'tamil', 'kannada', 'malayalam', 'marathi', 'gujarati', 'punjabi', 'oriya', 'odia',
    'gemini', 'vijay', 'sun tv', 'kalignar', 'etv', 'sakshi', 'test', 'dummy', 'promo', 'sample',
    'shopping', 'teleshopping', 'home shop', 'local', 'cable', 'radio', 'fm',
    'latin', 'latam', 'brazil', 'mexico', 'spanish', 'portuguese', 'pluto'
]

# ==============================================================================
# ৩. ক্যাটাগরি ও কিওয়ার্ড লিস্ট (ভবিষ্যতে এখান থেকেই কিওয়ার্ড বাড়াতে/কমাতে/বদলাতে পারবেন)
#    সতর্কতা: কিওয়ার্ড বড়/ছোট হাতের অক্ষর যেভাবেই লেখেন সমস্যা নেই, তবে বাইরের কোনো চ্যানেল ঢুকবে না।
# ==============================================================================
KEYWORD_CATEGORIES = [
    {
        "priority": 1,
        "group": "Bangladeshi TV",
        "keywords": [
            'somoy', 'jamuna', 'ekattor', 'independent', 'channel 24', 'channel24',
            'dbc news', 'news 24', 'news24', 'ekushey', 'ntv', 'rtv', 'atn bangla',
            'atn news', 'banglavision', 'boishakhi', 'desh tv', 'maasranga', 'channel i',
            'deepto', 'btv', 'bangladesh television', 'nagorik', 'mohona', 'asian tv',
            'sa tv', 'satv', 'bijoy tv', 'ananda tv', 'nexus tv', 'duronto', 'mytv',
            'gaan bangla', 'global tv', 'ekhon', 'green tv', 'channel s', 'channel 9',
            'bangla tv', 'sangbad'
        ],
        "exclude": []
    },
    {
        "priority": 2,
        "group": "Sports Channels",
        "keywords": [
            't sports', 'tsports', 'gazi tv', 'gtv', 'star sports', 'sony sports',
            'sony ten', 'sony teen', 'ten sports', 'sports18', 'sports 18', 'willow',
            'ptv sports', 'dd sports', 'astrosports', 'bein sports', 'supersport',
            'sky sports', 'eurosport'
        ],
        "exclude": ['golf', 'racing', 'poker', 'outdoor', 'hunt', 'fight', 'ufc', 'billiards', 'darts']
    },
    {
        "priority": 3,
        "group": "Islamic TV",
        "keywords": [
            'islam', 'quran', 'madani', 'peace tv', 'makkah', 'madinah', 'sunnah', 'alhuda', 'iqra'
        ],
        "exclude": []
    },
    {
        "priority": 4,
        "group": "Indian Movie Channels",
        "keywords": [
            'star gold', 'sony max', 'zee cinema', 'and pictures', '&pictures',
            'goldmines', 'b4u movies', 'colors cineplex', 'zee classic', 'zee action',
            'rishtey cineplex'
        ],
        "exclude": []
    },
    {
        "priority": 5,
        "group": "English Movie Channels",
        "keywords": [
            'hbo', 'star movies', 'sony pix', 'movies now', '&flix', 'andflix',
            'mnx', 'wb', 'paramount', 'cinemax', 'sky cinema', 'film4', 'amc'
        ],
        "exclude": []
    },
    {
        "priority": 6,
        "group": "Kolkata Bangla",
        "keywords": [
            'star jalsha', 'star jalsha movies', 'zee bangla', 'zee bangla cinema', 'colors bangla',
            'abp ananda', 'sony aath', 'sangeet bangla', 'zee 24 ghanta', 'enterr10 bangla',
            'news18 bangla', 'tv9 bangla', 'aakash aath'
        ],
        "exclude": []
    },
    {
        "priority": 7,
        "group": "Kids Channels",
        "keywords": [
            'hungama', 'super hungama', 'pogo', 'cartoon network', 'cartoonnetwork',
            'sonic', 'nickelodeon', 'nick', 'disney'
        ],
        "exclude": []
    },
    {
        "priority": 8,
        "group": "Documentary & Info",
        "keywords": [
            'discovery', 'national geographic', 'nat geo', 'natgeo',
            'animal planet', 'history tv', 'history channel', 'planet earth'
        ],
        "exclude": []
    },
    {
        "priority": 9,
        "group": "Music Channels",
        "keywords": [
            'mnet', 'mtv', '9xm', 'zoom', 'b4u music', 'sangeet bangla'
        ],
        "exclude": []
    },
    {
        "priority": 10,
        "group": "International News",
        "keywords": [
            'bbc news', 'bbc world news', 'cnn', 'cnn international', 'al jazeera',
            'al jazeera english', 'aaj tak', 'ndtv india', 'ndtv 24x7', 'india today',
            'dw news', 'france 24'
        ],
        "exclude": []
    }
]


def clean_channel_name(name):
    cleaned = re.sub(r'[\(\[\{].*?[\)\]\}]', '', name)
    return cleaned.strip()

def normalize_text(text):
    return re.sub(r'[^a-zA-Z0-9]', '', text).lower()

def match_keyword(raw_lower_name, clean_space_name, norm_name, keyword):
    # '&pictures' বা '&flix' এর মতো '&' যুক্ত কিওয়ার্ড নিখুঁতভাবে ম্যাচ করার জন্য
    if '&' in keyword:
        kw_compact = re.sub(r'\s+', '', keyword.lower())
        name_compact = re.sub(r'\s+', '', raw_lower_name)
        return kw_compact in name_compact

    kw_tokens = re.findall(r'[a-z0-9]+', keyword.lower())
    if not kw_tokens:
        return False

    # এক শব্দের কিওয়ার্ড হলে
    if len(kw_tokens) == 1:
        tok = kw_tokens[0]
        if len(tok) <= 4:
            # ছোট শব্দ (যেমন: ntv, rtv, gtv, wb, hbo) পূর্ণ শব্দ হিসেবে ম্যাচ করবে
            pattern = rf'\b{re.escape(tok)}(?:hd|sd|fhd|uhd)?\b'
            return re.search(pattern, clean_space_name) is not None
        return tok in norm_name

    # একাধিক শব্দের কিওয়ার্ড হলে (যেমন: "sony sports", "sony teen", "star sports"):
    # ১) স্পেস ছাড়া একসাথে ম্যাচ (যেমন: "SonySportsHD", "TSports")
    kw_joined = ''.join(kw_tokens)
    if len(kw_joined) >= 5 and kw_joined in norm_name:
        return True

    # ২) কিওয়ার্ডের প্রতিটি শব্দ চ্যানেলের নামের যেকোনো জায়গায় থাকলে ম্যাচ করবে
    # (যেমন: "sony sports" ম্যাচ করবে "Sony sports", "Sony Teen Sports", "SONY SPORTS TEEN" সবগুলোতে)
    for tok in kw_tokens:
        pattern = rf'\b{re.escape(tok)}(?:hd|sd|fhd|uhd)?\b'
        if not re.search(pattern, clean_space_name):
            return False
    return True

def is_excluded_channel(channel):
    name_space = re.sub(r'[^a-zA-Z0-9]+', ' ', channel['name']).strip().lower()
    group_space = re.sub(r'[^a-zA-Z0-9]+', ' ', channel['group']).strip().lower()

    for word in EXCLUDED_WORDS:
        w_space = re.sub(r'[^a-zA-Z0-9]+', ' ', word).strip().lower()
        if not w_space:
            continue
        pattern = rf'\b{re.escape(w_space)}\b'
        if re.search(pattern, name_space) or re.search(pattern, group_space):
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
    raw_lower_name = channel['name'].lower()
    clean_space_name = re.sub(r'[^a-z0-9]+', ' ', raw_lower_name).strip()
    norm_name = normalize_text(raw_lower_name)

    for cat in KEYWORD_CATEGORIES:
        if any(match_keyword(raw_lower_name, clean_space_name, norm_name, ex) for ex in cat.get("exclude", [])):
            continue

        if any(match_keyword(raw_lower_name, clean_space_name, norm_name, kw) for kw in cat["keywords"]):
            return (cat["priority"], 0, cat["group"])

    return None

def fetch_channels_by_group():
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

    print(f"🔄 মোট {len(sources)} টি কাস্টম প্লেলিস্ট থেকে কিওয়ার্ড অনুযায়ী চ্যানেল কালেক্ট করা হচ্ছে...")

    candidate_channels = []
    seen_urls = set()  # শুধুমাত্র ডুপ্লিকেট stream_url বাদ দেবে, একই নামের ভিন্ন URL সবগুলো নেবে

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
        matched_in_this_playlist = 0

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
                            matched_in_this_playlist += 1
                            candidate_channels.append((ch_obj, res, playlist_idx, channel_order))
                            seen_urls.add(stream_url)
            i += 1

        print(f"📥 প্লেলিস্ট #{playlist_idx} থেকে {matched_in_this_playlist} টি নতুন কিওয়ার্ড-ম্যাচড চ্যানেল পাওয়া গেছে।")

    print(f"\n⚡ সর্বমোট {len(candidate_channels)} টি ইউনিক স্ট্রিম চেক করা হচ্ছে...")

    working_channels = []
    
    with ThreadPoolExecutor(max_workers=80) as executor:
        futures = [executor.submit(check_single_stream, item) for item in candidate_channels]
        for future in as_completed(futures):
            result = future.result()
            if result:
                working_channels.append(result)

    working_channels.sort(key=lambda x: (x[1][0], x[0]['name'].lower(), x[2], x[3]))

    total_count = len(working_channels)

    m3u_header = f'#EXTM3U name="{MY_NAME} IPTV | Total Channels: {total_count}"\n\n'
    m3u_lines = [m3u_header]
    json_channels = []

    for ch, res, _, _ in working_channels:
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
