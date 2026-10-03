# 개발 이력

2025.04.28 ~ 2025.07.25 동안 만든 모든 버전을 파일 단위로 확인하고, 결과보고서·최종 발표자료의 일정과 판단 근거를 함께 정리한 기록임. 저장소에는 최종본(v5.0)만 포함하며, 이전 버전의 코드는 포함하지 않음.

## 단계별 흐름

| 기간 | 단계 | 버전 | 무엇을, 왜 바꿨나 |
|---|---|---|---|
| 04.28 ~ 05.02 | 기획·주제 선정 | — | 금융보안원이 제공한 주제를 바탕으로 "작성지침 준수 여부 자동 검토"로 목표와 세부 주제를 정함 |
| 05.05 ~ 05.16 | 데이터 수집·전처리 | v0.1 ~ v0.2 | 개인정보보호위원회 작성지침과 5개 업권 기업의 처리방침을 수집함. 지침 PDF를 조항 단위로 비교할 수 있도록 Markdown 표로 정리하고, 지침이 개정되는 시점마다 기준이 달라 최근 4개 개정판을 모두 전처리함 |
| 05.19 ~ 05.30 | LLM 분석 | v0.3 ~ v1.0 | 프롬프팅으로 지침과 기업 조항을 반복 비교해 매핑함. 한 지침에 여러 조항이 대응하는 1:N 문제와 제목 누락 오류가 생겨 RAG·LangChain 방향을 함께 시험함. 흩어진 스크립트를 모듈 구조와 Streamlit 앱으로 묶어 중간 점검함 |
| 06.02 ~ 06.13 | RAG 도입 | v1.1 ~ v2.0 | 지침과 조항을 임베딩해 벡터 유사도로 비교함. LLM 방식보다 시간과 API 비용은 줄었지만 정확도는 비슷해 한쪽으로 대체하지 않고 병행함. 많은 기업이 처리방침을 PDF가 아닌 웹페이지로 게시해 URL 입력을 추가함 |
| 06.16 ~ 06.27 | 디버깅·분석 고도화 | v2.1 ~ v2.2 | 1:N·N:1 매핑 문제를 풀기 위해 프롬프트 고도화, 고유 키워드 우선 매칭, 내용 충족도 분석을 시도함. 그 결과 키워드+LLM, LLM, RAG, 내용 충족도의 4가지 분석 방식을 확정함 |
| 07.01 ~ 07.11 | AI Agent 구현 | v2.3 ~ v4.0 | 분석 방식과 기능이 늘면서 필요한 기능만 골라 실행하기 어렵고, 기능을 추가할 때마다 구조가 복잡해짐. 팀원 코드를 통합한 뒤 분석 기능을 도구로 분리하고, LangChain Agent가 자연어 명령에 따라 도구를 골라 실행하도록 바꿈 |
| 07.14 ~ 07.25 | UI/UX 개선 | v5.0 | Streamlit은 빠른 구현에는 유리했지만 화면 구성, 프론트엔드·백엔드 분리, 유지보수에 한계가 있어 React + Flask로 전환함. 결과 보고서를 웹에서 바로 확인하고 입력·출력 파일을 웹에서 관리하도록 개선함 |

## 버전별 변화

기간은 버전 안 파일들의 가장 이른·늦은 수정일임.

| 버전 | 기간 | 진입 파일 | 주요 변화 |
|---|---|---|---|
| v0.1 | 04.28 ~ 05.13 | `py/0513*.py` | PDF 텍스트 추출(PyPDF2)과 LLM 분석 초기 실험, Streamlit 화면 |
| v0.2 | 04.28 ~ 05.19 | `py/0430_*.py` | 지침–기업 조항 LLM 매핑 스크립트(기본 분석, 매핑 분석), 팀원별 실험 |
| v0.3 | 05.19 ~ 05.26 | `0519.py` ~ `0523_2.py`, `auto_date*.py` | 매핑 개선, RAG 실험(`0520_rag.py`), 적용일자 자동 추출 실험(정규식 → LLM, PDF·Markdown·URL 입력별) |
| v0.4 | 05.19 ~ 05.26 | `main.py` | `core/`(평가·지침 관리·매핑·방침 파싱)와 `utils/`로 모듈 구조를 재구성함 |
| v1.0 | 05.23 ~ 05.26 | `app.py` | 중간 점검용 Streamlit 앱 "개인정보 처리방침 분석 도구" |
| v1.1 | ~ 06.04 | `app.py` | 분석(`analysis.py`)·PDF 처리 수정 |
| v1.2 | ~ 06.04 | `app.py` | 지침 처리·텍스트 처리 수정 |
| v1.3 | ~ 06.11 | `app.py` | URL 입력(Selenium) 추가, 키워드 매칭용 키워드 파일 추가 |
| v2.0 | ~ 06.11 | `app.py` | 키워드 매칭을 `utils/keyword_matcher.py`로 정리, 분석 수정 |
| v2.1 | ~ 06.16 | `app.py` | 화면·분석·키워드 매칭 고도화 |
| v2.2 | ~ 06.23 | `app.py` | 분석 수정 |
| v2.2-exp | ~ 07.01 | `app.py` | v2.2에서 갈라진 실험 분기(파일 6개 수정) |
| v2.3 | ~ 07.01 | `app.py` | `rag_system.py`·`chatbot.py` 추가, 팀원 코드 통합, LangChain 도입 |
| v3.0 | ~ 07.08 | `app.py`, `app_mcp.py` | MCP Agent 도입(`utils/mcp_agent.py`, `test_mcp_agent.py`) |
| v3.0-flask | ~ 07.08 | `app.py`, `main.py` | Flask + MCP 에이전트 서버 시제품(`templates/`, `static/`). 병행 분기 |
| v3.1 | ~ 07.09 | `app.py`, `app_mcp.py` | MCP Agent·텍스트 처리 수정 |
| v3.2 | ~ 07.11 | `app.py`, `app_original.py` | 분석 기능을 `mcp_tools/` 도구로 분리하고, `app_mcp.py` 방식을 정리함 |
| v3.3 | ~ 07.11 | `app.py` | 자연어 명령 파서(`hybrid_command_parser.py`) 추가, 충족도 도구 수정 |
| v4.0 | ~ 07.11 | `agent.py`, `web_app.py` | 채팅형 LangChain Agent(`agent.py`)와 기존 분석 화면(`web_app.py`)으로 재편 |
| **v5.0** | ~ **07.18** | `backend/app.py`, `frontend/` | **Flask API(21개) + LangChain Agent(도구 12개) + React UI. 이 저장소의 코드** |

## 참고 자료

- 개인정보보호위원회 개인정보 처리방침 작성지침 4개 개정판(2020.12, 2022.03, 2024.04, 2025.04) — `backend/policy/`에 Markdown으로 포함
- 개인정보 보호법, 기업별 개인정보 처리방침 원문 — 각 기관·기업의 공개 자료(저장소 미포함)
- 참고 논문
  - A Prompt Pattern Catalog to Enhance Prompt Engineering with ChatGPT
  - Enhancing Causal Relationship Detection Using Prompt Engineering and Large Language Models
  - Large Language Models in Finance: A Survey
- LangGraph + MCP 에이전트 실습 템플릿(외부 공개 저장소) — Agent 구조 학습에 참고
