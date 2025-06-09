from fastapi import FastAPI, File, UploadFile, Form, HTTPException, Request, status
from fastapi.responses import Response, JSONResponse

from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
import os
import aiohttp
import io
import json
from bson import ObjectId, json_util
import datetime
from openai import OpenAI

import mistral
import db
import security

mistral_key = os.getenv("MISTRAL_API_KEY")
openai_api_key = os.environ.get('OPENAI_API_KEY')
db_password = os.getenv("DB_PASSWORD")
database = db.connect_to_mongodb_atlas()
mistral_client = mistral.Mistral(api_key=mistral_key)
openai_client = OpenAI(api_key=openai_api_key)

app = FastAPI(
    title="SW-Design API",
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
    
# Node list 回應    
class NoteListResponse(BaseModel):
    user_id: str
    note_ids: List[str]
    total_notes: int
    retrieved_at: str

# 模糊搜尋結果中的單個筆記項目
class SearchResultItem(BaseModel):
    note_id: str
    title: str
    summary: str

# 模糊搜尋回應
class SearchResponse(BaseModel):
    query: str
    user_id: str
    notes: Dict[str, List[str]]
    total_matches: int
    searched_notes: int
    search_time: str


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

@app.post("/api/upload", status_code=200, tags=["上傳日記"])
async def upload_diary_entry(
    user_id: str = Form(...),
    note_id: str = Form(...),
    line_id: int = Form(...),
    type: str = Form(...),
    text: Optional[str] = Form(None),
    audio: Optional[UploadFile] = File(None), # 可選的 .wav 檔案
    image: Optional[UploadFile] = File(None), # 可選的 .jpg 檔案
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
    - **image**: (可選) .jpg 格式的圖片檔案
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
    image_content = None
    video_content = None
    
    if audio:
        # 檢查檔案類型 (範例)
        if not audio.filename.endswith(".wav"):
            raise HTTPException(status_code=400, detail="音訊檔案必須是 .wav 格式。")
        # 模擬處理音訊檔案
        audio_content = await audio.read()
        print(f"  接收到音訊檔案: {audio.filename}, 大小: {len(audio_content)} bytes, 內容類型: {audio.content_type}")
        
    if image:
        # 檢查檔案類型 (範例)
        if not image.filename.endswith(".jpg"):
            raise HTTPException(status_code=400, detail="音訊檔案必須是 .jpg 格式。")
        # 模擬處理音訊檔案
        image_content = await image.read()
        print(f"  接收到音訊檔案: {image.filename}, 大小: {len(image_content)} bytes, 內容類型: {image.content_type}")

    if video:
        # 檢查檔案類型 (範例)
        if not video.filename.endswith(".mp4"):
            raise HTTPException(status_code=400, detail="影片檔案必須是 .mp4 格式。")
        # 模擬處理影片檔案
        video_content = await video.read()
        print(f"  接收到影片檔案: {video.filename}, 大小: {len(video_content)} bytes, 內容類型: {video.content_type}")
    
    await db.save_diary_entry(
            database,
            user_id,
            note_id,
            line_id,
            type,
            text,
            audio,
            audio_content,
            image,
            image_content,
            video,
            video_content
        )

    # 根據您的需求，回應一個空的 JSON 物件
    return {}

@app.post("/api/create", status_code=200, tags=["新增日記"])
async def create_diary(
    user_id: str = Form(...),
    note_id: str = Form(...),
):
    """
    創建一個新的日記條目。
    
    - **user_id**: 使用者的唯一識別碼。
    - **note_id**: 筆記的唯一識別碼。
    """
    print(f"接收到創建日記請求: user_id={user_id}, note_id={note_id}")
    
    await db.add_note_id_to_note_list(database, user_id, note_id)
    
    # 返回成功回應
    return JSONResponse(content={"message": "日記創建成功"})

@app.post("/api/delete", status_code=200, tags=["刪除日記"])
async def delete_diary(
    user_id: str = Form(...),
    note_id: str = Form(...),
):
    """
    刪除指定的日記條目。
    
    - **user_id**: 使用者的唯一識別碼。
    - **note_id**: 筆記的唯一識別碼。
    """
    print(f"接收到刪除日記請求: user_id={user_id}, note_id={note_id}")
    
    # 刪除指定的日記條目
    try:
        await db.delete_note_from_note_list(database, user_id, note_id)
    
        # 返回成功回應
        return JSONResponse(content={"message": "日記刪除成功"})
    except Exception as e:
        print(f"刪除日記時發生錯誤: {e}")
        raise HTTPException(status_code=500, detail=f"刪除日記時發生錯誤: {str(e)}")

@app.get("/api/note_list/{user_id}", tags=["獲得筆記列表"])
async def get_user_note_list_simple(user_id: str):
    """
    獲取使用者的筆記 ID 列表（簡化版本，直接回傳陣列）
    
    參數:
    - user_id: 使用者 ID
    
    返回:
    - note_id 的 JSON 陣列
    """
    global client
    
    try:
        note_ids = await db.get_sorted_note_list(database, user_id)
        return note_ids  # 直接回傳陣列
        
    except Exception as e:
        print(f"API 處理時發生錯誤: {e}")
        raise HTTPException(status_code=500, detail=f"獲取筆記列表時發生錯誤: {str(e)}")

@app.get("/api/notes/{user_id}/{note_id}", tags=["獲取筆記內容"])
async def get_note_content(
    user_id: str,
    note_id: str,
):
    """
    獲取指定筆記的所有內容，包含文字、音訊和影片。
    
    參數:
    - user_id: 使用者 ID
    - note_id: 筆記 ID
    
    回傳:
    - 筆記的所有內容，按 line_id 排序
    """
    
    print(f"接收到筆記內容請求: user_id={user_id}, note_id={note_id}")
    
    # 獲取筆記內容
    content = await db.get_content_from_note_id(database, user_id, note_id)
    
    if "error" in content and content["error"]:
        raise HTTPException(status_code=500, detail=content["message"])
    
    # 使用 json_util 處理 MongoDB 特定類型
    return JSONResponse(content=json.loads(json_util.dumps(content)))

@app.get("/api/notes/{user_id}/{note_id}/hashtags", response_model=list[str], tags=["獲取 hashtags"])
async def get_note_hashtags_api(
    user_id: str,
    note_id: str
):
    """
    獲取指定筆記的 hashtags 列表
    
    參數:
    - user_id: 使用者 ID
    - note_id: 筆記 ID
    
    返回:
    - hashtags 的字串列表
    """
    global client  # 假設您已經設置了全域的 MongoDB 客戶端
    
    try:
        # 呼叫函數獲取 hashtags
        hashtags = await db.get_note_hashtags(database, user_id, note_id)
        
        # 如果找不到筆記，回傳 404 錯誤
        if not hashtags and not await db.note_exists(database, user_id, note_id):
            raise HTTPException(
                status_code=404, 
                detail=f"找不到使用者 {user_id} 的筆記 {note_id}"
            )
        
        return hashtags  # 直接回傳 hashtags 列表
        
    except HTTPException:
        # 重新拋出 HTTP 異常
        raise
    except Exception as e:
        print(f"API 處理時發生錯誤: {e}")
        raise HTTPException(
            status_code=500, 
            detail=f"獲取標籤時發生錯誤: {str(e)}"
        )

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
    summary_content = await mistral.generate_summary_from_note(database, user_id, note_id, custom_prompt, openai_client)
    # return {"summary": summary_content}
    print(f"接收到摘要請求: note_id={note_id}, custom_prompt={custom_prompt}")
    return {"summary": f"{summary_content}"}

@app.post("/api/gen_hashtag", tags=["生成 hashtags"])
async def get_summary(
    user_id: str = Form(...),
    note_id: str = Form(...),
):
    """
    根據筆記 ID 生成 hashtags
    """
    # --- 實際的摘要邏輯會在這裡 ---
    # 例如：
    hashtags = await mistral.generate_hashtag_from_note(database, user_id, note_id, openai_client)
    # return {"summary": summary_content}
    print(f"接收到 hashtags 請求: note_id={note_id}, hashtags={hashtags}")
    return {"hashtags": f"{hashtags}"}

# GPU_SERVER_URL = "http://140.114.91.158:8760/transcribe"

# @app.post("/api/audio/transcribe", response_model=TranscribeResponse, tags=["語音服務"])
# async def transcribe_audio(audio: UploadFile = File(...), language: str = Form("zh")):
#     """
#     接收 .wav 音檔並將其轉換為文字。
    
#     - **audio**: 要轉錄的音訊檔案 (.wav 格式)
#     - **language**: 音訊的語言代碼 (預設為中文 'zh')
#     """
#     if not audio.filename.endswith((".wav", ".mp3", ".m4a")):
#         raise HTTPException(status_code=400, detail="僅支援 .wav、.mp3 或 .m4a 格式的音檔。")

#     try:
#         print(f"接收到音檔: {audio.filename}, 內容類型: {audio.content_type}, 語言: {language}")
        
#         # 讀取上傳的音訊檔案內容
#         content = await audio.read()
        
#         # 準備要發送到 GPU Server 的檔案和表單資料
#         form_data = aiohttp.FormData()
#         form_data.add_field('file', 
#                            io.BytesIO(content),
#                            filename=audio.filename,
#                            content_type=audio.content_type)
#         form_data.add_field('language', language)
        
#         # 發送請求到 GPU Server
#         async with aiohttp.ClientSession() as session:
#             async with session.post(GPU_SERVER_URL, data=form_data) as response:
#                 if response.status != 200:
#                     error_text = await response.text()
#                     print(f"GPU Server 回應錯誤: {response.status}, {error_text}")
#                     raise HTTPException(
#                         status_code=500, 
#                         detail=f"語音轉文字服務發生錯誤: {error_text}"
#                     )
                
#                 # 解析 GPU Server 的回應
#                 result = await response.json()
                
#                 if "error" in result:
#                     raise HTTPException(
#                         status_code=500, 
#                         detail=f"語音轉文字處理失敗: {result['error']}"
#                     )
                
#                 if "text" not in result:
#                     raise HTTPException(
#                         status_code=500, 
#                         detail="語音轉文字服務回應格式不正確"
#                     )
                
#                 print(f"成功獲取轉錄結果: {result['text'][:50]}...")
#                 return {"text": result["text"]}
                
#     except aiohttp.ClientError as e:
#         print(f"連接 GPU Server 時發生錯誤: {str(e)}")
#         raise HTTPException(
#             status_code=503, 
#             detail=f"無法連接到語音轉文字服務: {str(e)}"
#         )
#     except Exception as e:
#         print(f"處理音訊轉文字時發生未預期的錯誤: {str(e)}")
#         raise HTTPException(
#             status_code=500, 
#             detail=f"處理請求時發生錯誤: {str(e)}"
#         )

@app.post("/api/audio/transcribe", response_model=TranscribeResponse, tags=["語音轉文字"])
async def transcribe_audio(audio: UploadFile = File(...), language: str = Form("zh-TW")):
    """
    接收音檔並使用 OpenAI Whisper API 將其轉換為文字。
    
    - **audio**: 要轉錄的音訊檔案 (支援多種格式：mp3, mp4, mpeg, mpga, m4a, wav, webm)
    - **language**: 音訊的語言代碼 (預設為中文 'zh')
    """
    
    # OpenAI Whisper 支援的檔案格式
    supported_formats = (".mp3", ".mp4", ".mpeg", ".mpga", ".m4a", ".wav", ".webm")
    
    if not audio.filename.lower().endswith(supported_formats):
        raise HTTPException(
            status_code=400, 
            detail=f"僅支援以下格式的音檔: {', '.join(supported_formats)}"
        )

    try:
        print(f"接收到音檔: {audio.filename}, 內容類型: {audio.content_type}, 語言: {language}")
        
        # 讀取上傳的音訊檔案內容
        content = await audio.read()
        
        # 檢查檔案大小 (OpenAI 限制 25MB)
        if len(content) > 25 * 1024 * 1024:  # 25MB
            raise HTTPException(
                status_code=400,
                detail="音檔大小不能超過 25MB"
            )
        
        print(f"音檔大小: {len(content)} bytes")
        
        # 使用 OpenAI Whisper API 進行轉錄
        audio_file = io.BytesIO(content)
        audio_file.name = audio.filename  # 設定檔名，OpenAI 需要這個來判斷格式
        
        # 語言代碼轉換 (如果需要)
        language_mapping = {
            "zh-TW": "zh-TW",
            "en": "en",
            "ja": "ja",
            "ko": "ko",
            # 可以根據需要添加更多語言映射
        }
        
        whisper_language = language_mapping.get(language, language)
        
        # 呼叫 OpenAI Whisper API
        response = openai_client.audio.transcriptions.create(
            model="gpt-4o-transcribe",
            file=audio_file,
            language=whisper_language,  # 指定語言可以提高準確性
            response_format="text",     # 直接返回文字，也可以選擇 "json", "srt", "verbose_json", "vtt"
            temperature=0.2,            # 降低溫度以獲得更一致的結果
        )
        
        # OpenAI 直接返回文字內容
        transcribed_text = response.strip() if isinstance(response, str) else response
        
        print(f"成功獲取轉錄結果: {transcribed_text[:50]}...")
        
        return {"text": transcribed_text}
        
    except Exception as e:
        print(f"使用 OpenAI 轉錄音訊時發生錯誤: {str(e)}")
        
        # 根據不同的錯誤類型提供更具體的錯誤訊息
        if "rate limit" in str(e).lower():
            raise HTTPException(
                status_code=429,
                detail="API 請求頻率超過限制，請稍後再試"
            )
        elif "invalid file format" in str(e).lower():
            raise HTTPException(
                status_code=400,
                detail="不支援的音檔格式"
            )
        elif "file too large" in str(e).lower():
            raise HTTPException(
                status_code=400,
                detail="音檔檔案過大，請壓縮後再上傳"
            )
        else:
            raise HTTPException(
                status_code=500,
                detail=f"語音轉文字處理失敗: {str(e)}"
            )

@app.get("/api/search/{user_id}", response_model=SearchResponse, tags=["搜尋功能"])
async def search_notes(user_id: str, query: str):
    """
    根據提供的查詢字串進行模糊搜尋。
    """
    try:
        # 先取得使用者的所有 note_id
        note_ids = await db.get_sorted_note_list(database, user_id)
        
        if not note_ids:
            raise HTTPException(status_code=404, detail=f"使用者 {user_id} 沒有任何筆記")
        
        # 進行模糊搜尋
        
        search_result = await db.fuzzy_search(database, user_id, note_ids, query)
        
        # 計算總匹配數
        total_matches = sum(len(texts) for texts in search_result.values())
        
        return SearchResponse(
            query=query,
            user_id=user_id,
            notes=search_result,
            total_matches=total_matches,
            searched_notes=len(note_ids),
            search_time=datetime.datetime.now().isoformat()
        )
    
    except Exception as e:
        print(f"搜尋 API 處理時發生錯誤: {e}")
        raise HTTPException(status_code=500, detail=f"搜尋時發生錯誤: {str(e)}")


# @app.post("/api/tag/suggest", response_model=TagSuggestResponse, tags=["標籤功能"])
# async def suggest_tags(payload: TagSuggestRequest):
#     """
#     根據日記 ID 建議相關標籤。
#     """
#     # --- 實際的標籤建議邏輯會在這裡 ---
#     # 例如：
#     # suggested_tags = await generate_tags_for_diary(payload.diary_id)
#     # return {"tags": suggested_tags}
#     print(f"接收到標籤建議請求: diary_id={payload.diary_id}")
#     return {"tags": ["#旅行", "#工作", f"#{payload.diary_id}相關"]}


@app.get("/api/notify/{user_id}", tags=["通知與分析"])
async def check_notifications(user_id: str):
    """
    進行情緒偵測並決定是否需要通知用戶。
    """
    notify = await mistral.generate_notify(database, user_id, openai_client)
    print(f"接收到通知檢查請求: {notify}")
    return notify

@app.get("/api/link/{user_id}/{note_id}", tags=["連結功能"])
async def get_note_link(user_id: str, note_id: str):
    result = await mistral.get_event_link_from_note(database, user_id, note_id, openai_client)
    print(result)
    return result

@app.post("/api/register", status_code=status.HTTP_201_CREATED)
async def register_user(
    username: str = Form(...),
    password: str = Form(...),
):
    db = database['auth_db']
    users_collection = db['users']
    
    # 檢查使用者是否已存在
    existing_user = users_collection.find_one({"username": username})
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already registered"
        )   
    
    # 雜湊密碼
    hashed_password = security.get_password_hash(password)
    
    # 建立使用者資料
    user_data = dict()
    user_data["username"] = username
    user_data["hashed_password"] = hashed_password

    # 存入資料庫
    users_collection.insert_one(user_data)
    
    return {"message": "User created successfully", "username": username}

@app.post("/api/login")
async def login_user(
    username: str = Form(...),
    password: str = Form(...),
):
    print(f"接收到登入請求: username={username}, password={password}")
    
    db = database['auth_db']
    users_collection = db['users']
    
    # 從資料庫尋找使用者
    db_user = users_collection.find_one({"username": username})
    
    if not db_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Incorrect username or password"
        )
        
    # 驗證密碼
    if not security.verify_password(password, db_user["hashed_password"]):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Incorrect username or password"
        )
        
    # 在這個簡單範例中，我們只返回成功訊息
    # 在實際應用中，這裡會生成 JWT (JSON Web Token)[2]
    return {"message": "Login successful", "username": username}

# 若要在本地運行此應用程式，可以使用 uvicorn：
# uvicorn main:app --reload
# (假設此檔案名為 main.py)
