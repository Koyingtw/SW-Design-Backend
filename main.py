from fastapi import FastAPI, File, UploadFile, Form, HTTPException, Request
from fastapi.responses import Response, JSONResponse

from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
import os
import aiohttp
import io
import json
from bson import ObjectId, json_util

import mistral
import db

mistral_key = os.getenv("MISTRAL_API_KEY")
db_password = os.getenv("DB_PASSWORD")
database = db.connect_to_mongodb_atlas()
mistral_client = mistral.Mistral(api_key=mistral_key)

app = FastAPI(
    title="我的筆記 API",
    description="提供筆記相關功能的 API 服務",
    version="1.0.0",
)

# --- Pydantic 模型定義 ---

# AI 統整請求體
class SummaryRequest(BaseModel):
    note_id: str
    custom_prompt: Optional[str] = None

# AI 統整回應
class SummaryResponse(BaseModel):
    summary: str

# 模糊搜尋結果中的單個筆記項目
class SearchResultItem(BaseModel):
    note_id: str
    title: str
    summary: str

# 模糊搜尋回應
class SearchResponse(BaseModel):
    results: List[SearchResultItem]

# 標籤建議請求體
class TagSuggestRequest(BaseModel):
    diary_id: str # 根據您的描述，這裡應為 diary_id

# 標籤建議回應
class TagSuggestResponse(BaseModel):
    tags: List[str]

# 回顧輯中的筆記項目
class RecapNoteItem(BaseModel):
    note_id: str
    title: str

# 回顧輯中的單個回顧項目
class RecapItem(BaseModel):
    hashtag: str
    summary: str
    notes: List[RecapNoteItem]

# 回顧輯生成回應
class RecapResponse(BaseModel):
    recaps: List[RecapItem]

# 情緒偵測中的情緒分析
class MoodAnalysis(BaseModel):
    mood_trend: str
    mood_scores: List[float]

# 情緒偵測回應
class NotifyResponse(BaseModel):
    should_notify: bool
    reason: List[str]
    mood_analysis: MoodAnalysis
    last_note_days_ago: int

# 語音轉文字回應
class TranscribeResponse(BaseModel):
    text: str

async def upload_diary_entry_handler(
    client,
    user_id: str,
    note_id: str,
    line_id: int,
    entry_type: str,
    text: str = None,
    audio = None,
    video = None
):
    try:
        # 處理音訊檔案
        audio_content = None
        if audio:
            if not audio.filename.endswith(".wav"):
                raise HTTPException(status_code=400, detail="音訊檔案必須是 .wav 格式。")
            audio_content = await audio.read()
            print(f"接收到音訊檔案: {audio.filename}, 大小: {len(audio_content)} bytes")
        
        # 處理影片檔案
        video_content = None
        if video:
            if not video.filename.endswith(".mp4"):
                raise HTTPException(status_code=400, detail="影片檔案必須是 .mp4 格式。")
            video_content = await video.read()
            print(f"接收到影片檔案: {video.filename}, 大小: {len(video_content)} bytes")
        
        # 儲存日記條目
        result = await db.save_diary_entry(
            client,
            user_id,
            note_id,
            line_id,
            entry_type,
            text,
            audio,
            audio_content,
            video,
            video_content
        )
        
        return result
    
    except Exception as e:
        print(f"處理日記上傳請求時發生錯誤: {e}")
        raise HTTPException(status_code=500, detail=f"處理請求時發生錯誤: {str(e)}")


# --- API 端點 ---

