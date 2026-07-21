const API_URL = "/todos";
const STORAGE_KEY = "todo_backup_local";

// 【修正】順序を一番上に移動し、どこからでも安全に読み込めるようにしました
const KEY_STORAGE_NAME = "todo_api_key";

// 1. 新しいAPIキーを入力させる関数
function getNewApiKey() {
  const userInput = prompt("APIキー（合言葉）を入力してください:");
  if (userInput) {
    API_KEY = userInput;
    localStorage.setItem(KEY_STORAGE_NAME, API_KEY);
  } else {
    API_KEY = null;
  }
}

// 最初にブラウザの記憶からAPIキーを取得。なければ入力させる
let API_KEY = localStorage.getItem(KEY_STORAGE_NAME);
if (!API_KEY) {
  getNewApiKey();
}

// 2. Todoリストを取得
// isInitialLoad: ページ読み込み直後の呼び出しかどうか。
// 「サーバー空っぽ時の自動復元」は初回ロード時（＝サーバーのDBが消えていて復元が必要なケース）
// にのみ発動させ、削除操作などによる意図的な空状態と誤認しないようにする。
async function fetchTodos(isInitialLoad = false) {
  if (!API_KEY) {
    getNewApiKey();
    if (API_KEY) fetchTodos(isInitialLoad);
    return;
  }

  const response = await fetch(API_URL, {
    headers: {
      "X-API-KEY": API_KEY,
    },
  });

  // 401エラー（キー間違い）の時の処理
  if (response.status === 401) {
    alert("認証エラー: APIキーが正しくありません。再入力してください。");
    localStorage.removeItem(KEY_STORAGE_NAME); // 間違った記憶を消去
    getNewApiKey(); // 正しいキーを入力し直してもらう
    fetchTodos(isInitialLoad); // 新しいキーで再挑戦
    return;
  }

  if (!response.ok) return;
  const todos = await response.json();

  // サーバー空っぽ時の自動復元ロジック（初回ロード時のみ）
  if (todos.length === 0 && isInitialLoad) {
    const localBackup = localStorage.getItem(STORAGE_KEY);
    if (localBackup) {
      const parsedBackup = JSON.parse(localBackup);
      if (parsedBackup.length > 0) {
        await autoImportFromServer(parsedBackup);
        return;
      }
    }
  }

  // 画面描画
  // 画面描画
  const todoList = document.getElementById("todo-list");
  todoList.innerHTML = "";
  todos.forEach((todo) => {
    const li = document.createElement("li");
    const checkbox = document.createElement("input");
    checkbox.type = "checkbox";
    checkbox.checked = todo.done;
    checkbox.onchange = () => toggleTodo(todo.id, todo.title, checkbox.checked);

    const span = document.createElement("span");
    span.textContent = todo.title;
    // 【修正】todo.todo.done を todo.done に変更
    span.className = todo.done ? "completed" : "";

    const btn = document.createElement("button");
    btn.textContent = "削除";
    btn.onclick = () => deleteTodo(todo.id);
    btn.className = "delete-btn"; // スタイルを適用

    li.appendChild(checkbox);
    li.appendChild(span);
    li.appendChild(btn);

    todoList.appendChild(li);
  });
  localStorage.setItem(STORAGE_KEY, JSON.stringify(todos));
}

// 自動復元用
async function autoImportFromServer(jsonData) {
  await fetch("/todos/import", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "X-API-KEY": API_KEY,
    },
    body: JSON.stringify(jsonData),
  });
  fetchTodos();
}

// 3. 新しいTodoを追加
async function createTodo() {
  const input = document.getElementById("todo-input");
  const title = input.value.trim();
  if (!title) return;

  await fetch(API_URL, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "X-API-KEY": API_KEY,
    },
    body: JSON.stringify({
      title: title,
      done: false,
    }),
  });

  input.value = "";
  await fetchTodos();
}

// 4. Todoの更新
async function toggleTodo(id, title, done) {
  await fetch(`${API_URL}/${id}`, {
    method: "PUT",
    headers: {
      "Content-Type": "application/json",
      "X-API-KEY": API_KEY,
    },
    body: JSON.stringify({
      title: title,
      done: done,
    }),
  });
  await fetchTodos();
}

// 5. Todoを削除
async function deleteTodo(id) {
  if (!confirm("本当に削除しますか？")) return;
  await fetch(`${API_URL}/${id}`, {
    method: "DELETE",
    headers: {
      "X-API-KEY": API_KEY,
    },
  });
  await fetchTodos();
}

// 6. 手動エクスポート (JSONダウンロード)
async function exportJSON() {
  const response = await fetch("/todos/export", {
    headers: {
      "X-API-KEY": API_KEY,
    },
  });
  if (!response.ok) return;
  const data = await response.json();

  const blob = new Blob([JSON.stringify(data, null, 2)], {
    type: "application/json",
  });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = `todo-backup-${new Date().toISOString().slice(0, 10)}.json`;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  URL.revokeObjectURL(url);
}

// 7. 手動インポート (JSONアップロード)
async function importJSON() {
  const fileInput = document.getElementById("import-file");
  const file = fileInput.files[0];
  if (!file) {
    alert("ファイルを選択してください。");
    return;
  }

  const reader = new FileReader();
  reader.onload = async function (e) {
    try {
      const jsonData = JSON.parse(e.target.result);
      await autoImportFromServer(jsonData);
      alert("データを正常に復元しました！");
      fileInput.value = "";
    } catch (err) {
      alert("JSONファイルの解析に失敗しました。");
    }
  };
  reader.readAsText(file);
}

// 最初に読み込みを実行（初回ロードなので自動復元ロジックを有効にする）
fetchTodos(true);
