from src.graph.nodes.collect import format_activity, route_after_collect
from src.schemas.activity_schema import CommitInfo


def test_format_activity_lists_repo_sha_and_message_body():
    activity = {
        "owner/repo": [
            CommitInfo(
                sha="a1b2c3d4e5",
                message="feat: 수집 노드 추가\n\n- 레포별로 묶기\n",
                authored_at="2026-10-20T10:00:00+09:00",
            )
        ]
    }
    text = format_activity("2026-10-20", activity)

    assert "(레포 1개, 커밋 1개)" in text
    assert "## owner/repo" in text
    assert "- a1b2c3d feat: 수집 노드 추가" in text
    assert "    - 레포별로 묶기" in text


def test_route_after_collect():
    assert route_after_collect({"activity": {}}) == "no_activity"
    assert route_after_collect({"activity": {"owner/repo": []}}) == "has_activity"
