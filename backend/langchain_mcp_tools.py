"""
LangChain MCP Tools for Privacy Policy Analysis
LangChain을 사용하여 MCP 구조를 구현합니다.
"""

import os
import json
import pandas as pd
from datetime import datetime
from typing import Any, Dict, List, Optional
from utils.pdf_processor import validate_privacy_policy
from utils.text_processor import extract_date_with_llm
from langchain.tools import BaseTool
from pydantic import BaseModel, Field
from mcp_tools import (
    FileFinder, PDFProcessor, TextProcessor, 
    LLMAnalysis, KeywordAnalysis, RAGAnalysis, 
    ComplianceAnalysis, ReportGenerator
)
import re # Added missing import for re

# 환경 변수에서 설정값 가져오기
INPUT_FOLDER = os.getenv("INPUT_FOLDER", "input")
OUTPUT_FOLDER = os.getenv("OUTPUT_FOLDER", "output")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# MCP 스타일의 데이터 저장소 (실제 MCP 서버 대신)
class MCPDataStore:
    """MCP 스타일의 데이터 저장소"""
    
    def __init__(self):
        self.data = {
            'files': [],
            'extracted_text': None,
            'company_df': None,
            'guideline_version': '2504',
            'company_name': None,
            'file_path': None,
            'analysis_results': {},
            'current_session': {}
        }
    
    def set(self, key: str, value: Any):
        """데이터 설정"""
        self.data[key] = value
    
    def get(self, key: str, default=None):
        """데이터 가져오기"""
        return self.data.get(key, default)
    
    def clear(self):
        """데이터 초기화"""
        self.data = {
            'files': [],
            'extracted_text': None,
            'company_df': None,
            'guideline_version': '2504',
            'company_name': None,
            'file_path': None,
            'analysis_results': {},
            'current_session': {}
        }

# 전역 MCP 데이터 저장소
mcp_store = MCPDataStore()

class FileFinderInput(BaseModel):
    company_name: Optional[str] = Field(None, description="검색할 회사명 (선택사항)")

class FileFinderTool(BaseTool):
    name: str = "file_finder"
    description: str = "PDF 파일을 찾아서 목록을 반환합니다. 회사명을 지정하면 해당 회사의 파일만 찾습니다."
    args_schema: type = FileFinderInput
    
    def _run(self, company_name: Optional[str] = None) -> str:
        """파일 찾기 실행 (MCP 스타일)"""
        try:
            file_finder = FileFinder(INPUT_FOLDER)
            result = file_finder.find_files(company_name)
            
            if result['success']:
                files = result['files']
                message = f"{len(files)}개의 파일을 찾았습니다:\n"
                
                # MCP 스타일로 데이터 저장
                mcp_store.set('files', files)
                if files:
                    mcp_store.set('file_path', files[0])
                    mcp_store.set('company_name', file_finder.get_company_name_from_filename(files[0]))
                    message += f"• {mcp_store.get('company_name')}: {files[0]}\n"
                    # 추가 파일들도 표시
                    for file_path in files[1:]:
                        company = file_finder.get_company_name_from_filename(file_path)
                        message += f"• {company}: {file_path}\n"
                else:
                    message += "찾은 파일이 없습니다."
                # 로그 추가
                print("file_finder가 찾은 파일명:", files[0] if files else None)
                print("mcp_store에 저장된 file_path:", mcp_store.get('file_path'))
                return message
            else:
                return f"파일 찾기 실패: {result['message']}"
        except Exception as e:
            return f"파일 찾기 중 오류 발생: {str(e)}"

class PDFProcessorInput(BaseModel):
    file_path: Optional[str] = Field(None, description="처리할 PDF 파일 경로 (선택사항)")

class PDFProcessorTool(BaseTool):
    name: str = "pdf_processor"
    description: str = "PDF 파일을 텍스트로 추출합니다. 파일 경로를 지정하지 않으면 이전에 찾은 파일을 사용합니다."
    args_schema: type = PDFProcessorInput
    
    def _run(self, file_path: Optional[str] = None) -> str:
        # file_path 인자가 들어와도 무시하고, mcp_store에서만 읽음
        file_path = mcp_store.get('file_path')
        print(f"[LOG] PDFProcessorTool: 실제 사용되는 file_path: {file_path}")
        if not file_path:
            return "PDF 파일 경로가 없습니다. 먼저 file_finder를 실행하세요."
        pdf_processor = PDFProcessor()
        result = pdf_processor.process_pdf(file_path)
        if result['success']:
            mcp_store.set('extracted_text', result['extracted_text'])
        return result['message']

