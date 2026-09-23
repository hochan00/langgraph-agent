from pydantic import BaseModel


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
