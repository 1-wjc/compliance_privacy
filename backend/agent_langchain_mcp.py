"""
개인정보 처리방침 자동화 분석 서비스 - LangChain MCP Agent 기반 (Flask API용)
"""

import pandas as pd
import os
from datetime import datetime
import traceback
from dotenv import load_dotenv

# 환경 변수 로드
load_dotenv()

# LangChain MCP Agent 임포트
from langchain_mcp_agent import create_mcp_agent, LangChainMCPAgent

# 환경 변수에서 설정값 가져오기
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
INPUT_FOLDER = os.getenv("INPUT_FOLDER", "input")
OUTPUT_FOLDER = os.getenv("OUTPUT_FOLDER", "output")

# 전역 변수로 상태 관리 (Streamlit 세션 상태 대신)
agent = None
processing = False

def initialize_agent():
    """LangChain MCP Agent 초기화"""
    global agent
    try:
        if agent is None:
            print("LangChain MCP Agent를 초기화하고 있습니다...")
            agent = create_mcp_agent()
            print("Agent 초기화 완료!")
        return True
    except Exception as e:
        print(f"Agent 초기화 실패: {str(e)}")
        return False

def process_command_with_agent(command: str):
    """LangChain MCP Agent를 사용한 명령 처리"""
    global processing
    try:
        processing = True
        
        # Agent 초기화 확인
        if not initialize_agent():
            return {
                'success': False,
                'message': "Agent 초기화에 실패했습니다."
            }
        
        # Agent 실행
        print(f"LangChain MCP Agent가 명령을 처리하고 있습니다: {command}")
        
        result = agent.run_agent(command)
        
        return {
            'success': True,
            'message': result
        }
        
    except Exception as e:
        return {
            'success': False,
            'message': f"명령 처리 중 오류가 발생했습니다: {str(e)}"
        }
    finally:
        processing = False

def run_full_analysis(company_name: str = None):
    """전체 분석 실행 (full_analysis 도구 사용)"""
    global processing
    try:
        processing = True
        
        # Agent 초기화 확인
        if not initialize_agent():
            return {
                'success': False,
                'message': "Agent 초기화에 실패했습니다."
            }
        
        # 전체 분석 실행
        print("MCP full_analysis를 실행하고 있습니다...")
        
        result = agent.run_full_analysis(company_name)
        
        return {
            'success': True,
            'message': result
        }
        
    except Exception as e:
        return {
            'success': False,
            'message': f"전체 분석 중 오류가 발생했습니다: {str(e)}"
        }
    finally:
        processing = False

def check_mcp_data():
    """MCP 저장소 상태 확인"""
    try:
        if agent is None:
            return {
                'success': False,
                'message': "Agent가 초기화되지 않았습니다. 먼저 Agent를 초기화해주세요."
            }
        
        result = agent.check_mcp_data()
        return {
            'success': True,
            'message': result
        }
        
    except Exception as e:
        return {
            'success': False,
            'message': f"MCP 데이터 확인 중 오류가 발생했습니다: {str(e)}"
        }

def clear_mcp_store():
    """MCP 저장소 초기화"""
    try:
        if agent is None:
            return {
                'success': False,
                'message': "Agent가 초기화되지 않았습니다. 먼저 Agent를 초기화해주세요."
            }
        
        agent.clear_mcp_store()
        return {
            'success': True,
            'message': "MCP 저장소가 초기화되었습니다."
        }
        
    except Exception as e:
        return {
            'success': False,
            'message': f"MCP 저장소 초기화 중 오류가 발생했습니다: {str(e)}"
        }

def list_files():
    """파일 목록 조회"""
    try:
        if not os.path.exists(INPUT_FOLDER):
            return {
                'success': False,
                'message': f"{INPUT_FOLDER} 폴더가 존재하지 않습니다."
            }
        
        pdf_files = [f for f in os.listdir(INPUT_FOLDER) if f.endswith('.pdf')]
        
        if not pdf_files:
            return {
                'success': True,
                'message': f"{INPUT_FOLDER} 폴더에 PDF 파일이 없습니다."
            }
        
        message = f"{INPUT_FOLDER} 폴더에서 {len(pdf_files)}개의 PDF 파일을 찾았습니다:\n\n"
        for file in pdf_files:
            file_path = os.path.join(INPUT_FOLDER, file)
            file_size = os.path.getsize(file_path)
            size_mb = file_size / (1024 * 1024)
            message += f"• {file} ({size_mb:.2f} MB)\n"
        
        return {
            'success': True,
            'message': message
        }
        
    except Exception as e:
        return {
            'success': False,
            'message': f"파일 목록 조회 중 오류가 발생했습니다: {str(e)}"
        }

def show_config():
    """현재 설정 표시"""
    config_text = f"""
<h3>현재 설정</h3>
<ul>
  <li><b>Input 폴더</b>: <code>{INPUT_FOLDER}</code></li>
  <li><b>Output 폴더</b>: <code>{OUTPUT_FOLDER}</code></li>
  <li><b>OpenAI API 키</b>: {'설정됨' if OPENAI_API_KEY else '설정되지 않음'}</li>
</ul>

<h3>설정 변경 방법</h3>
<ol>
  <li>프로젝트 루트에 <code>.env</code> 파일 생성</li>
  <li>다음 내용 추가:
    <pre>
INPUT_FOLDER=your/input/path
OUTPUT_FOLDER=your/output/path
OPENAI_API_KEY=your-api-key
    </pre>
  </li>
  <li>애플리케이션 재시작</li>
</ol>

<h3>폴더 상태</h3>
<ul>
  <li>Input 폴더 존재: {'예' if os.path.exists(INPUT_FOLDER) else '아니오'}</li>
  <li>Output 폴더 존재: {'예' if os.path.exists(OUTPUT_FOLDER) else '아니오'}</li>
</ul>

<h3>Agent 정보</h3>
<ul>
  <li>Agent 상태: {'초기화됨' if agent else '초기화되지 않음'}</li>
  <li>Agent 타입: LangChain MCP Agent</li>
  <li>MCP 패키지 의존성: 없음 (LangChain만 사용)</li>
</ul>
"""
    
    return {
        'success': True,
        'message': config_text
    }