class TextProcessorInput(BaseModel):
    extracted_text: Optional[str] = Field(None, description="PDF에서 추출된 텍스트 (선택사항)")

class TextProcessorTool(BaseTool):
    name: str = "text_processor"
    description: str = "추출된 텍스트를 구조화하고 분석용 데이터프레임으로 변환합니다."
    args_schema: type = TextProcessorInput
    
    def _run(self, extracted_text: Optional[str] = None) -> str:
        """텍스트 처리 실행 (MCP 스타일)"""
        try:
            # MCP 스타일로 텍스트 결정
            if extracted_text is None:
                extracted_text = mcp_store.get('extracted_text')
                if extracted_text is None:
                    return "처리할 텍스트가 없습니다. 먼저 pdf_processor를 사용해주세요."
            
            text_processor = TextProcessor()
            result = text_processor.process_text(extracted_text)
            
            if result['success']:
                # MCP 스타일로 결과 저장
                mcp_store.set('company_df', result['dataframe'])
                mcp_store.set('guideline_version', result.get('recommended_guideline', '2504'))
                return f"텍스트 처리 완료: {result['message']}, 작성지침 버전: {mcp_store.get('guideline_version')}"
            else:
                return f"텍스트 처리 실패: {result['message']}"
        except Exception as e:
            return f"텍스트 처리 중 오류 발생: {str(e)}"

class LLMAnalysisInput(BaseModel):
    guideline_version: Optional[str] = Field(None, description="작성지침 버전 (선택사항)")

class LLMAnalysisTool(BaseTool):
    name: str = "llm_analysis"
    description: str = "LLM 프롬프팅을 사용하여 개인정보 처리방침을 분석합니다."
    args_schema: type = LLMAnalysisInput
    
    def _run(self, company_name: Optional[str] = None, guideline_version: Optional[str] = None) -> str:
        try:
            # 1. 파일 찾기
            file_finder = FileFinder(INPUT_FOLDER)
            file_result = file_finder.find_files(company_name)
            if not file_result['success'] or not file_result['files']:
                return f"파일 찾기 실패: {file_result['message']}"
            file_path = file_result['files'][0]  # 첫 번째 파일만 사용
            # 2. PDF 처리
            pdf_processor = PDFProcessor()
            pdf_result = pdf_processor.process_pdf(file_path)
            if not pdf_result['success']:
                return f"PDF 처리 실패: {pdf_result['message']}"
            # 3. 텍스트 구조화
            text_processor = TextProcessor()
            text_result = text_processor.process_text(pdf_result['extracted_text'])
            if not text_result['success']:
                return f"텍스트 처리 실패: {text_result['message']}"
            guideline = guideline_version or text_result.get('recommended_guideline', '2024년 4월')
            # 4. 분석 실행
            analyzer = LLMAnalysis()
            analysis_result = analyzer.analyze(text_result['dataframe'], guideline)
            if not analysis_result['success']:
                return f"LLM 분석 실패: {analysis_result['message']}"
            mcp_store.set('analysis_results', {'llm_analysis': analysis_result})
            return f"LLM 분석 성공: {analysis_result['message']}"
        except Exception as e:
            return f"LLM 분석 중 오류 발생: {str(e)}"

class KeywordAnalysisInput(BaseModel):
    guideline_version: Optional[str] = Field(None, description="작성지침 버전 (선택사항)")

