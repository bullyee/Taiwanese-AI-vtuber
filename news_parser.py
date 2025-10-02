import json
import os
import re
import requests
from bs4 import BeautifulSoup
from datetime import datetime
import socket
import struct
import urllib.request

# TTS API Client
class TTSClient:
    def __init__(self, host: str, token: str):
        self.__host = host
        self.__token = token

    def askForService(self, text: str, language: str, model: str, output_path: str):
        if not text:
            raise ValueError("Text must not be empty.")
        language = language.lower()
        if language == "hakka":
            port = 10010
            model = model or "hedusi"
        elif language == "taiwanese":
            port = 10012
            model = model or "M12"
        elif language == "chinese":
            port = 10015
            model = model or "M60"
        else:
            raise ValueError("Unsupported language")

        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.connect((self.__host, port))
            msg = bytes(self.__token + "@@@" + text + "@@@" + model + "@@@" + language, "utf-8")
            msg = struct.pack(">I", len(msg)) + msg
            sock.sendall(msg)

            with open(output_path, "wb") as f:
                while True:
                    data = sock.recv(8192)
                    if not data:
                        break
                    f.write(data)
        except Exception as e:
            print(f"TTS error for sentence '{text}': {e}")
        finally:
            sock.close()

# 爬蟲函式
def crawl_udn_news():
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36'}
    url = 'https://udn.com/news/cate/2/7227'

    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        news_items = soup.select('.story-list__news')[:20]
        if not news_items:
            print("找不到新聞。")
            return []

        results = []
        os.makedirs("images", exist_ok=True)  # 創建 images 目錄

        for news_idx, item in enumerate(news_items, 1):
            # 提取標題
            title_tag = item.select_one('.story-list__text h2 a')
            title = title_tag.get_text(strip=True) if title_tag else '無標題'
            link = title_tag['href'] if title_tag and 'href' in title_tag.attrs else None
            if not link:
                print(f"新聞 '{title}' 無有效連結，跳過內容爬取。")
                continue
            if not link.startswith('http'):
                link = 'https://udn.com' + link

            try:
                article_response = requests.get(link, headers=headers)
                article_response.raise_for_status()
                article_soup = BeautifulSoup(article_response.text, 'html.parser')

                # 提取時間
                time_tag = article_soup.select_one('.article-content__subinfo time')
                time = time_tag.get_text(strip=True) if time_tag else '無時間'
                try:
                    time = datetime.strptime(time, '%Y-%m-%d %H:%M').strftime('%Y-%m-%d %H:%M')
                except ValueError:
                    time = '時間格式錯誤'

                # 移除內文插圖
                for figure in article_soup.select('.article-content__editor figure'):
                    figure.decompose()

                # 提取封面圖片並下載
                cover_image = article_soup.select_one('figure.article-content__cover img')
                image_url = cover_image['src'] if cover_image and 'src' in cover_image.attrs else None
                if image_url:
                    try:
                        image_response = requests.get(image_url, headers=headers)
                        image_response.raise_for_status()
                        image_extension = image_url.split('.')[-1].split('&')[0]  # 提取檔案副檔名
                        image_path = f"images/news{news_idx}_image.{image_extension}"
                        with open(image_path, 'wb') as f:
                            f.write(image_response.content)
                    except requests.RequestException as e:
                        print(f"無法下載新聞 '{title}' 的封面圖片：{e}")
                        image_path = None
                else:
                    image_path = None

                # 移除封面圖片的 figcaption
                cover_figcaption = article_soup.select_one('figure.article-content__cover figcaption')
                if cover_figcaption:
                    cover_figcaption.decompose()

                # 提取主要內容
                content_paragraphs = article_soup.select('.article-content__paragraph .article-content__editor p')
                content = []
                for p in content_paragraphs:
                    if p.find_parent('div', style=re.compile(r'position: relative;.*background-color:#fff')):
                        continue
                    text = p.get_text(strip=True)
                    if text:
                        content.append(text)

                content_text = '\n'.join(content) if content else '無內文'

                # 分句處理：以 。、！、？、， 或 。」 為結尾
                sentences = []
                current = ""
                i = 0
                while i < len(content_text):
                    current += content_text[i]
                    if content_text[i] in "。！？,，":
                        if i + 1 < len(content_text) and content_text[i] == "。" and content_text[i + 1] == "」":
                            current += "」"
                            i += 1
                        sentences.append(current.strip())
                        current = ""
                    i += 1
                if current.strip():
                    sentences.append(current.strip())

                news_item = {
                    'title': title,
                    'time': time,
                    'content': content_text,
                    'verbatim': sentences,
                    'image': image_path
                }
                results.append(news_item)

            except requests.RequestException as e:
                print(f"錯誤爬取內容：{e}")
                continue

        return results

    except requests.RequestException as e:
        print(f"主頁面無法連線：{e}")
        return []

# 主程式
if __name__ == "__main__":
    os.makedirs("audio", exist_ok=True)

    tts_client = TTSClient(host="140.116.245.157", token="mi2stts")
    news_list = crawl_udn_news()  # 取得新聞

    for news_idx, news in enumerate(news_list, 1):
        print(f"[新聞 {news_idx}] {news['title']} ({news['time']})")
        content1 = {}
        for sent_idx, sentence in enumerate(news['verbatim'], 1):
            print(f"  ({sent_idx}) {sentence}")
            filename = f"audio/news{news_idx}_{sent_idx}.wav"
            tts_client.askForService(
                text=sentence,
                language="taiwanese",
                model="M12",
                output_path=filename
            )
            content1[str(sent_idx)] = sentence

        print(f"  圖片: {news['image'] if news['image'] else '無圖片'}")
        print("-" * 40)

        news["news_idx"] = news_idx
        del news["content"]
        del news["verbatim"]
        news["content"] = content1

    with open("news.json", "w", encoding="utf-8") as f:
        json.dump(news_list, f, ensure_ascii=False, indent=2)

    print("已將新聞資料輸出至 news.json")