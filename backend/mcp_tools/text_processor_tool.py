"""
텍스트 처리 도구
기존 utils.text_processor 기능을 래핑하여 채팅 인터페이스에서 사용할 수 있도록 합니다.
"""

import pandas as pd
from typing import Dict, Optional
from utils.text_processor import (
    convert_to_markdown, 
    create_dataframe, 
    extract_application_date,
    select_appropriate_guideline
)
from utils.guideline_processor import get_guideline_versions


class TextProcessor:
    def __init__(self):
        pass
    
    def process_text(self, extracted_text: str) -> Dict:
        """
        추출된 텍스트를 구조화된 형태로 변환합니다.
        
        Args:
            extracted_text: PDF에서 추출된 텍스트
            
        Returns:
            Dict: 처리 결과
        """
        try:
            # 마크다운으로 변환
            markdown_text = convert_to_markdown(extracted_text)
            
            if not markdown_text:
                return {
                    'success': False,
                    'message': "❌ 텍스트를 마크다운으로 변환할 수 없습니다.",
                    'dataframe': None,
                    'application_date': None,
                    'recommended_guideline': None
                }
            
            # DataFrame 생성
            df = create_dataframe(markdown_text)
            
            if df is None or df.empty:
                return {
                    'success': False,
                    'message': "❌ 구조화된 DataFrame을 생성할 수 없습니다.",
                    'dataframe': None,
                    'application_date': None,
                    'recommended_guideline': None
                }
            
            # 적용일자 추출
            application_date = extract_application_date(extracted_text)
            
            # 작성지침 버전 추천
            guideline_versions = get_guideline_versions()
            recommended_guideline = None
            if application_date:
                recommended_guideline = select_appropriate_guideline(application_date, guideline_versions)
            # 추출 실패 시 최신 버전(2024년 4월)로 대체
            if not recommended_guideline:
                recommended_guideline = '2024년 4월'
            
            return {
                'success': True,
                'message': f"✅ 텍스트 구조화 완료: {len(df)}개 조항 추출" + \
                          (f", 적용일자: {application_date}" if application_date else ""),
                'dataframe': df,
                'application_date': application_date,
                'recommended_guideline': recommended_guideline,
                'markdown_text': markdown_text,
                'stats': {
                    'total_clauses': len(df),
                    'total_characters': len(extracted_text),
                    'markdown_length': len(markdown_text) if markdown_text else 0
                }
            }
            
        except Exception as e:
            return {
                'success': False,
                'message': f"❌ 텍스트 처리 중 오류가 발생했습니다: {str(e)}",
                'dataframe': None,
                'application_date': None,
                'recommended_guideline': None
            }
    
    def extract_date_only(self, extracted_text: str) -> Dict:
        """
        텍스트에서 적용일자만 추출합니다.
        
        Args:
            extracted_text: PDF에서 추출된 텍스트
            
        Returns:
            Dict: 추출 결과
        """
        try:
            application_date = extract_application_date(extracted_text)
            
            if application_date:
                # 작성지침 버전 추천
                guideline_versions = get_guideline_versions()
                recommended_guideline = select_appropriate_guideline(application_date, guideline_versions)
                
                return {
                    'success': True,
                    'message': f"✅ 적용일자 추출 완료: {application_date}",
                    'application_date': application_date,
                    'recommended_guideline': recommended_guideline
                }
            else:
                return {
                    'success': False,
                    'message': "❌ 적용일자를 찾을 수 없습니다.",
                    'application_date': None,
                    'recommended_guideline': None
                }
                
        except Exception as e:
            return {
                'success': False,
                'message': f"❌ 적용일자 추출 중 오류가 발생했습니다: {str(e)}",
                'application_date': None,
                'recommended_guideline': None
            }
    
    def convert_to_markdown_only(self, extracted_text: str) -> Dict:
        """
        텍스트를 마크다운으로만 변환합니다.
        
        Args:
            extracted_text: PDF에서 추출된 텍스트
            
        Returns:
            Dict: 변환 결과
        """
        try:
            markdown_text = convert_to_markdown(extracted_text)
            
            if markdown_text:
                return {
                    'success': True,
                    'message': f"✅ 마크다운 변환 완료: {len(markdown_text):,} 글자",
                    'markdown_text': markdown_text
                }
            else:
                return {
                    'success': False,
                    'message': "❌ 마크다운 변환에 실패했습니다.",
                    'markdown_text': None
                }
                
        except Exception as e:
            return {
                'success': False,
                'message': f"❌ 마크다운 변환 중 오류가 발생했습니다: {str(e)}",
                'markdown_text': None
            } 