class KeywordAnalysisTool(BaseTool):
    name: str = "keyword_analysis"
    description: str = "키워드 매칭과 프롬프팅을 사용하여 개인정보 처리방침을 분석합니다."
    args_schema: type = KeywordAnalysisInput
    
    def _run(self, company_name: Optional[str] = None, guideline_version: Optional[str] = None) -> str:
        try:
            # 1. 파일 찾기
            file_finder = FileFinder(INPUT_FOLDER)
            file_result = file_finder.find_files(company_name)
            print(f"[LOG] file_finder result: {file_result}")
            if not file_result['success'] or not file_result['files']:
                return f"파일 찾기 실패: {file_result['message']}"
            file_path = file_result['files'][0]  # 첫 번째 파일만 사용
            print(f"[LOG] file_path used for analysis: {file_path}")
            # 2. PDF 처리
            pdf_processor = PDFProcessor()
            pdf_result = pdf_processor.process_pdf(file_path)
            if not pdf_result['success']:
                return f"PDF 처리 실패: {pdf_result['message']}"
            # 3. 텍스트 구조화
            text_processor = TextProcessor()
            text_result = text_processor.process_text(pdf_result['extracted_text'])
            if not text_result['success']:
                return f"텍스트 처리 실패: {text_result['message']}"
            # guideline_version 우선순위: 인자로 받은 값 > 추출된 값 > 기본값
            guideline = guideline_version or text_result.get('recommended_guideline', '2024년 4월')
            print(f"[LOG] guideline_version used: {guideline}")
            print(f"[LOG] DataFrame shape: {text_result['dataframe'].shape if text_result['dataframe'] is not None else 'None'}")
            # 4. 분석 실행
            analyzer = KeywordAnalysis()
            print(f"[LOG] Calling analyze with guideline_version: {guideline}")
            analysis_result = analyzer.analyze(text_result['dataframe'], guideline)
            if not analysis_result['success']:
                return f"키워드 분석 실패: {analysis_result['message']}"
            mcp_store.set('analysis_results', {'keyword_analysis': analysis_result})
            return f"키워드 분석 성공: {analysis_result['message']}"
        except Exception as e:
            return f"키워드 분석 중 오류 발생: {str(e)}"

class RAGAnalysisInput(BaseModel):
    guideline_version: Optional[str] = Field(None, description="작성지침 버전 (선택사항)")

class RAGAnalysisTool(BaseTool):
    name: str = "rag_analysis"
    description: str = "RAG(Retrieval-Augmented Generation)를 사용하여 개인정보 처리방침을 분석합니다."
    args_schema: type = RAGAnalysisInput
    
    def _run(self, company_name: Optional[str] = None, guideline_version: Optional[str] = None, **kwargs) -> str:
        try:
            if not OPENAI_API_KEY:
                return "OpenAI API 키가 설정되지 않아 RAG 분석을 실행할 수 없습니다."
            # 1. 파일 찾기
            file_finder = FileFinder(INPUT_FOLDER)
            file_result = file_finder.find_files(company_name)
            if not file_result['success'] or not file_result['files']:
                return f"파일 찾기 실패: {file_result['message']}"
            file_path = file_result['files'][0]  # 첫 번째 파일만 사용
            # 2. PDF 처리
            pdf_processor = PDFProcessor()
            pdf_result = pdf_processor.process_pdf(file_path)
            if not pdf_result['success']:
                return f"PDF 처리 실패: {pdf_result['message']}"
            # 3. 텍스트 구조화
            text_processor = TextProcessor()
            text_result = text_processor.process_text(pdf_result['extracted_text'])
            if not text_result['success']:
                return f"텍스트 처리 실패: {text_result['message']}"
            guideline = guideline_version or text_result.get('recommended_guideline', '2024년 4월')
            # 4. 분석 실행
            analyzer = RAGAnalysis(OPENAI_API_KEY)
            analysis_result = analyzer.analyze(text_result['dataframe'], guideline)
            if not analysis_result['success']:
                return f"RAG 분석 실패: {analysis_result['message']}"
            mcp_store.set('analysis_results', {'rag_analysis': analysis_result})
            return f"RAG 분석 성공: {analysis_result['message']}"
        except Exception as e:
            return f"RAG 분석 중 오류 발생: {str(e)}"

class ComplianceAnalysisInput(BaseModel):
    guideline_version: Optional[str] = Field(None, description="작성지침 버전 (선택사항)")

class ComplianceAnalysisTool(BaseTool):
    name: str = "compliance_analysis"
    description: str = "내용 충족도 분석을 수행하여 개인정보 처리방침의 준수 여부를 확인합니다."
    args_schema: type = ComplianceAnalysisInput
    
    def _run(self, company_name: Optional[str] = None, guideline_version: Optional[str] = None) -> str:
        try:
            # 1. 파일 찾기
            file_finder = FileFinder(INPUT_FOLDER)
            file_result = file_finder.find_files(company_name)
            if not file_result['success'] or not file_result['files']:
                return f"파일 찾기 실패: {file_result['message']}"
            file_path = file_result['files'][0]  # 첫 번째 파일만 사용
            # 2. PDF 처리
            pdf_processor = PDFProcessor()
            pdf_result = pdf_processor.process_pdf(file_path)
            if not pdf_result['success']:
                return f"PDF 처리 실패: {pdf_result['message']}"
            # 3. 텍스트 구조화
            text_processor = TextProcessor()
            text_result = text_processor.process_text(pdf_result['extracted_text'])
            if not text_result['success']:
                return f"텍스트 처리 실패: {text_result['message']}"
            guideline = guideline_version or text_result.get('recommended_guideline', '2024년 4월')
            # 4. 분석 실행
            analyzer = ComplianceAnalysis()
            analysis_result = analyzer.analyze(text_result['dataframe'], guideline)
            if not analysis_result['success']:
                return f"충족도 분석 실패: {analysis_result['message']}"
            mcp_store.set('analysis_results', {'compliance_analysis': analysis_result})
            return f"충족도 분석 성공: {analysis_result['message']}"
        except Exception as e:
            return f"충족도 분석 중 오류 발생: {str(e)}"

