FROM python:3.12-slim

WORKDIR /app

# 依存関係だけ先にコピーしてレイヤーキャッシュを効かせる
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# アプリケーション本体をコピー（.env や todo.db は .dockerignore で除外）
COPY main.py database.py models.py ./
COPY static ./static

# SQLiteの永続化用ディレクトリ（docker-composeでvolumeをマウントする場所）
RUN mkdir -p /app/data

EXPOSE 8000

# 本番向けに fastapi run を使用（fastapi dev はホットリロード用の開発サーバー）
CMD ["fastapi", "run", "main.py", "--host", "0.0.0.0", "--port", "8000"]
