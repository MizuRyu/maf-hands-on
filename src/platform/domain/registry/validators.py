"""WorkflowSpec の DAG バリデーション。"""

from __future__ import annotations

from src.platform.domain.registry.models.workflow_spec import WorkflowSpec


def validate_workflow_dag(spec: WorkflowSpec) -> tuple[list[str], list[str]]:
    """WorkflowSpec の DAG を検証する。(errors, warnings) を返す。"""
    errors: list[str] = []
    warnings: list[str] = []
    step_ids = set(spec.steps.keys())

    # 開始ステップが 1 つ以上あること
    start_steps = [sid for sid, s in spec.steps.items() if not s.depends_on]
    if not start_steps:
        errors.append("開始ステップ (depends_on が空) が 1 つもありません")

    # depends_on の参照先が存在すること
    for sid, step in spec.steps.items():
        for dep in step.depends_on:
            if dep not in step_ids:
                errors.append(f"ステップ '{sid}' の depends_on '{dep}' は存在しません")

    # 循環依存の検出 (トポロジカルソート)
    if not errors:
        visited: set[str] = set()
        in_stack: set[str] = set()

        def _has_cycle(node: str) -> bool:
            if node in in_stack:
                return True
            if node in visited:
                return False
            visited.add(node)
            in_stack.add(node)
            for dep in spec.steps[node].depends_on:
                if _has_cycle(dep):
                    return True
            in_stack.discard(node)
            return False

        for sid in step_ids:
            if _has_cycle(sid):
                errors.append("ステップ間に循環依存があります")
                break

    # 到達可能性: 全ステップが開始ステップから到達可能か
    if not errors:
        reachable: set[str] = set()
        # depends_on の逆グラフを構築
        dependents: dict[str, list[str]] = {sid: [] for sid in step_ids}
        for sid, step in spec.steps.items():
            for dep in step.depends_on:
                dependents[dep].append(sid)

        queue = list(start_steps)
        while queue:
            current = queue.pop()
            if current in reachable:
                continue
            reachable.add(current)
            queue.extend(dependents[current])

        unreachable = step_ids - reachable
        if unreachable:
            errors.append(f"到達不能なステップがあります: {', '.join(sorted(unreachable))}")

    return errors, warnings
