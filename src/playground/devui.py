"""DevUI サーバー起動スクリプト。playground のエンティティを DevUI で提供する。"""

from __future__ import annotations

import logging

DEVUI_PORT = 8090


def main() -> None:
    """DevUI サーバーを起動する。"""
    from dotenv import load_dotenv

    # config モジュール読み込み前に .env をロードする
    load_dotenv()

    from agent_framework.devui import serve

    from src.playground.agents.sample_agent import get_sample_agent
    from src.playground.aoai_client import get_aoai_client

    logging.basicConfig(level=logging.INFO, format="%(message)s")
    logger = logging.getLogger(__name__)

    client = get_aoai_client()
    entities = [
        get_sample_agent(client),
    ]

    logger.info("Starting DevUI on http://localhost:%s", DEVUI_PORT)
    serve(entities=entities, port=DEVUI_PORT, auto_open=True)


if __name__ == "__main__":
    main()
