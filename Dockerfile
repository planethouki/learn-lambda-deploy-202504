FROM public.ecr.aws/lambda/python:3.11

# 作業ディレクトリを設定
WORKDIR ${LAMBDA_TASK_ROOT}

# 依存関係ファイルをコピー
COPY requirements.txt .

# 依存関係のインストール
RUN pip install -r requirements.txt

# 関数コードをコピー
COPY functions/ ./functions/

# Lambda関数ハンドラを設定
# 注: 実際のハンドラはserverless.ymlで設定されるため、ここではダミーを設定
CMD ["functions/hello.handler"]
