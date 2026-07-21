import os

from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

# データベースファイルの保存場所を指定
# 環境変数 DATABASE_URL があればそちらを優先
# 未設定の場合はプロジェクト直下に「todo.db」を作成
SQLALCHEMY_DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./todo.db")

# SQLite固有の接続設定（複数スレッドからのアクセスを許可）は、SQLite使用時のみ付与
connect_args = (
    {"check_same_thread": False}
    if SQLALCHEMY_DATABASE_URL.startswith("sqlite")
    else {}
)

# データベースへの接続エンジンを作成
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args=connect_args)

# データベースとやり取りする「セッション」のファクトリーを作成
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 後でデータベースのテーブル（モデル）を作るためのベースクラス
Base = declarative_base()


# 各APIリクエストごとにデータベース接続を開き、終わったら自動で閉じる仕組み（Dependency）
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()