def show_help():
    """도움말 표시"""
    help_text = f'''

<div style="font-size: 1.05em; line-height: 1.7;">
  <h3>📂 파일 준비</h3>
  <ul>
    <li>📥 PDF 파일을 <code>{INPUT_FOLDER}</code> 폴더에 넣어주세요.</li>
    <li>🏷️ 파일명에 회사명을 포함시키면 더 정확한 분석이 가능합니다.<br>
      예: <code>OO기업_개인정보처리방침.pdf</code>
    </li>
    <li>🌐 <b>URL로 업로드한 경우</b>:<br>
      업로드된 파일명은 <code>[url_도메인_날짜_시간.pdf]</code> 형식입니다.<br>
      <b>url 분석을 하려면 해당 파일명을 명령어로 입력해야 합니다.</b><br>
      <b>예: <code>[url_example_com_20240612_153012.pdf] 분석해줘</b></code>
    </li>
  </ul>
  <hr>
  <h3>📋 사용 가능한 명령어</h3>
  <ul>
    <li><b>[회사명] 분석해줘</b><br>
      특정 회사의 개인정보 처리방침 분석<br>
      예: <code>ㅇㅇ카드 분석해줘</code>, <code>ㅇㅇ기업 분석해줘</code><br>
      URL로 업로드한 파일은 파일명 전체를 입력해야 분석됩니다.<br>
      예: <code>[url_example_com_20240612_153012.pdf] 분석해줘</code>
    </li>
    <li><b>분석해줘</b><br>
      📂 <code>{INPUT_FOLDER}</code> 폴더의 모든 PDF 파일 분석
    </li>
    <li><b>전체 분석해줘</b><br>
      명시적으로 전체 분석 실행
    </li>
  </ul>
  <h4>🧩 개별 분석</h4>
  <ul>
    <li><b>[회사명] LLM 분석해줘</b> : <span style="font-family:emoji;">🤖</span> LLM 프롬프팅 분석만 실행</li>
    <li><b>[회사명] 키워드 분석해줘</b> : <span style="font-family:emoji;">🏷️</span> 키워드 분석만 실행</li>
    <li><b>[회사명] RAG 분석해줘</b> : <span style="font-family:emoji;">🔗</span> RAG 분석만 실행</li>
    <li><b>[회사명] 충족도 분석해줘</b> : <span style="font-family:emoji;">📋</span> 충족도 분석만 실행</li>
  </ul>
  <h4>🗃️ MCP 관련 명령</h4>
  <ul>
    <li><b>MCP 데이터 확인</b> : <span style="font-family:emoji;">📊</span> MCP 저장소의 현재 상태 확인</li>
    <li><b>MCP 저장소 초기화</b> : <span style="font-family:emoji;">🧹</span> MCP 저장소 데이터 초기화</li>
  </ul>
  <h4>🛠️ 기타 명령</h4>
  <ul>
    <li><b>적용 날짜 추출</b> : OO기업의 개인정보 처리방침 적용날짜 추출</li>
    <li><b>문서 검증</b> : OO기업의 문서가 개인정보 처리방침이 맞는지 검증</li>
    <li><b>파일 목록</b> : <span style="font-family:emoji;">📄</span> <code>{INPUT_FOLDER}</code> 폴더의 PDF 파일 목록 확인</li>
    <li><b>설정</b> : <span style="font-family:emoji;">⚙️</span> 현재 설정 확인</li>
    <li><b>도움말</b> : <span style="font-family:emoji;">ℹ️</span> 이 도움말 표시</li>
    <li><b>도구 목록</b> : <span style="font-family:emoji;">🧰</span> 사용 가능한 도구 목록 확인</li>
  </ul>
  <hr>
  <h3>📊 분석 결과</h3>
  <ul>
    <li><span style="font-family:emoji;">📑</span> 각 분석별로 별도의 CSV 파일이 생성됩니다.</li>
    <li><span style="font-family:emoji;">📝</span> 전체 분석 시에는 HTML 종합 보고서도 생성됩니다.</li>
    <li><span style="font-family:emoji;">👁️</span> 퀵메뉴에서 "분석결과목록"을 누르면 결과 파일을 미리보기로 바로 확인할 수 있습니다.</li>
    <li><span style="font-family:emoji;">📁</span> 결과는 <code>{OUTPUT_FOLDER}/기업명_분석방법_시간/</code> 폴더에 저장됩니다.</li>
  </ul>
</div>
'''
    return {
        'success': True,
        'message': help_text
    }

def show_tools():
    """사용 가능한 도구 목록 표시"""
    try:
        if agent is None:
            return {
                'success': False,
                'message': "Agent가 초기화되지 않았습니다. 먼저 Agent를 초기화해주세요."
            }
        
        tools = agent.get_available_tools()
        message = "**사용 가능한 MCP 도구 목록:**\n\n"
        
        for tool_name in tools:
            description = agent.get_tool_description(tool_name)
            message += f"• **{tool_name}**: {description}\n"
        
        return {
            'success': True,
            'message': message
        }
        
    except Exception as e:
        return {
            'success': False,
            'message': f"도구 목록 조회 중 오류가 발생했습니다: {str(e)}"
        } 

# 서버 시작 시 자동으로 Agent를 초기화
initialize_agent() 