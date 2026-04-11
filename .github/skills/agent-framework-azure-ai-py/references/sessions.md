# セッション管理リファレンス

会話状態の管理とマルチターン対話のパターン。

> **v1.0.0 変更点**: `AgentThread` / `get_new_thread()` は廃止。`create_session()` / `session=` に移行。

## 概要

セッションはエージェント実行をサーバーサイドの会話状態にリンクし、以下を可能にする:
- コンテキストを維持したマルチターン会話
- 会話の永続化と再開
- セッションベースのメッセージ履歴

---

## セッションの作成と使用

### 基本的なマルチターン会話

```python
from agent_framework import Agent
from agent_framework.foundry import FoundryChatClient
from azure.identity import AzureCliCredential

client = FoundryChatClient(
    project_endpoint="https://<project>.services.ai.azure.com",
    model="gpt-4o-mini",
    credential=AzureCliCredential(),
)

agent = Agent(client=client, name="ChatAgent", instructions="あなたは親切なアシスタントです。")

session = agent.create_session()

result1 = await agent.run("私の名前はアリスです", session=session)
print(f"Agent: {result1.text}")

result2 = await agent.run("私の名前は何？", session=session)
print(f"Agent: {result2.text}")

result3 = await agent.run("私の名前でジョークを言って", session=session)
print(f"Agent: {result3.text}")
```

---

## 会話の永続化

### セッション ID の保存

```python
import json

async def save_conversation(session, filepath: str):
    data = {
        "service_session_id": session.service_session_id,
    }
    with open(filepath, "w") as f:
        json.dump(data, f)

session = agent.create_session()
await agent.run("会話を開始", session=session)
await save_conversation(session, "conversation.json")
```

### 会話の再開

```python
import json

async def load_and_resume(agent, filepath: str):
    with open(filepath) as f:
        data = json.load(f)

    session = agent.create_session(service_session_id=data["service_session_id"])
    result = await agent.run("会話を続けて", session=session)
    return result
```

---

## セッション + ストリーミング

```python
session = agent.create_session()

print("Agent: ", end="", flush=True)
async for chunk in agent.run("Python について教えて", session=session, stream=True):
    if chunk.text:
        print(chunk.text, end="", flush=True)
print()

# 非ストリーミングでフォローアップ
result = await agent.run("さっきの言語は何だっけ？", session=session)
print(f"Agent: {result.text}")

# 再びストリーミング
print("Agent: ", end="", flush=True)
async for chunk in agent.run("コード例を見せて", session=session, stream=True):
    if chunk.text:
        print(chunk.text, end="", flush=True)
print()
```

---

## セッション + ツール

```python
from typing import Annotated
from pydantic import Field
from agent_framework import tool

@tool
def search_database(
    query: Annotated[str, Field(description="検索クエリ")]
) -> str:
    return f"'{query}' の結果: アイテムA, アイテムB, アイテムC"

@tool
def get_item_details(
    item_name: Annotated[str, Field(description="アイテム名")]
) -> str:
    return f"{item_name} の詳細: 価格 ¥9,900, 在庫あり"

agent = Agent(
    client=client,
    name="ShoppingAgent",
    instructions="ユーザーが商品を見つけて詳細を知るのを助けます。",
    tools=[search_database, get_item_details],
)

session = agent.create_session()

result1 = await agent.run("ノートパソコンを検索して", session=session)
result2 = await agent.run("アイテムA の詳細を教えて", session=session)
result3 = await agent.run("在庫はある？", session=session)
```

---

## 複数の並行会話

```python
import asyncio

async def handle_user_session(client, user_id: str, messages: list[str]):
    agent = Agent(
        client=client,
        name=f"Agent-{user_id}",
        instructions="あなたは親切なアシスタントです。",
    )

    session = agent.create_session()

    for message in messages:
        result = await agent.run(message, session=session)
        print(f"[{user_id}] Agent: {result.text}")

async def main():
    client = FoundryChatClient(
        project_endpoint="https://<project>.services.ai.azure.com",
        model="gpt-4o-mini",
        credential=AzureCliCredential(),
    )

    await asyncio.gather(
        handle_user_session(client, "user1", ["こんにちは", "2+2は？"]),
        handle_user_session(client, "user2", ["やあ", "ジョーク教えて"]),
        handle_user_session(client, "user3", ["おはよう", "今日の天気は？"]),
    )
```

---

## セッションのベストプラクティス

### やるべきこと

```python
# 論理的な会話ごとに新しいセッションを作成
session = agent.create_session()

# 同じセッションを渡してコンテキストを維持
await agent.run("メッセージ1", session=session)
await agent.run("メッセージ2", session=session)

# 再開が必要な会話のセッション ID を保存
session_id = session.service_session_id
```

### やってはいけないこと

```python
# メッセージごとに新しいセッションを作成しない（コンテキストが失われる）
for msg in messages:
    session = agent.create_session()  # NG！
    await agent.run(msg, session=session)

# 異なるエージェント間でセッションを共有しない
session1 = agent1.create_session()
await agent2.run("こんにちは", session=session1)  # 問題が起きる可能性

# セッションを渡し忘れない（シングルターンのみになる）
await agent.run("メッセージ1")
await agent.run("メッセージ2")  # 前のメッセージを参照できない
```

---

## セッションのライフサイクル

```
1. agent.create_session()
   -> セッションオブジェクト作成
   -> サーバーサイドのセッションは初回 run 時に作成

2. agent.run(..., session=session)
   -> メッセージがセッションに追加
   -> エージェント応答がセッションに追加
   -> コンテキストが蓄積

3. (任意) session.service_session_id を保存
   -> 後で会話を再開するため

4. (任意) agent.create_session(service_session_id=...) で再開
   -> 既存の会話を継続
```

---

## ステートレス vs ステートフル

### ステートレス（セッションなし）
```python
result = await agent.run("2+2は？")
```

### ステートフル（セッションあり）
```python
session = agent.create_session()
result1 = await agent.run("好きな色は青です", session=session)
result2 = await agent.run("私の好きな色は？", session=session)  # 青と答える
```
