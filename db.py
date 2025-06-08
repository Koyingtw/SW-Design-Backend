import pymongo
import os
import datetime
import io
import datetime
from bson import ObjectId
import pymongo
import gridfs
import base64

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

async def save_image_to_mongodb(
    client, 
    user_id: str, 
    note_id: str, 
    line_id: int, 
    image_file,
    image_content: bytes
):
    """
    將上傳的圖片檔案存儲到 MongoDB 中，使用 GridFS。
    """
    try:
        # 獲取使用者的資料庫
        db, _ = get_db_and_collection(client, user_id, note_id)
        
        # 使用 GridFS 存儲音訊檔案
        fs = gridfs.GridFS(db, collection=note_id)
        
        # 準備檔案元資料
        metadata = {
            "user_id": user_id,
            "note_id": note_id,
            "line_id": line_id,
            "filename": image_file.filename,
            "content_type": image_file.content_type,
            "upload_date": datetime.datetime.now(),
            "file_size": len(image_content)
        }
        
        # 將檔案內容轉換為 BytesIO 物件
        file_data = io.BytesIO(image_content)
        
        # 將檔案存儲到 GridFS
        file_id = fs.put(
            file_data, 
            filename=image_file.filename,
            content_type=image_file.content_type,
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
    image_file = None,
    image_content = None,
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
        
        # 處理圖片檔案
        if image_file and image_content:
            image_file_id = await save_image_to_mongodb(
                client, 
                user_id, 
                note_id, 
                line_id, 
                image_file, 
                image_content
            )
            note_item["image_file_id"] = image_file_id
        
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
    
# 在指定使用者的 note_list 集合中加入新的 note_id
async def add_note_id_to_note_list(client, user_id: str, note_id: str, hashtags: list[str] = None):
    """
    在指定使用者的 note_list 集合中加入新的 note_id 作為獨立文檔
    
    參數:
    - client: MongoDB 客戶端連接
    - user_id: 使用者 ID
    - note_id: 要加入的筆記 ID
    - hashtags: 標籤列表（可選）
    
    返回:
    - 操作結果
    """
    try:
        # 獲取使用者的資料庫
        db = client[user_id]
        collection = db['note_list']
        
        # 準備要插入的文檔
        note_entry = {
            "note_id": note_id,
            "hashtags": hashtags if hashtags is not None else [],
            "updated_at": datetime.datetime.now()
        }
        
        # 使用 update_one 並使用 upsert 確保不重複加入
        result = collection.update_one(
            {"note_id": note_id},  # 查詢條件：根據 note_id 查找
            {
                "$set": note_entry,
                "$setOnInsert": {"created_at": datetime.datetime.now()}  # 只在插入時設定 created_at
            },
            upsert=True  # 如果文件不存在則創建
        )
        
        if result.upserted_id:
            print(f"成功新增 note_id: {note_id} 到 note_list")
        else:
            print(f"成功更新 note_id: {note_id} 的資料")
            
        return {
            "success": True,
            "note_id": note_id,
            "modified_count": result.modified_count,
            "upserted_id": result.upserted_id,
            "is_new": result.upserted_id is not None
        }
        
    except Exception as e:
        print(f"更新 note_list 時發生錯誤: {e}")
        return {
            "success": False,
            "error": str(e)
        }

async def delete_note_from_note_list(client, user_id: str, note_id: str):
    """
    從指定使用者的 note_list 集合中刪除指定的 note_id
    
    參數:
    - client: MongoDB 客戶端連接
    - user_id: 使用者 ID
    - note_id: 要刪除的筆記 ID
    
    返回:
    - 操作結果
    """
    try:
        # 獲取使用者的資料庫
        db = client[user_id]
        collection = db['note_list']
        
        # 刪除指定 note_id 的文檔
        result = collection.delete_one({"note_id": note_id})
        
        collection = db[note_id]
        collection.drop()
        
        if result.deleted_count > 0:
            print(f"成功刪除 note_id: {note_id} 從 note_list")
            return {"success": True, "note_id": note_id}
        else:
            print(f"找不到 note_id: {note_id} 在 note_list 中")
            return {"success": False, "error": "Note not found", "note_id": note_id}
        
            
    except Exception as e:
        print(f"刪除筆記時發生錯誤: {e}")
        return {"success": False, "error": str(e), "note_id": note_id}
            
    except Exception as e:
        print(f"刪除筆記時發生錯誤: {e}")
        return {"success": False, "error": str(e), "note_id": note_id}

async def get_sorted_note_list(client, user_id: str) -> list[str]:
    """
    從指定使用者的 note_list 集合中獲取所有 note_id，並按順序排序後回傳
    
    參數:
    - client: MongoDB 客戶端連接
    - user_id: 使用者 ID
    
    返回:
    - 排序後的 note_id 列表
    """
    try:
        # 獲取使用者的資料庫
        db = client[user_id]
        collection = db['note_list']
        
        # 查詢所有文檔，只取得 note_id 欄位
        cursor = collection.find({}, {"note_id": 1, "_id": 0}).sort("note_id", 1)
        
        # 提取所有 note_id
        note_ids = [doc["note_id"] for doc in cursor]
        
        print(f"成功獲取使用者 {user_id} 的 {len(note_ids)} 個筆記")
        return note_ids
        
    except Exception as e:
        print(f"獲取 note_list 時發生錯誤: {e}")
        return []
        
async def get_content_from_note_id(client, user_id: str, note_id: str) -> dict[str, any]:
    """
    從 MongoDB 中獲取指定筆記的所有內容，包括文字、音訊和影片。
    
    參數:
    - client: MongoDB 客戶端連接
    - user_id: 使用者 ID
    - note_id: 筆記 ID
    
    返回:
    - 包含筆記所有內容的 JSON 格式資料
    """
    try:
        # 獲取使用者的資料庫和筆記集合
        db = client[f"{user_id}"]
        note_collection = db[f"{note_id}"]
        
        # 查詢所有筆記項目，並按 line_id 排序
        cursor = note_collection.find().sort("line_id", 1)
        
        # 將游標轉換為列表
        items = []
        
        for doc in cursor:
            # 建立基本項目資訊
            item = {
                "line_id": doc.get("line_id", 0),
                "type": doc.get("type", "unknown"),
                "created_at": doc.get("created_at", datetime.datetime.now()).isoformat(),
                "updated_at": doc.get("updated_at", datetime.datetime.now()).isoformat()
            }
            
            # 添加文字內容（如果有）
            if "text" in doc:
                item["text"] = doc["text"]
            
            # 處理音訊檔案
            if "audio_file_id" in doc and doc["type"] == "audio":
                audio_file_id = doc["audio_file_id"]
                
                # 從 note_id.chunks 集合中獲取所有相關的 chunks
                chunks_collection = db[f"{note_id}.chunks"]
                chunks = list(chunks_collection.find({"files_id": ObjectId(audio_file_id)}).sort("n", 1))
                
                if chunks:
                    # 拼接所有 chunks 的二進制數據
                    audio_data = b''
                    for chunk in chunks:
                        try:
                            # 檢查不同的 chunk 資料結構
                            chunk_binary_data = None
                            
                            # 方法 1: 檢查是否有 data.binary.base64 結構
                            if "data" in chunk and isinstance(chunk["data"], dict) and "binary" in chunk["data"]:
                                if isinstance(chunk["data"]["binary"], dict) and "base64" in chunk["data"]["binary"]:
                                    chunk_binary_data = chunk["data"]["binary"]["base64"]
                                elif isinstance(chunk["data"]["binary"], str):
                                    chunk_binary_data = chunk["data"]["binary"]
                            
                            # 方法 2: 檢查是否直接有 data 欄位包含 base64 字串
                            elif "data" in chunk and isinstance(chunk["data"], str):
                                chunk_binary_data = chunk["data"]
                            
                            # 方法 3: 檢查是否有其他可能的結構
                            elif "data" in chunk and hasattr(chunk["data"], 'decode'):
                                # 如果 data 是 bytes 類型，直接使用
                                audio_data += chunk["data"]
                                continue
                            
                            # 如果找到了 base64 資料，進行解碼
                            if chunk_binary_data:
                                # 確保是字串類型
                                if isinstance(chunk_binary_data, bytes):
                                    chunk_binary_data = chunk_binary_data.decode('utf-8')
                                
                                # 從 base64 轉換回二進制數據
                                chunk_data = base64.b64decode(chunk_binary_data)
                                audio_data += chunk_data
                            else:
                                print(f"警告：無法解析 chunk 資料結構: {chunk}")
                                
                        except Exception as chunk_error:
                            print(f"處理 chunk 時發生錯誤: {chunk_error}")
                            print(f"Chunk 內容: {chunk}")
                            continue
                    
                    # 獲取檔案的元資料
                    files_collection = db[f"{note_id}.files"]
                    file_metadata = files_collection.find_one({"_id": ObjectId(audio_file_id)})
                    
                    if file_metadata:
                        item["audio_data"] = base64.b64encode(audio_data).decode('utf-8')  # 轉換為 base64 字串以便 JSON 序列化
                        item["audio_filename"] = file_metadata.get("filename", "audio.wav")
                        item["audio_content_type"] = file_metadata.get("contentType", "audio/wav")
                        item["audio_size"] = len(audio_data)
                    else:
                        # 如果找不到元資料，仍然返回數據但使用默認值
                        item["audio_data"] = base64.b64encode(audio_data).decode('utf-8')
                        item["audio_filename"] = "audio.wav"
                        item["audio_content_type"] = "audio/wav"
                        item["audio_size"] = len(audio_data)
            
            # 處理圖片檔案（類似的邏輯）
            if "image_file_id" in doc and doc["type"] == "image":
                image_file_id = doc["image_file_id"]
                
                # 從 note_id.chunks 集合中獲取所有相關的 chunks
                chunks_collection = db[f"{note_id}.chunks"]
                chunks = list(chunks_collection.find({"files_id": ObjectId(image_file_id)}).sort("n", 1))
                
                if chunks:
                    # 拼接所有 chunks 的二進制數據
                    image_data = b''
                    for chunk in chunks:
                        try:
                            # 檢查不同的 chunk 資料結構
                            chunk_binary_data = None
                            
                            # 方法 1: 檢查是否有 data.binary.base64 結構
                            if "data" in chunk and isinstance(chunk["data"], dict) and "binary" in chunk["data"]:
                                if isinstance(chunk["data"]["binary"], dict) and "base64" in chunk["data"]["binary"]:
                                    chunk_binary_data = chunk["data"]["binary"]["base64"]
                                elif isinstance(chunk["data"]["binary"], str):
                                    chunk_binary_data = chunk["data"]["binary"]
                            
                            # 方法 2: 檢查是否直接有 data 欄位包含 base64 字串
                            elif "data" in chunk and isinstance(chunk["data"], str):
                                chunk_binary_data = chunk["data"]
                            
                            # 方法 3: 檢查是否有其他可能的結構
                            elif "data" in chunk and hasattr(chunk["data"], 'decode'):
                                # 如果 data 是 bytes 類型，直接使用
                                image_data += chunk["data"]
                                continue
                            
                            # 如果找到了 base64 資料，進行解碼
                            if chunk_binary_data:
                                # 確保是字串類型
                                if isinstance(chunk_binary_data, bytes):
                                    chunk_binary_data = chunk_binary_data.decode('utf-8')
                                
                                # 從 base64 轉換回二進制數據
                                chunk_data = base64.b64decode(chunk_binary_data)
                                image_data += chunk_data
                            else:
                                print(f"警告：無法解析 chunk 資料結構: {chunk}")
                                
                        except Exception as chunk_error:
                            print(f"處理 chunk 時發生錯誤: {chunk_error}")
                            print(f"Chunk 內容: {chunk}")
                            continue
                    # 獲取檔案的元資料
                    files_collection = db[f"{note_id}.files"]
                    file_metadata = files_collection.find_one({"_id": ObjectId(image_file_id)})
                    if file_metadata:
                        item["image_data"] = base64.b64encode(image_data).decode('utf-8')
                        item["image_filename"] = file_metadata.get("filename", "image.jpg")
                        item["image_content_type"] = file_metadata.get("contentType", "image/jpeg")
                        item["image_size"] = len(image_data)
                    else:
                        # 如果找不到元資料，仍然返回數據但使用默認值
                        item["image_data"] = base64.b64encode(image_data).decode('utf-8')
                        item["image_filename"] = "image.jpg"
                        item["image_content_type"] = "image/jpeg"
                        item["image_size"] = len(image_data)
            
            # 處理影片檔案（類似的邏輯）
            if "video_file_id" in doc and doc["type"] == "video":
                video_file_id = doc["video_file_id"]
                
                # 從 note_id.chunks 集合中獲取所有相關的 chunks
                chunks_collection = db[f"{note_id}.chunks"]
                chunks = list(chunks_collection.find({"files_id": ObjectId(video_file_id)}).sort("n", 1))
                
                if chunks:
                    # 拼接所有 chunks 的二進制數據
                    video_data = b''
                    for chunk in chunks:
                        try:
                            # 檢查不同的 chunk 資料結構
                            chunk_binary_data = None
                            
                            # 方法 1: 檢查是否有 data.binary.base64 結構
                            if "data" in chunk and isinstance(chunk["data"], dict) and "binary" in chunk["data"]:
                                if isinstance(chunk["data"]["binary"], dict) and "base64" in chunk["data"]["binary"]:
                                    chunk_binary_data = chunk["data"]["binary"]["base64"]
                                elif isinstance(chunk["data"]["binary"], str):
                                    chunk_binary_data = chunk["data"]["binary"]
                            
                            # 方法 2: 檢查是否直接有 data 欄位包含 base64 字串
                            elif "data" in chunk and isinstance(chunk["data"], str):
                                chunk_binary_data = chunk["data"]
                            
                            # 方法 3: 檢查是否有其他可能的結構
                            elif "data" in chunk and hasattr(chunk["data"], 'decode'):
                                # 如果 data 是 bytes 類型，直接使用
                                video_data += chunk["data"]
                                continue
                            
                            # 如果找到了 base64 資料，進行解碼
                            if chunk_binary_data:
                                # 確保是字串類型
                                if isinstance(chunk_binary_data, bytes):
                                    chunk_binary_data = chunk_binary_data.decode('utf-8')
                                
                                # 從 base64 轉換回二進制數據
                                chunk_data = base64.b64decode(chunk_binary_data)
                                video_data += chunk_data
                            else:
                                print(f"警告：無法解析 chunk 資料結構: {chunk}")
                                
                        except Exception as chunk_error:
                            print(f"處理 chunk 時發生錯誤: {chunk_error}")
                            print(f"Chunk 內容: {chunk}")
                            continue
                    
                    # 獲取檔案的元資料
                    files_collection = db[f"{note_id}.files"]
                    file_metadata = files_collection.find_one({"_id": ObjectId(video_file_id)})
                    
                    if file_metadata:
                        item["video_data"] = base64.b64encode(video_data).decode('utf-8')  # 轉換為 base64 字串以便 JSON 序列化
                        item["video_filename"] = file_metadata.get("filename", "video.mp4")
                        item["video_content_type"] = file_metadata.get("contentType", "video/mp4")
                        item["video_size"] = len(video_data)
                    else:
                        # 如果找不到元資料，仍然返回數據但使用默認值
                        item["video_data"] = base64.b64encode(video_data).decode('utf-8')
                        item["video_filename"] = "video.mp4"
                        item["video_content_type"] = "video/mp4"
                        item["video_size"] = len(video_data)
            
            # 將項目添加到列表中
            items.append(item)
        
        # 建立回應
        response = {
            "note_id": note_id,
            "user_id": user_id,
            "items": items,
            "total_items": len(items),
            "retrieved_at": datetime.datetime.now().isoformat()
        }
        
        return response
        
    except Exception as e:
        print(f"獲取筆記內容時發生錯誤: {e}")
        import traceback
        traceback.print_exc()  # 印出完整的錯誤追蹤
        # 返回錯誤資訊
        return {
            "error": True,
            "message": f"獲取筆記內容時發生錯誤: {str(e)}",
            "note_id": note_id,
            "user_id": user_id
        }

async def note_exists(client, user_id: str, note_id: str) -> bool:
    """
    檢查指定的筆記是否存在於 note_list 中
    
    參數:
    - client: MongoDB 客戶端連接
    - user_id: 使用者 ID
    - note_id: 筆記 ID
    
    返回:
    - 如果筆記存在返回 True，否則返回 False
    """
    try:
        db = client[user_id]
        collection = db['note_list']
        
        # 只檢查文檔是否存在，不需要獲取內容
        doc = collection.find_one({"note_id": note_id}, {"_id": 1})
        
        return doc is not None
        
    except Exception as e:
        print(f"檢查筆記存在性時發生錯誤: {e}")
        return False

async def get_note_hashtags(client, user_id: str, note_id: str) -> list[str]:
    """
    從指定使用者的 note_list 集合中獲取特定筆記的 hashtags
    
    參數:
    - client: MongoDB 客戶端連接
    - user_id: 使用者 ID
    - note_id: 筆記 ID
    
    返回:
    - hashtags 列表，如果找不到筆記則返回空列表
    """
    try:
        # 獲取使用者的資料庫
        db = client[user_id]
        collection = db['note_list']
        
        # 查詢指定 note_id 的文檔，只取得 hashtags 欄位
        doc = collection.find_one(
            {"note_id": note_id},
            {"hashtags": 1, "_id": 0}  # 只返回 hashtags 欄位，不返回 _id
        )
        
        if doc is None:
            print(f"找不到 note_id: {note_id} 在使用者 {user_id} 的 note_list 中")
            return []
        
        # 獲取 hashtags，如果不存在則返回空列表
        hashtags = doc.get("hashtags", [])
        
        print(f"成功獲取 note_id: {note_id} 的標籤: {hashtags}")
        return hashtags
        
    except Exception as e:
        print(f"獲取筆記標籤時發生錯誤: {e}")
        return []

async def update_note_hashtags(client, user_id: str, note_id: str, hashtags: list[str]):
    """
    更新指定筆記的 hashtags
    
    參數:
    - client: MongoDB 客戶端連接
    - user_id: 使用者 ID
    - note_id: 筆記 ID
    - hashtags: 新的標籤列表
    
    返回:
    - 操作結果字典
    """
    try:
        # 獲取使用者的資料庫
        db = client[user_id]
        collection = db['note_list']
        
        # 更新指定 note_id 的 hashtags
        result = collection.update_one(
            {"note_id": note_id},
            {
                "$set": {
                    "hashtags": hashtags,
                    "updated_at": datetime.datetime.now()
                }
            }
        )
        
        if result.matched_count == 0:
            print(f"找不到 note_id: {note_id} 在使用者 {user_id} 的 note_list 中")
            return {
                "success": False, 
                "error": "Note not found",
                "note_id": note_id,
                "user_id": user_id
            }
        
        print(f"成功更新 note_id: {note_id} 的標籤為: {hashtags}")
        return {
            "success": True,
            "note_id": note_id,
            "user_id": user_id,
            "hashtags": hashtags,
            "modified_count": result.modified_count,
            "updated_at": datetime.datetime.now().isoformat()
        }
        
    except Exception as e:
        print(f"更新標籤時發生錯誤: {e}")
        return {
            "success": False,
            "error": str(e),
            "note_id": note_id,
            "user_id": user_id
        }

async def fuzzy_search(client, user_id: str, note_ids: list[str], query: str) -> dict[str, list[str]]:
    """
    在 user_id 資料庫中，對所有 note_id 的集合進行模糊搜尋，找出 text 欄位包含 query 的文件，
    並以字典形式回傳，key 為 note_id，value 為符合條件的 text 列表。
    
    參數:
    - client: MongoDB 客戶端連接
    - user_id: 使用者 ID
    - note_ids: 要搜尋的筆記 ID 列表
    - query: 搜尋關鍵字
    
    返回:
    - 字典，key 為 note_id，value 為包含關鍵字的 text 列表
    """
    result = {}
    
    try:
        # 獲取使用者的資料庫
        db = client[user_id]
        
        # 遍歷每個 note_id
        for note_id in note_ids:
            collection = db[note_id]
            print(note_id)
            
            # 使用 $regex 進行模糊搜尋，忽略大小寫
            cursor = collection.find({
                "text": {"$regex": query, "$options": "i"},
                "type": "text"  # 只搜尋 type 為 text 的文件
            })
            
            # 提取符合條件的 text 內容
            texts = []
            for doc in cursor:
                if "text" in doc:
                    texts.append(doc["text"])
            
            # 如果找到符合條件的文字，加入結果
            if texts:
                result[note_id] = texts
        
        print(f"搜尋完成，在 {len(result)} 個筆記中找到包含 '{query}' 的內容")
        return result
        
    except Exception as e:
        print(f"模糊搜尋時發生錯誤: {e}")
        return {}

