FROM public.ecr.aws/lambda/python:3.11

# 作業ディレクトリを設定
WORKDIR ${LAMBDA_TASK_ROOT}

RUN yum install -y gcc make

# 依存関係ファイルをコピー（ビルドキャッシュを活用するため、コードより先にコピー）
COPY requirements.txt .

# 依存関係のインストール
RUN pip install -r requirements.txt --no-cache-dir

# 関数コードをコピー
COPY functions/ ./functions/

# Lambda関数ハンドラを設定
# 注: 実際のハンドラはserverless.ymlで設定されるため、ここではダミーを設定
CMD ["functions/hello.handler"]
