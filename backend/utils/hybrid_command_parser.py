"""
하이브리드 명령 파서
키워드 기반 매칭과 LLM 기반 의도 분석을 결합한 명령 처리 시스템
"""

import re
import json
import asyncio
from typing import Dict, Optional, List
from openai import OpenAI
import os
from dotenv import load_dotenv

load_dotenv()

class HybridCommandParser:
    def __init__(self):
        self.openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY")) if os.getenv("OPENAI_API_KEY") else None
        
        # 키워드 정규화 매핑
        self.keyword_mappings = {
            # LLM 관련
            '엘엘엠': 'llm',
            'LLM': 'llm',
            'llm': 'llm',
            '언어모델': 'llm',
            '대화형': 'llm',
            
            # RAG 관련
            '래그': 'rag',
            'RAG': 'rag',
            'rag': 'rag',
            '알에이지': 'rag',
            '벡터': 'rag',
            '임베딩': 'rag',
            '유사도': 'rag',
            '벡터검색': 'rag',
            '문서검색': 'rag',
            
            # 키워드 관련
            '키워드': 'keyword',
            'keyword': 'keyword',
            '키워드매칭': 'keyword',
            '단어매칭': 'keyword',
            
            # 충족도 관련
            '충족도': 'compliance',
            '컴플라이언스': 'compliance',
            'compliance': 'compliance',
            '내용충족도': 'compliance',
            '요구사항': 'compliance',
            '준수': 'compliance',
            '만족도': 'compliance'
        }
        
        # 제외할 키워드 (회사명 추출 시)
        self.excluded_words = {
            'llm', 'rag', '키워드', 'keyword', '충족도', 'compliance', '컴플라이언스',
            '분석', '해줘', '해주세요', '부탁해', '부탁합니다', '실행', '진행',
            '처리방침', '개인정보', '개인정보처리방침', '정책', '문서',
            '전체', '모든', '모두', '다', '를', '을', '이', '가', '은', '는',
            '으로', '로', '에서', '에게', '한테', '께', '만', '도', '조차', '마저',
            '파일', '목록', '설정', '도움말', 'help', 'config'
        }
    
    def normalize_command(self, command: str) -> str:
        """명령어 정규화"""
        # 소문자 변환
        normalized = command.lower()
        
        # 키워드 매핑 적용
        for original, mapped in self.keyword_mappings.items():
            normalized = normalized.replace(original.lower(), mapped)
        
        # 특수문자 정리
        normalized = re.sub(r'[^\w\s가-힣]', ' ', normalized)
        
        # 연속된 공백 제거
        normalized = re.sub(r'\s+', ' ', normalized).strip()
        
        return normalized
    
    def extract_company_name(self, command: str) -> Optional[str]:
        """회사명 추출 (조사 제거 포함)"""
        words = command.split()
        
        for word in words:
            # 길이 체크
            if len(word) <= 1:
                continue
                
            # 제외 키워드 체크
            if word.lower() in self.excluded_words:
                continue
                
            # 조사 제거
            cleaned_word = self.remove_particles(word)
            
            if cleaned_word and len(cleaned_word) > 1:
                return cleaned_word
        
        return None
    
    def remove_particles(self, word: str) -> str:
        """한국어 조사 제거"""
        particles = ['을', '를', '이', '가', '은', '는', '에', '에서', '으로', '로', '와', '과', '의', '도', '만', '부터', '까지', '께서', '한테', '에게']
        
        for particle in particles:
            if word.endswith(particle):
                return word[:-len(particle)]
        
        return word
    
    def parse_traditional(self, command: str) -> Dict:
        """전통적인 키워드 기반 파싱"""
        normalized = self.normalize_command(command)
        company_name = self.extract_company_name(command)
        
        # 개별 분석 명령 처리
        if 'llm' in normalized and '분석' in normalized:
            return {
                'success': True,
                'method': 'llm',
                'company_name': company_name,
                'confidence': 0.95,
                'source': 'traditional'
            }
        
        elif 'keyword' in normalized and '분석' in normalized:
            return {
                'success': True,
                'method': 'keyword',
                'company_name': company_name,
                'confidence': 0.95,
                'source': 'traditional'
            }
        
        elif 'rag' in normalized and '분석' in normalized:
            return {
                'success': True,
                'method': 'rag',
                'company_name': company_name,
                'confidence': 0.95,
                'source': 'traditional'
            }
        
        elif 'compliance' in normalized and '분석' in normalized:
            return {
                'success': True,
                'method': 'compliance',
                'company_name': company_name,
                'confidence': 0.95,
                'source': 'traditional'
            }
        
        elif '전체' in normalized and '분석' in normalized:
            return {
                'success': True,
                'method': 'full',
                'company_name': company_name,
                'confidence': 0.95,
                'source': 'traditional'
            }
        
        elif '분석' in normalized and not any(keyword in normalized for keyword in ['llm', 'keyword', 'rag', 'compliance']):
            return {
                'success': True,
                'method': 'full',
                'company_name': company_name,
                'confidence': 0.9,
                'source': 'traditional'
            }
        
        elif '파일' in normalized or '목록' in normalized:
            return {
                'success': True,
                'method': 'list_files',
                'company_name': None,
                'confidence': 0.95,
                'source': 'traditional'
            }
        
        elif '도움말' in normalized or 'help' in normalized:
            return {
                'success': True,
                'method': 'help',
                'company_name': None,
                'confidence': 0.95,
                'source': 'traditional'
            }
        
        elif '설정' in normalized or 'config' in normalized:
            return {
                'success': True,
                'method': 'config',
                'company_name': None,
                'confidence': 0.95,
                'source': 'traditional'
            }
        
        return {
            'success': False,
            'method': None,
            'company_name': company_name,
            'confidence': 0.0,
            'source': 'traditional'
        }
    
    def parse_with_llm(self, command: str) -> Dict:
        """LLM을 사용한 의도 분석"""
        if not self.openai_client:
            return {
                'success': False,
                'method': None,
                'company_name': None,
                'confidence': 0.0,
                'source': 'llm',
                'error': 'OpenAI API 키가 설정되지 않았습니다.'
            }
        
        try:
            prompt = f"""
다음 사용자 명령을 분석하여 의도를 파악해주세요:

명령: "{command}"

분석 기준:
1. 분석 방법 (method):
   - "llm": LLM 프롬프팅 분석
   - "keyword": 키워드+프롬프팅 분석  
   - "rag": RAG 분석 (벡터 임베딩, 유사도 검색)
   - "compliance": 내용 충족도 분석
   - "full": 전체 분석 (4가지 모두)
   - "list_files": 파일 목록 조회
   - "help": 도움말 표시
   - "config": 설정 표시

2. 회사명 추출:
   - 명령에서 회사명을 추출하세요 (조사 제거)
   - 회사명이 없으면 null

3. 신뢰도 (confidence):
   - 0.0-1.0 범위의 신뢰도
   - 명확한 의도일수록 높은 점수

응답은 반드시 다음 JSON 형식으로만 해주세요:
{{
    "method": "분석_방법",
    "company_name": "회사명_또는_null",
    "confidence": 0.95,
    "reasoning": "판단_근거"
}}
"""
            
            response = self.openai_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.0,
                max_tokens=200
            )
            
            content = response.choices[0].message.content.strip()
            
            # JSON 추출
            json_start = content.find('{')
            json_end = content.rfind('}') + 1
            
            if json_start != -1 and json_end != -1:
                json_str = content[json_start:json_end]
                parsed = json.loads(json_str)
                
                return {
                    'success': True,
                    'method': parsed.get('method'),
                    'company_name': parsed.get('company_name'),
                    'confidence': parsed.get('confidence', 0.5),
                    'reasoning': parsed.get('reasoning', ''),
                    'source': 'llm'
                }
            else:
                return {
                    'success': False,
                    'method': None,
                    'company_name': None,
                    'confidence': 0.0,
                    'source': 'llm',
                    'error': 'JSON 파싱 실패'
                }
                
        except Exception as e:
            return {
                'success': False,
                'method': None,
                'company_name': None,
                'confidence': 0.0,
                'source': 'llm',
                'error': str(e)
            }
    
    def parse_command(self, command: str) -> Dict:
        """하이브리드 명령 파싱"""
        # 1단계: 전통적인 키워드 방식 시도
        traditional_result = self.parse_traditional(command)
        
        # 높은 신뢰도로 성공하면 바로 반환
        if traditional_result['success'] and traditional_result['confidence'] >= 0.9:
            return traditional_result
        
        # 2단계: LLM 방식 시도
        llm_result = self.parse_with_llm(command)
        
        # LLM 결과가 성공적이고 신뢰도가 높으면 반환
        if llm_result['success'] and llm_result['confidence'] >= 0.7:
            return llm_result
        
        # 3단계: 두 결과 중 더 나은 것 선택
        if traditional_result['confidence'] >= llm_result['confidence']:
            return traditional_result
        else:
            return llm_result if llm_result['success'] else traditional_result 