import os
import sys
import hmac
from fastapi import Depends, FastAPI, HTTPException, Security, status
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.security import APIKeyHeader
from sqlalchemy.orm import Session
from pydantic import BaseModel
from dotenv import load_dotenv

import models
from database import engine, get_db



models.Base.metadata.create_all(bind=engine)

# ドキュメント機能をオフ
app = FastAPI(docs_url=None, redoc_url=None, openapi_url=None)

# 秘密の合言葉
load_dotenv() # ローカル開発時は .env ファイルを読み込む
API_KEY = os.getenv("TODO_API_KEY")
if not API_KEY:
    print("エラー: 環境変数 TODO_API_KEY が設定されていません。")
    sys.exit(1)
API_KEY_NAME = "X-API-KEY"

# リクエストのヘッダーから「X-API-KEY」を探す設定
api_key_header = APIKeyHeader(name=API_KEY_NAME, auto_error=False)


# 合言葉が正しいかチェックする関数
def verify_api_key(header_key: str = Security(api_key_header)):
    if not header_key or not hmac.compare_digest(header_key, API_KEY):
        raise HTTPException(status_code=401, detail="認証エラー")
    return header_key


app.mount("/static", StaticFiles(directory="static"), name="static")


class TodoCreate(BaseModel):
    title: str
    done: bool = False


class TodoResponse(BaseModel):
    id: int
    title: str
    done: bool

    class Config:
        from_attributes = True


# HTML画面の表示だけは、全員に見せても中身（Todoデータ）は空なので認証不要にします
@app.get("/")
def read_index():
    return FileResponse("static/index.html")


# --- APIエンドポイント（Depends(verify_api_key) を追加して保護） ---


# 取得・作成・更新・削除のすべてに認証を義務付けます
@app.get(
    "/todos",
    response_model=list[TodoResponse],
    dependencies=[Depends(verify_api_key)],
)
def get_todos(db: Session = Depends(get_db)):
    return db.query(models.DBTodo).all()


@app.post(
    "/todos", response_model=TodoResponse, dependencies=[Depends(verify_api_key)]
)
def create_todo(todo: TodoCreate, db: Session = Depends(get_db)):
    db_todo = models.DBTodo(title=todo.title, done=todo.done)
    db.add(db_todo)
    db.commit()
    db.refresh(db_todo)
    return db_todo

@app.put(
    "/todos/{todo_id}",
    response_model=TodoResponse,
    dependencies=[Depends(verify_api_key)],
)
def update_todo(
    todo_id: int, updated_todo: TodoCreate, db: Session = Depends(get_db)
):
    db_todo = (
        db.query(models.DBTodo).filter(models.DBTodo.id == todo_id).first()
    )
    if db_todo is None:
        raise HTTPException(
            status_code=404, detail="指定されたIDのTodoが見つかりません。"
        )
    db_todo.title = updated_todo.title
    db_todo.done = updated_todo.done
    db.commit()
    db.refresh(db_todo)
    return db_todo


@app.delete("/todos/{todo_id}", dependencies=[Depends(verify_api_key)])
def delete_todo(todo_id: int, db: Session = Depends(get_db)):
    db_todo = (
        db.query(models.DBTodo).filter(models.DBTodo.id == todo_id).first()
    )
    if db_todo is None:
        raise HTTPException(
            status_code=404, detail="指定されたIDのTodoが見つかりません。"
        )
    db.delete(db_todo)
    db.commit()
    return {"message": f"ID {todo_id} のTodoを削除しました。"}

# エクスポート用：すべてのTodoデータをJSON配列としてエクスポートする
@app.get("/todos/export", dependencies=[Depends(verify_api_key)])
def export_todos(db: Session = Depends(get_db)):
    # データベースの全Todoを取得
    todos = db.query(models.DBTodo).all()
    
    # 外部保存用にシンプルなリスト形式に変換
    return [{"title": todo.title, "done": todo.done} for todo in todos]


# インポート用：外部のJSONデータをデータベースに一括インポート（読み込み）する
@app.post("/todos/import", dependencies=[Depends(verify_api_key)])
def import_todos(todos: list[TodoCreate], db: Session = Depends(get_db)):
    # 安全のため、一度現在のデータベースのTodosをすべてクリアします（重複防止）
    db.query(models.DBTodo).delete()
    
    # 送られてきたJSONリストをデータベースに一括登録
    for item in todos:
        db_todo = models.DBTodo(title=item.title, done=item.done)
        db.add(db_todo)
        
    db.commit()
    return {"message": f"{len(todos)}個のTodoを正常にインポートしました。"}