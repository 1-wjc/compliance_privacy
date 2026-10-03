"""
RAG 분석 도구
기존 utils.rag_system 기능을 래핑하여 채팅 인터페이스에서 사용할 수 있도록 합니다.
"""

import pandas as pd
import os
from typing import Dict
from utils.rag_system import RAGSystem


class RAGAnalysis:
    def __init__(self, openai_api_key: str):
        self.rag_system = RAGSystem(openai_api_key)
    
    def analyze(self, company_df: pd.DataFrame, guideline_version: str) -> Dict:
        """
        RAG 시스템을 사용하여 개인정보 처리방침의 적절성을 평가합니다.
        
        Args:
            company_df: 기업 개인정보 처리방침 DataFrame
            guideline_version: 작성지침 버전
            
        Returns:
            Dict: 분석 결과
        """
        try:
            # 작성지침 벡터 스토어 구축
            self.rag_system.build_guideline_vectorstore(guideline_version)
            print("[DEBUG] RAG 분석: 벡터 스토어 구축 완료")
            
            # 기업 정책 추가
            self.rag_system.add_company_policy(company_df)
            print("[DEBUG] RAG 분석: 기업 정책 추가 완료")
            
            # 적절성 평가 수행
            print("[DEBUG] RAG 분석: 적절성 평가 시작")
            evaluation_result = self.rag_system.evaluate_adequacy(company_df)
            
            # 결과를 DataFrame으로 변환
            evaluation_df = pd.DataFrame(evaluation_result['evaluation_results'])
            
            # CSV용 DataFrame 생성
            analysis_df = pd.DataFrame([
                {
                    "필수 지침 조항명": item['guideline_clause'],
                    "적절성 점수": f"{item['adequacy_score']:.2f}",
                    "임베딩 유사도": f"{item['embedding_similarity']:.2f}",
                    "매칭된 기업 조항명": item['matched_company_clause'] or '',
                    "개선 방향": item['explanation']
                }
                for item in evaluation_result['evaluation_results']
            ])
            
            # 통계 계산
            total_score = evaluation_result['overall_score']
            high_score_count = len([item for item in evaluation_result['evaluation_results'] 
                                  if item['adequacy_score'] >= 0.8])
            medium_score_count = len([item for item in evaluation_result['evaluation_results'] 
                                    if 0.5 <= item['adequacy_score'] < 0.8])
            low_score_count = len([item for item in evaluation_result['evaluation_results'] 
                                 if item['adequacy_score'] < 0.5])
            
            return {
                'success': True,
                'message': f"✅ RAG 분석 완료: 전체 적절성 점수 {total_score:.1%}",
                'analysis_df': analysis_df,
                'evaluation_result': evaluation_result,
                'stats': {
                    'overall_score': total_score,
                    'total_score': evaluation_result['total_score'],
                    'max_score': evaluation_result['max_score'],
                    'high_score_count': high_score_count,
                    'medium_score_count': medium_score_count,
                    'low_score_count': low_score_count,
                    'guideline_version': guideline_version
                }
            }
            
        except Exception as e:
            return {
                'success': False,
                'message': f"❌ RAG 분석 중 오류가 발생했습니다: {str(e)}",
                'analysis_df': None,
                'evaluation_result': None,
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
            filename = f"{company_name}_rag_analysis.csv"
            filepath = os.path.join(output_path, filename)
            
            # CSV 파일 저장
            analysis_df.to_csv(filepath, index=False, encoding='utf-8-sig')
            
            return {
                'success': True,
                'message': f"✅ RAG 분석 결과 저장 완료: {timestamp_folder}/{filename}",
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