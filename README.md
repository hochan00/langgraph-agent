# dev-retro-agent

> **개발자 회고 에이전트** — 오늘 GitHub에 올린 커밋을 분석해서, 실제 근거에 기반한 회고를
> 자동으로 작성하고 노션에 정리해주는 멀티 에이전트 시스템

---

## 목차

- [핵심 아이디어](#핵심-아이디어)
- [사용 시나리오](#사용-시나리오)
- [아키텍처](#아키텍처)
  - [멀티 에이전트 구조](#멀티-에이전트-구조)
  - [에이전트별 역할·입출력](#에이전트별-역할입출력)
- [노션 저장 구조](#노션-저장-구조)
- [서비스 방향성](#서비스-방향성)
- [기술 스택](#기술-스택)
- [프로젝트 구조](#프로젝트-구조)
- [설치 및 실행](#설치-및-실행)
- [설계 결정](#설계-결정)
- [구현 현황](#구현-현황)

---

## 핵심 아이디어

개발자에게 그날 공부하고 개발한 내용을 회고 형식으로 정리하는 습관은 중요하지만, 매일 직접 쓰기는
번거롭습니다. 반면 **그날 무엇을 했는지에 대한 가장 정확한 기록은 이미 GitHub 커밋에 존재**합니다.

이 프로젝트는 그 커밋 기록을 근거 삼아 회고를 대신 작성합니다. 핵심은 **"오늘 실제로 한 일"과
"회고에 적힌 내용"이 반드시 일치하도록 검증**하는 것 — 안 한 일을 했다고 지어내면 안 되기 때문에,
생성된 회고는 항상 원본 커밋·코드 변경 내용에 근거했는지 확인을 거칩니다.

| 사람이 직접 하면 | 에이전트가 하면 |
|---|---|
| 그날 뭘 했는지 기억을 더듬어 회고를 씀 | 커밋·diff를 근거로 **실제로 한 일만** 회고에 반영 (근거검증) |
| 노션에 새 페이지를 만들지, 오늘 항목을 덮어쓸지 매번 확인 | 오늘 항목이 이미 있는지 확인 후 신규/갱신 판단 + 승인 요청 |
| 여러 레포를 각각 따로 기록 | 레포별로 구조화된 데이터베이스에 날짜순으로 정리 |

## 사용 시나리오

**A. 정상 흐름 — 오늘 활동이 있는 경우**

프론트엔드에서 레포를 선택하고 "오늘 회고 작성" 버튼 클릭
→ 커밋 분석(사소한 커밋은 메시지만, 의미 있는 변경은 diff까지 확인)
→ 회고 초안 생성 + 근거 검증
→ "이 내용으로 저장할까요?" 승인 요청
→ 승인 시 노션 데이터베이스에 저장, 링크 반환

**B. 활동이 없는 경우**

오늘 커밋이 하나도 없으면, 회고를 억지로 만들지 않고 "오늘은 기록할 활동이 없어요"로 즉시 종료합니다.

**C. 수정 요청이 있는 경우**

승인 대신 "이 부분 다르게 써줘"라고 응답하면, 회고를 다시 작성해 **이전 안과 달라진 점을 보여주고**
재승인을 요청합니다. 승인될 때까지 반복됩니다.

---

## 아키텍처

### 멀티 에이전트 구조

```mermaid
flowchart TD
    START([버튼 클릭 - repo, date]) --> a_agent

    subgraph analyst["commit_analyst — 내부 ReAct 루프"]
        direction TB
        a_agent["agent<br/>fetch_commits · fetch_diff 중<br/>스스로 선택"]
        a_tools["tools<br/>선택된 도구 실행"]
        a4["구조화 출력<br/>CommitAnalysis"]
        a_agent -->|도구 호출 있음| a_tools --> a_agent
        a_agent -->|충분히 판단함 - 도구 호출 없음| a4
    end

    a4 -->|has_activity: false| END1([종료 - 활동 없음])
    a4 -->|has_activity: true| w_agent

    subgraph writer[report_writer]
        direction TB
        w_agent["agent<br/>fetch_readme 필요시 호출"]
        w_tools["tools<br/>fetch_readme 실행"]
        w2[초안 생성]
        w3{근거검증 통과?}
        w4[RetroDraft]
        w_agent -->|도구 호출 있음| w_tools --> w_agent
        w_agent -->|충분함 - 도구 호출 없음| w2 --> w3
        w3 -->|실패 - 최대 2회| w2
        w3 -->|통과| w4
    end

    w4 --> n1

    subgraph notion[notion_writer]
        direction TB
        n1["check_existing_entry(repo, date)"]
        n2[confirm_action - interrupt]
        n1 --> n2
    end

    n2 -->|승인| n3["create_or_update_entry"] --> END2([저장 완료])
    n2 -.->|거절 + 수정요청 - 이전 안과 diff 표시| w2
```

**핵심 설계 포인트 1 — 자율성은 "에이전트 내부"에만 두고, 에이전트 "사이" 순서는 고정한다**: 처음엔
"diff까지 볼 가치 있나"를 그래프의 조건부 엣지 하나로 표현했지만, 그러면 판단이 매 커밋마다 반복되지
못하고 전체에 대해 한 번만 갈리는 형식적 분기가 됩니다. 그래서 `commit_analyst` 자체를
`fetch_commits`·`fetch_diff`를 `bind_tools`한 **자기만의 `agent ⇄ tools` 루프(ReAct)**로 만들어,
커밋별로 "이건 메시지만, 이건 diff까지" 를 필요한 만큼 반복 판단하게 합니다. `report_writer`도
`fetch_readme` 호출 여부를 같은 방식의 루프로 스스로 정합니다. 반면 **에이전트 사이의 순서**
(분석 → 작성 → 저장)는 고정된 그래프 엣지입니다 — 이 순서까지 LLM이 매번 판단하게 하면(완전 동적
멀티에이전트) 실행이 불안정해지고, 반대로 각 에이전트 내부까지 고정 로직이면 "에이전트"라 부르기
어려워집니다. 자율성의 경계를 **"에이전트 내부의 tool-calling 루프"** 로 긋고, 그 바깥(오케스트레이션)은
설계자가 고정한다는 원칙입니다.

**핵심 설계 포인트 1-1 — ReAct 루프와 도구 실행의 결과는 구조화 출력으로 변환한다**: 일반적인 ReAct
루프는 도구 호출이 끝나면 자유 텍스트로 답하고 종료하지만, 여기서는 다음 에이전트가 정해진 필드
(`CommitAnalysis`, `RetroDraft`)를 그대로 이어받아야 합니다. 그래서 루프가 종료된 시점(마지막 메시지에
도구 호출이 없음)에 구조화 출력(`with_structured_output`) 호출을 한 번 더 거쳐 Pydantic 모델로
정리하는 단계를 각 에이전트 말미에 둡니다.

**핵심 설계 포인트 1-2 — 근거검증(grounding check)은 도구 루프가 아니라 명시적 그래프 엣지로 남긴다**:
`report_writer`의 "초안 생성 → 근거검증 → 실패 시 재생성"은 ReAct로 흡수하지 않았습니다. ReAct는
"외부에서 무엇을 더 관찰할지"를 위한 패턴이고, 근거검증은 "이미 만든 결과물을 스스로 채점"하는 별개의
관심사이기 때문입니다 — 이전 CRAG의 `grade_hallucination` 패턴을 그대로 재사용해 명시적 리트라이
엣지로 표현합니다.

**핵심 설계 포인트 2 — 생성과 저장을 분리한다**: `report_writer`는 노션 API를 전혀 모르고, 텍스트만
만듭니다. `notion_writer`는 반대로 텍스트를 수정하는 능력이 없고, 저장 여부만 판단합니다. 수정
요청이 오면 `notion_writer`가 직접 고치는 게 아니라 `report_writer`로 되돌아가는 엣지로 처리합니다 —
"판단/생성 노드"와 "실행 노드"를 분리하는 원칙을 그대로 적용한 것입니다.

**핵심 설계 포인트 3 — LLM이 판단할 것과 코드가 보장할 것을 나눈다**: 회고 내용 요약처럼 판단이
필요한 일은 LLM이 맡지만, **이미 확정된 사실은 LLM에게 다시 묻지 않습니다.** 예를 들어 `repo`는
`fetch_commits`가 호출되는 순간 그 인자값을 그대로 상태에 저장하고, 이후 `fetch_diff`에는
`InjectedState`로 자동 주입합니다. LLM의 도구 스키마에서 해당 인자가 아예 제외되므로 값을 잘못
재생성할 여지가 없습니다. `date` 역시 코드가 직접 계산합니다. ([설계 결정](#설계-결정) 참고)

### 에이전트별 역할·입출력

**`commit_analyst`** — 내부 `agent ⇄ tools` 루프 (ReAct)
- 도구: `fetch_commits(repo, date)`, `fetch_diff(commit_sha)` — 둘 다 `bind_tools`로 LLM에 위임,
  어떤 커밋의 diff까지 볼지·몇 번 호출할지는 에이전트가 스스로 반복 판단
- 루프 종료(도구 호출 없음) 후 구조화 출력으로 변환:
  ```python
  class CommitAnalysis(BaseModel):
      has_activity: bool       # 오늘 커밋이 있었는지 (분기 기준)
      commit_count: int
      summary: str              # 오늘 있었던 작업 서술
      key_changes: list[str]    # 주요 변경사항 목록
  ```

**`report_writer`** — 정보 수집은 ReAct 루프, 근거검증은 명시적 리트라이 엣지
- 도구: `fetch_readme(repo)` (배경 맥락 참고용 — 필요하다고 판단할 때만 호출)
- 입력: `CommitAnalysis`
- 내부: (루프) 필요시 `fetch_readme` 호출 → 초안 생성 → `key_changes`에 실제로 근거하는지 검증
  → 실패 시 최대 2회 재생성(그래프 엣지, 도구 루프 아님)
- 출력:
  ```python
  class RetroDraft(BaseModel):
      report: str        # 회고 본문
      grounded: bool       # 근거검증 통과 여부
  ```

**`notion_writer`**
- 도구: `check_existing_entry(repo, date)`, `create_or_update_entry(...)`
- 입력: `RetroDraft`
- 내부: 기존 항목 확인 → `confirm_action`(interrupt 기반 HITL) → 승인 시 저장, 거절 시 `report_writer`로 회귀
- 출력:
  ```python
  class WriteResult(BaseModel):
      status: Literal["saved", "updated", "pending_confirmation"]
      page_url: str | None
      is_new_entry: bool
  ```

---

## 노션 저장 구조

프리폼 페이지 트리(레포 페이지 → 날짜별 하위 페이지)가 아니라 **데이터베이스**로 구성합니다.
사용자가 데이터베이스를 직접 만들지 않아도 되도록, **부모 페이지 하나만 만들어 연결해두면 그
밑에 인라인 데이터베이스를 첫 실행 시 자동 생성**하는 방식을 목표로 합니다 (현재 구현 상태는
[구현 현황](#구현-현황) 참고).

| 날짜 (Title) | 레포지토리 (Text) | 페이지 본문 |
|---|---|---|
| 2026-07-29 | hochan00/langgraph-agent | 회고 내용 (노션 블록) |
| 2026-07-28 | hochan00/langgraph-agent | 회고 내용 (노션 블록) |

프리폼 페이지 구조였다면 "오늘 항목이 이미 있는지"를 제목 문자열 비교로 확인해야 했겠지만(Notion
API가 페이지 제목만 검색 가능하다는 제약 때문), 속성 기반 데이터베이스는
`databases.query(filter: 레포명==X, 날짜==오늘)`로 **정확하게 필터링**할 수 있습니다. 벡터 인덱스나
증분 동기화 같은 별도 검색 인프라가 필요 없습니다 — 이 프로젝트가 다루는 데이터가 애초에 구조화된
성격(레포+날짜)이기 때문입니다.

**마크다운 → 노션 블록 변환**: 노션 API는 `rich_text`에 `**굵게**`, `- 목록` 같은 마크다운 문자를
그대로 넣으면 **서식으로 해석하지 않고 문자 그대로 표시**합니다. 서식은 블록 타입
(`heading_1~3`, `bulleted_list_item`)과 `annotations`(`bold` 등)로 별도 명시해야 합니다. 직접
구현한 `_markdown_to_blocks()`는 제목·리스트·굵게 3종류만 지원하고 2000자 제한도 처리하지 않아,
`md2notionpage` 라이브러리로 교체할 예정입니다.

---

## 서비스 방향성

다른 사용자도 실제로 쓸 수 있는 서비스로 만든다면 어떤 방향이어야 하는지 정리한 설계 메모입니다.
**단, 이 프로젝트는 짧게 배포했다가 내리는 포트폴리오 목적이라 실제 다중 사용자 서비스화(특히
GitHub OAuth)는 지금 스코프에서 하지 않기로 결정했습니다** — 아래는 "이렇게 확장 가능하게
설계해뒀다"를 보여주기 위한 방향성이지, 현재 구현 계획은 아닙니다. (구체적인 작업 목록은
[구현 현황](#구현-현황) 참고)

### 저장 구조 — 자체 데이터베이스 + 선택적 Notion 내보내기

회고는 자체 데이터베이스(SQLite)에 저장하고, 서비스 화면에서 목록·상세를 바로 열람합니다. Notion
연동은 선택 사항이며, 연동되어 있으면 자동으로 함께 저장됩니다.

Notion을 유일한 저장소로 두지 않는 이유는 두 가지입니다. 첫째, Notion 계정이 없는 사용자도
서비스를 쓸 수 있어야 합니다. 둘째, 조회 기간을 하루뿐 아니라 주간·월간처럼 유연하게 다루려면
자체 스키마가 필요합니다 — Notion 속성으로는 "하루짜리 항목"과 "기간 항목"을 함께 감당하기
어색합니다.

### 왜 Notion의 공식 GitHub 동기화를 쓰지 않는가

"Notion이 이미 GitHub 동기화 기능을 제공하니 그 위에 AI 요약만 얹으면 되지 않을까"를 검토했습니다.
비슷한 방식으로 만들어진 서비스([GitNotion](https://dev.to/dax-side/i-built-an-mcp-server-that-syncs-github-into-notion-and-generates-ai-reports-5ao6))가
있어서 소스 코드까지 직접 확인했습니다.

Notion 공식 GitHub 연동은 **저장소·PR·이슈만 동기화**하며(커밋은 동기화 대상이 아님), 동기화되는
속성도 Title/Assignees/Description/State/Reviewers 등 **메타데이터뿐**입니다. GitNotion도
`octokit.repos.listCommits`(커밋 메시지 목록)만 사용하고 `additions`/`deletions`는 `0`으로
하드코딩되어 있어, 실제 diff는 어디에서도 가져오지 않습니다. 두 경우 모두 **커밋 메시지만 보고
요약하는 방식**이라, 이 프로젝트의 핵심인 "코드 변경 근거 확인"을 대체할 수 없습니다. GitHub
API를 직접 연동합니다(`fetch_commits`/`fetch_diff`).

### 인증 — GitHub OAuth 로그인

여러 사용자가 쓰려면 회고의 소유권을 구분할 수 있어야 합니다. **GitHub OAuth 로그인**으로 이
문제를 해결합니다:

1. GitHub이 검증한 사용자 ID를 받아, 위조 불가능한 소유권 구분자로 사용
2. 로그인 인가 과정에서 GitHub 접근 토큰도 함께 획득 — 사용자가 PAT을 직접 발급해 붙여넣을
   필요가 없어짐

브라우저에 저장된 값(예: `thread_id`)은 서버가 검증할 방법이 없어 위조에 취약하므로 소유권
구분자로 쓰지 않습니다. Notion은 부가 기능이므로 별도 OAuth 앱을 만들지 않고, API 키를 직접
입력받는 방식을 유지합니다. GitHub 토큰은 State가 아니라 [Runtime Context](#구현-현황)로
주입해, 체크포인터에 저장되지 않고 LLM 도구 스키마에도 노출되지 않도록 합니다.

---

## 기술 스택

| 분류 | 기술 | 선택 이유 |
|------|------|----------|
| 언어 | Python 3.13 | — |
| 프레임워크 | FastAPI | 비동기 지원, 자동 Swagger 문서화 |
| 오케스트레이션 | LangChain · LangGraph | 멀티 에이전트 그래프, `InjectedState`, human-in-the-loop(`interrupt`) |
| LLM | Google Gemini 3.5 Flash Lite | tool-calling 지원, 무료 티어. `src/core/llm.py`에서 Claude로 교체 가능 |
| 외부 연동 | GitHub API (`PyGithub`) | 커밋·diff·README 조회, 개인 액세스 토큰(PAT)으로 인증 |
| 외부 연동 | Notion API (`notion-client`) | 데이터베이스 조회·생성, 무료, rate limit 3 req/s |
| 프롬프트 관리 | YAML + `ChatPromptTemplate` | 프롬프트 문구를 코드에서 분리. `load_prompt`는 deprecated라 미사용 |
| 모니터링 | LangSmith | 멀티 에이전트 실행 과정 자동 트레이싱 |
| 패키지 관리 | uv | 빠른 의존성 해석, `pyproject.toml` + `uv.lock` |
| 배포 | Docker · GitHub Actions · EC2(t4g/arm64) | main 브랜치 push 시 자동 빌드·배포 |

> **이전 버전(notion-assistant) 대비 의존성 감소**: 개인 노트 검색을 위한 벡터 임베딩
> (Qwen3-Embedding-0.6B, torch, sentence-transformers)이 더 이상 필요 없습니다. 이 프로젝트가
> 다루는 데이터(GitHub 커밋, 노션 DB 항목)는 전부 구조화된 조회로 처리 가능하기 때문입니다. 이는
> 배포 이미지 크기와 런타임 메모리 요구량도 함께 줄여줍니다.

---

## 프로젝트 구조

> 아래는 **현재 구현된 파일 기준**입니다. 목표 아키텍처(3-에이전트) 대비 미구현 항목은
> [구현 현황](#구현-현황)을 참고하세요.

```
dev-retro-agent/
├── src/
│   ├── main.py                        # FastAPI 앱, 정적 파일 마운트(캐시 비활성화)
│   │
│   ├── core/
│   │   ├── config.py                  # pydantic-settings 기반 환경변수
│   │   └── llm.py                     # LLM 인스턴스 (Gemini / Claude 전환 지점)
│   │
│   ├── router/
│   │   └── agent_router.py            # POST /api/agent — 회고 생성 트리거
│   │
│   ├── schemas/
│   │   ├── agent_schema.py            # AgentRequest / AgentResponse
│   │   └── retro_schema.py            # RetroDraft
│   │
│   ├── graph/
│   │   ├── graph.py                   # 노드·엣지 조립, MemorySaver 체크포인터
│   │   ├── state.py                   # AgentState (messages, retro_draft, repo, date)
│   │   └── nodes/
│   │       ├── agent.py               # ReAct 루프 + 라우팅 + finalize
│   │       └── notion_write.py        # notion_writer
│   │
│   ├── tools/
│   │   ├── list_repo.py               # list_repos
│   │   ├── fetch_commits.py           # fetch_commits
│   │   ├── fetch_diff.py              # fetch_diff (repo는 InjectedState로 주입)
│   │   └── create_or_update_entry.py  # 노션 페이지 생성 + 마크다운→블록 변환
│   │
│   ├── services/
│   │   └── notion_client.py           # Notion API 클라이언트
│   │
│   └── prompts/
│       └── AGENT_PROMPT.yaml          # 시스템 프롬프트
│
├── static/                            # 테스트용 채팅 콘솔 (index.html, script.js, style.css)
├── Dockerfile
├── docker-compose.yml
└── .github/workflows/deploy.yml       # main push → arm64 빌드 → EC2 재기동
```

---

## 설치 및 실행

### 1. 패키지 설치

```bash
uv sync
```

### 2. 환경변수 설정

프로젝트 루트에 `.env` 파일을 만들고 아래 값을 채웁니다.

```env
# =====langsmith 설정=====
LANGSMITH_TRACING=true
LANGSMITH_ENDPOINT=https://api.smith.langchain.com
LANGSMITH_API_KEY=
LANGSMITH_PROJECT=

# =====GCP 설정=====
GOOGLE_API_KEY=

# =====Cluade 설정=====
ANTHROPIC_API_KEY=

# =====Notion 설정=====
NOTION_API_KEY=
NOTION_PARENT_PAGE_URL=

# =====Git Hub 설정=====
GITHUB_TOKEN=
```

| 변수 | 발급 방법 |
|---|---|
| `GOOGLE_API_KEY` | Google AI Studio에서 발급 |
| `ANTHROPIC_API_KEY` | Claude로 교체해 쓸 때만 필요 |
| `GITHUB_TOKEN` | GitHub Settings → Developer settings → Personal access tokens (`repo` 권한) |
| `NOTION_API_KEY` | Notion Integrations에서 Internal Integration 생성 |
| `NOTION_PARENT_PAGE_URL` | 회고를 저장할 부모 페이지의 노션 URL을 **그대로 복사해서 붙여넣기**.
  `field_validator`가 URL 끝의 32자리 문자열을 자동으로 추출하므로 ID만 따로 잘라낼 필요 없음 |

> **주의 1**: `NOTION_API_KEY`만으로는 접근할 수 없습니다. 노션에서 부모 페이지를 열고
> `•••` → 연결(Connections) → 생성한 Integration을 **직접 추가**해야 합니다. 이 단계를 빠뜨리면
> `Could not find page with ID: ...` 오류가 발생합니다.
>
> **주의 2**: 배포 환경(EC2)의 `.env`는 로컬과 별개입니다. `.env`는 `.dockerignore`에 있어
> 이미지에 굽지 않고 `docker-compose`의 `env_file`로 런타임 주입되므로, 새 변수를 추가했다면
> 서버의 `.env`도 갱신하고 `docker compose up -d --force-recreate`로 컨테이너를 재생성해야 합니다.

### 3. 노션 부모 페이지 준비

빈 페이지를 하나 만들고 위 Integration을 연결하기만 하면 됩니다. 속성이 있는 데이터베이스를
직접 만들 필요는 없습니다 — 그 페이지 밑에 회고용 인라인 데이터베이스가 필요 시점에 자동
생성됩니다 (구현 상태는 [구현 현황](#구현-현황) 참고).

### 4. 서버 실행

```bash
uv run uvicorn src.main:app --reload
```

- 채팅 콘솔: `http://localhost:8000`
- Swagger UI: `http://localhost:8000/docs`

---

## 설계 결정

<details>
<summary><b>왜 2개 도구가 아니라 멀티 에이전트인가</b></summary>

처음엔 `generate_daily_report` + `write_report` 2개 도구를 하나의 ReAct 루프가 호출하는 구조를
고려했습니다. 하지만 이 구조는 내부가 고정 순서 파이프라인이라 "정교한 워크플로우"이지 "멀티
에이전트"라 부르기 어려웠습니다. 그래서 각자 독립된 도구 접근과 판단 범위를 가진 `commit_analyst` /
`report_writer` / `notion_writer` 세 에이전트로 재설계했습니다. 다만 전체 무제한 자율성(에이전트가
전체 실행 순서까지 매번 판단)은 스코프 규율(완성도 우선)과 충돌하므로, 에이전트 **사이**의 순서는
고정하고 자율성은 각 에이전트 **내부**로만 한정했습니다.

여기서 구분해야 할 것은 **"도구가 여러 개인 것"과 "에이전트가 여러 개인 것"은 다른 축**이라는
점입니다. 도구가 2개든 3개든, 그것을 부를지 말지 판단하는 주체가 하나면 그건 여전히 단일
에이전트입니다. 멀티 에이전트가 성립하려면 (1) 판단 루프가 여러 개이고, (2) 각자 책임 범위가
다르며, (3) 그 사이에 구조화된 산출물을 넘기는 핸드오프가 있어야 합니다.
</details>

<details>
<summary><b>왜 "diff를 볼지 말지"를 조건부 엣지가 아니라 에이전트 내부 ReAct 루프로 두는가</b></summary>

처음 설계에서는 이 판단이 그래프의 조건부 엣지 하나였습니다. 그런데 이러면 커밋이 여러 개일 때도
전체에 대해 한 번만 갈리는 형식적 분기가 되어, "각 커밋을 보고 판단한다"는 의도와 맞지 않았습니다.
그래서 `commit_analyst`를 `fetch_commits`·`fetch_diff`에 `bind_tools`한 자기만의 `agent ⇄ tools`
루프(ReAct)로 바꿔, 커밋별로 필요한 만큼 반복 판단하게 했습니다. 같은 이유로 `report_writer`의
`fetch_readme` 호출도 고정 호출이 아니라 루프 안에서 필요하다고 판단할 때만 호출합니다. 다만 판단
성격이 다른 "근거검증 재생성"(이미 만든 결과물을 스스로 채점)까지 이 루프에 욱여넣지는 않았습니다 —
ReAct는 "외부에서 무엇을 더 관찰할지"를 위한 패턴이라, 자기 채점은 기존 CRAG의 명시적 리트라이
엣지(`grade_hallucination` 패턴)로 남겨뒀습니다.

**실행 중 확인한 한계**: 이 구조는 "몇 번 반복하고 언제 멈출지"를 LLM이 스스로 정하기 때문에
신뢰성 한계가 뚜렷합니다. 프롬프트에 "무조건 모든 커밋에 대해 `fetch_diff`를 호출하라"고 최대
강도로 명시했는데도, 10개가 넘는 커밋 중 한 번도 호출하지 않고 커밋 메시지만으로 회고를 지어내는
경우가 있었습니다. 이는 "안 한 일을 지어내지 않는다"는 이 프로젝트의 핵심 원칙과 정면으로
충돌하므로, **순회 자체는 코드(`for` 루프)가 보장하고 LLM에는 커밋 하나 단위의 좁은 판단만 맡기는**
하이브리드 구조로 전환하는 것이 개선 방향입니다. 프롬프트 강도를 높이는 것으로는 해결되지 않는
문제라는 것을 실험으로 확인했습니다.
</details>

<details>
<summary><b>왜 <code>repo</code>를 LLM이 채우지 않고 <code>InjectedState</code>로 주입하는가</b></summary>

`repo`는 하나의 실행 안에서 절대 바뀌지 않는 고정값입니다. 그런데 초기 구조에서는 매
`fetch_diff` 호출마다 LLM이 이 값을 처음부터 다시 생성해야 했고, 대화가 길어질수록 오타·환각이
누적됐습니다. 실제로 `"hochan00/langgraph-agent"`가 `"hochan00/langgraph-asset"`으로 바뀌거나,
인자 키 이름 자체가 `"repo"`가 아닌 깨진 문자열로 생성되어 GitHub API가 404를 반환했습니다.

`InjectedState`로 선언하면 해당 인자가 **LLM에게 노출되는 도구 스키마에서 아예 제외되고**,
`ToolNode`가 실행 시점에 그래프 상태에서 값을 주입합니다. LLM이 틀릴 수 있는 지점 자체를
없애는 것이, 프롬프트로 정확성을 요구하는 것보다 확실합니다. 같은 원칙으로 `date`도 LLM에게 묻지
않고 코드가 직접 계산합니다.
</details>

<details>
<summary><b>왜 프롬프트를 YAML로 분리하고 <code>load_prompt</code>는 쓰지 않는가</b></summary>

프롬프트 문구는 코드보다 훨씬 자주 바뀝니다. 문구만 고친 커밋을 코드 변경과 구분하고 diff
가독성을 확보하기 위해 `src/prompts/*.yaml`로 분리했습니다.

다만 LangChain의 `load_prompt()`는 `langchain-core 1.2.21`부터 **deprecated**이며 2.0.0에서
제거 예정입니다. 또한 이 함수는 `_type`/`input_variables`/`template` 형식의 전용 스키마만
인식해서, 사람이 읽고 고치기 좋은 자유 형식 YAML과 맞지 않습니다(자유 형식 YAML을 넘기면
`ValidationError`). 그래서 `yaml.safe_load`로 직접 파싱한 뒤
`ChatPromptTemplate.from_messages`로 구성하는 방식을 택했습니다.
</details>

<details>
<summary><b>왜 노션 저장을 프리폼 페이지가 아니라 데이터베이스로 하는가</b></summary>

Notion API의 `search` 엔드포인트는 페이지 제목만 검색합니다(본문 검색 불가). 프리폼 페이지 트리로
저장하면 "오늘 항목이 이미 있는지" 확인할 때 이 제약에 걸립니다. 반면 레포명·날짜를 정식 속성으로
갖는 데이터베이스는 `databases.query`로 정확한 필터링이 가능해 이 문제를 원천적으로 피합니다. 이
프로젝트가 다루는 데이터(레포+날짜)가 애초에 표 형태로 구조화하기 적합하다는 점도 이 선택을
뒷받침합니다.
</details>

<details>
<summary><b>왜 지금은 개인 액세스 토큰(PAT)만 쓰는가 — Runtime Context는 갖췄지만 OAuth는 안 함</b></summary>

각 도구는 더 이상 `settings.GITHUB_TOKEN`처럼 전역 설정을 직접 읽지 않습니다. `StateGraph(context_schema=RetroContext)` +
도구의 `runtime: ToolRuntime[RetroContext]`로 **"이번 실행은 어떤 자격증명으로"를 실행 단위로 주입받는
구조는 이미 갖췄습니다.** 즉 다중 사용자 지원의 전제 조건(요청마다 다른 토큰을 흘려보낼 수 있는
배관)은 완성된 상태입니다.

다만 그 위에 얹을 **GitHub OAuth 로그인은 만들지 않기로 결정**했습니다. 이유는 다중 사용자
서비스를 안 만들어서가 아니라, **이 프로젝트가 짧게 배포했다가 내리는 포트폴리오용**이기 때문입니다
— 그 짧은 구간에 낯선 사용자가 실제로 로그인해 자기 계정으로 쓸 상황 자체가 없어서, OAuth의
효용(사용자별 토큰 격리)이 성립하지 않습니다. 반면 OAuth(콜백 처리·세션·토큰 저장)는 이
프로젝트가 보여주려는 핵심(LangGraph ReAct 루프·멀티 에이전트·HITL)과 무관한 별도 영역이라,
시간을 쓸 가치 대비 비용이 안 맞습니다.

그래서 지금은 `agent_router.py`가 `settings`에서 읽은 **하나의 전역 토큰 값**을 모든 요청의
Context에 동일하게 채워 넣는 상태입니다 — 배관(Context 주입)은 다중 사용자용으로 만들어졌지만,
그 배관에 흐르는 값 자체는 여전히 1인분입니다. Notion도 같은 이유로 OAuth 앱화하지 않고 API 키
직접 입력 방식을 유지합니다. (실제로 여러 사용자가 동시에 쓰는 서비스가 된다면 왜 이 구조로는
부족한지는 [`md2notionpage`의 `os.environ` 인증 절충](#앞으로-구현할-것) 항목에 정리해뒀습니다 —
현재는 토큰이 시스템 전체에 하나뿐이라 안전하지만, 진짜 다중 사용자가 되는 순간 경합 조건이 됩니다.)
</details>

---

## 구현 현황

목표는 위 [멀티 에이전트 구조](#멀티-에이전트-구조)이며, 현재는 **단일 `agent` 노드가 커밋 분석과
회고 작성을 함께 담당하는 중간 단계**입니다. 전체 파이프라인(커밋 조회 → diff 확인 → 회고 작성 →
노션 저장)이 끝까지 동작하는 것을 먼저 확인한 뒤, 에이전트 분리를 진행하는 순서로 작업 중입니다.

### 지금까지 구현한 것

- **GitHub 연동 도구 3종** — `list_repos`(최근 한 달 커밋 레포 조회), `fetch_commits`(커밋
  `sha`+`message` 조회), `fetch_diff`(커밋별 파일명·patch 조회)
- **ReAct 루프** — 세 도구를 `bind_tools`로 바인딩해 커밋별로 diff 확인 여부를 반복 판단
- **커밋 접두사 기반 판단 프롬프트** — `feat`/`fix`/`refactor`는 diff 확인, `chore`/`docs` 등은
  메시지만으로 판단하도록 YAML 프롬프트에 규칙 명시
- **`InjectedState` 기반 `repo` 주입** — LLM이 레포명을 재생성하다 틀리는 문제를 구조적으로 차단
- **자격증명 Runtime Context 주입** — `StateGraph(context_schema=RetroContext)` +
  도구의 `runtime: ToolRuntime[RetroContext]`로 `github_token`/`notion_api_key`/`notion_page_id`를
  실행 단위로 주입. State가 아닌 Context라 체크포인터에 저장되지 않고 LLM 도구 스키마에도
  노출되지 않음 (`InjectedState`와 같은 원칙)
- **3분기 라우팅** — `continue`(도구 실행) / `end`(회고 생성) / `wait`(인사·되묻기는 저장 없이 종료)
- **`RetroDraft` 구조화 출력** — 모델별로 다른 `content` 형태(문자열 / 블록 리스트)를
  `_extract_text()`로 정규화
- **노션 저장** — 데이터베이스에 페이지 생성, 마크다운(제목·불릿·굵게)을 노션 블록으로 변환
- **대화 상태 유지** — `MemorySaver` 체크포인터 + `thread_id` 기반 세션
- **테스트용 채팅 콘솔** — 정적 프론트엔드(마크다운 렌더링, IME 조합 중 Enter 무시 처리)
- **배포 파이프라인** — Dockerfile, docker-compose, GitHub Actions(arm64 크로스 빌드 → EC2 재기동)

### 앞으로 구현할 것

- **GitHub OAuth 로그인 — 보류**: 실행 단위 자격증명 주입 구조는 만들어뒀지만, 이 프로젝트는
  잠깐 배포했다가 내리는 포트폴리오용이라 실제로 낯선 여러 사용자가 지속적으로 로그인해 쓸 상황이
  없음. 그래서 OAuth 자체는 지금 스코프에서 제외하고, 이미 갖춰진 Context 주입 구조로 "확장
  가능하게 설계는 해뒀다"는 상태로 남겨둠 (판단 근거는 [설계 결정](#설계-결정) 참고)
- **노션 저장 방식 전환 — 부모 페이지 + 인라인 DB 자동 생성**: 지금은 데이터베이스를 미리 만들어
  ID를 `.env`에 넣어야 하는데, 사용자가 노션에서 속성까지 맞춰 DB를 직접 만들어야 해서 진입장벽이
  높음. 부모 페이지 하나만 만들어 연결해두면, 그 밑에 인라인 데이터베이스를 첫 실행 시 자동
  생성하는 방식으로 전환 (`_get_or_create_database`: `blocks.children.list`로 기존 인라인 DB
  확인 → 없으면 `databases.create(..., is_inline=True)`)
- **마크다운 → 노션 변환을 `md2notionpage`로 교체**: 직접 구현한 `_markdown_to_blocks`는
  제목·리스트·굵게 3종류만 지원하고 노션의 블록당 2000자 제한도 처리하지 않음. `md2notionpage`
  라이브러리로 교체. 다만 이 라이브러리는 `NOTION_SECRET` 환경변수로만 인증해서(함수 인자로 토큰을
  못 받음) Context 주입 원칙과 어긋남 — 호출 직전 `os.environ["NOTION_SECRET"] = runtime.context["notion_api_key"]`로
  값 출처는 Context를 유지한 채 라이브러리 요구사항에 맞추는 절충안을 씀. 실제 다중 사용자 환경이
  되기 전까지(=OAuth 전까지)는 시스템 전체에 토큰이 하나뿐이라 안전함
- **자체 회고 데이터베이스(SQLite) + 열람 화면** — Notion 없이도 서비스 화면에서 회고 목록/상세를
  바로 볼 수 있도록 자체 저장소를 두고, Notion 저장은 연동되어 있을 때만 자동으로 함께 실행되는
  선택 기능으로 전환. 배포 시 컨테이너 재생성에도 데이터가 남도록 볼륨 마운트 필요
  (ChromaDB 볼륨을 제거했던 것과 반대로, 이번엔 새로 추가해야 함)
- **기간 지정 조회** — 지금은 "오늘" 하루로 고정. `fetch_commits`에 `since`/`until`을 추가해
  레포 전체 이력(현재는 필터 없이 전부 조회됨) 대신 특정 기간만 가져오고, 사용자가 하루·주간 등
  기간을 직접 선택할 수 있도록 확장
- **커밋 순회를 코드가 보장하도록 리팩터링** — 현재는 LLM이 `fetch_diff` 호출 횟수를 스스로
  정해서, 커밋이 많을 때 일부만 확인하거나 아예 건너뛰는 문제가 있음. `for` 루프로 순회를
  강제하고 LLM에는 커밋 하나 단위의 좁은 판단만 맡기는 하이브리드 구조로 전환
- **`commit_analyst` 분리 + `CommitAnalysis` 구조화 출력** — 커밋 분석을 독립 에이전트로 분리하고
  `has_activity`(활동 없음 조기 종료 분기), `commit_count`, `summary`, `key_changes`를 산출
- **`report_writer` 분리 + `fetch_readme`** — 회고 작성을 독립 에이전트로 분리하고, 배경 맥락이
  필요할 때만 README를 조회하는 루프 추가
- **근거검증(grounding) 루프** — 생성된 회고가 `key_changes`에 실제로 근거하는지 검증하고,
  실패 시 최대 2회 재생성하는 명시적 리트라이 엣지 추가
- **`check_existing_entry`** — `databases.query`로 같은 레포·날짜 항목이 이미 있는지 확인해
  신규 생성 대신 갱신 처리 (현재는 항상 새 페이지 생성)
- **`confirm_action` HITL** — `interrupt` 기반 저장 전 승인 절차. 거절 시 수정 요청을 반영해
  회고를 다시 작성하고 이전 안과의 차이를 보여준 뒤 재승인
- **버튼 기반 트리거** — 현재는 채팅 메시지로 트리거. 프론트엔드 레포 선택 UI +
  `github_router`(에이전트가 아닌 일반 API)를 만들어 `repo`/`date`를 명시적 입력으로 전환
- **`github_client.py` 분리** — 현재 각 도구 파일에 흩어져 있는 PyGithub 호출을 서비스 레이어로 통합
