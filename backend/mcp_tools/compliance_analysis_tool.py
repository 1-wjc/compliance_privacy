"""
내용 충족도 분석 도구
기존 utils.analysis의 내용 충족도 분석 기능을 래핑하여 채팅 인터페이스에서 사용할 수 있도록 합니다.
"""

import pandas as pd
import os
from typing import Dict, List, Union
from utils.analysis import analyze_content_compliance_phased
from utils.guideline_processor import process_guideline


class ComplianceAnalysis:
    def __init__(self):
        pass
    
    def analyze(self, company_df: Union[pd.DataFrame, List[Dict]], guideline_version: str) -> Dict:
        """
        내용 충족도 분석을 수행합니다.
        
        Args:
            company_df: 기업 개인정보 처리방침 DataFrame 또는 딕셔너리 리스트
            guideline_version: 작성지침 버전
            
        Returns:
            Dict: 분석 결과
        """
        try:
            # 작성지침 로드
            guideline_content_all = process_guideline(guideline_version)
            
            # 필수 조항만 선택
            mandatory_clauses = []
            for item in guideline_content_all:
                clause_title = item['clause']
                if '(해당시)' not in clause_title and '(권장)' not in clause_title:
                    mandatory_clauses.append(item)
            
            # 기업 조항을 딕셔너리 리스트로 변환
            if isinstance(company_df, pd.DataFrame):
                company_clauses = company_df.to_dict('records')
            elif isinstance(company_df, list):
                company_clauses = company_df
            else:
                # 다른 타입인 경우 DataFrame으로 변환 시도
                company_clauses = pd.DataFrame(company_df).to_dict('records')
            
            # 내용 충족도 분석 수행
            compliance_results = analyze_content_compliance_phased(company_clauses, mandatory_clauses, guideline_version)
            
            # 기본 분석 결과 DataFrame 생성
            basic_df = pd.DataFrame([
                {
                    "필수 지침 조항명": item['clause'],
                    "작성여부": "✅" if item['is_compliant'] else "❌",
                    "매칭된 기업 조항명": item['related_content'],
                    "이유": item['detailed_explanation'][:100] + "..." if len(item['detailed_explanation']) > 100 else item['detailed_explanation']
                }
                for item in compliance_results
            ])
            
            # 상세 분석 결과 DataFrame 생성
            detailed_df = pd.DataFrame([
                {
                    "필수 지침 조항명": item['clause'],
                    "충족 여부": "✅" if item['is_compliant'] else "❌",
                    "관련 기업 조항": item['related_content'],
                    "상세 설명": item['detailed_explanation']
                }
                for item in compliance_results
            ])
            
            # 통계 계산
            total_clauses = len(compliance_results)
            compliant_clauses = sum(1 for item in compliance_results if item['is_compliant'])
            compliance_rate = (compliant_clauses / total_clauses * 100) if total_clauses > 0 else 0
            
            return {
                'success': True,
                'message': f"✅ 내용 충족도 분석 완료: {compliant_clauses}/{total_clauses} 조항 충족 ({compliance_rate:.1f}%)",
                'basic_df': basic_df,
                'detailed_df': detailed_df,
                'raw_results': compliance_results,
                'stats': {
                    'total_clauses': total_clauses,
                    'compliant_clauses': compliant_clauses,
                    'compliance_rate': compliance_rate,
                    'guideline_version': guideline_version
                }
            }
            
        except Exception as e:
            return {
                'success': False,
                'message': f"❌ 내용 충족도 분석 중 오류가 발생했습니다: {str(e)}",
                'basic_df': None,
                'detailed_df': None,
                'raw_results': [],
                'stats': {}
            }
    
    def save_results(self, basic_df: pd.DataFrame, detailed_df: pd.DataFrame, 
                    output_base_path: str, company_name: str, timestamp_folder: str = None) -> Dict:
        """
        분석 결과를 CSV 파일로 저장합니다.
        
        Args:
            basic_df: 기본 분석 결과 DataFrame
            detailed_df: 상세 분석 결과 DataFrame
            output_base_path: 기본 출력 경로
            company_name: 회사명
            timestamp_folder: 타임스탬프 폴더명 (기업명+시간)
            
        Returns:
            Dict: 저장 결과
        """
        try:
            # 타임스탬프 폴더가 제공되지 않으면 현재 시간으로 생성
            if timestamp_folder is None:
                from datetime import datetime
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                timestamp_folder = f"{company_name}_{timestamp}"
            
            # 출력 디렉토리 생성 (기본경로/기업명+시간/)
            output_path = os.path.join(output_base_path, timestamp_folder)
            os.makedirs(output_path, exist_ok=True)
            
            # 파일명 생성 (기존 파일명 유지)
            basic_filename = f"{company_name}_compliance_basic.csv"
            detailed_filename = f"{company_name}_compliance_detailed.csv"
            
            basic_filepath = os.path.join(output_path, basic_filename)
            detailed_filepath = os.path.join(output_path, detailed_filename)
            
            # CSV 파일 저장
            basic_df.to_csv(basic_filepath, index=False, encoding='utf-8-sig')
            detailed_df.to_csv(detailed_filepath, index=False, encoding='utf-8-sig')
            
            return {
                'success': True,
                'message': f"✅ 내용 충족도 분석 결과 저장 완료: {timestamp_folder}/{basic_filename}, {detailed_filename}",
                'basic_filepath': basic_filepath,
                'detailed_filepath': detailed_filepath,
                'basic_filename': basic_filename,
                'detailed_filename': detailed_filename,
                'timestamp_folder': timestamp_folder
            }
            
        except Exception as e:
            return {
                'success': False,
                'message': f"❌ 결과 저장 중 오류가 발생했습니다: {str(e)}",
                'basic_filepath': None,
                'detailed_filepath': None,
                'basic_filename': None,
                'detailed_filename': None,
                'timestamp_folder': None
            }