@app.post("/api/upload", status_code=200, tags=["日記管理"])
async def upload_diary_entry(
    user_id: str = Form(...),
    note_id: str = Form(...),
    line_id: int = Form(...),
    type: str = Form(...),
    text: Optional[str] = Form(None),
    audio: Optional[UploadFile] = File(None), # 可選的 .wav 檔案
    video: Optional[UploadFile] = File(None)  # 可選的 .mp4 檔案
):
    """
    上傳日記條目，包含文字、以及可選的音訊和影片檔案。
    - **user_id**: 使用者的唯一識別碼。
    - **note_id**: 筆記的唯一識別碼。
    - **line_id**: 在筆記中的行號或順序。
    - **type**: 內容類型 (例如 "text", "audio_text")。
    - **text**: 相關的文字內容。
    - **audio**: (可選) .wav 格式的音訊檔案。
    - **video**: (可選) .mp4 格式的影片檔案。
    """
    # 這裡可以加入處理接收到的資料和檔案的邏輯
    # 例如：儲存檔案、驗證檔案類型、更新資料庫等

    print(f"接收到日記上傳請求:")
    print(f"  user_id: {user_id}")
    print(f"  note_id: {note_id}")
    print(f"  line_id: {line_id}")
    print(f"  type: {type}")
    print(f"  text: {text}")
    
    if line_id == 0:
        db.clear_diary_collection(database, user_id, note_id)

    audio_content = None
    video_content = None
    
    if audio:
        # 檢查檔案類型 (範例)
        if not audio.filename.endswith(".wav"):
            raise HTTPException(status_code=400, detail="音訊檔案必須是 .wav 格式。")
        # 模擬處理音訊檔案
        audio_content = await audio.read()
        print(f"  接收到音訊檔案: {audio.filename}, 大小: {len(audio_content)} bytes, 內容類型: {audio.content_type}")
        # 實際應用中您可能會將檔案儲存到某處:
        # with open(f"uploads/audios/{audio.filename}", "wb") as f:
        #     f.write(audio_content)

    if video:
        # 檢查檔案類型 (範例)
        if not video.filename.endswith(".mp4"):
            raise HTTPException(status_code=400, detail="影片檔案必須是 .mp4 格式。")
        # 模擬處理影片檔案
        video_content = await video.read()
        print(f"  接收到影片檔案: {video.filename}, 大小: {len(video_content)} bytes, 內容類型: {video.content_type}")
        # 實際應用中您可能會將檔案儲存到某處:
        # with open(f"uploads/videos/{video.filename}", "wb") as f:
        #     f.write(video_content)
        
    # result = await upload_diary_entry_handler(
    #     database,
    #     user_id,
    #     note_id,
    #     line_id,
    #     type,
    #     text,
    #     audio,
    #     video
    # )
    
    result = await db.save_diary_entry(
            database,
            user_id,
            note_id,
            line_id,
            type,
            text,
            audio,
            audio_content,
            video,
            video_content
        )

    # 根據您的需求，回應一個空的 JSON 物件
    return {}

@app.get("/api/notes/{user_id}/{note_id}", tags=["筆記管理"])
async def get_note_content(
    user_id: str,
    note_id: str,
):
    """
    獲取指定筆記的所有內容，包含文字、音訊和影片。
    
    參數:
    - user_id: 使用者 ID
    - note_id: 筆記 ID
    - include_binary: 是否在回應中包含音訊和影片的二進制資料
    
    回傳:
    - 筆記的所有內容，按 line_id 排序
    """
    
    print(f"接收到筆記內容請求: user_id={user_id}, note_id={note_id}")
    
    # 獲取筆記內容
    content = await db.get_content_from_note_id(database, user_id, note_id)
    
    if "error" in content and content["error"]:
        raise HTTPException(status_code=500, detail=content["message"])
    
    # 如果不需要包含二進制資料，則移除
    # if not include_binary:
    #     for item in content["items"]:
    #         if "audio_data" in item:
    #             del item["audio_data"]
    #         if "video_data" in item:
    #             del item["video_data"]
    
    # 使用 json_util 處理 MongoDB 特定類型
    return JSONResponse(content=json.loads(json_util.dumps(content)))


@app.post("/api/summary", response_model=SummaryResponse, tags=["AI 功能"])
async def get_summary(
    user_id: str = Form(...),
    note_id: str = Form(...),
    custom_prompt: Optional[str] = Form(None)
):
    """
    根據筆記 ID 和可選的自訂提示生成內容摘要。
    """
    # --- 實際的摘要邏輯會在這裡 ---
    # 例如：
    summary_content = await mistral.generate_summary_from_note(database, user_id, note_id, custom_prompt, mistral_client)
    # return {"summary": summary_content}
    print(f"接收到摘要請求: note_id={note_id}, custom_prompt={custom_prompt}")
    return {"summary": f"{summary_content}"}

GPU_SERVER_URL = "http://140.114.91.158:8760/transcribe"

