import requests
import json
import re
import time
import subprocess
from concurrent.futures import ThreadPoolExecutor, as_completed

MY_NAME = "Ahmed Store"

COLLECTED_M3U_FILE = "collected_playlist.m3u"
FINAL_M3U_FILE = "playlist.m3u"
FINAL_JSON_FILE = "playlist.json"

CHECK_STREAM_ALIVE = True
SKIP_CHECK_FOR_BDIX = True

# ==============================================================================
# ১. কাস্টম প্লেলিস্টের URL গুলো এখানে বসান (খালি স্লট অটোমেটিক স্কিপ করবে)
# ==============================================================================
CUSTOM_PLAYLISTS = [
    "https://raw.githubusercontent.com/time2shine/Rokon-IPTV/3463896769491e8492dc7953e7b5315431fed440/playlist.m3u",  # প্লেলিস্ট ১
    "https://raw.githubusercontent.com/sarsx3/aladin430/refs/heads/main/playlists/eamin-tv.m3u",  # কাস্টম প্লেলিস্ট ২
    "https://raw.githubusercontent.com/sm-monirulislam/SM-IPTV/refs/heads/main/new_isp.m3u",  # কাস্টম প্লেলিস্ট ৩
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
# ২. যে শব্দগুলো চ্যানেলের নাম বা গ্রুপে থাকলে চ্যানেলটি বাদ যাবে
# ==============================================================================
EXCLUDED_WORDS = [
    'telugu', 'tamil', 'kannada', 'malayalam', 'marathi', 'gujarati', 'punjabi', 'oriya', 'odia',
    'gemini', 'vijay', 'sun tv', 'kalignar', 'etv', 'sakshi', 'test', 'dummy', 'promo', 'sample',
    'shopping', 'teleshopping', 'home shop', 'radio', 'fm',
    'latin', 'latam', 'brazil', 'mexico', 'spanish', 'portuguese', 'pluto'
]

# ==============================================================================
# ৩. ক্যাটাগরি ও কিওয়ার্ড লিস্ট
# ==============================================================================
KEYWORD_CATEGORIES = [
    {
        "priority": 1,
        "group": "Bangla",
        "keywords": [
            # বাংলাদেশের জাতীয়, নিউজ, বিনোদন ও সব চ্যানেল
            'btv', 'bangladesh television', 'btv world', 'btv chattogram', 'btv news',
            'sangsad', 'somoy', 'jamuna', 'ekattor', 'independent', 'channel 24', 'channel24',
            'dbc news', 'news 24', 'news24', 'atn news', 'ekhon', 'desh tv', 'star news bd',
            'atn bangla', 'channel i', 'ntv', 'rtv', 'ekushey', 'etv bangla', 'banglavision',
            'bangla vision', 'boishakhi', 'maasranga', 'deepto', 'sa tv', 'satv', 'asian tv',
            'mohona', 'bijoy tv', 'mytv', 'channel 9', 'nagorik', 'ananda tv', 'nexus tv',
            'global tv', 'green tv', 'channel s', 'bangla tv', 'sangbad', 'duronto',
            'gaan bangla', 'gaanbangla', 'movie bangla', 'channel 16', 'channel sixteen',
            'titas tv', 'diganta', 'islamic tv', 'peace tv bangla', 'iqra bangla',
            'madani bangla', 'atn music', 'bangla 21', 'falguni',
            # কলকাতা বাংলার সব জনপ্রিয় চ্যানেল
            'star jalsha', 'star jalsha movies', 'jalsha movies', 'zee bangla',
            'zee bangla cinema', 'colors bangla', 'abp ananda', 'sony aath',
            'sangeet bangla', 'zee 24 ghanta', '24 ghanta', 'enterr10 bangla',
            'news18 bangla', 'tv9 bangla', 'aakash aath', 'sun bangla', 'rupashi bangla',
            'dhoom music', 'kolkata tv', 'republic bangla', 'calcutta news', 'r plus'
        ],
        "exclude": []
    },
    {
        "priority": 2,
        "group": "Sports Channels",
        "keywords": [
            # বাংলাদেশ, ইন্ডিয়া ও সাবকন্টিনেন্টের সব জনপ্রিয় স্পোর্টস চ্যানেল
            't sports', 'tsports', 'gazi tv', 'gtv',
            'star sports', 'star cricket', 'sony sports', 'sony ten', 'sony teen',
            'sony six', 'sony espn', 'ten sports', 'ten cricket', 'sports18', 'sports 18',
            'dd sports', 'fancode', 'willow', 'criclife', 'cricbuzz',
            'ptv sports', 'geo super', 'a sports hd', 'asports',
            # মধ্যপ্রাচ্য ও এশিয়ার জনপ্রিয় স্পোর্টস চ্যানেল
            'bein sports', 'bein sport', 'astrosports', 'astro cricket', 'astro supersport',
            'astro arena', 'ssc sports', 'ssc 1', 'ssc 2', 'ssc 3', 'ssc 4', 'ssc 5',
            'ssc extra', 'abu dhabi sports', 'ad sports', 'dubai sports', 'alkass', 'sharjah sports',
            # ইউরোপ, ইউকে, আমেরিকা ও গ্লোবাল ইন্টারন্যাশনাল স্পোর্টস চ্যানেল
            'sky sports', 'sky sport', 'tnt sports', 'tnt sport', 'bt sports', 'bt sport',
            'eurosport', 'premier sports', 'viaplay sports', 'setanta sports',
            'supersport', 'super sport', 'espn', 'fox sports', 'fox sport', 'fox cricket',
            'cbs sports', 'nbc sports', 'tsn', 'sportsnet', 'dazn',
            'arena sport', 'arena sports', 'eleven sports', 'nova sports', 'sportklub',
            'nba tv', 'nfl network', 'mlb network', 'nhl network', 'mutv', 'lfctv',
            'real madrid tv', 'barca tv', 'formula 1', 'motogp', 'olympic channel'
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
        "group": "Hindi Movie",
        "keywords": [
            'star gold', 'sony max', 'sony wah', 'zee cinema', 'zee classic',
            'zee action', 'zee bollywood', 'zee anmol cinema', 'and pictures', '&pictures',
            '&xplor', 'andxplor', 'colors cineplex', 'rishtey cineplex', 'b4u movies',
            'b4u kadak', 'goldmines', 'utv movies', 'utv action', 'movies ok',
            'shemaroo bollywood', 'maha movie', 'cinema tv', 'manoranjan tv',
            'manoranjan movies', 'wow cinema', 'enterr10 movies', 'star utsav movies',
            'housefull movies', 'housefull action', 'box cinema', 'abzy movies',
            'abzy cool', 'movie house'
        ],
        "exclude": []
    },
    {
        "priority": 5,
        "group": "Movie",
        "keywords": [
            'hbo', 'star movies', 'sony pix', 'movies now', '&flix', 'andflix',
            'mnx', 'wb', 'paramount', 'cinemax', 'sky cinema', 'film4', 'amc'
        ],
        "exclude": []
    },
    {
        "priority": 6,
        "group": "Hindi",
        "keywords": [
            'star plus', 'star bharat', 'star utsav', 'life ok',
            'sony tv', 'sony entertainment', 'sony set', 'set india', 'set hd', 'set asia',
            'sony sab', 'sab tv', 'sony pal',
            'zee tv', 'zee anmol', 'zindagi',
            'colors', 'colors rishtey', 'rishtey', '&tv', 'andtv',
            'dangal', 'dangal 2', 'big magic', 'shemaroo tv', 'shemaroo umang',
            'ishara', 'ishara tv', 'nazara', 'azaad', 'sahara one',
            'dd national', 'dd bharati', 'dd retro', 'enterr10', 'manoranjan grand'
        ],
        "exclude": []
    },
    {
        "priority": 7,
        "group": "Kids",
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
        "group": "Music",
        "keywords": [
            '9xm', '9x jalwa', '9x tashan', '9x jhakaas', 'mastiii', 'masti tv',
            'zing', 'zoom', 'b4u music', 'mtv', 'mtv beats', 'mtv hits', 'mtv live',
            'mtv music', 'mtv 90s', 'mtv 00s', 'club mtv', 'vh1', 'bindass',
            'sony mix', 'music india', 'showbox', 'e24', 'mnet', '8xm', 'ary musik',
            'trace urban', 'trace hits', 'now 70s', 'now 80s', 'now 90s', 'now rock',
            'deluxe music', 'clubbing tv', 'kiss tv', 'magic tv', 'heart tv',
            'sangeet bangla', 'gaan bangla', 'dhoom music'
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
    if '&' in keyword:
        kw_compact = re.sub(r'\s+', '', keyword.lower())
        name_compact = re.sub(r'\s+', '', raw_lower_name)
        return kw_compact in name_compact

    kw_tokens = re.findall(r'[a-z0-9]+', keyword.lower())
    if not kw_tokens:
        return False

    if len(kw_tokens) == 1:
        tok = kw_tokens[0]
        if len(tok) <= 4:
            pattern = rf'\b{re.escape(tok)}(?:hd|sd|fhd|uhd|tv)*\b'
            return re.search(pattern, clean_space_name) is not None
        return tok in norm_name

    kw_joined = ''.join(kw_tokens)
    if len(kw_joined) >= 5 and kw_joined in norm_name:
        return True

    for tok in kw_tokens:
        pattern = rf'\b{re.escape(tok)}(?:hd|sd|fhd|uhd|tv)*\b'
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

def is_bdix_or_local_url(url):
    lower_url = url.lower()
    if re.match(r'^https?://(10\.|192\.168\.|172\.(1[6-9]|2[0-9]|3[0-1])\.|103\.)', lower_url):
        return True
    bdix_markers = ['bdix', 'ftpbd', 'aynaott', 'jagobd', 'bdiptv', '.com.bd', '.net.bd', '.org.bd']
    return any(marker in lower_url for marker in bdix_markers)

def fetch_playlist_content(url, playlist_idx):
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
        "Cache-Control": "no-cache"
    }

    last_status = None

    for attempt in range(1, 4):
        try:
            response = requests.get(url, headers=headers, timeout=20, allow_redirects=True)
            last_status = response.status_code
            if response.status_code == 200 and "#EXTINF" in response.text:
                return response.text
            if response.status_code in (429, 500, 502, 503, 504):
                print(f"⏳ প্লেলিস্ট #{playlist_idx} Status {response.status_code} দিয়েছে, আবার চেষ্টা করা হচ্ছে ({attempt}/3)...")
                time.sleep(attempt * 2)
                continue
            break
        except Exception as e:
            if attempt == 3:
                print(f"⚠️ প্লেলিস্ট #{playlist_idx} requests এরর: {e}")
            time.sleep(attempt * 2)

    try:
        result = subprocess.run(
            ["curl", "-sSL", "--retry", "2", "--max-time", "20", "-A", headers["User-Agent"], url],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="ignore"
        )
        if result.returncode == 0 and "#EXTINF" in result.stdout:
            print(f"✅ প্লেলিস্ট #{playlist_idx} curl ব্যাকআপ দিয়ে সফলভাবে লোড হয়েছে!")
            return result.stdout
    except Exception:
        pass

    print(f"⚠️ প্লেলিস্ট #{playlist_idx} লোড হয়নি (Status: {last_status})")
    return None

def parse_m3u_text(raw_data):
    channels = []
    lines = raw_data.splitlines()
    i = 0

    while i < len(lines):
        line = lines[i].strip()
        if line.startswith("#EXTINF:"):
            info_line = line
            stream_url = ""
            extvlcopt_lines = []
            referer = ""
            user_agent = ""

            j = i + 1
            while j < len(lines):
                next_line = lines[j].strip()
                if not next_line:
                    j += 1
                    continue
                if next_line.startswith("#EXTINF:"):
                    break
                if next_line.startswith("#EXTVLCOPT:"):
                    extvlcopt_lines.append(next_line)
                    lower_opt = next_line.lower()
                    if lower_opt.startswith("#extvlcopt:http-referrer="):
                        referer = next_line.split("=", 1)[1].strip()
                    elif lower_opt.startswith("#extvlcopt:http-user-agent="):
                        user_agent = next_line.split("=", 1)[1].strip()
                    j += 1
                    continue
                if not next_line.startswith("#"):
                    stream_url = next_line
                    i = j
                    break
                j += 1

            if stream_url:
                raw_name = info_line.split(",")[-1].strip() if "," in info_line else ""
                if not raw_name:
                    tvg_name_match = re.search(r'tvg-name="([^"]*)"', info_line)
                    raw_name = tvg_name_match.group(1).strip() if tvg_name_match else "Unknown Channel"

                clean_name = clean_channel_name(raw_name)

                logo_match = re.search(r'tvg-logo="([^"]*)"', info_line)
                logo = logo_match.group(1) if logo_match else ""

                group_match = re.search(r'group-title="([^"]*)"', info_line)
                group = group_match.group(1) if group_match else "General"

                channels.append({
                    "name": clean_name if clean_name else raw_name,
                    "logo": logo,
                    "group": group,
                    "stream_url": stream_url,
                    "extvlcopt": extvlcopt_lines,
                    "referer": referer,
                    "user_agent": user_agent
                })
        i += 1

    return channels

def check_single_stream(item):
    ch_obj, priority, order_idx = item
    url = ch_obj['stream_url']

    if SKIP_CHECK_FOR_BDIX and is_bdix_or_local_url(url):
        return item

    headers = {
        "User-Agent": ch_obj.get("user_agent") or "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    }
    if ch_obj.get("referer"):
        headers["Referer"] = ch_obj["referer"]
        headers["Origin"] = ch_obj["referer"].rstrip("/")

    try:
        with requests.get(url, headers=headers, timeout=10, stream=True, allow_redirects=True) as get_resp:
            if get_resp.status_code in (200, 206):
                content_type = get_resp.headers.get("Content-Type", "").lower()
                if "text/html" in content_type:
                    return None
                return item
    except Exception:
        pass

    return None

def step1_collect_all_keyword_channels():
    sources = []
    for idx, custom_url in enumerate(CUSTOM_PLAYLISTS, start=1):
        clean_url = custom_url.strip()
        if clean_url and clean_url.startswith(("http://", "https://")):
            sources.append((clean_url, idx))

    if not sources:
        print("⚠️ কোনো বৈধ কাস্টম প্লেলিস্ট URL পাওয়া যায়নি!")
        return 0

    print(f"🔄 [ধাপ ১] মোট {len(sources)} টি প্লেলিস্ট থেকে কিওয়ার্ডের সব চ্যানেল (BDIX + International) কালেক্ট করা হচ্ছে...")

    all_collected = []

    for url, playlist_idx in sources:
        raw_data = fetch_playlist_content(url, playlist_idx)
        if not raw_data:
            continue

        parsed_channels = parse_m3u_text(raw_data)
        matched_count = 0

        for ch_obj in parsed_channels:
            if not is_excluded_channel(ch_obj):
                res = categorize_and_prioritize(ch_obj)
                if res is not None:
                    _, _, display_group = res
                    ch_obj["group"] = display_group
                    all_collected.append(ch_obj)
                    matched_count += 1

        print(f"📥 প্লেলিস্ট #{playlist_idx} থেকে {matched_count} টি কিওয়ার্ড-ম্যাচড চ্যানেল কালেক্ট হয়েছে।")

    if not all_collected:
        print("⚠️ কোনো চ্যানেল কালেক্ট হয়নি! আগের ফাইলগুলো অক্ষত রাখা হলো।")
        return 0

    m3u_lines = [f'#EXTM3U name="{MY_NAME} Collected | Total: {len(all_collected)}"\n\n']
    for ch in all_collected:
        m3u_lines.append(f'#EXTINF:-1 tvg-logo="{ch["logo"]}" group-title="{ch["group"]}",{ch["name"]}\n')
        for opt_line in ch.get("extvlcopt", []):
            m3u_lines.append(f'{opt_line}\n')
        m3u_lines.append(f'{ch["stream_url"]}\n')

    with open(COLLECTED_M3U_FILE, "w", encoding="utf-8") as cf:
        cf.writelines(m3u_lines)

    print(f"💾 [ধাপ ১ সম্পন্ন] সর্বমোট {len(all_collected)} টি চ্যানেল '{COLLECTED_M3U_FILE}' ফাইলে সেভ হয়েছে।\n")
    return len(all_collected)

def step2_build_fresh_final_playlist():
    try:
        with open(COLLECTED_M3U_FILE, "r", encoding="utf-8") as cf:
            collected_raw = cf.read()
    except FileNotFoundError:
        print(f"⚠️ '{COLLECTED_M3U_FILE}' ফাইল পাওয়া যায়নি!")
        return

    collected_channels = parse_m3u_text(collected_raw)
    if not collected_channels:
        print("⚠️ কালেক্টেড প্লেলিস্টে কোনো চ্যানেল নেই!")
        return

    group_priority_map = {cat["group"]: cat["priority"] for cat in KEYWORD_CATEGORIES}

    unique_stream_items = []
    seen_urls = set()

    for idx, ch in enumerate(collected_channels):
        stream_url = ch["stream_url"].strip()
        if stream_url and stream_url not in seen_urls:
            seen_urls.add(stream_url)
            priority = group_priority_map.get(ch["group"], 99)
            unique_stream_items.append((ch, priority, idx))

    duplicate_removed = len(collected_channels) - len(unique_stream_items)
    print(f"🧹 [ধাপ ২] '{COLLECTED_M3U_FILE}' থেকে {duplicate_removed} টি ডুপ্লিকেট স্ট্রিম URL বাদ দেওয়া হয়েছে।")

    if CHECK_STREAM_ALIVE:
        print(f"⚡ {len(unique_stream_items)} টি ইউনিক স্ট্রিম প্রসেস করা হচ্ছে (BDIX সংরক্ষিত + International লাইভ চেক)...")
        fresh_channels = []
        with ThreadPoolExecutor(max_workers=80) as executor:
            futures = [executor.submit(check_single_stream, item) for item in unique_stream_items]
            for future in as_completed(futures):
                result = future.result()
                if result:
                    fresh_channels.append(result)
    else:
        print(f"⏭️ স্ট্রিম চেক স্কিপ করে {len(unique_stream_items)} টি ইউনিক স্ট্রিম নেওয়া হচ্ছে...")
        fresh_channels = unique_stream_items

    fresh_channels.sort(key=lambda x: (x[1], x[0]["name"].lower(), x[2]))

    total_count = len(fresh_channels)
    m3u_lines = [f'#EXTM3U name="{MY_NAME} IPTV | Total Channels: {total_count}"\n\n']
    json_channels = []

    for ch, _, _ in fresh_channels:
        m3u_lines.append(f'#EXTINF:-1 tvg-logo="{ch["logo"]}" group-title="{ch["group"]}",{ch["name"]}\n')
        for opt_line in ch.get("extvlcopt", []):
            m3u_lines.append(f'{opt_line}\n')
        m3u_lines.append(f'{ch["stream_url"]}\n')

        json_item = {
            "name": ch["name"],
            "logo": ch["logo"],
            "group": ch["group"],
            "stream_url": ch["stream_url"]
        }
        if ch.get("referer"):
            json_item["referer"] = ch["referer"]
        if ch.get("user_agent"):
            json_item["user_agent"] = ch["user_agent"]
        json_channels.append(json_item)

    json_data = {
        "playlist_name": MY_NAME,
        "total_channels": total_count,
        "status": "success",
        "channels": json_channels
    }

    with open(FINAL_JSON_FILE, "w", encoding="utf-8") as jf:
        json.dump(json_data, jf, indent=4, ensure_ascii=False)

    with open(FINAL_M3U_FILE, "w", encoding="utf-8") as mf:
        mf.writelines(m3u_lines)

    print(f"\n✅ ফাইনাল প্লেলিস্ট তৈরি সম্পন্ন!")
    print(f"📄 কালেক্টেড ফাইল: {COLLECTED_M3U_FILE} ({len(collected_channels)} টি)")
    print(f"📄 ফাইনাল ফাইল: {FINAL_M3U_FILE} ও {FINAL_JSON_FILE} ({total_count} টি)")

def main():
    count = step1_collect_all_keyword_channels()
    if count > 0:
        step2_build_fresh_final_playlist()

if __name__ == "__main__":
    main()
