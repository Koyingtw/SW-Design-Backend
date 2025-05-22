import pymongo
import os
import datetime
import io
import datetime
from bson import ObjectId
import pymongo
import gridfs

def connect_to_mongodb_atlas():
    DB_PASSWORD = os.getenv("DB_PASSWORD")
    
    # 建立連接
    try:
        # 使用 ServerApi 版本 1
        client = pymongo.MongoClient(f"mongodb+srv://Koying:{DB_PASSWORD}@cluster.uohrrhq.mongodb.net/?retryWrites=true&w=majority&appName=Cluster")

        
        # 測試連接是否成功
        client.admin.command('ping')
        print("成功連接到 MongoDB Atlas!")
        client.list_database_names()
        
        return client
        
    except Exception as e:
        print(f"連接到 MongoDB Atlas 時發生錯誤: {e}")
        return None

def get_db_and_collection(client, user_id: str, note_id: str):
    # 取得資料庫 (以 user_id 為名)
    db = client[f"{user_id}"]  # 加上前綴避免與系統資料庫名稱衝突
    
    # 取得集合 (以 note_id 為名)
    collection = db[f"{note_id}"]
    
    return db, collection


def clear_diary_collection(client, user_id, note_id):
    """
    清除指定用戶的日記集合中的所有資料。
    """
    
    # 取得資料庫和集合
    db = client[user_id]
    collection = db[note_id]
    
    result = collection.delete_many({})
    # 刪除所有資料
    print(f"刪除 {result.deleted_count} 筆日記資料")
    
def get_db_and_collection(client, user_id: str, note_id: str):
    # 取得資料庫 (以 user_id 為名)
    db = client[f"{user_id}"]  # 加上前綴避免與系統資料庫名稱衝突
    
    # 取得集合 (以 note_id 為名)
    collection = db[f"{note_id}"]
    
    return db, collection

# 儲存音訊檔案到 MongoDB
async def save_audio_to_mongodb(
    client, 
    user_id: str, 
    note_id: str, 
    line_id: int, 
    audio_file,
    audio_content: bytes
):
    """
    將上傳的音訊檔案存儲到 MongoDB 中，使用 GridFS。
    """
    try:
        # 獲取使用者的資料庫
        db, _ = get_db_and_collection(client, user_id, note_id)
        
        # 使用 GridFS 存儲音訊檔案
        # fs = pymongo.gridfs.GridFS(db, collection="audio_files")
        fs = gridfs.GridFS(db, collection=note_id)
        
        # 準備檔案元資料
        metadata = {
            "user_id": user_id,
            "note_id": note_id,
            "line_id": line_id,
            "filename": audio_file.filename,
            "content_type": audio_file.content_type,
            "upload_date": datetime.datetime.now(),
            "file_size": len(audio_content)
        }
        
        # 將檔案內容轉換為 BytesIO 物件
        file_data = io.BytesIO(audio_content)
        
        # 將檔案存儲到 GridFS
        file_id = fs.put(
            file_data, 
            filename=audio_file.filename,
            content_type=audio_file.content_type,
            metadata=metadata
        )
        
        print(f"音訊檔案已成功存儲到 MongoDB，檔案 ID: {file_id}")
        return str(file_id)
        
    except Exception as e:
        print(f"存儲音訊檔案到 MongoDB 時發生錯誤: {e}")
        raise

# 儲存影片檔案到 MongoDB
async def save_video_to_mongodb(
    client, 
    user_id: str, 
    note_id: str, 
    line_id: int, 
    video_file,
    video_content: bytes
):
    """
    將上傳的影片檔案存儲到 MongoDB 中，使用 GridFS。
    """
    try:
        # 獲取使用者的資料庫
        db, _ = get_db_and_collection(client, user_id, note_id)
        
        # 使用 GridFS 存儲影片檔案
        fs = pymongo.gridfs.GridFS(db, collection="video_files")
        
        # 準備檔案元資料
        metadata = {
            "user_id": user_id,
            "note_id": note_id,
            "line_id": line_id,
            "filename": video_file.filename,
            "content_type": video_file.content_type,
            "upload_date": datetime.datetime.now(),
            "file_size": len(video_content)
        }
        
        # 將檔案內容轉換為 BytesIO 物件
        file_data = io.BytesIO(video_content)
        
        # 將檔案存儲到 GridFS
        file_id = fs.put(
            file_data, 
            filename=video_file.filename,
            content_type=video_file.content_type,
            metadata=metadata
        )
        
        print(f"影片檔案已成功存儲到 MongoDB，檔案 ID: {file_id}")
        return str(file_id)
        
    except Exception as e:
        print(f"存儲影片檔案到 MongoDB 時發生錯誤: {e}")
        raise

