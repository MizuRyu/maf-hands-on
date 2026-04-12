"""Platform 共通ルーター。"""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter

from src.platform.api.schemas.common import API_PREFIX, BaseResponse

router = APIRouter(prefix=API_PREFIX, tags=["platform"])


class PlatformOptionsResponse(BaseResponse[dict[str, Any]]):
    pass


@router.get("/platform/options", response_model=PlatformOptionsResponse)
async def get_platform_options() -> PlatformOptionsResponse:
    from src.platform.agents.policy import PlatformPolicy

    policy = PlatformPolicy.load()
    return PlatformOptionsResponse(
        data={
            "models": ["gpt-5-nano"],
            "tool_types": ["function", "mcp", "agent_as_tool", "hosted"],
            "middleware": ["audit", "security"],
            "features": {
                "history": {"default": policy.defaults.history_enabled},
                "compaction": {"default": policy.defaults.compaction_enabled},
                "tools": {"default": True},
                "structured_output": {"default": False},
            },
            "compaction_strategies": ["sliding_window", "token_budget", "summarization"],
            "foundry": {
                "deployment_types": ["prompt", "hosted", "workflow", "none"],
            },
        }
    )
