import json
import datetime
import random

def handler(event, context):
    """
    Hoge Lambda関数
    ランダムな数値とともにメッセージを返します
    """
    current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    random_number = random.randint(1, 100)
    
    body = {
        "message": "Hogeからのメッセージです！",
        "function": "hoge",
        "random_number": random_number,
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
