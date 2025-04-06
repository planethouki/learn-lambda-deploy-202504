import json
import logging
import os
from dotenv import load_dotenv
from symbolchain.CryptoTypes import PrivateKey
from symbolchain.symbol.KeyPair import KeyPair
from symbolchain.facade.SymbolFacade import SymbolFacade
from symbolchain.symbol.TransactionFactory import TransactionFactory
from symbolchain.symbol.Network import Address
import requests

# ロギングの設定
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# 環境変数の読み込み
def load_environment():
    """環境変数を読み込む関数"""
    # 開発環境では.envファイルから環境変数を読み込む
    if os.path.exists('.env'):
        load_dotenv()
    
    # 環境変数から設定を読み込む
    symbol_private_key = os.environ.get('SYMBOL_PRIVATE_KEY')
    symbol_node_url = os.environ.get('SYMBOL_NODE_URL')
    symbol_recipient_address = os.environ.get('SYMBOL_RECIPIENT_ADDRESS')
    symbol_mosaic_id = int(os.environ.get('SYMBOL_MOSAIC_ID', '0'), 16) if os.environ.get('SYMBOL_MOSAIC_ID') else None
    
    # 必須の環境変数が設定されているか確認
    if not symbol_private_key:
        raise ValueError("SYMBOL_PRIVATE_KEYが設定されていません")
    if not symbol_node_url:
        raise ValueError("SYMBOL_NODE_URLが設定されていません")
    
    return {
        'private_key': symbol_private_key,
        'node_url': symbol_node_url,
        'recipient_address': symbol_recipient_address,
        'mosaic_id': symbol_mosaic_id,
    }

def create_transaction(config, recipient_address_str, message, amount, network_type='testnet'):
    """トランザクションを作成して署名する関数"""
    # 送信先アドレスの変換
    recipient_address = Address(recipient_address_str)

    network_time = requests.get(f"{config['node_url']}/node/time").json()
    receive_timestamp: int = int(
        network_time["communicationTimestamps"]["receiveTimestamp"]
    )
    deadline_timestamp: int = receive_timestamp + (
        2 * 60 * 60 * 1000
    )  # 2時間後（ミリ秒単位）
    
    # Symbolファサードの作成
    sym_facade = SymbolFacade(network_type)
    
    # 秘密鍵からキーペアを生成
    key_pair = KeyPair(PrivateKey(config['private_key']))
    
    # トランザクションファクトリの作成
    factory = sym_facade.transaction_factory
    
    # トランザクションの作成
    transaction = factory.create({
        'type': 'transfer_transaction_v1',
        'signer_public_key': key_pair.public_key,
        'recipient_address': recipient_address,
        'mosaics': [{'mosaic_id': config['mosaic_id'], 'amount': amount}],
        'message': bytes(1) + message.encode('utf8'),
        "deadline": deadline_timestamp,
        'fee': 30000,
    })
    
    # トランザクションの署名
    signature = sym_facade.sign_transaction(key_pair, transaction)
    
    # 署名済みトランザクションの作成
    signed_transaction = factory.attach_signature(transaction, signature)
    
    # トランザクションのペイロード（16進数）
    payload = sym_facade.transaction_factory.attach_signature(transaction, signature)
    
    # トランザクションのハッシュ
    transaction_hash = sym_facade.hash_transaction(transaction)
    
    return {
        'transaction': transaction,
        'signature': signature,
        'payload': payload,
        'hash': transaction_hash
    }

def announce_transaction(config, transaction_data):
    """トランザクションをネットワークにアナウンスする関数"""
    try:
        # HTTPリクエストを使用してトランザクションをアナウンス
        announce_url = f"{config['node_url']}/transactions"
        headers = {'Content-Type': 'application/json'}
        
        response = requests.put(announce_url, headers=headers, data=transaction_data['payload'])
        
        if response.status_code == 202:
            logger.info("トランザクションが正常にアナウンスされました")
            result = {
                "transaction_hash": str(transaction_data['hash']),
                "status": "announced"
            }
        else:
            logger.error(f"トランザクションのアナウンスに失敗しました: {response.text}")
            result = {
                "transaction_hash": str(transaction_data['hash']),
                "status": "failed",
                "error": response.text
            }
    
    except Exception as e:
        logger.error(f"トランザクションのアナウンス中にエラーが発生しました: {str(e)}")
        result = {
            "transaction_hash": str(transaction_data['hash']),
            "status": "error",
            "error": str(e)
        }
    
    return result

def process_transaction(recipient_address=None, message=None, amount=None):
    """トランザクションの処理を行う関数"""
    try:
        # 環境変数の読み込み
        config = load_environment()
        
        # デフォルト値の設定
        recipient_address = recipient_address or config['recipient_address']
        message = message or 'Symbolトランザクションのテストメッセージ'
        amount = amount or 1000  # マイクロXYM単位（1 XYM = 1,000,000 マイクロXYM）
        
        # 送信先アドレスが設定されていない場合はエラー
        if not recipient_address:
            raise ValueError("送信先アドレスが設定されていません")
        
        # トランザクションの作成と署名
        transaction_data = create_transaction(config, recipient_address, message, amount)
        
        # トランザクションのアナウンス
        result = announce_transaction(config, transaction_data)
        
        return {
            "success": True,
            "message": "トランザクションが正常に送信されました",
            "transaction_hash": result.get('transaction_hash', ''),
            "status": result.get('status', '')
        }
        
    except Exception as e:
        logger.error(f"エラーが発生しました: {str(e)}")
        return {
            "success": False,
            "message": "トランザクション送信中にエラーが発生しました",
            "error": str(e)
        }
