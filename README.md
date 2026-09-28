# Paper2Agent Studio

논문 PDF를 업로드하면 **분석 → 새 MCP 에이전트 생성 → 실제 호출 검증 → 자동 등록**까지 진행하는 로컬 연구 작업 공간입니다. 기존 MedSAM, MedMNIST, Cellpose, HD-BET, nnU-Net, MedKG 도구와 데이터 자동 분석도 계속 사용할 수 있습니다.

## 실행

```bash
./dev.sh             # 프론트엔드 http://localhost:5173, API http://127.0.0.1:8765
./run.sh             # 빌드된 웹앱 + API http://localhost:8765
```

이미 프론트엔드가 실행 중이면 백엔드만 시작할 수 있습니다.

```bash
cd backend
.venv/bin/python -m uvicorn app.main:app --host 127.0.0.1 --port 8765
```

필수 환경: Python 3.10+, Node.js, `uv`, Poppler의 `pdftotext`/`pdfinfo`, 로그인된 Claude Code. 새 연구 코드 에이전트를 만들려면 `~/.claude/skills/paper2agent/`에 Paper2Agent 스킬 전체가 필요합니다. Claude Code 인증은 `claude auth login`으로 설정합니다. 추가 API 키 입력 없이 현재 계정을 사용합니다.

## 논문에서 에이전트 만들기

1. 첫 화면에서 PDF를 놓거나 **논문 선택하고 시작**을 누릅니다. 파일 선택 즉시 작업을 생성합니다.
2. 논문 내용과 저장소 링크를 추출하고 Claude가 분석합니다. 인용문은 해당 PDF 페이지에 실제로 존재하는지 대조합니다.
3. 저자의 코드 저장소를 찾으면 설치된 Paper2Agent/Paper2MCP 스킬로 새 연구 코드 MCP 서버를 생성합니다. 저장소는 선택 사항에서 직접 지정할 수도 있습니다.
4. 코드 저장소가 없는 논문은 별도 **논문 지식 에이전트**를 만듭니다. `paper_overview`, `paper_search`, `paper_page` 도구로 요약과 원문을 조회하며, 논문의 실험·모델을 구현했다고 표시하지 않습니다.
5. 새 서버에 실제 연결하고 도구를 호출한 뒤에만 에이전트 보관함에 자동 등록합니다. 에이전트 ZIP, 생성 보고서, 원본 PDF를 내려받을 수 있습니다.

파일은 30 MB, 300쪽까지 지원합니다. 스캔본은 미리 OCR 처리해야 합니다. PDF 텍스트 추출은 그림·수식·표의 시각 구조를 완전히 보존하지 않으므로 원본을 함께 확인하세요. 매우 긴 논문은 분석용 발췌가 페이지별로 제한되며, 전체 추출 본문은 검색 도구에서 사용할 수 있습니다. 논문 내용은 연결된 Claude 계정에 전달됩니다.

진행 중인 작업은 **작업 중단**, 실패·중단된 작업은 **다시 생성하기**로 제어합니다. 재시도는 이전 파일을 덮어쓰지 않는 새 작업 공간에서 시작합니다. 서버 재시작으로 중단된 작업은 `interrupted`로 남고 자동 과금 재실행하지 않습니다. 생성은 한 번에 한 작업씩 진행됩니다. 코드 빌드는 기본 1시간/15 USD 모델 사용량 한도를 갖고, 분석은 4분/2 USD 한도를 갖습니다. CLI 사용량 추정치와 실제 계정 청구는 다를 수 있습니다.

생성 작업은 서버에 설치된 Claude Code의 `auto` 권한 모드를 사용하며 권한 검사를 우회하지 않습니다. 모델, 데이터, 인증, 권한 또는 검증이 부족하면 완료로 표시하지 않고 원인과 재시도 방법을 보여줍니다. 각 연구 저장소에 따라 추가 패키지·데이터·GPU가 필요할 수 있습니다.

Claude 호출 실패는 안전 정책 차단, 인증, 계정 사용량, 작업별 예산, 도구 권한, 입력 길이, 응답 형식, CLI 호환성, 연결·서비스 오류로 구분해 안내합니다. 안전 정책 차단이 표시되면 논문과 요청 내용을 검토하고 오탐이 의심될 경우 Anthropic 지원팀에 문의하세요. 오류를 이유로 모델을 자동 전환하거나 권한 검사를 해제하지 않습니다. 분류되지 않은 오류는 확인되지 않은 원인을 추측하지 않으며, 원본 오류에 포함될 수 있는 비밀정보와 문서 내용을 화면에 표시하지 않습니다.

