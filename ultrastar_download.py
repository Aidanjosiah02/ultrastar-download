from bs4 import BeautifulSoup
from pathlib import Path
import random
import re
import requests
from timeit import default_timer
from urllib.parse import urlparse, parse_qs
import rookiepy
import subprocess


main_headers = {
    'accept-encoding': 'gzip, deflate, br',
    'accept-language': 'en-GB,en;q=0.9,en-US;q=0.8',
    'sec-ch-ua': '"Chromium";v="104", " Not A;Brand";v="99", "Microsoft Edge";v="104"',
    'sec-ch-ua-mobile': '?0',
    'sec-ch-ua-platform': '"Windows"',
    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/104.0.5112.102 Safari/537.36 Edg/104.0.1293.63'
}
navigate_headers = main_headers
navigate_headers.update({
    'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
    'cache-control': 'max-age=0',
    'sec-fetch-dest': 'document',
    'sec-fetch-mode': 'navigate',
    'sec-fetch-site': 'same-origin',
    'sec-fetch-user': '?1',
    'upgrade-insecure-requests': '1'
})



ROOT = Path("./")
BATCH = (ROOT / "batch.txt")
MUSIC_DIR = Path("C:\\Program Files (x86)\\UltraStar Deluxe\\songs")

tempmail_domainList = ['1secmail.com', '1secmail.net', '1secmail.org']
tempmail_domain = random.choice(tempmail_domainList)
download_pattern = r'https://bandcamp.com/download\?.+'
fsig_pattern = r'&fsig=([a-z0-9]{32})'
ts_pattern = r'&ts=([0-9]{10}\.[0-9])'
background_pattern = re.compile(r'background-image: url\((.*?)\);', re.MULTILINE | re.DOTALL)
imgurl_pattern = r'https://f4.bcbits.com/img/(.*\.[a-z]+)'
windows_forbidden = r'[<>:"/\\|?*]'
random_twelve = str(random.randrange(100000000000,999999999999))
mib = 1048576
gib = 1024*mib


urls = []
with open((BATCH), 'r') as batch:
    lines = batch.read().splitlines()
    for line in lines:
        urls.append(line)



results = []
for url in urls:
    print(url)
    if url == "":
        continue
    url_txt = url.replace('detail', 'gettxt')
    parsed_url = urlparse(url)
    url_id = parse_qs(parsed_url.query)['id']
    url_id_str = str(url_id[0])

    # get txt
    payload = {
        "link": "gettxt",
        "id": url_id_str,
        "wd": "1"
    }
    import rookiepy

    cookies = rookiepy.edge(["usdb.animux.de"])
    sessid = {"PHPSESSID": cookies[0]['value']} 
    response = requests.post(url_txt, headers=navigate_headers, data=payload, cookies=sessid)
    soup = BeautifulSoup(response.text, "html.parser")
    form = soup.find('form', {'id': 'myform'})
    input = str(form('input')) #if error occurs, cookie is wrong. See line 94
    sub1 = "value=\""
    sub2 = "\"/>"
    result1 = ""
    for index in range(input.index(sub1) + len(sub1), input.index(sub2)):
        result1 = result1 + input[index]

    title = ""
    mp3_string = "#MP3:"
    mp3_extension = ".mp3"
    mp3_string_full = ""
    video_string = "#VIDEO:"
    video_string_full = ""
    for line in result1.split("\n"):
        if mp3_string in line:
            line_length = len(line) - len(mp3_extension)
            title = re.sub(windows_forbidden, '', line[len(mp3_string):(line_length - 1)])
            mp3_string_full = line
        if video_string in line:
            video_string_full = line
        if title != "" and video_string_full != "":
            break
    result1 = result1.replace(video_string_full, f'{video_string}{title}.webm')
    result1 = result1.replace(mp3_string_full, f'{mp3_string}{title}.mp3')
    


    song_path = (MUSIC_DIR / title)
    
    song_path.mkdir(parents=True, exist_ok=True)
    song_txt_path = song_path / (title + ".txt")
    # if song_txt_path.exists == False:
    with open(song_txt_path, 'w', newline='') as song_txt:
        song_txt.write(result1)
    # else:
    #     print(f"Text file exists for {title}. Skipping writing. If you intend to replace it, please delete the file.")
    


    response = requests.get(url, headers=navigate_headers)
    soup = BeautifulSoup(response.text, "html.parser")
    iframe_embed = soup.find('iframe', {'class': 'embed'})
    input = str(iframe_embed)
    sub1 = "src=\""
    sub2 = "\" width="
    video_url = ""
    for index in range(input.index(sub1) + len(sub1), input.index(sub2)):
        video_url = video_url + input[index]


    print(f"yt-dlp -f 140 -x --audio-format mp3 --audio-quality 0 --replace-in-metadata title \"[\\U0000002A\\U0000005C\\U0000002F\\U0000003A\\U00000022\\U0000003F\\U0000007C\\U00010000-\\U0010FFFF]\" \"\" -o \"{song_path / title}.mp3\" {video_url}")
    ytdlp_command_audio = f"yt-dlp -f 140 -x --audio-format mp3 --audio-quality 0 --replace-in-metadata title \"[\\U0000002A\\U0000005C\\U0000002F\\U0000003A\\U00000022\\U0000003F\\U0000007C\\U00010000-\\U0010FFFF]\" \"\" -o \"{song_path / title}.mp3\" {video_url}"
    ytdlp_command_video = f"yt-dlp -f \"bestvideo[height<=1080]\" --replace-in-metadata title \"[\\U0000002A\\U0000005C\\U0000002F\\U0000003A\\U00000022\\U0000003F\\U0000007C\\U00010000-\\U0010FFFF]\" \"\" -o \"{song_path / title}.%(ext)s\" {video_url}"
    ytdlp_run = subprocess.call("cd /d %s & %s" % (song_path, ytdlp_command_audio), shell=True)
    ytdlp_run = subprocess.call("cd /d %s & %s" % (song_path, ytdlp_command_video), shell=True)


