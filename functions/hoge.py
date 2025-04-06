import json
import datetime
import os
import logging
from dotenv import load_dotenv
from symbolchain.CryptoTypes import PrivateKey
from symbolchain.symbol.KeyPair import KeyPair
from symbolchain.facade.SymbolFacade import SymbolFacade
from symbolchain.symbol.TransactionFactory import TransactionFactory
from symbolchain.symbol.IdGenerator import generate_mosaic_id
from symbolchain.symbol.Network import Address

# ロギングの設定
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# 開発環境では.envファイルから環境変数を読み込む
# Lambda環境では環境変数が直接設定されるため、この処理はスキップされる
if os.path.exists('.env'):
    load_dotenv()

# 環境変数から設定を読み込む
SYMBOL_PRIVATE_KEY = os.environ.get('SYMBOL_PRIVATE_KEY')
SYMBOL_NODE_URL = os.environ.get('SYMBOL_NODE_URL')
SYMBOL_RECIPIENT_ADDRESS = os.environ.get('SYMBOL_RECIPIENT_ADDRESS')
SYMBOL_MOSAIC_ID = int(os.environ.get('SYMBOL_MOSAIC_ID'), 16)

# Symbolネットワークの設定
NETWORK_TYPE = 'testnet'

def handler(event, context):
    """
    Hoge Lambda関数
    Symbol SDKを使用してトランザクションを生成、送信します
    """
    try:
        # リクエストパラメータの取得
        body = {}
        if event.get('body'):
            body = json.loads(event['body'])
        
        # 送信先アドレス（リクエストから取得するか、デフォルト値を使用）
        recipient_address_str = body.get('recipient_address', SYMBOL_RECIPIENT_ADDRESS)
        recipient_address = Address(recipient_address_str)
        
        # 送信するメッセージ（リクエストから取得するか、デフォルト値を使用）
        message = body.get('message', 'Symbolトランザクションのテストメッセージ')
        
        # 送信するXYMの量（リクエストから取得するか、デフォルト値を使用）
        amount = int(body.get('amount', 1000))  # マイクロXYM単位（1 XYM = 1,000,000 マイクロXYM）
        
        # トランザクション生成と送信
        result = create_and_announce_transaction(recipient_address, message, amount)
        
        # レスポンスの作成
        response_body = {
            "message": "トランザクションが正常に送信されました",
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

def create_and_announce_transaction(recipient_address, message, amount):
    """
    トランザクションを生成し、ネットワークにアナウンスする関数
    
    Args:
        recipient_address: 送信先アドレス
        message: 送信するメッセージ
        amount: 送信するXYMの量（マイクロXYM単位）
        
    Returns:
        dict: トランザクション結果
    """
    # 秘密鍵が設定されていない場合はエラー
    if not SYMBOL_PRIVATE_KEY:
        raise ValueError("SYMBOL_PRIVATE_KEYが設定されていません")
    
    sym_facade = SymbolFacade(NETWORK_TYPE)
    
    # 秘密鍵からキーペアを生成
    key_pair = KeyPair(PrivateKey(SYMBOL_PRIVATE_KEY))
    
    # トランザクションファクトリの作成
    factory = sym_facade.transaction_factory
    
    # トランザクションの作成
    transaction = factory.create({
        'type': 'transfer_transaction_v1',
        'signer_public_key': key_pair.public_key,
        'recipient_address': recipient_address,
        'mosaics': [{'mosaic_id': SYMBOL_MOSAIC_ID, 'amount': amount}],
        'message': bytes(1) + message.encode('utf8'),
        'fee': 30000
    })
    
    # トランザクションの署名
    signature = sym_facade.sign_transaction(key_pair, transaction)
    
    # 署名済みトランザクションの作成
    signed_transaction = factory.attach_signature(transaction, signature)
    
    # トランザクションのペイロード（16進数）
    payload = sym_facade.transaction_factory.attach_signature(transaction, signature)
    
    # トランザクションのハッシュ
    transaction_hash = sym_facade.hash_transaction(transaction)
    
    logger.info(f"トランザクションを送信します: {transaction_hash}")
    
    # トランザクションのアナウンス
    try:
        # HTTPリクエストを使用してトランザクションをアナウンス
        import requests
        
        announce_url = f"{SYMBOL_NODE_URL}/transactions"
        headers = {'Content-Type': 'application/json'}
        
        response = requests.put(announce_url, headers=headers, data=payload)
        
        if response.status_code == 202:
            logger.info("トランザクションが正常にアナウンスされました")
            return {
                "transaction_hash": str(transaction_hash),
                "status": "announced"
            }
        else:
            logger.error(f"トランザクションのアナウンスに失敗しました: {response.text}")
            return {
                "transaction_hash": str(transaction_hash),
                "status": "failed",
                "error": response.text
            }
    
    except Exception as e:
        logger.error(f"トランザクションのアナウンス中にエラーが発生しました: {str(e)}")
        return {
            "transaction_hash": tr(transaction_hash),
            "status": "error",
            "error": str(e)
        }
