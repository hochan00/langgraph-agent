# DevLog Agent

> GitHub 커밋과 실제 코드 변경 내역(diff)을 근거로 그날의 개발 작업 내용을 정리해, Obsidian 데일리 노트로 남겨주는 LLM 에이전트

---

## 소개

하루 동안 무엇을 개발했는지 정리해 두면 작업 이력을 관리하고 나중에 돌아보기 좋지만, 매일 직접 쓰기는 번거롭습니다.
그런데 그날 한 작업은 이미 GitHub 커밋과 코드 변경 이력에 가장 정확하게 남아 있습니다.

DevLog Agent는 이 기록을 읽어 하루의 작업 내용을 자동으로 정리합니다. 단, 커밋 메시지만 요약하면 실제로 코드가 어떻게
바뀌었는지 확인하지 않은 채 그럴듯한 문장을 만들어낼 수 있습니다. 그래서 이 에이전트는 **"실제로 한 작업만 적는다"** 를
원칙으로 합니다.

## 요구사항

### 기능

| 기능 | 설명 |
|---|---|
| 일일 활동 수집 | 지정한 날짜(기본: 어제)에 작성한 커밋을 모든 레포에서 모아 레포별로 묶습니다 |
| 근거 기반 분석 | 커밋마다 메시지만으로 충분한지, 실제 코드 변경(diff)까지 확인해야 하는지 에이전트가 판단합니다 |
| 작업 내용 정리 | 레포별 작업 요약, 주요 변경사항, 커밋 목록을 정리합니다 |
| 근거검증 | 정리된 내용이 실제 커밋·diff에 근거하는지 확인하고, 근거가 부족하면 다시 작성합니다 |
| Obsidian 저장 | 로컬 Obsidian 볼트의 데일리 노트에 저장합니다 |

### 비기능

- **사실과 판단의 분리** — 커밋 목록·레포명·날짜처럼 지어낼 여지가 없는 정보는 LLM이 아니라 코드가 채웁니다.
- **사용자 노트 보존** — 노트에 직접 쓴 내용은 건드리지 않고 자동 생성 영역만 갱신하며, 같은 날짜로 다시 실행해도 결과가 같습니다.
- **자격증명 분리** — GitHub 토큰 등 인증 정보는 환경변수로 관리하고 LLM 입력이나 실행 기록에 남기지 않습니다.
- **로컬 실행** — 볼트가 로컬에 있으므로 서버 배포 없이 로컬에서 명령어로 실행합니다.
- **추적 가능성** — 에이전트의 도구 호출과 판단 흐름을 추적할 수 있어야 합니다.

## 동작 흐름

```mermaid
flowchart TD
    START([날짜 지정]) --> collect["collect_activity<br/>그날의 전체 커밋 수집 · 레포별 정리"]
    collect -->|커밋 없음| END1([종료])
    collect --> agent

    subgraph loop["agent ⇄ tools (ReAct 루프)"]
        direction TB
        agent["agent<br/>커밋별로 diff 확인 여부 판단"]
        tools["fetch_diff"]
        agent -->|도구 호출| tools --> agent
    end

    agent -->|판단 완료| analyze["analyze_activity<br/>구조화 출력으로 레포별 분석"]
    analyze --> write

    subgraph writer["note_writer"]
        direction TB
        write["작업 내용 정리"] --> check{근거검증 통과?}
        check -->|실패 시 재작성| write
    end

    check --> DRAFT([정리 결과 반환])
    DRAFT -.->|확인 · 수정 후 저장| VAULT[(Obsidian 볼트<br/>데일리 노트)]
```

### 설계 포인트
- **자율 판단과 고정 순서의 분리** — 어떤 커밋의 diff를 볼지는 에이전트가 판단하고, 수집 → 분석 → 정리 → 검증 순서는 그래프
  엣지로 고정합니다. 판단 기준은 시스템 프롬프트에 명시하고, 프롬프트는 YAML 파일로 코드와 분리해 관리합니다.
- **사실 조회는 코드가** — 그날 어떤 커밋이 있었는지는 판단할 일이 아니라 조회할 일이므로, 수집은 LLM이 아닌 고정 노드가 담당합니다.
  diff 조회 도구도 수집된 레포·커밋이 아니면 거부합니다.
- **생성과 저장의 분리** — 그래프는 정리 결과를 만드는 데까지만 담당하고, 저장은 그래프 밖(CLI 실행기, 웹 콘솔)에서 처리합니다.
- **자격증명 분리** — GitHub 토큰은 그래프 상태가 아닌 실행 단위 컨텍스트로 전달해, LLM 입력과 추적 기록에 남지 않게 합니다.

### 커밋 수집
GitHub 커밋 검색 API로 `author:{사용자} author-date:{하루 범위}`를 조회합니다. 날짜 경계는 설정한 시간대(기본 `Asia/Seoul`) 기준입니다.
검색 API는 **기본 브랜치의 커밋만** 검색하므로, 다른 브랜치에만 있는 커밋은 수집되지 않습니다.

## 데일리 노트 형식

