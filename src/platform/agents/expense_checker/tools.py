"""経費チェッカー Agent のツール定義。"""

from typing import Annotated

from agent_framework import tool

EXPENSE_POLICY = {
    "交通費": {"daily_limit": 10000, "requires_receipt": True},
    "交際費": {"daily_limit": 30000, "requires_receipt": True, "requires_approval": True},
    "備品購入": {"daily_limit": 50000, "requires_receipt": True},
    "通信費": {"daily_limit": 5000, "requires_receipt": False},
    "その他": {"daily_limit": 10000, "requires_receipt": True},
}


@tool
def check_expense_policy(
    category: Annotated[str, "経費カテゴリ (交通費, 交際費, 備品購入, 通信費, その他)"],
    amount: Annotated[int, "経費金額 (円)"],
) -> str:
    """経費が会社ポリシーに準拠しているかチェックする。"""
    policy = EXPENSE_POLICY.get(category)
    if policy is None:
        return f"警告: 不明なカテゴリ '{category}'。有効なカテゴリ: {', '.join(EXPENSE_POLICY.keys())}"

    issues: list[str] = []
    daily_limit = policy["daily_limit"]
    if amount > daily_limit:
        issues.append(f"金額 {amount:,}円 が日次上限 {daily_limit:,}円 を超過")
    if policy.get("requires_approval"):
        issues.append("事前承認が必要なカテゴリです")

    if issues:
        return f"ポリシー確認結果 [{category}]: " + "; ".join(issues)
    return f"ポリシー確認結果 [{category}]: 問題なし (金額: {amount:,}円, 上限: {daily_limit:,}円)"


@tool
def calculate_total(
    items: Annotated[str, "経費項目リスト (改行区切り, 各行 '項目名,金額' 形式)"],
    tax_rate: Annotated[float, "消費税率 (例: 0.10)"] = 0.10,
) -> str:
    """経費の合計金額を計算する (税込/税抜)。"""
    total = 0
    parsed_items: list[str] = []

    for line in items.strip().split("\n"):
        line = line.strip()
        if not line:
            continue
        parts = line.split(",")
        if len(parts) != 2:
            parsed_items.append(f"  - {line} (フォーマットエラー)")
            continue
        name = parts[0].strip()
        try:
            amount = int(parts[1].strip())
        except ValueError:
            parsed_items.append(f"  - {name}: 金額不正")
            continue
        total += amount
        parsed_items.append(f"  - {name}: {amount:,}円")

    tax = int(total * tax_rate)
    total_with_tax = total + tax

    result = "経費明細:\n" + "\n".join(parsed_items)
    result += f"\n\n小計: {total:,}円"
    result += f"\n消費税 ({tax_rate:.0%}): {tax:,}円"
    result += f"\n合計 (税込): {total_with_tax:,}円"
    return result