class ReportGeneratorInput(BaseModel):
    company_name: Optional[str] = Field(None, description="회사명 (선택사항)")

class ReportGeneratorTool(BaseTool):
    name: str = "report_generator"
    description: str = "분석 결과를 바탕으로 종합 보고서를 생성합니다."
    args_schema: type = ReportGeneratorInput
    
    def _run(self, company_name: Optional[str] = None) -> str:
        """보고서 생성 실행 (MCP 스타일)"""
        try:
            if company_name is None:
                company_name = mcp_store.get('company_name')
            
            if company_name is None:
                return "회사명이 없습니다. 먼저 file_finder를 사용해주세요."
            
            # MCP 저장소에서 분석 결과 가져오기
            analysis_results = mcp_store.get('analysis_results', {})
            
            # 분석 결과 구성
            report_data = {
                'guideline_version': mcp_store.get('guideline_version'),
                'company_name': company_name,
                'file_info': {'filename': mcp_store.get('file_path')} if mcp_store.get('file_path') else {},
                'application_date': None
            }
            
            # 각 분석 결과 추가
            for analysis_type, result in analysis_results.items():
                report_data[analysis_type] = result
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            timestamp_folder = f"{company_name}_{timestamp}"
            
            report_generator = ReportGenerator()
            result = report_generator.generate_comprehensive_report(
                company_name, report_data, OUTPUT_FOLDER, timestamp_folder
            )
            
            if result['success']:
                # 실제 파일 경로를 포함한 링크 생성
                report_path = os.path.join(OUTPUT_FOLDER, timestamp_folder, f"{company_name}_종합보고서.html")
                if os.path.exists(report_path):
                    # 안내 멘트 추가
                    return (
                        f"보고서 생성 완료: {result['message']}\n\n"
                        f"보고서 파일은 output/{timestamp_folder} 폴더에서 직접 확인할 수 있습니다."
                    )
                else:
                    return f"보고서 생성 완료: {result['message']}"
            else:
                return f"보고서 생성 실패: {result['message']}"
        except Exception as e:
            return f"보고서 생성 중 오류 발생: {str(e)}"