# 儲存日記條目到 MongoDB
async def save_diary_entry(
    client,
    user_id: str,
    note_id: str,
    line_id: int,
    entry_type: str,
    text: str = None,
    audio_file = None,
    audio_content = None,
    video_file = None,
    video_content = None
):
    """
    將日記條目儲存到 MongoDB。
    
    參數:
    - client: MongoDB 客戶端連接
    - user_id: 使用者 ID
    - note_id: 筆記 ID
    - line_id: 行號
    - entry_type: 條目類型
    - text: 文字內容 (可選)
    - audio_file: 音訊檔案 (可選)
    - audio_content: 音訊內容 (可選)
    - video_file: 影片檔案 (可選)
    - video_content: 影片內容 (可選)
    
    返回:
    - 儲存結果
    """
    try:
        # 獲取使用者的資料庫和筆記集合
        db, note_collection = get_db_and_collection(client, user_id, note_id)
        
        # 創建基本的筆記文檔
        note_item = {
            "line_id": line_id,
            "type": entry_type,
            "created_at": datetime.datetime.now(),
            "updated_at": datetime.datetime.now()
        }
        
        # 如果有文字內容，加入到文檔
        if text:
            note_item["text"] = text
        
        # 處理音訊檔案
        if audio_file and audio_content:
            audio_file_id = await save_audio_to_mongodb(
                client, 
                user_id, 
                note_id, 
                line_id, 
                audio_file, 
                audio_content
            )
            note_item["audio_file_id"] = audio_file_id
        
        # 處理影片檔案
        if video_file and video_content:
            video_file_id = await save_video_to_mongodb(
                client, 
                user_id, 
                note_id, 
                line_id, 
                video_file, 
                video_content
            )
            note_item["video_file_id"] = video_file_id
        
        # 將筆記文檔存儲到筆記集合中
        result = note_collection.update_one(
            {"line_id": line_id},
            {"$set": note_item},
            upsert=True
        )
        
        print(f"筆記文檔已存儲到 MongoDB，{'插入新文檔' if result.upserted_id else '更新現有文檔'}")
        
        return {
            "success": True,
            "note_id": note_id,
            "line_id": line_id,
            "type": entry_type,
            "has_text": text is not None,
            "has_audio": "audio_file_id" in note_item,
            "has_video": "video_file_id" in note_item
        }
        
    except Exception as e:
        print(f"儲存日記條目到 MongoDB 時發生錯誤: {e}")
        raise
    
        
async def get_content_from_note_id(client, user_id: str, note_id: str) -> str:
    """
    從指定的 user_id 和 note_id 的 MongoDB 資料庫中，獲取所有 type 為 'text' 的日記內容，
    並依照 line_id 排序後拼接成一個字串。
    
    參數:
    - client: MongoDB 客戶端連接
    - user_id: 使用者 ID
    - note_id: 筆記 ID
    
    返回:
    - 拼接後的完整文字內容
    """
    try:
        # 取得資料庫和集合
        db = client[f"{user_id}"]
        collection = db[f"{note_id}"]
        
        # 查詢所有 type == 'text' 的文件，並依 line_id 排序
        # 由於 PyMongo 的 cursor 不是 async iterable，所以使用同步方式查詢
        docs = list(collection.find({"type": "text"}).sort("line_id", 1))
        
        # 拼接所有 text 欄位
        texts = []
        for doc in docs:
            if "text" in doc:
                texts.append(doc["text"])
        
        # 將所有文字內容合併成一個字串
        full_text = "\n".join(texts)
        return full_text
    except Exception as e:
        print(f"取得日記內容時發生錯誤: {e}")
        return ""