@app.post("/api/audio/transcribe", response_model=TranscribeResponse, tags=["語音服務"])
async def transcribe_audio(audio: UploadFile = File(...), language: str = Form("zh")):
    """
    接收 .wav 音檔並將其轉換為文字。
    
    - **audio**: 要轉錄的音訊檔案 (.wav 格式)
    - **language**: 音訊的語言代碼 (預設為中文 'zh')
    """
    if not audio.filename.endswith((".wav", ".mp3", ".m4a")):
        raise HTTPException(status_code=400, detail="僅支援 .wav、.mp3 或 .m4a 格式的音檔。")

    try:
        print(f"接收到音檔: {audio.filename}, 內容類型: {audio.content_type}, 語言: {language}")
        
        # 讀取上傳的音訊檔案內容
        content = await audio.read()
        
        # 準備要發送到 GPU Server 的檔案和表單資料
        form_data = aiohttp.FormData()
        form_data.add_field('file', 
                           io.BytesIO(content),
                           filename=audio.filename,
                           content_type=audio.content_type)
        form_data.add_field('language', language)
        
        # 發送請求到 GPU Server
        async with aiohttp.ClientSession() as session:
            async with session.post(GPU_SERVER_URL, data=form_data) as response:
                if response.status != 200:
                    error_text = await response.text()
                    print(f"GPU Server 回應錯誤: {response.status}, {error_text}")
                    raise HTTPException(
                        status_code=500, 
                        detail=f"語音轉文字服務發生錯誤: {error_text}"
                    )
                
                # 解析 GPU Server 的回應
                result = await response.json()
                
                if "error" in result:
                    raise HTTPException(
                        status_code=500, 
                        detail=f"語音轉文字處理失敗: {result['error']}"
                    )
                
                if "text" not in result:
                    raise HTTPException(
                        status_code=500, 
                        detail="語音轉文字服務回應格式不正確"
                    )
                
                print(f"成功獲取轉錄結果: {result['text'][:50]}...")
                return {"text": result["text"]}
                
    except aiohttp.ClientError as e:
        print(f"連接 GPU Server 時發生錯誤: {str(e)}")
        raise HTTPException(
            status_code=503, 
            detail=f"無法連接到語音轉文字服務: {str(e)}"
        )
    except Exception as e:
        print(f"處理音訊轉文字時發生未預期的錯誤: {str(e)}")
        raise HTTPException(
            status_code=500, 
            detail=f"處理請求時發生錯誤: {str(e)}"
        )

@app.get("/api/search", response_model=SearchResponse, tags=["搜尋功能"])
async def search_notes(query: str):
    """
    根據提供的查詢字串進行模糊搜尋。
    """
    # --- 實際的模糊搜尋邏輯會在這裡 ---
    # 例如：
    # search_results = await perform_fuzzy_search(query)
    # return {"results": search_results}
    print(f"接收到搜尋請求: query={query}")
    # 模擬搜尋結果
    mock_results = [
        SearchResultItem(note_id="note123", title="關於 FastAPI 的筆記", summary=f"這是與 '{query}' 相關的 FastAPI 筆記摘要..."),
        SearchResultItem(note_id="note456", title="Python 學習心得", summary=f"這是與 '{query}' 相關的 Python 學習摘要..."),
    ]
    return {"results": mock_results}

@app.post("/api/tag/suggest", response_model=TagSuggestResponse, tags=["標籤功能"])
async def suggest_tags(payload: TagSuggestRequest):
    """
    根據日記 ID 建議相關標籤。
    """
    # --- 實際的標籤建議邏輯會在這裡 ---
    # 例如：
    # suggested_tags = await generate_tags_for_diary(payload.diary_id)
    # return {"tags": suggested_tags}
    print(f"接收到標籤建議請求: diary_id={payload.diary_id}")
    return {"tags": ["#旅行", "#工作", f"#{payload.diary_id}相關"]}

@app.get("/api/recap", response_model=RecapResponse, tags=["回顧功能"])
async def generate_recap():
    """
    生成回顧輯，包含不同主題的摘要和相關筆記。
    """
    # --- 實際的回顧輯生成邏輯會在這裡 ---
    # 例如：
    # recap_data = await create_recap_collection()
    # return {"recaps": recap_data}
    print("接收到回顧輯生成請求")
    mock_recaps = [
        RecapItem(
            hashtag="#旅行",
            summary="關於最近幾次旅行的精彩回顧與體驗總結。",
            notes=[
                RecapNoteItem(note_id="trip001", title="京都五日遊"),
                RecapNoteItem(note_id="trip002", title="宜蘭溫泉之旅"),
            ]
        ),
        RecapItem(
            hashtag="#工作",
            summary="本月工作重點事項與專案進度回顧。",
            notes=[
                RecapNoteItem(note_id="proj001", title="Q3 專案規劃"),
                RecapNoteItem(note_id="task005", title="客戶會議記錄"),
            ]
        )
    ]
    return {"recaps": mock_recaps}

@app.post("/api/notify", response_model=NotifyResponse, tags=["通知與分析"])
async def check_notifications():
    """
    進行情緒偵測並決定是否需要通知用戶。
    """
    # --- 實際的情緒偵測與通知判斷邏輯會在這裡 ---
    # 例如：
    # notification_status = await analyze_user_mood_and_activity()
    # return notification_status
    print("接收到情緒偵測請求")
    # 模擬回應
    return NotifyResponse(
        should_notify=True,
        reason=["negative_mood_trend", "inactivity"],
        mood_analysis=MoodAnalysis(
            mood_trend="negative",
            mood_scores=[0.2, 0.3, 0.1, 0.15]
        ),
        last_note_days_ago=10
    )

# 若要在本地運行此應用程式，可以使用 uvicorn：
# uvicorn main:app --reload
# (假設此檔案名為 main.py)
