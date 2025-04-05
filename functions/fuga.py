import json
import datetime
import uuid

def handler(event, context):
    """
    Fuga Lambda関数
    ユニークIDとともにメッセージを返します
    """
    current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    unique_id = str(uuid.uuid4())
    
    body = {
        "message": "Fugaが応答しました！",
        "function": "fuga",
        "unique_id": unique_id,
        "timestamp": current_time
    }
    
    response = {
        "statusCode": 200,
        "headers": {
            "Content-Type": "application/json"
        },
        "body": json.dumps(body, ensure_ascii=False)
    }
    
    return response
