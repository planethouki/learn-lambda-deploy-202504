import json
import datetime
import logging
import os
from functions.symbol_transaction import process_transaction

# ロギングの設定
logger = logging.getLogger()
logger.setLevel(logging.INFO)

def handler(event, context):
    """
    Hoge Lambda関数
    Symbol SDKを使用してトランザクションを生成、送信します
    """
    try:
        # トランザクション処理の実行
        result = process_transaction()
        
        # レスポンスの作成
        if result['success']:
            response_body = {
                "message": result['message'],
                "function": "hoge",
                "transaction_hash": result.get('transaction_hash', ''),
                "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
            
            response = {
                "statusCode": 200,
                "headers": {
                    "Content-Type": "application/json"
                },
                "body": json.dumps(response_body, ensure_ascii=False)
            }
        else:
            raise Exception(result.get('error', '不明なエラー'))
        
    except Exception as e:
        logger.error(f"エラーが発生しました: {str(e)}")
        
        error_body = {
            "message": "トランザクション送信中にエラーが発生しました",
            "error": str(e),
            "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        
        response = {
            "statusCode": 500,
            "headers": {
                "Content-Type": "application/json"
            },
            "body": json.dumps(error_body, ensure_ascii=False)
        }
    
    return response
