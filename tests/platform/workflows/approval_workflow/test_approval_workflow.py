"""申請承認ワークフローのユニットテスト。"""

from __future__ import annotations

from src.platform.workflows.approval_workflow.contracts import (
    ApprovalRequest,
    ApprovalResult,
)
from src.platform.workflows.approval_workflow.workflow import (
    WORKFLOW_META,
    build_approval_workflow,
)


class TestApprovalWorkflowMeta:
    def test_workflow_meta(self) -> None:
        """WorkflowMeta が正しい。"""
        assert WORKFLOW_META.name == "approval-workflow"
        assert len(WORKFLOW_META.executor_ids) == 4

    def test_build_workflow(self) -> None:
        """ワークフローが構築できる。"""
        workflow = build_approval_workflow()
        assert workflow is not None


class TestApprovalWorkflowRun:
    async def test_auto_approve_low_amount(self) -> None:
        """低額申請は自動承認される。"""
        workflow = build_approval_workflow()
        request = ApprovalRequest(
            request_id="req-001",
            requester="user-1",
            category="交通費",
            amount=3000,
            description="タクシー代",
        )
        result = await workflow.run(request)
        outputs = result.get_outputs()
        assert len(outputs) == 1
        output: ApprovalResult = outputs[0]
        assert output.approved is True
        assert output.reviewer == "system"
        assert output.notification_sent is True

    async def test_validation_error_empty_requester(self) -> None:
        """空の申請者はバリデーションエラー。"""
        workflow = build_approval_workflow()
        request = ApprovalRequest(
            request_id="req-002",
            requester="",
            category="交通費",
            amount=3000,
            description="テスト",
        )
        result = await workflow.run(request)
        outputs = result.get_outputs()
        assert len(outputs) == 1
        output: ApprovalResult = outputs[0]
        assert output.approved is False
        assert "バリデーションエラー" in output.comment

    async def test_validation_error_negative_amount(self) -> None:
        """負の金額はバリデーションエラー。"""
        workflow = build_approval_workflow()
        request = ApprovalRequest(
            request_id="req-003",
            requester="user-1",
            category="交通費",
            amount=-100,
            description="テスト",
        )
        result = await workflow.run(request)
        outputs = result.get_outputs()
        assert len(outputs) == 1
        output: ApprovalResult = outputs[0]
        assert output.approved is False

    async def test_validation_error_unknown_category(self) -> None:
        """不明なカテゴリはバリデーションエラー。"""
        workflow = build_approval_workflow()
        request = ApprovalRequest(
            request_id="req-004",
            requester="user-1",
            category="不明",
            amount=1000,
            description="テスト",
        )
        result = await workflow.run(request)
        outputs = result.get_outputs()
        assert len(outputs) == 1
        output: ApprovalResult = outputs[0]
        assert output.approved is False
