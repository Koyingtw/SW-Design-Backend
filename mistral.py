import os
from mistralai import Mistral
from openai import OpenAI
import time
import requests
import db

async def generate_summary_from_note(client, user_id: str, note_id: str, custom_prompt: str, openai_client) -> str:
    """
    生成日記摘要的函數
    
    Args:
        client: 資料庫客戶端
        user_id: 用戶ID
        note_id: 日記ID
        custom_prompt: 自定義摘要需求
        openai_client: OpenAI 客戶端
    
    Returns:
        str: 生成的摘要
    """
    
    # 獲取日記內容
    note_content_all = await db.get_content_from_note_id(client, user_id, note_id)
    note_content = ""
    for content in note_content_all['items']:
        if content['type'] == 'text':
            note_content += content['text']
    
    print(f"日記內容：{note_content}")
    
    # 優化的 system prompt
    system_prompt = """你是一個專業的日記摘要助手，擅長從個人日記中提取核心信息並生成簡潔有意義的摘要。

你的任務是根據用戶的日記內容生成摘要，需要：
1. 保留日記的核心信息和重要細節
2. 維持原文的情感色彩和語調
3. 結構清晰，邏輯順暢
4. 使用自然流暢的繁體中文表達
5. 避免過度解釋或添加個人觀點
6. 摘要長度適中（通常為原文的 1/3 到 1/2）

根據用戶的特殊需求調整摘要重點和風格。"""

    # 構建 user prompt
    base_prompt = "請為以下日記內容生成摘要："
    
    # 如果有自定義需求，加入到 prompt 中
    if custom_prompt and custom_prompt.strip():
        user_prompt = f"{base_prompt}\n\n特殊需求：{custom_prompt}\n\n日記內容：\n{note_content}"
    else:
        user_prompt = f"{base_prompt}\n\n日記內容：\n{note_content}"
    
    model = "gpt-4o"
    
    try:
        response = openai_client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.4,  # 適中的創造性
            max_tokens=300,   # 根據需要調整
            top_p=0.9,       # 提高輸出品質
        )
        
        summary = response.choices[0].message.content.strip()
        print(f"生成的摘要：{summary}")
        
        return summary
        
    except Exception as e:
        print(f"生成摘要時發生錯誤: {e}")
        # 返回簡單的默認摘要
        return "無法生成摘要，請稍後再試。"


async def generate_hashtag_from_note(client, user_id: str, note_id: str, openai_client) -> str:
    # 獲取日記內容
    note_content_all = await db.get_content_from_note_id(client, user_id, note_id)
    note_content = ""
    for content in note_content_all['items']:
        if content['type'] == 'text':
            note_content += content['text'] + "\n"
    
    print(f"日記內容：{note_content}")
    
    # 優化的 system prompt
    system_prompt = """你是一個專業的日記分析助手，擅長從日記內容中提取關鍵信息並生成相關的 hashtag。

你的任務是分析日記內容，並生成 3-6 個簡潔且有意義的 hashtag，涵蓋以下方面：
- 當天的主要活動或事件
- 情緒狀態或心情
- 出現的重要人物或關係
- 地點或場所
- 學習、工作或生活主題
- 特殊的體驗或感受

生成規則：
1. 每個 hashtag 保持簡潔（1-3 個詞）
2. 使用繁體中文
3. 不要包含 # 符號
4. 只輸出 hashtag，以逗號分隔
5. 不要輸出任何解釋或額外文字
6. 避免過於籠統的詞彙，要具體且有意義"""

    # 優化的 user prompt
    user_prompt = f"""請分析以下日記內容，生成 3-6 個相關的 hashtag：

日記內容：
{note_content}

請直接輸出 hashtag，格式：hashtag1,hashtag2,hashtag3"""

    model = "gpt-4o"
    
    try:
        response = openai_client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.3,  # 降低溫度以獲得更一致的結果
            max_tokens=100,   # 限制輸出長度
        )
        
        # 取得模型回應並處理
        corrected_text = response.choices[0].message.content.strip()
        print(f"AI 生成的 hashtags: {corrected_text}")
        
        # 清理和處理 hashtags
        corrected_list = [tag.strip() for tag in corrected_text.split(',') if tag.strip()]
        
        # 進一步清理，移除可能的符號
        cleaned_hashtags = []
        for tag in corrected_list:
            # 移除可能的 # 符號和其他特殊字符
            clean_tag = tag.replace('#', '').replace('「', '').replace('」', '').strip()
            if clean_tag:  # 只添加非空的 hashtag
                cleaned_hashtags.append(clean_tag)
        
        # 限制 hashtag 數量（3-6個）
        if len(cleaned_hashtags) > 6:
            cleaned_hashtags = cleaned_hashtags[:6]
        elif len(cleaned_hashtags) < 3:
            # 如果生成的 hashtag 太少，可以添加一些通用的備用選項
            default_tags = ["日常", "生活記錄", "今日感想"]
            cleaned_hashtags.extend(default_tags[:3-len(cleaned_hashtags)])
        
        print(f"處理後的 hashtags: {cleaned_hashtags}")
        
        # 更新資料庫
        await db.update_note_hashtags(client, user_id, note_id, cleaned_hashtags)
        
        return f"{cleaned_hashtags}"
        
    except Exception as e:
        print(f"生成 hashtag 時發生錯誤: {e}")
        # 返回默認 hashtags
        default_hashtags = ["日記", "生活", "記錄"]
        await db.update_note_hashtags(client, user_id, note_id, default_hashtags)
        return f"{default_hashtags}"

