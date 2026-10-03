"""
키워드 분석 도구
기존 utils.analysis의 키워드+LLM 분석 기능을 래핑하여 채팅 인터페이스에서 사용할 수 있도록 합니다.
"""

import pandas as pd
import os
from typing import Dict, List
from utils.analysis import analyze_policy_content
from utils.guideline_processor import process_guideline


class KeywordAnalysis:
    def __init__(self):
        pass
    
    def analyze(self, company_df: pd.DataFrame, guideline_version: str) -> Dict:
        """
        키워드 매칭 + LLM을 사용하여 개인정보 처리방침을 분석합니다.
        
        Args:
            company_df: 기업 개인정보 처리방침 DataFrame
            guideline_version: 작성지침 버전
            
        Returns:
            Dict: 분석 결과
        """
        try:
            print(f"[LOG] KeywordAnalysis.analyze called with guideline_version: {guideline_version}")
            print(f"[LOG] company_df shape: {company_df.shape if company_df is not None else 'None'}")
            # 작성지침 로드
            guideline_content_all = process_guideline(guideline_version)
            print(f"[LOG] Number of guideline clauses loaded: {len(guideline_content_all)}")
            # 필수 조항만 선택
            mandatory_clauses = []
            for item in guideline_content_all:
                clause_title = item['clause']
                if '(해당시)' not in clause_title and '(권장)' not in clause_title:
                    mandatory_clauses.append(item)
            print(f"[LOG] Number of mandatory clauses: {len(mandatory_clauses)}")
            print(f"[LOG] Calling analyze_policy_content with version: {guideline_version} and {len(mandatory_clauses)} clauses")
            # 키워드 + LLM 분석 수행 (기존 함수 사용)
            analysis_results = analyze_policy_content(company_df, mandatory_clauses, guideline_version)
            
            # 결과를 DataFrame으로 변환
            analysis_df = pd.DataFrame([
                {
                    "필수 지침 조항명": item['clause'],
                    "작성여부": "✅" if item['is_matched'] else "❌",
                    "매칭된 기업 조항명": (
                        item['matched_clauses'][0]['clause_name'] 
                        if item.get('matched_clauses') and len(item['matched_clauses']) > 0 
                        else item.get('matched_clause_name', '')
                    ),
                    "이유": (
                        item['matched_clauses'][0]['explanation'] 
                        if item.get('matched_clauses') and len(item['matched_clauses']) > 0 
                        else item.get('explanation', '')
                    )
                }
                for item in analysis_results
            ])
            
            # 통계 계산
            total_clauses = len(analysis_results)
            matched_clauses = sum(1 for item in analysis_results if item['is_matched'])
            match_rate = (matched_clauses / total_clauses * 100) if total_clauses > 0 else 0
            
            return {
                'success': True,
                'message': f"✅ 키워드+LLM 분석 완료: {matched_clauses}/{total_clauses} 조항 매칭 ({match_rate:.1f}%)",
                'analysis_df': analysis_df,
                'raw_results': analysis_results,
                'stats': {
                    'total_clauses': total_clauses,
                    'matched_clauses': matched_clauses,
                    'match_rate': match_rate,
                    'guideline_version': guideline_version
                }
            }
            
        except Exception as e:
            return {
                'success': False,
                'message': f"❌ 키워드+LLM 분석 중 오류가 발생했습니다: {str(e)}",
                'analysis_df': None,
                'raw_results': [],
                'stats': {}
            }
    
    def save_results(self, analysis_df: pd.DataFrame, output_base_path: str, company_name: str, timestamp_folder: str = None) -> Dict:
        """
        분석 결과를 CSV 파일로 저장합니다.
        
        Args:
            analysis_df: 분석 결과 DataFrame
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
            filename = f"{company_name}_keyword_analysis.csv"
            filepath = os.path.join(output_path, filename)
            
            # CSV 파일 저장
            analysis_df.to_csv(filepath, index=False, encoding='utf-8-sig')
            
            return {
                'success': True,
                'message': f"✅ 키워드 분석 결과 저장 완료: {timestamp_folder}/{filename}",
                'filepath': filepath,
                'filename': filename,
                'timestamp_folder': timestamp_folder
            }
            
        except Exception as e:
            return {
                'success': False,
                'message': f"❌ 결과 저장 중 오류가 발생했습니다: {str(e)}",
                'filepath': None,
                'filename': None,
                'timestamp_folder': None
            } 