"""
파일 탐색 도구
input 폴더에서 PDF 파일을 찾아주는 도구입니다.
"""

import os
import glob
import unicodedata
from typing import List, Dict, Optional


class FileFinder:
    def __init__(self, input_folder: str = "input"):
        self.input_folder = input_folder
        
    def find_files(self, company_name: Optional[str] = None) -> Dict:
        """
        PDF 파일을 찾습니다.
        
        Args:
            company_name: 회사명 (선택사항)
            
        Returns:
            Dict: 검색 결과
        """
        try:
            # input 폴더가 존재하는지 확인
            if not os.path.exists(self.input_folder):
                return {
                    'success': False,
                    'message': f"📁 {self.input_folder} 폴더가 존재하지 않습니다.",
                    'files': []
                }
            
            # PDF 파일 검색
            pdf_pattern = os.path.join(self.input_folder, "*.pdf")
            all_pdf_files = glob.glob(pdf_pattern)
            
            if not all_pdf_files:
                return {
                    'success': False,
                    'message': f"📁 {self.input_folder} 폴더에 PDF 파일이 없습니다.",
                    'files': []
                }
            
            # 회사명이 지정된 경우 필터링
            if company_name:
                filtered_files = []
                # 한글 정규화 (NFC)
                company_name_normalized = unicodedata.normalize('NFC', company_name)
                
                for file_path in all_pdf_files:
                    filename = os.path.basename(file_path)
                    # 파일명도 정규화
                    filename_normalized = unicodedata.normalize('NFC', filename)
                    
                    if company_name_normalized.lower() in filename_normalized.lower():
                        filtered_files.append(file_path)
                
                if filtered_files:
                    return {
                        'success': True,
                        'message': f"🔍 '{company_name}' 관련 파일 {len(filtered_files)}개를 찾았습니다.",
                        'files': filtered_files
                    }
                else:
                    return {
                        'success': False,
                        'message': f"🔍 '{company_name}' 관련 파일을 찾을 수 없습니다.",
                        'files': all_pdf_files  # 전체 파일 목록 반환
                    }
            else:
                # 모든 파일 반환
                return {
                    'success': True,
                    'message': f"📁 총 {len(all_pdf_files)}개의 PDF 파일을 찾았습니다.",
                    'files': all_pdf_files
                }
                
        except Exception as e:
            return {
                'success': False,
                'message': f"❌ 파일 탐색 중 오류가 발생했습니다: {str(e)}",
                'files': []
            }
    
    def get_company_name_from_filename(self, file_path: str) -> str:
        """
        파일명에서 회사명을 추출합니다.
        "개인정보처리방침"을 제외하고 기업명을 찾습니다.
        
        Args:
            file_path: 파일 경로
            
        Returns:
            str: 추출된 회사명
        """
        filename = os.path.basename(file_path)
        # 한글 정규화
        filename = unicodedata.normalize('NFC', filename)
        
        # 확장자 제거
        name_without_ext = os.path.splitext(filename)[0]
        
        # "개인정보처리방침" 제거
        name_cleaned = name_without_ext.replace("개인정보처리방침", "")
        
        # 구분자로 분리하여 회사명 추출
        if '_' in name_cleaned:
            # "_"로 분리된 경우: "개인정보처리방침_우리은행" → "_우리은행" → "우리은행"
            parts = name_cleaned.split('_')
            for part in parts:
                if part.strip():  # 빈 문자열이 아닌 첫 번째 부분
                    return part.strip()
        elif '-' in name_cleaned:
            # "-"로 분리된 경우
            parts = name_cleaned.split('-')
            for part in parts:
                if part.strip():
                    return part.strip()
        else:
            # 구분자가 없는 경우 정리된 이름 그대로 반환
            if name_cleaned.strip():
                return name_cleaned.strip()
        
        # 위의 모든 경우에 해당하지 않으면 원본 파일명 반환
        return name_without_ext
    
    def list_all_files(self) -> Dict:
        """
        input 폴더의 모든 PDF 파일을 나열합니다.
        
        Returns:
            Dict: 파일 목록
        """
        result = self.find_files()
        
        if result['success']:
            file_info = []
            for file_path in result['files']:
                company_name = self.get_company_name_from_filename(file_path)
                file_size = os.path.getsize(file_path)
                file_info.append({
                    'path': file_path,
                    'filename': os.path.basename(file_path),
                    'company': company_name,
                    'size': f"{file_size / 1024 / 1024:.1f}MB"
                })
            
            return {
                'success': True,
                'message': f"📋 발견된 파일 목록:",
                'files': result['files'],
                'file_info': file_info
            }
        else:
            return result 