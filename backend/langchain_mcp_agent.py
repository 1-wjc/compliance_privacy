"""
LangChain MCP Agent for Privacy Policy Analysis
LangChain을 사용하여 MCP agent를 구현합니다.
"""

import os
import json
import pandas as pd
from datetime import datetime
from typing import Dict, List, Any
from dotenv import load_dotenv

# LangChain imports
from langchain.agents import AgentExecutor, create_openai_tools_agent
from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.schema import SystemMessage, HumanMessage
from langchain.tools import BaseTool

# Custom MCP tools import
from langchain_mcp_tools import get_all_mcp_tools, clear_mcp_store

# 환경 변수 로드
load_dotenv()

# 환경 변수에서 설정값 가져오기
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
INPUT_FOLDER = os.getenv("INPUT_FOLDER", "input")
OUTPUT_FOLDER = os.getenv("OUTPUT_FOLDER", "output")

class LangChainMCPAgent:
    """LangChain을 사용한 MCP Agent"""
    
    def __init__(self):
        """Agent 초기화"""
        self.llm = None
        self.agent = None
        self.tools = None
        self.agent_executor = None
        
        # OpenAI API 키 확인
        if not OPENAI_API_KEY:
            raise ValueError("OpenAI API 키가 설정되지 않았습니다. .env 파일에 OPENAI_API_KEY를 설정해주세요.")
        
        self._initialize_agent()
    
    def _initialize_agent(self):
        """Agent 초기화"""
        # LLM 설정
        self.llm = ChatOpenAI(
            model="gpt-4o-mini",
            temperature=0,
            api_key=OPENAI_API_KEY
        )
        
        # MCP Tools 가져오기
        self.tools = get_all_mcp_tools()
        
        # System prompt 설정 (MCP 스타일)
        system_prompt = """당신은 개인정보 처리방침 분석을 위한 MCP(Model Context Protocol) Agent입니다.

MCP 특징:
- 각 도구는 MCP 저장소를 통해 데이터를 공유합니다
- 도구들은 순차적으로 실행되며 이전 단계의 결과를 자동으로 사용합니다
- 데이터는 MCP 저장소에 자동으로 저장되고 다음 도구에서 사용됩니다

주요 기능:
1. PDF 파일에서 개인정보 처리방침 텍스트 추출
2. 4가지 분석 방법으로 개인정보 처리방침 분석:
   - LLM 프롬프팅 분석
   - 키워드+프롬프팅 분석  
   - RAG 분석
   - 내용 충족도 분석
3. 분석 결과를 CSV 파일과 HTML 보고서로 저장

사용 가능한 MCP 도구들:
- file_finder: PDF 파일 찾기 (MCP 저장소에 파일 정보 저장)
- pdf_processor: PDF 텍스트 추출 (MCP 저장소에서 파일 경로 가져옴)
- text_processor: 텍스트 구조화 (MCP 저장소에서 추출된 텍스트 사용)
- llm_analysis: LLM 분석 (MCP 저장소에서 구조화된 데이터 사용)
- keyword_analysis: 키워드 분석 (MCP 저장소에서 구조화된 데이터 사용)
- rag_analysis: RAG 분석 (MCP 저장소에서 구조화된 데이터 사용)
- compliance_analysis: 충족도 분석 (MCP 저장소에서 구조화된 데이터 사용)
- report_generator: 보고서 생성 (MCP 저장소의 모든 분석 결과 사용)
- full_analysis: 모든 분석을 한 번에 실행 (MCP 저장소 자동 관리)
- mcp_data: MCP 저장소의 현재 상태 확인

중요한 규칙:
1. 사용자가 특정 분석만 요청하면 해당 분석만 실행하세요:
   - "LLM 분석해줘" → llm_analysis만 실행
   - "키워드 분석해줘" → keyword_analysis만 실행
   - "RAG 분석해줘" → rag_analysis만 실행
   - "충족도 분석해줘" → compliance_analysis만 실행

2. 사용자가 전체 분석을 요청하면 full_analysis를 사용하세요:
   - "분석해줘", "전체 분석해줘", "[회사명] 분석해줘" → full_analysis 실행

3. 개별 분석 후에는 해당 분석에 대한 보고서만 생성하세요.

MCP 워크플로우:
1. file_finder로 분석할 파일 찾기 → MCP 저장소에 파일 정보 저장
2. pdf_processor로 PDF 텍스트 추출 → MCP 저장소에 추출된 텍스트 저장
3. text_processor로 텍스트 구조화 → MCP 저장소에 구조화된 데이터 저장
4. 요청된 분석 방법만 실행 → MCP 저장소에 분석 결과 저장
5. report_generator로 해당 분석에 대한 보고서 생성

**매우 중요: pdf_processor는 반드시 file_finder가 저장한 file_path만 사용해야 한다. 명령어에서 추출한 파일명, 임의로 생성한 파일명, 사용자가 입력한 파일명은 절대 사용하지 마라. file_finder가 실행된 후 mcp_store에 저장된 file_path만 pdf_processor가 사용해야 한다. 만약 file_finder의 결과가 아닌 다른 파일명을 사용하면 분석이 반드시 실패한다. 반드시 file_finder의 결과를 그대로 사용하라.**

사용자 요청에 따라 적절한 MCP 도구들을 순차적으로 사용하여 분석을 완료하세요.
각 도구는 MCP 저장소를 통해 데이터를 자동으로 공유하므로 별도의 데이터 전달이 필요하지 않습니다.
"""
        
        # Agent prompt template
        prompt = ChatPromptTemplate.from_messages([
            ("system", system_prompt),
            MessagesPlaceholder(variable_name="chat_history"),
            ("human", "{input}"),
            MessagesPlaceholder(variable_name="agent_scratchpad"),
        ])
        
        # Agent 생성
        self.agent = create_openai_tools_agent(
            llm=self.llm,
            tools=self.tools,
            prompt=prompt
        )
        
        # Agent executor 생성
        self.agent_executor = AgentExecutor(
            agent=self.agent,
            tools=self.tools,
            verbose=True,
            handle_parsing_errors=True,
            max_iterations=20
        )
    
    def run_agent(self, user_input: str) -> str:
        """Agent 실행"""
        try:
            result = self.agent_executor.invoke({
                "input": user_input,
                "chat_history": []
            })
            return result["output"]
        except Exception as e:
            return f"Agent 실행 중 오류 발생: {str(e)}"
    
    def get_available_tools(self) -> List[str]:
        """사용 가능한 도구 목록 반환"""
        return [tool.name for tool in self.tools]
    
    def get_tool_description(self, tool_name: str) -> str:
        """특정 도구의 설명 반환"""
        for tool in self.tools:
            if tool.name == tool_name:
                return tool.description
        return f"도구 '{tool_name}'를 찾을 수 없습니다."
    
    def run_full_analysis(self, company_name: str = None) -> str:
        """전체 분석 실행 (full_analysis 도구 사용)"""
        try:
            full_analysis_tool = next(tool for tool in self.tools if tool.name == "full_analysis")
            result = full_analysis_tool._run(company_name)
            return result
        except Exception as e:
            return f"전체 분석 중 오류 발생: {str(e)}"
    
    def check_mcp_data(self) -> str:
        """MCP 저장소 상태 확인"""
        try:
            mcp_data_tool = next(tool for tool in self.tools if tool.name == "mcp_data")
            result = mcp_data_tool._run()
            return result
        except Exception as e:
            return f"MCP 데이터 확인 중 오류 발생: {str(e)}"
    
    def clear_mcp_store(self):
        """MCP 저장소 초기화"""
        clear_mcp_store()

def create_mcp_agent() -> LangChainMCPAgent:
    """MCP Agent 인스턴스 생성"""
    return LangChainMCPAgent()

# 사용 예시
if __name__ == "__main__":
    try:
        agent = create_mcp_agent()
        print("LangChain MCP Agent가 성공적으로 생성되었습니다.")
        print(f"사용 가능한 도구들: {agent.get_available_tools()}")
        
        # MCP 저장소 상태 확인
        print("\nMCP 저장소 초기 상태:")
        print(agent.check_mcp_data())
        
        # 테스트 실행
        result = agent.run_agent("KB카드 분석해줘")
        print(f"\n결과: {result}")
        
        # MCP 저장소 최종 상태 확인
        print("\nMCP 저장소 최종 상태:")
        print(agent.check_mcp_data())
        
    except Exception as e:
        print(f"Agent 생성 실패: {str(e)}") 