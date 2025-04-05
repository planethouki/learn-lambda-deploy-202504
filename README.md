# AWS Lambda Learn

Python 3.11で実装されたAWS Lambda関数のサンプルプロジェクトです。Serverless Frameworkを使用してデプロイします。

## 概要

このプロジェクトには、3つのシンプルなLambda関数が含まれています：

1. **hello** - 基本的な挨拶メッセージを返します
2. **hoge** - ランダムな数値とともにメッセージを返します
3. **fuga** - ユニークIDとともにメッセージを返します

各関数はHTTP APIエンドポイントとして公開されます。

## 前提条件

- Node.js (v14以上)
- npm (v6以上)
- Python 3.11
- AWS CLI (設定済み)
- AWS認証情報（アクセスキーとシークレットキー）

## セットアップ

1. 依存関係をインストールします：

```bash
npm install
```

## デプロイ

AWS環境にデプロイするには：

```bash
npm run deploy
```

特定の関数だけをデプロイするには：

```bash
npm run deploy:function -- --function hello
```

## 削除

デプロイしたリソースを削除するには：

```bash
npm run remove
```

## エンドポイント

デプロイ後、以下のエンドポイントが利用可能になります：

- `GET /hello` - Hello関数
- `GET /hoge` - Hoge関数
- `GET /fuga` - Fuga関数

実際のURLはデプロイ後に表示されます。
