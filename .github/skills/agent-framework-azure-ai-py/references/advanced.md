# 上級パターン リファレンス

構造化出力、OpenAPI ツール、ファイル処理等の上級パターン。

## Pydantic による構造化出力

### 基本的なレスポンスフォーマット

```python
from pydantic import BaseModel, ConfigDict
from agent_framework import Agent
from agent_framework.foundry import FoundryChatClient
from azure.identity import AzureCliCredential

class MovieRecommendation(BaseModel):
    model_config = ConfigDict(extra="forbid")

    title: str
    year: int
    genre: str
    rating: float
    summary: str

client = FoundryChatClient(
    project_endpoint="https://<project>.services.ai.azure.com",
    model="gpt-4o-mini",
    credential=AzureCliCredential(),
)

agent = Agent(
    client=client,
    name="MovieAgent",
    instructions="ユーザーの好みに基づいて映画を推薦します。",
)

result = await agent.run(
    "SF 映画を推薦して",
    options={"response_format": MovieRecommendation},
)
movie = MovieRecommendation.model_validate_json(result.text)
print(f"{movie.title} ({movie.year}) - {movie.rating}/10")
```

> **v1.0.0 変更点**: `response_format=Model` 直接渡し → `options={"response_format": Model}`。

### 複雑なネスト構造

```python
from pydantic import BaseModel, ConfigDict, Field
from typing import Optional

class Address(BaseModel):
    model_config = ConfigDict(extra="forbid")
    street: str
    city: str
    country: str
    postal_code: Optional[str] = None

class Person(BaseModel):
    model_config = ConfigDict(extra="forbid")
    name: str
    age: int
    email: str
    address: Address
    hobbies: list[str] = Field(default_factory=list)

class TeamResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")
    team_name: str
    members: list[Person]
    total_members: int

agent = Agent(client=client, name="TeamGenerator", instructions="架空のチームデータを生成します。")

result = await agent.run(
    "3人のソフトウェアエンジニアのチームを作って",
    options={"response_format": TeamResponse},
)
team = TeamResponse.model_validate_json(result.text)
for member in team.members:
    print(f"- {member.name}, {member.age}歳, {member.address.city}")
```

### 実行時のレスポンスフォーマット切り替え

```python
class QuickAnswer(BaseModel):
    answer: str
    confidence: float

class DetailedAnalysis(BaseModel):
    summary: str
    key_points: list[str]
    recommendations: list[str]
    sources: list[str]

agent = Agent(client=client, name="FlexibleAgent", instructions="要求された形式で情報を提供します。")

# 簡潔な回答
quick_result = await agent.run(
    "Python とは？",
    options={"response_format": QuickAnswer},
)

# 詳細な分析
detailed_result = await agent.run(
    "マイクロサービスアーキテクチャの利点を分析して",
    options={"response_format": DetailedAnalysis},
)
```

### JSON Schema dict での指定（v1.0.0 新機能）

```python
# Pydantic モデルの代わりに JSON Schema dict も使用可能
schema = {"type": "object", "properties": {"name": {"type": "string"}, "score": {"type": "integer"}}}
result = await agent.run(
    "評価結果を返して",
    options={"response_format": schema},
)
# result.value は dict 型
```

---

## OpenAPI ツール

```python
from agent_framework import Agent, OpenAPITool
from agent_framework.foundry import FoundryChatClient
from azure.identity import AzureCliCredential

openapi_spec = {
    "openapi": "3.0.0",
    "info": {"title": "Weather API", "version": "1.0.0"},
    "paths": {
        "/weather/{city}": {
            "get": {
                "operationId": "getWeather",
                "summary": "都市の天気を取得",
                "parameters": [
                    {
                        "name": "city",
                        "in": "path",
                        "required": True,
                        "schema": {"type": "string"}
                    }
                ],
                "responses": {
                    "200": {
                        "description": "天気データ",
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object",
                                    "properties": {
                                        "temperature": {"type": "number"},
                                        "conditions": {"type": "string"}
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }
    }
}

client = FoundryChatClient(
    project_endpoint="https://<project>.services.ai.azure.com",
    model="gpt-4o-mini",
    credential=AzureCliCredential(),
)

agent = Agent(
    client=client,
    name="WeatherAPIAgent",
    instructions="Weather API を使って天気の質問に回答します。",
    tools=[
        OpenAPITool(
            name="WeatherAPI",
            spec=openapi_spec,
            base_url="https://api.weather.example.com",
        ),
    ],
)
```

### 認証付き OpenAPI

```python
from agent_framework import OpenAPITool

openapi_tool = OpenAPITool(
    name="SecureAPI",
    spec="https://api.example.com/openapi.json",
    base_url="https://api.example.com",
    headers={
        "Authorization": "Bearer your-api-key",
        "X-API-Version": "2024-01",
    },
)
```