`{볼트}/개발기록/26.10.20.md`처럼 날짜별 노트에 저장합니다(폴더·파일명 형식은 설정으로 변경 가능). `<!-- devlog -->` 마커 사이만
자동으로 갱신되므로, 노트에 직접 적어 둔 내용은 그대로 유지되고 같은 날짜로 다시 실행해도 내용이 중복되지 않습니다.
프론트매터는 기존 키를 보존한 채 `devlog_*` 키만 갱신하며, `devlog_status: reviewed`로 바꾼 노트는 덮어쓰지 않습니다.

```markdown
---
date: 2026-10-20
devlog_status: draft
devlog_grounded: true
devlog_repos: [owner/repo]
devlog_commits: 5
---

<!-- devlog:start -->
## 개발 작업 정리

### owner/repo
(작업 요약)

**주요 변경사항**
- ...

**커밋**
- `a1b2c3d` feat: ...
<!-- devlog:end -->
```

## 기술 스택

| 분류 | 기술 |
|---|---|
| 언어 | Python 3.13 (uv) |
| 서버 | FastAPI, Uvicorn |
| 에이전트 | LangGraph, LangChain |
| LLM | Google Gemini (`gemini-3.5-flash-lite`) |
| 관측 | LangSmith |
| 외부 연동 | PyGithub (GitHub API) |
| 저장 | Obsidian (로컬 볼트 마크다운) |
| 프론트엔드 | HTML / CSS / JavaScript |

## 프로젝트 구조

```
langgraph-agent/
├── src/
│   ├── main.py                 # FastAPI 앱, 웹 콘솔 서빙
│   ├── core/                   # 환경변수 설정, LLM 생성, 날짜 계산
│   ├── router/                 # API 엔드포인트
│   ├── services/               # GitHub 커밋 수집
│   ├── graph/
│   │   ├── graph.py            # 노드·엣지 조립
│   │   ├── runner.py           # 요청 단위 실행
│   │   ├── state.py            # 그래프 상태
│   │   ├── context.py          # 실행 단위 자격증명
│   │   └── nodes/              # 수집, 에이전트, 분석 노드
│   ├── tools/                  # diff 조회 도구
│   ├── jobs/                   # 일일 정리 실행기 (CLI)
│   ├── schemas/                # 구조화 출력·API 스키마
│   └── prompts/                # 시스템 프롬프트 (YAML)
├── static/                     # 웹 콘솔
└── tests/
```

## 시작하기

### 1. 설치
```bash
uv sync
```

### 2. 환경변수
`.env.example`을 복사해 프로젝트 루트에 `.env` 파일을 만듭니다.

```env
GOOGLE_API_KEY=
GITHUB_TOKEN=
GITHUB_LOGIN=
TIMEZONE=Asia/Seoul
OBSIDIAN_VAULT_PATH=/절대경로/내/볼트
OBSIDIAN_DAILY_DIR=개발기록
OBSIDIAN_NOTE_FORMAT=%y.%m.%d

# 선택 (LangSmith 추적)
LANGSMITH_TRACING=true
LANGSMITH_API_KEY=
LANGSMITH_PROJECT=langgraph-agent
```

| 변수 | 설명 |
|---|---|
| `GOOGLE_API_KEY` | Google AI Studio에서 발급 |
| `GITHUB_TOKEN` | GitHub Personal access token (비공개 레포까지 포함하려면 `repo` 권한) |
| `GITHUB_LOGIN` | 커밋을 검색할 GitHub 사용자 (비우면 토큰 소유자) |
| `TIMEZONE` | 날짜 경계 기준 시간대 (기본 `Asia/Seoul`) |
| `OBSIDIAN_VAULT_PATH` | Obsidian 볼트의 절대경로 |
| `OBSIDIAN_DAILY_DIR` | 볼트 안에서 노트를 저장할 폴더 (기본 `개발기록`) |
| `OBSIDIAN_NOTE_FORMAT` | 노트 파일명 날짜 형식 (기본 `%y.%m.%d` → `26.10.20.md`) |
| `LANGSMITH_*` | LangSmith 추적 설정 (사용하지 않으면 `LANGSMITH_TRACING=false`) |

### 3. 실행

CLI (현재는 저장 없이 분석 결과만 출력합니다):
```bash
uv run python -m src.jobs.daily_summary --dry-run                     # 어제 작업
uv run python -m src.jobs.daily_summary --date 2026-10-20 --dry-run   # 특정 날짜
```
커밋이 없는 날은 "활동 없음"만 출력합니다.

서버:
```bash
uv run uvicorn src.main:app --reload
```
| 엔드포인트 | 설명 |
|---|---|
| `GET /health` | 헬스체크 |
| `GET /api/days?days=14` | 최근 N일 중 커밋이 있었던 날짜와 커밋 수 |

### 4. 테스트
```bash
uv run pytest
```

## 개발 상태

- [x] 하루치 커밋 수집 (모든 레포, 설정 시간대 기준 날짜 경계)
- [x] 커밋별 diff 확인 판단 (agent ⇄ fetch_diff)
- [x] 레포별 활동 분석 (구조화 출력)
- [x] CLI 드라이런
- [ ] 작업 정리 작성과 근거검증
- [ ] Obsidian 데일리 노트 저장
- [ ] 웹 콘솔

## 향후 계획

- 기본 브랜치 외 브랜치의 커밋까지 수집 (GitHub 이벤트 API 보완)
- 주간·월간 단위 작업 정리
- PR·이슈 활동 포함