class FullAnalysisTool(BaseTool):
    name: str = "full_analysis"
    description: str = "모든 분석 방법을 순차적으로 실행하여 완전한 분석을 수행합니다."
    
    def _run(self, company_name: Optional[str] = None) -> str:
        """전체 분석 실행 (MCP 스타일)"""
        try:
            # MCP 저장소 초기화
            mcp_store.clear()
            
            # 1. 파일 찾기
            file_finder = FileFinder(INPUT_FOLDER)
            file_result = file_finder.find_files(company_name)
            print(f"🔍 파일 찾기 결과: {file_result['success']} - {file_result['message']}")
            
            results = []
            if not file_result['success'] or not file_result['files']:
                # 회사명 명시
                company_label = company_name if company_name else '(회사명 미지정)'
                results.append(f"{company_label}: 파일을 찾을 수 없습니다. ({file_result['message']})")
                return f"전체 분석 완료:\n" + "\n".join(results)
            files_to_process = file_result['files']
            
            for file_path in files_to_process:
                company_name_from_file = file_finder.get_company_name_from_filename(file_path)
                print(f"📄 처리 중인 파일: {file_path} (회사명: {company_name_from_file})")
                
                # MCP 저장소에 데이터 저장
                mcp_store.set('file_path', file_path)
                mcp_store.set('company_name', company_name_from_file)
                
                # 2. PDF 처리
                pdf_processor = PDFProcessor()
                pdf_result = pdf_processor.process_pdf(file_path)
                print(f"📖 PDF 처리 결과: {pdf_result['success']} - {pdf_result['message']}")
                
                if not pdf_result['success']:
                    results.append(f"{company_name_from_file} (파일: {os.path.basename(file_path)}): PDF 처리 실패 - {pdf_result['message']}")
                    continue
                
                # MCP 저장소에 추출된 텍스트 저장
                mcp_store.set('extracted_text', pdf_result['extracted_text'])
                print(f"📝 추출된 텍스트 길이: {len(pdf_result['extracted_text'])} 문자")
                
                # 3. 텍스트 구조화
                text_processor = TextProcessor()
                text_result = text_processor.process_text(pdf_result['extracted_text'])
                print(f"📊 텍스트 구조화 결과: {text_result['success']} - {text_result['message']}")
                
                if not text_result['success']:
                    results.append(f"{company_name_from_file} (파일: {os.path.basename(file_path)}): 텍스트 처리 실패 - {text_result['message']}")
                    continue
                
                # MCP 저장소에 구조화된 데이터 저장
                mcp_store.set('company_df', text_result['dataframe'])
                mcp_store.set('guideline_version', text_result.get('recommended_guideline', '2504'))
                print(f"📋 DataFrame 크기: {text_result['dataframe'].shape if text_result['dataframe'] is not None else 'None'}")
                
                # 4. 분석 실행
                analyses = [
                    ('llm_analysis', LLMAnalysis()),
                    ('keyword_analysis', KeywordAnalysis()),
                    ('rag_analysis', RAGAnalysis(OPENAI_API_KEY) if OPENAI_API_KEY else None),
                    ('compliance_analysis', ComplianceAnalysis())
                ]
                
                analysis_results = {}
                
                for analysis_name, analyzer in analyses:
                    print(f"[DEBUG] analysis_name: {analysis_name}")
                    if analyzer is None:
                        print(f"⚠️ {analysis_name} 분석 건너뛰기: analyzer가 None")
                        continue
                    
                    try:
                        print(f"🔬 {analysis_name} 분석 시작...")
                        analysis_result = analyzer.analyze(mcp_store.get('company_df'), mcp_store.get('guideline_version'))
                        print(f"🔬 {analysis_name} 분석 결과: {analysis_result['success']} - {analysis_result['message']}")
                        
                        if analysis_result['success']:
                            print(f"[DEBUG] analysis_results key 저장: {analysis_name}")
                            analysis_results[analysis_name] = analysis_result
                            print(f"✅ {analysis_name} 분석 성공, DataFrame 크기: {analysis_result.get('analysis_df', pd.DataFrame()).shape if analysis_result.get('analysis_df') is not None else 'None'}")
                            # 분석 성공 메시지에 분석 종류, 회사명, 파일명 명시
                            results.append(f"{company_name_from_file} (파일: {os.path.basename(file_path)}): {analysis_name} 분석 성공 - {analysis_result['message']}")
                        else:
                            print(f"❌ {analysis_name} 분석 실패: {analysis_result['message']}")
                            results.append(f"{company_name_from_file} (파일: {os.path.basename(file_path)}): {analysis_name} 분석 실패 - {analysis_result['message']}")
                    except Exception as e:
                        error_msg = f"{company_name_from_file} (파일: {os.path.basename(file_path)}) {analysis_name} 분석 실패: {str(e)}"
                        print(f"💥 {error_msg}")
                        results.append(error_msg)
                
                print(f"📈 총 {len(analysis_results)}개 분석 완료")
                
                # 5. 보고서 생성
                try:
                    report_data = {
                        'guideline_version': mcp_store.get('guideline_version'),
                        'company_name': company_name_from_file,
                        'file_info': pdf_result['file_info'],
                        'application_date': text_result.get('application_date'),
                        **analysis_results
                    }
                    
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    timestamp_folder = f"{company_name_from_file}_{timestamp}"
                    
                    report_generator = ReportGenerator()
                    report_result = report_generator.generate_comprehensive_report(
                        company_name_from_file, report_data, OUTPUT_FOLDER, timestamp_folder
                    )
                    results.append(f"{company_name_from_file} (파일: {os.path.basename(file_path)}): 보고서 생성 성공 - {report_result['message']}")
                except Exception as e:
                    results.append(f"{company_name_from_file} (파일: {os.path.basename(file_path)}): 보고서 생성 실패 - {str(e)}")
            
            return f"전체 분석 완료:\n" + "\n".join(results)
        
        except Exception as e:
            return f"전체 분석 중 오류 발생: {str(e)}"

