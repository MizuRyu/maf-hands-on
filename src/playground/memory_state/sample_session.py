"""Session / Memory サンプル。AgentSession でマルチターン会話と状態管理。"""

from __future__ import annotations

import asyncio
import logging

from agent_framework import Agent, AgentSession, BaseChatClient, InMemoryHistoryProvider

from src.playground.aoai_client import get_aoai_client

logger = logging.getLogger(__name__)


def _build_agent(client: BaseChatClient) -> Agent:
    return Agent(
        client=client,
        name="session-agent",
        description="セッション管理のデモ用 Agent",
        instructions="あなたは親切なアシスタントです。会話の文脈を覚えて回答してください。日本語で回答。",
        context_providers=[InMemoryHistoryProvider()],
    )


async def main() -> None:
    client = get_aoai_client()
    agent = _build_agent(client)
    session = AgentSession()

    # マルチターン会話
    conversation = [
        "私の名前は田中です。よろしく。",
        "好きな食べ物はカレーです。覚えておいて。",
        "私の名前と好きな食べ物は何でしたっけ?",
    ]

    for msg in conversation:
        logger.info("User: %s", msg)
        result = await agent.run(msg, session=session)
        logger.info("Agent: %s\n", result.text)

    # セッション状態の確認
    logger.info("Session ID: %s", session.session_id)
    logger.info("Session state keys: %s", list(session.state.keys()))

    # セッションのシリアライズ/デシリアライズ
    serialized = session.to_dict()
    restored = AgentSession.from_dict(serialized)
    logger.info("Restored session ID: %s", restored.session_id)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    asyncio.run(main())
