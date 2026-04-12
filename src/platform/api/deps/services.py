"""Application Service / Repository の DI プロバイダ。"""

from __future__ import annotations

from typing import Annotated

from azure.cosmos.aio import CosmosClient
from fastapi import Depends

from src.platform.api.deps.cosmos import get_cosmos_client
from src.platform.application.run_management.workflow_execution_service import (
    WorkflowExecutionService,
)
from src.platform.application.spec_management.agent_spec_service import (
    AgentSpecService,
)
from src.platform.application.spec_management.tool_spec_service import ToolSpecService
from src.platform.application.spec_management.workflow_spec_service import (
    WorkflowSpecService,
)
from src.platform.domain.execution.repositories.execution_repository import (
    WorkflowExecutionRepository,
)
from src.platform.domain.execution.repositories.step_repository import (
    WorkflowExecutionStepRepository,
)
from src.platform.domain.registry.repositories.agent_spec_repository import (
    AgentSpecRepository,
)
from src.platform.domain.registry.repositories.tool_spec_repository import (
    ToolSpecRepository,
)
from src.platform.domain.registry.repositories.workflow_spec_repository import (
    WorkflowSpecRepository,
)
from src.platform.domain.sessions.repositories.session_repository import (
    SessionRepository,
)
from src.platform.infrastructure.db.cosmos.repositories.cosmos_agent_spec_repository import (
    CosmosAgentSpecRepository,
)
from src.platform.infrastructure.db.cosmos.repositories.cosmos_session_repository import (
    CosmosSessionRepository,
)
from src.platform.infrastructure.db.cosmos.repositories.cosmos_tool_spec_repository import (
    CosmosToolSpecRepository,
)
from src.platform.infrastructure.db.cosmos.repositories.cosmos_workflow_execution_repository import (
    CosmosWorkflowExecutionRepository,
)
from src.platform.infrastructure.db.cosmos.repositories.cosmos_workflow_execution_step_repository import (
    CosmosWorkflowExecutionStepRepository,
)
from src.platform.infrastructure.db.cosmos.repositories.cosmos_workflow_spec_repository import (
    CosmosWorkflowSpecRepository,
)
from src.platform.infrastructure.settings.config import config


async def get_agent_spec_repo(
    client: Annotated[CosmosClient, Depends(get_cosmos_client)],
) -> AgentSpecRepository:
    db = client.get_database_client(config.azure_cosmos_database_name)
    container = db.get_container_client("agents")
    return CosmosAgentSpecRepository(container)


async def get_workflow_spec_repo(
    client: Annotated[CosmosClient, Depends(get_cosmos_client)],
) -> WorkflowSpecRepository:
    db = client.get_database_client(config.azure_cosmos_database_name)
    container = db.get_container_client("workflows")
    return CosmosWorkflowSpecRepository(container)


async def get_tool_spec_repo(
    client: Annotated[CosmosClient, Depends(get_cosmos_client)],
) -> ToolSpecRepository:
    db = client.get_database_client(config.azure_cosmos_database_name)
    container = db.get_container_client("tools")
    return CosmosToolSpecRepository(container)


async def get_workflow_execution_repo(
    client: Annotated[CosmosClient, Depends(get_cosmos_client)],
) -> WorkflowExecutionRepository:
    db = client.get_database_client(config.azure_cosmos_database_name)
    container = db.get_container_client("workflow_executions")
    return CosmosWorkflowExecutionRepository(container)


async def get_workflow_execution_step_repo(
    client: Annotated[CosmosClient, Depends(get_cosmos_client)],
) -> WorkflowExecutionStepRepository:
    db = client.get_database_client(config.azure_cosmos_database_name)
    container = db.get_container_client("workflow_execution_steps")
    return CosmosWorkflowExecutionStepRepository(container)


async def get_agent_spec_service(
    repo: Annotated[AgentSpecRepository, Depends(get_agent_spec_repo)],
) -> AgentSpecService:
    return AgentSpecService(repo)


async def get_workflow_spec_service(
    repo: Annotated[WorkflowSpecRepository, Depends(get_workflow_spec_repo)],
) -> WorkflowSpecService:
    return WorkflowSpecService(repo)


async def get_tool_spec_service(
    repo: Annotated[ToolSpecRepository, Depends(get_tool_spec_repo)],
) -> ToolSpecService:
    return ToolSpecService(repo)


async def get_session_repo(
    client: Annotated[CosmosClient, Depends(get_cosmos_client)],
) -> SessionRepository:
    db = client.get_database_client(config.azure_cosmos_database_name)
    container = db.get_container_client("sessions")
    return CosmosSessionRepository(container)


async def get_workflow_execution_service(
    repo: Annotated[WorkflowExecutionRepository, Depends(get_workflow_execution_repo)],
) -> WorkflowExecutionService:
    return WorkflowExecutionService(repo)


def get_chat_client():
    from src.playground.aoai_client import get_aoai_client

    return get_aoai_client()


async def get_agent_factory(
    client: Annotated[CosmosClient, Depends(get_cosmos_client)],
):
    from src.platform.core.agent_factory import PlatformAgentFactory

    chat_client = get_chat_client()
    return PlatformAgentFactory(client=chat_client, cosmos_client=client)
