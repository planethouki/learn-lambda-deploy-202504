import json
import datetime

def handler(event, context):
    """
    Hello Lambda関数
    シンプルな挨拶メッセージを返します
    """
    current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    body = {
        "message": "こんにちは！AWS Lambda関数からのメッセージです。",
        "function": "hello",
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