## 파일과 설정

- `backend/app/paper_automation.py`: 영속 작업 큐, 단계, 취소/재시도, 생성/검증/등록
- `backend/app/paper_documents.py`: PDF 추출, 저장소 주소 검증, 원문 인용 검증
- `backend/app/paper_worker.py`: Claude Code 스트림 실행, 시간/사용량 제한, 종료 처리
- `backend/app/paper_agent_template.py`: 논문 지식 MCP의 신뢰된 템플릿
- `frontend/src/components/PaperAutomation.jsx`: 업로드, 진행 상태, 결과와 기록
- `data/paper_runs/<id>/`: 원본, 작업 기록, 시도별 생성물
- `data/agents.json`: 이 앱이 만든 에이전트 등록 정보

등록된 에이전트는 서버 재시작 후 다시 연결됩니다. 전역 `~/.claude.json`은 기존 에이전트를 읽는 용도로 사용하고 수정하지 않습니다. 이전 `4,0TBDisk` 마운트의 등록 경로는 실제 파일이 현재 디스크에 있는 경우 현재 경로로 보정합니다. 기본 업로드·작업 디렉터리는 프로젝트 위치에서 계산합니다.

| 환경변수 | 기본값 / 용도 |
|---|---|
| `PORT` | `8765` (`run.sh`) |
| `REBUILD=1` | 프론트엔드 강제 재빌드 |
| `PAPER2AGENT_CLAUDE_BIN` | `claude` |
| `PAPER2AGENT_SKILL` | `~/.claude/skills/paper2agent/SKILL.md` |
| `PAPER2AGENT_PAPER_DIR` | `data/paper_runs` |
| `PAPER2AGENT_REGISTRY` | `data/agents.json` |
| `PAPER2AGENT_ANALYSIS_TIMEOUT` | `240`초 |
| `PAPER2AGENT_BUILD_TIMEOUT` | `3600`초 |
| `PAPER2AGENT_ANALYSIS_BUDGET_USD` | `2` |
| `PAPER2AGENT_BUILD_BUDGET_USD` | `15` |
| `PAPER2AGENT_CLAUDE_JSON` | 기존 에이전트 목록, 기본 `~/.claude.json` |
| `PAPER2AGENT_ALLOWED_ROOTS` | 기존 연구 코드 루트 (`:` 구분) |
| `PAPER2AGENT_UPLOAD_DIR`, `PAPER2AGENT_JOB_DIR`, `PAPER2AGENT_AUTO_DIR`, `PAPER2AGENT_SKILLS_DIR` | 기존 파일/실행/논문 경로 재정의 |

## API

| Method | Path | 용도 |
|---|---|---|
| POST | `/api/paper-runs` | multipart `file`(PDF), `repository`(선택), `goal`(선택) → 자동 생성 시작, HTTP 202 |
| GET | `/api/paper-runs` | 생성 작업 목록 |
| GET | `/api/paper-runs/capabilities` | 서버 준비 상태와 업로드 제한 |
| GET | `/api/paper-runs/{id}` | 단계, 활동, 분석, 검증, 생성물 |
| POST | `/api/paper-runs/{id}/cancel` | 진행 중 작업 중단 |
| POST | `/api/paper-runs/{id}/retry` | `{repository?, goal?}`로 다시 생성 |
| GET | `/api/agents`, `/api/agents/{name}/tools` | 등록 에이전트와 실행 도구 |
| POST | `/api/agents/{name}/restart` | 에이전트 재연결 |
| POST | `/api/jobs` | `{agent, tool, arguments}` 도구 실행 |
| GET | `/api/jobs`, `/api/jobs/{id}` | 실행 기록/결과 |
| POST | `/api/upload` | 기존 데이터 분석용 업로드 |
| GET | `/api/files`, `/api/files/preview` | 허용된 작업 공간의 생성물 |
| GET | `/api/papers/{skill}` 및 `/section`, `/search`, `/asset/{cat}/{name}` | 등록 에이전트의 논문 읽기 |
| POST | `/api/auto/plan`, `/api/auto/run` | 기존 데이터 자동 분석 |
| GET | `/api/auto/runs`, `/api/auto/runs/{id}` | 데이터 분석 진행 및 결과 |
| GET | `/api/samples`, `/api/stats` | 예제 데이터와 서버 현황 |

