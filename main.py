from fastapi import FastAPI, File, UploadFile, Form, HTTPException, Request
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any

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


# --- API 端點 ---

@app.post("/api/summary", response_model=SummaryResponse, tags=["AI 功能"])
async def get_summary(payload: SummaryRequest):
    """
    根據筆記 ID 和可選的自訂提示生成內容摘要。
    """
    # --- 實際的摘要邏輯會在這裡 ---
    # 例如：
    # summary_content = await generate_summary_from_note(payload.note_id, payload.custom_prompt)
    # return {"summary": summary_content}
    print(f"接收到摘要請求: note_id={payload.note_id}, custom_prompt={payload.custom_prompt}")
    return {"summary": f"這是筆記 {payload.note_id} 的摘要。"}

@app.post("/api/audio/transcribe", response_model=TranscribeResponse, tags=["語音服務"])
async def transcribe_audio(audio: UploadFile = File(...)):
    """
    接收 .wav 音檔並將其轉換為文字。
    """
    if not audio.filename.endswith(".wav"):
        raise HTTPException(status_code=400, detail="僅支援 .wav 格式的音檔。")

    # --- 實際的語音轉文字邏輯會在這裡 ---
    # 例如：
    # audio_bytes = await audio.read()
    # transcribed_text = await process_audio_to_text(audio_bytes)
    # return {"text": transcribed_text}
    print(f"接收到音檔: {audio.filename}, 內容類型: {audio.content_type}")
    # 模擬語音轉文字
    content = await audio.read()
    return {"text": f"音檔 '{audio.filename}' ({len(content)} bytes) 的轉錄文字。"}

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
