from typing import TypedDict


class DevlogContext(TypedDict):
    """실행 단위로 전달하는 자격증명. 그래프 상태에 넣지 않아 LLM 입력과 추적 기록에 남지 않는다."""

    github_token: str
    github_login: str
