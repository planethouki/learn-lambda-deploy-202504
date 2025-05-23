import json
import logging
import os
import time
import asyncio
from dotenv import load_dotenv
from symbolchain.CryptoTypes import PrivateKey
from symbolchain.symbol.KeyPair import KeyPair
from symbolchain.facade.SymbolFacade import SymbolFacade
from symbolchain.symbol.Network import Address
from symbolchain.sc import Amount
import aiohttp
import requests
import secrets

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
    if not symbol_recipient_address:
        raise ValueError("SYMBOL_RECIPIENT_ADDRESSが設定されていません")
    if not symbol_mosaic_id:
        raise ValueError("SYMBOL_MOSAIC_IDが設定されていないか、不正な値です")
    
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
    
    # Symbolファサードの作成
    sym_facade = SymbolFacade(network_type)

    deadline_timestamp: int = sym_facade.now().add_hours(2).timestamp
    
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
    })

    transaction.fee = Amount(100 * transaction.size)
    
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

async def announce_transaction(config, transaction_data):
    """トランザクションをネットワークにアナウンスする関数（非同期版）"""
    try:
        # HTTPリクエストを使用してトランザクションをアナウンス
        announce_url = f"{config['node_url']}/transactions"
        headers = {'Content-Type': 'application/json'}
        
        async with aiohttp.ClientSession() as session:
            async with session.put(announce_url, headers=headers, data=transaction_data['payload']) as response:
                response_text = await response.text()
                
                if response.status == 202:
                    logger.info("トランザクションが正常にアナウンスされました")
                    result = {
                        "transaction_hash": str(transaction_data['hash']),
                        "status": "announced"
                    }
                else:
                    logger.error(f"トランザクションのアナウンスに失敗しました: {response_text}")
                    result = {
                        "transaction_hash": str(transaction_data['hash']),
                        "status": "failed",
                        "error": response_text
                    }
    
    except Exception as e:
        logger.error(f"トランザクションのアナウンス中にエラーが発生しました: {str(e)}")
        result = {
            "transaction_hash": str(transaction_data['hash']),
            "status": "error",
            "error": str(e)
        }
    
    return result

# 後方互換性のための同期版関数
def announce_transaction_sync(config, transaction_data):
    """トランザクションをネットワークにアナウンスする関数（同期版）"""
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

async def process_transaction():
    """トランザクションの処理を行う関数（非同期版）"""
    try:
        # 環境変数の読み込み
        config = load_environment()
        
        recipient_address = config['recipient_address']
        fixed_message = 'Symbolトランザクションのテストメッセージ'
        unixtime = int(time.time())
        message = f"{fixed_message} {unixtime}-{secrets.token_hex(3)}"
        amount = 1000
        
        # トランザクションの作成と署名
        transaction_data = create_transaction(config, recipient_address, message, amount)
        
        # トランザクションのアナウンス（非同期）
        result = await announce_transaction(config, transaction_data)
        
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

# 後方互換性のための同期版関数
def process_transaction_sync():
    """トランザクションの処理を行う関数（同期版）"""
    try:
        # 環境変数の読み込み
        config = load_environment()
        
        recipient_address = config['recipient_address']
        fixed_message = 'Symbolトランザクションのテストメッセージ'
        unixtime = int(time.time())
        message = f"{fixed_message} {unixtime}-{secrets.token_hex(3)}"
        amount = 1000
        
        # トランザクションの作成と署名
        transaction_data = create_transaction(config, recipient_address, message, amount)
        
        # トランザクションのアナウンス（同期）
        result = announce_transaction_sync(config, transaction_data)
        
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
