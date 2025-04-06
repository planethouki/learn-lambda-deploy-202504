#!/usr/bin/env python
"""
Symbolトランザクションをローカルから実行するためのスクリプト
"""
import argparse
import json
import logging
import asyncio
import time
import math
from symbol_transaction import process_transaction, process_transaction_sync

# ロギングの設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def process_with_throttling(semaphore, rate_per_second, i):
    """スロットリングを適用してトランザクションを処理する関数"""
    async with semaphore:
        logger.info(f"トランザクション {i+1} を処理中...")
        result = await process_transaction()
        
        # レート制限に基づいて待機時間を計算
        if rate_per_second > 0:
            wait_time = 1.0 / rate_per_second
            logger.debug(f"次のリクエストまで {wait_time:.2f} 秒待機")
            await asyncio.sleep(wait_time)
        
        return result

async def run_transactions_async(count=10, concurrency=10, rate_per_second=0):
    """トランザクションを非同期で実行する関数（スロットリング機能付き）"""
    logger.info(f"Symbolトランザクションを非同期で実行します（同時実行数: {concurrency}, レート: {rate_per_second if rate_per_second > 0 else '無制限'}/秒）...")
    start_time = time.time()
    
    # 同時実行数を制限するセマフォを作成
    semaphore = asyncio.Semaphore(concurrency)
    
    # トランザクションタスクを作成
    tasks = [
        process_with_throttling(semaphore, rate_per_second, i)
        for i in range(count)
    ]
    
    # タスクを実行
    results = await asyncio.gather(*tasks)
    
    end_time = time.time()
    total_time = end_time - start_time
    logger.info(f"非同期処理完了: {total_time:.2f}秒")
    logger.info(f"平均処理速度: {count / total_time:.2f} トランザクション/秒")
    
    # 最後のトランザクションの結果を返す
    return results[-1] if results else None

def run_transactions_sync(count=10):
    """トランザクションを同期的に実行する関数"""
    logger.info(f"Symbolトランザクションを同期的に実行します（{count}件）...")
    start_time = time.time()
    
    result = None
    # トランザクションを同期的に実行
    for i in range(count):
        logger.info(f"トランザクション {i+1} を処理中...")
        result = process_transaction_sync()
    
    end_time = time.time()
    total_time = end_time - start_time
    logger.info(f"同期処理完了: {total_time:.2f}秒")
    logger.info(f"平均処理速度: {count / total_time:.2f} トランザクション/秒")
    
    return result

def main():
    """メイン関数"""
    # コマンドライン引数の解析
    parser = argparse.ArgumentParser(description='Symbolトランザクションを実行するスクリプト')
    parser.add_argument('--sync', action='store_true', help='同期モードで実行する')
    parser.add_argument('--count', type=int, default=100, help='実行するトランザクションの数（デフォルト: 100）')
    parser.add_argument('--concurrency', type=int, default=10, help='同時実行数（デフォルト: 10）')
    parser.add_argument('--rate', type=float, default=60, help='1秒あたりの最大リクエスト数（デフォルト: 60）')
    args = parser.parse_args()
    
    if args.sync:
        # 同期モードで実行
        result = run_transactions_sync(args.count)
    else:
        # 非同期モードで実行
        result = asyncio.run(run_transactions_async(
            count=args.count,
            concurrency=args.concurrency,
            rate_per_second=args.rate
        ))
    
    # 結果の表示
    if result and result.get('success'):
        logger.info("トランザクションが正常に送信されました")
        logger.info(f"トランザクションハッシュ: {result.get('transaction_hash', '')}")
        logger.info(f"ステータス: {result.get('status', '')}")
    else:
        error_msg = result.get('error', '不明なエラー') if result else '結果がありません'
        logger.error(f"エラーが発生しました: {error_msg}")
    
    # 結果をJSON形式で出力
    if result:
        print(json.dumps(result, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    main()
