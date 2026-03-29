import requests
from bs4 import BeautifulSoup
from google import genai
import time
from dotenv import load_dotenv
import os

load_dotenv()

def send_line_message(notification_message):
    line_api_token=os.getenv("LINE_ACCESS_TOKEN")
    my_user_id=os.getenv("LINE_USER_ID")

    url="https://api.line.me/v2/bot/message/push"
    headers={
        "Content-Type":"application/json",
        "Authorization":"Bearer "+line_api_token
    }
    data={
        "to":my_user_id,
        "messages":[
            {
                "type":"text",
                "text":notification_message
            }
        ]
    }
    response=requests.post(url, headers=headers, json=data)
    if response.status_code ==200:
        print("Message sent successfully.")
    else:
        print(f"Failed to send message. Status code: {response.status_code}, Response: {response.text}")


def detail_sumary(detail_text):
    client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
    response = client.models.generate_content(
        model="gemini-3.1-flash-lite-preview", 
        contents="以下の文章を100文字以内で要約してください。"+detail_text
    )
    return response.text
def scrape_news(url):
    req=requests.get(url)
    req.encoding=req.apparent_encoding
    soup=BeautifulSoup(req.text,'html.parser')
    items=soup.find_all("article")
    messages=[]
    for i in range(1,min(3,len(items))):
        item=items[i]
        title=item.find("h1").text
        link=item.find("a")["href"]
        current_message=f"ニュースタイトル: {title}\nURL: {link}"

        content_req=requests.get(link)
        content_req.encoding=content_req.apparent_encoding
        content_soup=BeautifulSoup(content_req.text,'html.parser')
        content_detail_items=content_soup.find_all("article")
        detail_link_tag = content_soup.find("a", string=lambda text: text and "記事全文を読む" in text)

        if detail_link_tag:
            content_detail_url = detail_link_tag["href"]
            detail_req=requests.get(content_detail_url)
            detail_req.encoding=detail_req.apparent_encoding
            detail_soup=BeautifulSoup(detail_req.text,'html.parser')
            paragraphs=detail_soup.find_all("p")
            article_text="".join([p.text for p in paragraphs])
            current_message+="\n"+detail_sumary(article_text)+"\n"

        else:
            current_message+="\n詳細URLが見つかりませんでした\n"
        messages.append(current_message)
        time.sleep(15)
    return messages

def scrape_catecory_news(url):
    req=requests.get(url)
    req.encoding=req.apparent_encoding
    soup=BeautifulSoup(req.text,'html.parser')
    items=soup.find_all(id="topicList")
    messages=[]
    for i in range(1,min(3,len(items))):
        item=items[i]
        title=item.find("p").text
        link=item.find("a")["href"]
        messages.append(f"ニュースタイトル: {title}\nURL: {link}")
    return messages

if __name__ == "__main__":
    url="https://m.yahoo.co.jp/"
    send_message="おはようございます！\n今日のニュースをお伝えします。\n\n"
    for msg in scrape_news(url):
        send_message+=msg+"\n\n"
    send_message+="スポーツ\n"
    for msg in scrape_catecory_news("https://news.yahoo.co.jp/categories/sports"):
        send_message+=msg+"\n\n"
    send_line_message(send_message)

