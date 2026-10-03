"""
PDF 처리 도구
기존 utils.pdf_processor 기능을 래핑하여 채팅 인터페이스에서 사용할 수 있도록 합니다.
"""

import os
from typing import Dict
from utils.pdf_processor import extract_text_from_pdf, validate_privacy_policy


class PDFProcessor:
    def __init__(self):
        pass
    
    def process_pdf(self, file_path: str) -> Dict:
        """
        PDF 파일을 처리합니다.
        
        Args:
            file_path: PDF 파일 경로
            
        Returns:
            Dict: 처리 결과
        """
        try:
            if not os.path.exists(file_path):
                return {
                    'success': False,
                    'message': f"❌ 파일을 찾을 수 없습니다: {file_path}",
                    'extracted_text': None,
                    'is_valid': False
                }
            
            # PDF에서 텍스트 추출
            with open(file_path, 'rb') as file:
                extracted_text = extract_text_from_pdf(file)
            
            if not extracted_text or len(extracted_text.strip()) == 0:
                return {
                    'success': False,
                    'message': f"❌ PDF에서 텍스트를 추출할 수 없습니다: {os.path.basename(file_path)}",
                    'extracted_text': None,
                    'is_valid': False
                }
            
            # 개인정보 처리방침 문서인지 검증
            is_valid = validate_privacy_policy(extracted_text)
            
            if not is_valid:
                return {
                    'success': False,
                    'message': f"❌ 개인정보 처리방침 문서가 아닙니다: {os.path.basename(file_path)}",
                    'extracted_text': extracted_text,
                    'is_valid': False
                }
            
            return {
                'success': True,
                'message': f"✅ PDF 처리 완료: {os.path.basename(file_path)} ({len(extracted_text):,} 글자)",
                'extracted_text': extracted_text,
                'is_valid': True,
                'file_info': {
                    'filename': os.path.basename(file_path),
                    'size': f"{os.path.getsize(file_path) / 1024 / 1024:.1f}MB",
                    'text_length': len(extracted_text)
                }
            }
            
        except Exception as e:
            return {
                'success': False,
                'message': f"❌ PDF 처리 중 오류가 발생했습니다: {str(e)}",
                'extracted_text': None,
                'is_valid': False
            }
    
    def validate_only(self, file_path: str) -> Dict:
        """
        PDF 파일이 개인정보 처리방침인지만 검증합니다.
        
        Args:
            file_path: PDF 파일 경로
            
        Returns:
            Dict: 검증 결과
        """
        try:
            if not os.path.exists(file_path):
                return {
                    'success': False,
                    'message': f"❌ 파일을 찾을 수 없습니다: {file_path}",
                    'is_valid': False
                }
            
            # PDF에서 텍스트 추출
            with open(file_path, 'rb') as file:
                extracted_text = extract_text_from_pdf(file)
            
            if not extracted_text:
                return {
                    'success': False,
                    'message': f"❌ PDF에서 텍스트를 추출할 수 없습니다: {os.path.basename(file_path)}",
                    'is_valid': False
                }
            
            # 개인정보 처리방침 문서인지 검증
            is_valid = validate_privacy_policy(extracted_text)
            
            return {
                'success': True,
                'message': f"{'✅ 개인정보 처리방침 문서입니다' if is_valid else '❌ 개인정보 처리방침 문서가 아닙니다'}: {os.path.basename(file_path)}",
                'is_valid': is_valid
            }
            
        except Exception as e:
            return {
                'success': False,
                'message': f"❌ PDF 검증 중 오류가 발생했습니다: {str(e)}",
                'is_valid': False
            } 