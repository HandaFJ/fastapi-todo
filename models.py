from sqlalchemy import Boolean, Column, Integer, String
from database import Base


# データベースの「todos」テーブルの構造を定義します
class DBTodo(Base):
    __tablename__ = "todos"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True)
    done = Column(Boolean, default=False)