async def generate_notify(client, user_id, openai_client):
    note_ids = await db.get_sorted_note_list(client, user_id)
    print(f"note_ids: {note_ids}")
    
    if len(note_ids) > 5:
        note_ids = note_ids[-5:]  # 只取最近的五篇日記
        
    note_contents = []
    for note_id in note_ids:
        note_data = await db.get_content_from_note_id(client, user_id, note_id)
        
        # 提取文字內容
        note_content = ""
        for content in note_data['items']:
            if content['type'] == 'text':
                note_content += content['text']
        
        # 假設 note_data 中包含日期信息，你需要根據實際數據結構調整
        # 這裡需要你確認如何獲取日期，可能的方式：
        note_date = note_data.get('date') or note_data.get('created_at') or note_data.get('timestamp')
        
        note_contents.append({
            "date": note_date,
            "content": note_content
        })
    
    # 生成個性化通知
    notification_message = await generate_personalized_notification(openai_client, note_contents)
    
    return notification_message

async def generate_personalized_notification(openai_client, note_contents):
    """使用 ChatGPT API 生成個性化通知訊息"""
    
    # 構建 prompt
    recent_entries_text = ""
    for entry in note_contents:
        recent_entries_text += f"日期: {entry['date']}\n內容: {entry['content']}\n\n"
    
    prompt = f"""
    基於以下用戶最近的日記內容，生成一個溫暖且個性化的通知訊息，鼓勵用戶繼續記錄日記。

    最近的日記內容：
    {recent_entries_text}

    請生成一個簡短（50字以內）、溫暖且個性化的通知訊息，內容應該：
    1. 反映用戶最近的生活狀態或情緒
    2. 鼓勵用戶繼續記錄日記
    3. 語調溫暖友善
    4. 不要直接引用日記內容，而是基於內容生成相關的鼓勵

    只返回通知訊息，不需要其他說明。
    """
    
    try:
        response = openai_client.chat.completions.create(
            model="gpt-4o",  # 或使用 "gpt-4" 
            messages=[
                {
                    "role": "system", 
                    "content": "你是一個溫暖的日記助手，擅長根據用戶的日記內容生成個性化的鼓勵訊息。"
                },
                {
                    "role": "user", 
                    "content": prompt
                }
            ],
            max_tokens=100,
            temperature=0.7
        )
        
        notification = response.choices[0].message.content.strip()
        return notification
        
    except Exception as e:
        print(f"生成通知時發生錯誤: {e}")
        # 返回默認通知訊息
        return "今天也記錄一下你的生活故事吧！每一天都值得被記住 ✨"

def main():
    # 設定 API 金鑰
    api_key = os.getenv("MISTRAL_API_KEY")
    if not api_key:
        raise ValueError("請先設定環境變數 MISTRAL_API_KEY")
    
    # 初始化 Mistral 客戶端
    client = Mistral(api_key=api_key)
    
    # 定義要使用的模型
    # model = "mistral-large-latest"
    model="gpt-4o"
    
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