---

## Citation（出典引用）

### Citation の有効化

```python
agent = Agent(
    client=client,
    name="ResearchAgent",
    instructions="""ナレッジベースを使って質問に回答します。

    重要: 出典は常に次の形式で引用すること:
    【message_idx:search_idx†source_name】
    """,
    tools=[client.get_file_search_tool(vector_store_ids=["vs-my-store"])],
)
```

### Citation のパース

```python
import re

def parse_citations(text: str) -> list[dict]:
    pattern = r'【(\d+):(\d+)†([^】]+)】'
    citations = []

    for match in re.finditer(pattern, text):
        citations.append({
            "message_idx": int(match.group(1)),
            "search_idx": int(match.group(2)),
            "source": match.group(3),
        })

    return citations

result = await agent.run("Azure Functions とは？")
citations = parse_citations(result.text)
```

---

## プロバイダ設定オプション

### カスタムモデルとエンドポイント

```python
from agent_framework.foundry import FoundryChatClient

client = FoundryChatClient(
    project_endpoint="https://my-project.services.ai.azure.com",
    model="gpt-4o",
    credential=credential,
)
```

### OpenAI クライアント

```python
from agent_framework.openai import OpenAIChatClient

# OPENAI_API_KEY 環境変数から読み込み
client = OpenAIChatClient()

# または明示的に指定
client = OpenAIChatClient(api_key="sk-...")
```

---

## エージェントのライフサイクル管理

### as_agent パターン

```python
# クライアントから直接エージェント作成
agent = client.as_agent(name="MyAgent", instructions="あなたは親切なアシスタントです。")
result = await agent.run("こんにちは！")
```

### Agent クラスによる作成

```python
from agent_framework import Agent

agent = Agent(
    client=client,
    name="MyAgent",
    instructions="あなたは親切なアシスタントです。",
    tools=[...],
)
```

---

## エラーハンドリングパターン

### グレースフルデグラデーション

```python
async def run_with_fallback(agent, query: str, session=None):
    try:
        result = await agent.run(query, session=session)
        return result.text
    except Exception as e:
        print(f"ツール実行エラー: {e}")
        fallback_agent = Agent(
            client=client,
            name="FallbackAgent",
            instructions="知識のみに基づいて回答してください。",
        )
        result = await fallback_agent.run(query)
        return f"[フォールバック応答] {result.text}"
```

### リトライロジック

```python
import asyncio
from typing import Optional

async def run_with_retry(
    agent,
    query: str,
    session=None,
    max_retries: int = 3,
    delay: float = 1.0,
) -> Optional[str]:
    for attempt in range(max_retries):
        try:
            result = await agent.run(query, session=session)
            return result.text
        except Exception as e:
            if attempt == max_retries - 1:
                raise
            wait_time = delay * (2 ** attempt)
            print(f"試行 {attempt + 1} 失敗、{wait_time}秒後にリトライ: {e}")
            await asyncio.sleep(wait_time)
    return None
```

---

## パフォーマンス最適化

### 接続の再利用

```python
# 良い例: クライアントを再利用
client = FoundryChatClient(
    project_endpoint="https://<project>.services.ai.azure.com",
    model="gpt-4o-mini",
    credential=credential,
)

agent1 = Agent(client=client, name="Agent1", instructions="...")
agent2 = Agent(client=client, name="Agent2", instructions="...")

for query in queries:
    await agent1.run(query)
```

### 並行リクエスト

```python
import asyncio

async def process_queries(client, queries: list[str]) -> list[str]:
    agent = Agent(client=client, name="BatchAgent", instructions="簡潔に回答してください。")

    async def process_one(query: str) -> str:
        session = agent.create_session()
        result = await agent.run(query, session=session)
        return result.text

    results = await asyncio.gather(*[process_one(q) for q in queries])
    return results
```

---

## デバッグとロギング

### 詳細ログの有効化

```python
import logging

logging.basicConfig(level=logging.DEBUG)
azure_logger = logging.getLogger("azure")
azure_logger.setLevel(logging.DEBUG)

af_logger = logging.getLogger("agent_framework")
af_logger.setLevel(logging.DEBUG)
```

### ストリーミング中のツール呼び出し監視

```python
async for chunk in agent.run("何かを計算して", stream=True):
    if chunk.tool_calls:
        for tool_call in chunk.tool_calls:
            print(f"[DEBUG] ツール: {tool_call.name}")
            print(f"[DEBUG] 引数: {tool_call.arguments}")
    if chunk.text:
        print(chunk.text, end="", flush=True)
```
