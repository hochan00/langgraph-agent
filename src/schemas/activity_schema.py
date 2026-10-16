from pydantic import BaseModel, Field


class CommitInfo(BaseModel):
    """코드가 GitHub에서 직접 조회한 커밋. LLM이 만들지 않는다."""

    sha: str
    message: str
    authored_at: str  # 설정 시간대 기준 ISO 8601

    @property
    def short_sha(self) -> str:
        return self.sha[:7]

    @property
    def title(self) -> str:
        message = self.message.strip()
        return message.splitlines()[0] if message else "(메시지 없음)"


# 레포 이름(owner/repo) → 그날의 커밋 목록 (작성 시각 순)
Activity = dict[str, list[CommitInfo]]


class RepoActivity(BaseModel):
    repo: str = Field(description="커밋 목록에 적힌 레포 이름(owner/repo) 그대로")
    summary: str = Field(description="그 레포에서 무엇을 왜 바꿨는지. 확인한 커밋 메시지·diff에 근거한 내용만")
    key_changes: list[str] = Field(description="실제로 있었던 주요 변경사항을 짧은 항목으로")


class DailyActivity(BaseModel):
    """LLM이 만드는 레포별 분석. 커밋 목록은 포함하지 않는다(코드가 수집 결과로 채운다)."""

    repos: list[RepoActivity]
