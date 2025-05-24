import os
from mistralai import Mistral
import time
import requests
import db

async def generate_summary_from_note(client, user_id: str, note_id: str, custom_prompt: str, mistral_client) -> str:
    user_input = """
    請總結以下的日記內容，並生成出摘要，不要輸出多餘的符號：
    """
    user_input += custom_prompt
    # 這裡可以使用 Mistral API 來生成摘要
    
    note_content_all = await db.get_content_from_note_id(client, user_id, note_id)  # 假設這是一個函數，用來根據 note_id 獲取日記內容
    note_content = ""
    for content in note_content_all['items']:
        if content['type'] == 'text':
            note_content += content['text']
    print(f"日記內容：{note_content}")
    # return note_content
    user_input += f"日記內容：\n{note_content}"
    
    model = "mistral-large-latest"
    response = mistral_client.chat.complete(
        model=model,
        messages=[{"role": "user", "content": user_input}]
    )
    
    # 取得模型回應並輸出
    corrected_text = response.choices[0].message.content
    print(corrected_text)
    
    return f"{corrected_text}"


async def generate_hashtag_from_note(client, user_id: str, note_id: str, mistral_client) -> str:
    user_input = """
    請總結以下的日記內容，並生成出幾個 hashtag，像是當天發生了什麼事件、當天心情如何、出現了什麼人物、考了什麼試等等，並以一個字串：hashtag1,hashtag2 的格式（以逗點作為分割）呈現，不要輸出多餘的符號，也不要輸出原文，只要 hashtag 就好：
    """
    # 這裡可以使用 Mistral API 來生成摘要
    
    note_content_all = await db.get_content_from_note_id(client, user_id, note_id)  # 假設這是一個函數，用來根據 note_id 獲取日記內容
    note_content = ""
    for content in note_content_all['items']:
        if content['type'] == 'text':
            note_content += content['text']
    print(f"日記內容：{note_content}")
    # return note_content
    user_input += f"日記內容：\n{note_content}"
    
    model = "mistral-large-latest"
    response = mistral_client.chat.complete(
        model=model,
        messages=[{"role": "user", "content": user_input}]
    )
    
    # 取得模型回應並輸出
    corrected_text = response.choices[0].message.content
    print(f"corrected_text: {corrected_text}")
    corrected_list = corrected_text.split(',')
    await db.update_note_hashtags(client, user_id, note_id, corrected_list)  # 假設這是一個函數，用來更新日記的 hashtags
    
    return f"{corrected_list}"

def main():
    # 設定 API 金鑰
    api_key = os.getenv("MISTRAL_API_KEY")
    if not api_key:
        raise ValueError("請先設定環境變數 MISTRAL_API_KEY")
    
    # 初始化 Mistral 客戶端
    client = Mistral(api_key=api_key)
    
    # 定義要使用的模型
    model = "mistral-large-latest"
    
    # 輸入語音轉文字結果，並提供指令要求模型進行修正
    user_input = """
    請生成一個繁體中文的日記內容，並且要包含以下幾個要素：
    1. 今天的天氣
    2. 你今天做了什麼事情
    3. 你對今天的感受
    4. 明天的計畫
    5. 任何其他你想分享的事情
    例如：今天的天氣晴朗，我去公園散步，感覺心情很好，明天打算去看電影。
    請用繁體中文回答，並且要有條理地組織內容。
    """
    
    # 呼叫聊天完成 API
    response = client.chat.complete(
        model=model,
        messages=[{"role": "user", "content": user_input}]
    )
    
    # 取得模型回應並輸出
    corrected_text = response.choices[0].message.content
    print(corrected_text)
    
"""
今天，2023年10月10日，天氣陰沉，偶爾還飄著細雨。雖然天氣不太好，但我還是決定出門走走，去了附近的咖啡館。在那裡，我點了一杯拿鐵，邊喝邊看了一本新買的小說。

今天的感受還不錯，雖然天氣不太理想，但咖啡館裡的氛圍很舒適，讓我放鬆了不少。可能是因為下雨的緣故，咖啡館裡的人不多，環境安靜，非常適合閱讀和思考。

明天的計畫是去健身房鍛煉一下，最近工作忙碌，運動量有點不足，得補回來。下午打算去市場買些新鮮的食材，準備做一頓美味的晚餐。

最近忙著工作，週末终于有点時間放鬆一下。希望明天的天氣會好一點，這樣出門會更愉快。

今天還有一件值得一提的事情，我收到了一位老朋友的來信，讓我非常感動。他告訴我他最近的生活狀況，讓我回想起我們一起度過的美好時光。真希望有機會能再見面，重溫舊夢。

總的來說，今天雖然天氣不太好，但我過得很充實，心情也不錯。希望明天能夠更好地安排時間，讓自己更加健康和快樂。
"""