class MCPDataTool(BaseTool):
    name: str = "mcp_data"
    description: str = "MCP 저장소의 현재 데이터 상태를 확인합니다."
    
    def _run(self) -> str:
        """MCP 데이터 상태 확인"""
        try:
            data = mcp_store.data
            message = "MCP 저장소 현재 상태:\n\n"
            
            for key, value in data.items():
                if value is None:
                    message += f"• {key}: None\n"
                elif isinstance(value, (str, int, float)):
                    message += f"• {key}: {value}\n"
                elif isinstance(value, list):
                    message += f"• {key}: {len(value)}개 항목\n"
                elif isinstance(value, dict):
                    message += f"• {key}: {len(value)}개 키\n"
                else:
                    message += f"• {key}: {type(value).__name__}\n"
            
            return message
        except Exception as e:
            return f"MCP 데이터 확인 중 오류 발생: {str(e)}"

def clear_mcp_store():
    """MCP 저장소 초기화"""
    mcp_store.clear() 

class ApplicationDateExtractorTool(BaseTool):
    name: str = "application_date_extractor"
    description: str = "MCP 저장소의 추출된 텍스트에서 적용일자(날짜)만 추출하여 반환합니다. LLM 추출 우선, 실패 시 정규표현식 사용."
    args_schema: type = None

    def _run(self, input=None) -> str:
        """적용일자(날짜) 추출 (LLM 우선, 실패 시 정규표현식)"""
        try:
            text = mcp_store.get('extracted_text')
            if not text:
                return "적용일자를 추출할 텍스트가 없습니다. 먼저 pdf_processor를 사용해주세요."
            # 1. LLM 기반 추출 시도
            date_llm = extract_date_with_llm(text)
            if date_llm:
                return f"적용일자 추출 결과(LLM): {date_llm.strftime('%Y-%m-%d')}"
            # 2. 정규표현식 추출 (기존 방식)
            patterns = [
                r'(20[0-9]{2})[.\-/년 ]+([01]?[0-9])[.\-/월 ]+([0-3]?[0-9])[일]?',
                r'(20[0-9]{2})[.\-/년 ]+([01]?[0-9])[.\-/월 ]+([0-3]?[0-9])',
                r'(20[0-9]{2})[.\-/년 ]+([01]?[0-9])',
                r'(20[0-9]{2})'
            ]
            for pattern in patterns:
                match = re.search(pattern, text)
                if match:
                    year = match.group(1)
                    month = match.group(2) if len(match.groups()) > 1 else '01'
                    day = match.group(3) if len(match.groups()) > 2 else '01'
                    try:
                        month = str(int(month)).zfill(2)
                        day = str(int(day)).zfill(2)
                    except:
                        month = '01'
                        day = '01'
                    return f"적용일자 추출 결과(정규식): {year}-{month}-{day}"
            return "적용일자를 찾을 수 없습니다."
        except Exception as e:
            return f"적용일자 추출 중 오류 발생: {str(e)}"

class PrivacyPolicyValidationTool(BaseTool):
    name: str = "privacy_policy_validator"
    description: str = "MCP 저장소의 추출된 텍스트가 개인정보 처리방침 문서인지 LLM 기반으로 검증합니다."
    args_schema: type = None

    def _run(self, input=None) -> str:
        try:
            text = mcp_store.get('extracted_text')
            if not text:
                return "검증할 텍스트가 없습니다. 먼저 pdf_processor를 사용해주세요."
            is_policy = validate_privacy_policy(text)
            if is_policy:
                return "개인정보 처리방침 문서가 맞습니다."
            else:
                return "개인정보 처리방침 문서가 아닙니다."
        except Exception as e:
            return f"문서 검증 중 오류 발생: {str(e)}"

# 모든 tools를 리스트로 반환하는 함수
def get_all_mcp_tools() -> List[BaseTool]:
    """모든 MCP 스타일 LangChain tools를 반환합니다."""
    return [
        FileFinderTool(),
        PDFProcessorTool(),
        TextProcessorTool(),
        LLMAnalysisTool(),
        KeywordAnalysisTool(),
        RAGAnalysisTool(),
        ComplianceAnalysisTool(),
        ReportGeneratorTool(),
        FullAnalysisTool(),
        MCPDataTool(),
        ApplicationDateExtractorTool(),
        PrivacyPolicyValidationTool()
    ]