API 문서: `http://localhost:8765/docs`.

## 검증

```bash
cd backend
.venv/bin/python -m pytest tests -q
cd ../frontend
npm run build
```

논문 파이프라인 테스트는 실제 PDF 추출과 별도 MCP 프로세스의 도구 조회·호출·다운로드를 검증합니다. 외부 Claude 응답만 테스트 더블로 교체합니다. 유효하지 않은 업로드, 잘못된 원문 근거, 경로 이탈, 모델 실패, 취소, 재시도, 재시작 상태도 포함합니다.

Claude 연동 방식은 [공식 비대화형 실행 문서](https://code.claude.com/docs/en/headless)를 따릅니다.


## Q1 원고 완성: 기존 연구 결과에서 투고 원고까지

웹의 **Q1 원고 완성** 탭에서 내 초안(PDF/DOCX/MD/TXT)과 기존 결과(CSV/TSV/JSON/PDF/DOCX/TXT)를 선택합니다. 연구 유형, 언어, 목표 저널과 최신 투고 규정을 입력하면 자료 읽기 → 문헌 근거 수집 → 집필 → 별도 검토 호출 → 수정 및 재검토 → 파일 생성이 진행됩니다. 완료된 에이전트 실행 결과와 스캔에서 찾은 보고서를 선택해서 연결할 수도 있습니다. 새 실험은 실행하지 않습니다.

산출물은 Word 원고, Markdown 원고, BibTeX, 근거 JSON, 검토 보고서, 수정 내역, 전체 ZIP입니다. Word에는 작은 CSV/TSV 결과 표(최대 6열·40개 데이터 행)를 원래 값 그대로 추가합니다. 표가 큰 경우 본문 근거로 읽되 자동 표 삽입은 하지 않습니다. 본문·수치·선언문의 근거 부족은 보완 항목으로 남깁니다. 추가 자료와 저널 규정을 넣어 다시 작성하면 이전 원고와 검토 결과를 보존합니다. 취소와 서버 재시작 후 재작성도 지원합니다.

Q1은 저널의 등급입니다. 화면의 저널 정보는 **로컬 SCImago SJR 수집본의 연도·분야·Best Quartile**이며 JCR 등급이나 현재 등급 확인, 게재 확률로 해석하지 않습니다. 원고의 14개 내부 편집 항목은 모델 검토 결과이며 공식 보고 지침 전체의 준수 인증이 아닙니다. TRIPOD+AI, CLAIM 2024, STARD-AI, CONSORT/CONSORT-AI, PRISMA 등은 연구 유형별 안내로 제공하고, 기존 `Paper_Generation`의 코퍼스 기반 검토 규칙도 출처와 함께 사용합니다. 최신 저널 규정은 사용자가 제공한 내용을 기준으로 적용합니다.

숫자는 문단에 연결된 원문 발췌에서 문자열 기준으로 추적하고, 인용문은 해당 자료에서 실제로 존재하는지 확인합니다. 다른 논문의 문헌 근거만으로 본 연구의 방법·결과·윤리 선언을 통과시키지 않습니다. 의미적 지지 여부는 별도 모델 검토이며 전문가 확인이 필요합니다. 연구의 진위나 통계 분석을 재실행하지 않습니다. 누락된 연구·IRB·저자·이해상충 정보를 만들어 채우거나 자동 제출하지 않습니다.

### 연결된 연구 자원 조사

**연구 폴더 스캔**은 연결된 프로젝트의 모든 접근 가능한 폴더/파일 목록과 프로그램 확장자, 실행 파일 위치, 가상환경 패키지 목록을 조사합니다. 숨김·인증 파일, 캐시, 의존성 폴더, 심볼릭 링크는 제외합니다. 각 프로젝트는 최대 45초이며 제한에 도달하거나 접근 오류가 있으면 부분 조사로 표시합니다. 파일 본문을 일괄 읽거나 외부 모델에 전송하지 않습니다. 실제 집필에는 사용자가 선택한 자료만 복사합니다.

기본 연결 범위는 이 앱, Paper2Agent/Paper2Agent_out, MedKG, MedicalAI_Papers, NeuralNode_Research, 연결된 지식 베이스, Paper_Generation/Q1_Paper_Generation과 NeuralNode가 참조하는 문헌 DB 프로젝트입니다. 원본 연구 폴더와 프로그램은 수정하지 않습니다. 조사 결과는 `data/research/inventory.json`과 `inventory.md`에 저장합니다. 선택 가능한 결과 파일 목록은 프로젝트별 45개·전체 500개까지이며 나머지 파일은 직접 업로드할 수 있습니다.

문헌 검색은 `MedicalAI_Papers` SQLite FTS5를 읽기 전용으로 조회하므로 MedKG HTTP 서비스가 꺼져 있어도 동작합니다. 관련 문헌 최대 12건을 검색하고 상위 4건은 코퍼스에 원문 TXT가 있으면 관련 발췌를 추가합니다. 결과마다 초록/원문 발췌 범위를 표시합니다. DOI·서지·철회 플래그는 수집 시점 기준이며 외부 등록 기관에 현재 상태를 재확인하지 않습니다.

### 원고 기능 설정

| 환경 변수 | 기본값 / 의미 |
|---|---|
| `PAPER2AGENT_MANUSCRIPT_DIR` | `data/manuscripts` — 입력 스냅샷, 차수별 원고, 작업 상태 |
| `PAPER2AGENT_RESEARCH_DIR` | `data/research` — 조사 결과 |
| `PAPER2AGENT_RESEARCH_ROOTS` | 콜론으로 구분한 조사 대상 절대 경로; 생략하면 연결된 연구 프로젝트 |
| `PAPER2AGENT_CORPUS_DB` | 같은 디스크의 `MedicalAI_Papers/db/medical_ai_papers.sqlite` |
| `PAPER2AGENT_PAPER_PLATFORM` | `/media/jerisuh/HardDisk01/Paper_Generation` — 기존 편집 규칙 위치 |
| `PAPER2AGENT_MANUSCRIPT_BUDGET_USD` | `6` — Claude 호출 **1회** 한도, 정상 실행은 분석·집필·검토·수정·재검토 5회 |
| `PAPER2AGENT_MANUSCRIPT_TIMEOUT` | `900` — Claude 호출 1회 제한 시간(초) |

초안 포함 최대 10개 파일, 파일당 30 MB입니다. 텍스트/CSV/JSON 파일은 2 MB 이하의 결과 요약을 사용하세요. 모델 입력은 초안 65,000자, 추가 자료당 22,000자로 제한되며 발췌 발생 시 보완 항목으로 표시합니다. 스캔 PDF는 OCR 후 업로드해야 합니다. 업로드된 자료와 원고는 위 로컬 작업 디렉터리에 남습니다. 모델 작업은 기존 Claude CLI 로그인과 사용량을 사용합니다.

### 원고 API

- `GET /api/manuscripts/capabilities`, `GET /api/manuscripts`, `GET /api/manuscripts/{id}`
- `POST /api/manuscripts` — multipart `manuscript`, 선택 `results` 반복, `options` JSON. 옵션: `study_type`, `language`, `journal`, `journal_requirements`, `target_words`, `instructions`, `job_ids`, `resource_paths`.
- `POST /api/manuscripts/{id}/cancel`
- `POST /api/manuscripts/{id}/revise` — multipart 선택 `files` 반복, `instructions`, `journal`, `journal_requirements`
- `GET /api/research/inventory`, `POST /api/research/inventory/scan`
- `GET /api/research/journals?q=저널명`

상태 `review_ready`는 자동 검토에서 남은 문제가 없어 **저자 최종 검토용 원고**를 생성했다는 뜻입니다. `needs_evidence`에서도 원고와 보완 보고서를 내려받을 수 있습니다. 두 상태 모두 게재 승인이나 자동 제출을 뜻하지 않습니다.

보고 지침 출처: [EQUATOR AI/ML 지침 목록](https://www.equator-network.org/reporting-guidelines-study-design/artificial-intelligence-machine-learning-studies/), [TRIPOD](https://www.tripod-statement.org/), [CLAIM 2024](https://pubs.rsna.org/doi/10.1148/ryai.240300), [STARD-AI](https://www.nature.com/articles/s41591-025-03953-8), [PRISMA](https://www.prisma-statement.org/). 저널 등급 맥락: [Clarivate JCR 순위와 사분위 설명](https://clarivate.com/academia-government/blog/a-primer-on-ties-in-the-jcr/).
