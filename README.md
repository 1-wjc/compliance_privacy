# 개인정보 처리방침 작성 준수 여부 검토 AI Agent

기업의 개인정보 처리방침 PDF나 URL을 넣으면, 개인정보보호위원회 작성지침과 조항별로 비교해 **관련 조항·충족 여부·판단 근거**를 웹 화면과 HTML 보고서로 제공하는 서비스임. 자연어 명령을 받는 LangChain Agent가 분석 도구 12개를 골라 실행함.

- **구분:** 서울대학교 KDT 10기 캡스톤 프로젝트 · 금융보안원 연계(주제 제공 및 평가)
- **기간:** 2025.04.28 ~ 2025.07.25 (13주)
- **팀:** 4인 팀 (본인: 부팀장, 작성지침·기업 문서 수집·정리, 적용일자 추출·지침 추천 구현)
- **성과:** 종료 후 결과물을 금융보안원에 인계했으며, 기관의 컴플라이언스 AI 진단도구 개발 발표(2025.09.25 [보도자료](https://www.fsec.or.kr/bbs/detail?menuNo=69&bbsNo=11788))로 이어짐
- **기술:** Python, LangChain, OpenAI(GPT-4o·GPT-4o-mini), FAISS, Flask, React

## 배경과 문제

- 개인정보를 처리하는 기업은 개인정보 보호법 제30조에 따라 개인정보 처리방침을 공개할 의무가 있음.
- 작성지침은 필수·조건부 기재 항목을 정하며 주기적으로 개정됨(2020.12 / 2022.03 / 2024.04 / 2025.04).
- 담당자가 지침과 문서를 한 조항씩 대조하는 수작업은 시간이 많이 들고 판단이 일관되지 않음. 문서가 어느 개정판을 따라야 하는지도 함께 따져야 함.

## 접근 방법

### 주요 기능

| 기능 | 설명 |
|---|---|
| 문서 입력 | PDF 업로드 또는 URL 입력. URL은 Selenium으로 PDF화해 같은 흐름으로 처리함 |
| 문서 검증 | 업로드 문서가 개인정보 처리방침인지 LLM으로 판별함. 실패하면 키워드·문단 패턴으로 판별함 |
| 적용일자 추출과 지침 추천 | 문서 적용일자를 LLM으로 추출하고 실패하면 정규식으로 보완함. 적용일보다 늦지 않은 가장 최근 지침 개정판을 자동으로 선택함 |
| 4가지 분석 | LLM 조항 매핑, 키워드·LLM, 벡터 검색(RAG), 본문 충족도 |
| 보고서 | 요약, 항목별 충족 여부, 매칭 조항, 판단 이유를 담은 HTML 보고서 |
| AI Agent | "동양생명 키워드 분석해줘" 같은 자연어 명령으로 도구를 선택·실행함 |

#### 분석 방식

| 분석 | 처리 내용 |
|---|---|
| LLM 조항 매핑 | 지침 항목 하나에 관련 기업 조항을 최대 3개까지 연결하고 매핑 이유를 반환함 |
| 키워드·LLM | 조항 제목의 키워드 비교와 LLM 분석 경로를 구성함 |
| 벡터 검색(RAG) | OpenAIEmbeddings와 FAISS로 검색하고 유사도 점수를 냄(chunk_size 1000, overlap 200) |
| 본문 충족도 | 요구 내용 충족 여부, 관련 원문 문장, 판단 설명을 제공함 |

#### Agent 도구 (12개)

파일 찾기 · PDF 처리 · 텍스트 구조화 · 처리방침 검증 · 적용일자 추출 · LLM 분석 · 키워드 분석 · RAG 분석 · 충족도 분석 · 전체 분석 · 보고서 생성 · 공유 데이터 확인

도구 사이의 결과는 공유 상태 저장소로 전달함. 도구 선택은 GPT-4o-mini가, 문서 처리·날짜 추출·매핑·충족도 판단은 GPT-4o가 맡음.

### 시스템 구조

```
[React UI]        업로드·URL 입력 / 채팅 / 결과 미리보기 / 파일 관리   (frontend/, :3000)
     │ REST API (/api/*)
[Flask 백엔드]     업로드·분석·결과·미리보기 등 API 21개                (backend/app.py, :8080)
     │
[LangChain Agent]  자연어 명령 → 도구 선택 → 실행 → 관찰              (backend/langchain_mcp_agent.py)
     │
[도구 12개]        backend/langchain_mcp_tools.py → backend/mcp_tools/, backend/utils/
     │
[분석 기준]        작성지침 4개 개정판                                (backend/policy/)
```

## 결과

[`backend/output/동양생명_20250717_103241/`](backend/output/동양생명_20250717_103241/) — 동양생명 처리방침 분석 보고서

| 항목 | 출력 |
|---|---|
| 문서 적용일 → 선택 지침 | 2025-02-01 → 2024년 4월 |
| LLM 매핑 | 8/8 조항 (100.0%) |
| 키워드 분석 | 8/8 조항 (100.0%) |
| RAG 적절성 점수 | 85.4% |
| 본문 충족도 | 5/8 조항 (62.5%) |

관련 조항이 있어도 본문 충족 여부는 다르게 나올 수 있어 두 결과를 구분해 제공함. 수치는 이 문서에 대한 분석 출력이며, 정답 대비 모델 정확도가 아님.

## 폴더 구조

```
.
├── backend/
│   ├── app.py                   # Flask API 서버
│   ├── langchain_mcp_agent.py   # LangChain Agent
│   ├── agent_langchain_mcp.py   # Agent 실행·응답 처리
│   ├── langchain_mcp_tools.py   # Agent 도구 12개 정의
│   ├── mcp_tools/               # 분석·보고서 도구 구현
│   ├── utils/                   # PDF·텍스트 처리, 적용일자 추출, 분석, RAG
│   ├── policy/                  # 작성지침 4개 개정판(Markdown)
│   ├── input/                   # 분석할 PDF를 넣는 폴더(저장소에는 비어 있음)
│   ├── output/                  # 분석 결과(예시 1건 포함)
│   ├── requirements.txt
│   └── .env.example
├── frontend/                    # React 앱
└── docs/                        # 결과보고서·발표자료·개발 이력
```

## 실행 방법

#### 준비

- Python 3.12 (최종 백엔드 실행 기록 기준), Node.js 18 이상, Chrome(URL 입력 시 Selenium이 사용)
- OpenAI API 키. 분석할 때 API 호출 비용이 발생함

#### 1. 백엔드

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate          # macOS·Linux: source .venv/bin/activate
pip install -r requirements.txt
copy .env.example .env          # macOS·Linux: cp .env.example .env  → OPENAI_API_KEY 입력
python app.py                   # http://127.0.0.1:8080
```

#### 2. 프론트엔드

```bash
cd frontend
npm install
npm start                       # http://localhost:3000 (API는 8080으로 프록시)
```

#### 3. 사용

1. 화면의 "파일 업로드"에 처리방침 PDF를 올리거나 URL을 입력함. 기업 처리방침은 각 기업 홈페이지에 공개된 문서를 사용함.
2. 채팅창에 명령을 입력함. 예: `동양생명 키워드 분석해줘`, `씨티은행 전체 분석`, `파일 목록`, `도움말`
3. "분석결과" 패널에서 HTML 보고서를 미리보거나 내려받음.

- 저장소 사본에서 Python 3.12 가상환경 설치 → 백엔드 `/api/health` 응답(healthy), 프론트엔드 `npm ci`·`npm run build` 성공을 확인함(2026-10). `OPENAI_API_KEY`가 없으면 서버 시작 시 오류가 남.

## 배운 점

- **기준 시점도 데이터임.** 문서 내용뿐 아니라 적용일과 평가 기준의 개정 시점을 함께 다뤄야 공정한 자동 평가가 가능함.
- **규칙과 LLM은 역할을 나눌 때 효과적임.** 정해진 표현은 규칙이 빠르고 정확하고, 표기가 제각각인 부분은 LLM이 강함.
- **LLM 출력 형식을 좁게 제한하면 시스템이 단단해짐.** 적용일자를 `YYYY-MM-DD` 또는 `None`으로만 답하게 하자 후처리가 단순해지고 예외가 줄었음.
- **근거 제시가 중요함.** 점검자가 원문과 판단 이유를 직접 확인할 수 있는 구조여야 실무에서 신뢰받음.

## 팀과 역할

4인 팀으로 진행함. 본인은 부팀장으로 작성지침 4개 개정판과 기업 처리방침의 수집·정리를 맡았고, 문서 적용일자를 추출해 시점에 맞는 지침 개정판을 추천하는 기능을 구현함. 서비스 설계·구현과 발표 자료 제작·발표는 팀이 함께 수행함.

## 개발 과정

개별 실험 스크립트(v0.x) → Streamlit 분석 앱(v1.x) → 분석 고도화(v2.x) → 분석 기능 도구화와 MCP Agent(v3.x) → LangChain Agent(v4.0) → **React + Flask 서비스(v5.0, 이 저장소)** 순서로 발전함. 버전별 변화는 [docs/HISTORY.md](docs/HISTORY.md)에 정리함.

## 자료

- [결과보고서](docs/final_report.pdf) — 일정, 역할 분담, 구현 결과
- [최종 발표자료](docs/final_presentation.pdf) — 문제 정의, 분석 방식, 날짜·지침 추천 시연, 서비스 흐름
- [금융보안원 보도자료](https://www.fsec.or.kr/bbs/detail?menuNo=69&bbsNo=11788) — 결과물 인계 이후 기관의 컴플라이언스 AI 진단도구 발표
