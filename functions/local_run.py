#!/usr/bin/env python
"""
Symbolトランザクションをローカルから実行するためのスクリプト
"""
import argparse
import json
import logging
from symbol_transaction import process_transaction

# ロギングの設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def main():
    """メイン関数"""
    # トランザクション処理の実行
    logger.info("Symbolトランザクションを実行します...")
    result = process_transaction()
    
    # 結果の表示
    if result['success']:
        logger.info("トランザクションが正常に送信されました")
        logger.info(f"トランザクションハッシュ: {result.get('transaction_hash', '')}")
        logger.info(f"ステータス: {result.get('status', '')}")
    else:
        logger.error(f"エラーが発生しました: {result.get('error', '不明なエラー')}")
    
    # 結果をJSON形式で出力
    print(json.dumps(result, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    main()
