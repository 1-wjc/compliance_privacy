"""
보고서 생성 도구
모든 분석 결과를 통합하여 HTML 종합 보고서를 생성합니다.
"""

import pandas as pd
import os
from datetime import datetime
from typing import Dict, List, Optional


class ReportGenerator:
    def __init__(self):
        pass
    
    def generate_comprehensive_report(self, 
                                    company_name: str,
                                    analysis_results: Dict,
                                    output_base_path: str,
                                    timestamp_folder: str = None) -> Dict:
        """
        종합 보고서를 생성합니다.
        
        Args:
            company_name: 회사명
            analysis_results: 모든 분석 결과
            output_base_path: 기본 출력 경로
            timestamp_folder: 타임스탬프 폴더명 (기업명+시간)
            
        Returns:
            Dict: 생성 결과
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
            
            # HTML 보고서 생성
            html_content = self._generate_html_report(company_name, analysis_results)
            
            # 파일명 생성 (기존 파일명 유지)
            filename = f"{company_name}_comprehensive_report.html"
            filepath = os.path.join(output_path, filename)
            
            # HTML 파일 저장
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(html_content)
            
            return {
                'success': True,
                'message': f"✅ 종합 보고서 생성 완료: {timestamp_folder}/{filename}",
                'filepath': filepath,
                'filename': filename,
                'timestamp_folder': timestamp_folder
            }
            
        except Exception as e:
            return {
                'success': False,
                'message': f"❌ 보고서 생성 중 오류가 발생했습니다: {str(e)}",
                'filepath': None,
                'filename': None,
                'timestamp_folder': None
            }
    
    def _generate_html_report(self, company_name: str, analysis_results: Dict) -> str:
        """
        HTML 보고서 내용을 생성합니다.
        
        Args:
            company_name: 회사명
            analysis_results: 분석 결과
            
        Returns:
            str: HTML 내용
        """
        print("[DEBUG] analysis_results keys:", analysis_results.keys())
        print("[DEBUG] rag_analysis in analysis_results:", 'rag_analysis' in analysis_results)
        print("[DEBUG] rag_data:", analysis_results.get('rag_analysis'))
        # 현재 시간
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # HTML 템플릿 시작
        html = f"""
<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{company_name} 개인정보 처리방침 분석 보고서</title>
    <style>
        body {{
            font-family: 'Malgun Gothic', sans-serif;
            margin: 0;
            padding: 20px;
            background-color: #f5f5f5;
        }}
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            background-color: white;
            padding: 30px;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }}
        h1 {{
            color: #2c3e50;
            text-align: center;
            border-bottom: 3px solid #3498db;
            padding-bottom: 10px;
        }}
        h2 {{
            color: #34495e;
            margin-top: 30px;
            padding-left: 10px;
            border-left: 4px solid #3498db;
        }}
        .summary-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin: 20px 0;
        }}
        .summary-card {{
            background: #ecf0f1;
            padding: 20px;
            border-radius: 8px;
            text-align: center;
        }}
        .summary-card h3 {{
            margin: 0 0 10px 0;
            color: #2c3e50;
        }}
        .summary-card .value {{
            font-size: 24px;
            font-weight: bold;
            color: #3498db;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            margin: 20px 0;
        }}
        th, td {{
            padding: 12px;
            text-align: left;
            border-bottom: 1px solid #ddd;
        }}
        th {{
            background-color: #3498db;
            color: white;
        }}
        tr:nth-child(even) {{
            background-color: #f2f2f2;
        }}
        .status-success {{
            color: #27ae60;
            font-weight: bold;
        }}
        .status-fail {{
            color: #e74c3c;
            font-weight: bold;
        }}
        .score-high {{
            color: #27ae60;
            font-weight: bold;
        }}
        .score-medium {{
            color: #f39c12;
            font-weight: bold;
        }}
        .score-low {{
            color: #e74c3c;
            font-weight: bold;
        }}
        .metadata {{
            background-color: #ecf0f1;
            padding: 15px;
            border-radius: 5px;
            margin: 20px 0;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>📄 {company_name} 개인정보 처리방침 분석 보고서</h1>
        
        <div class="metadata">
            <p><strong>생성일시:</strong> {current_time}</p>
            <p><strong>분석 대상 기업명:</strong> {company_name}</p>
            <p><strong>기업방침 적용일자:</strong> {analysis_results.get('application_date', 'N/A')}</p>
            <p><strong>작성지침 버전:</strong> {analysis_results.get('guideline_version', 'N/A')}</p>
        </div>
"""
        
        # 분석 요약 섹션
        html += self._generate_summary_section(analysis_results)
        
        # 각 분석 결과 섹션
        if 'llm_analysis' in analysis_results:
            html += self._generate_analysis_section("🤖 LLM 프롬프팅 분석", analysis_results['llm_analysis'])
        
        if 'keyword_analysis' in analysis_results:
            html += self._generate_analysis_section("🏷️ 키워드+프롬프팅 분석", analysis_results['keyword_analysis'])
        
        if 'rag_analysis' in analysis_results:
            html += self._generate_rag_section(analysis_results['rag_analysis'])
        
        if 'compliance_analysis' in analysis_results:
            html += self._generate_compliance_section(analysis_results['compliance_analysis'])
        
        # HTML 종료
        html += """
    </div>
</body>
</html>
"""
        
        return html
    
    def _generate_summary_section(self, analysis_results: Dict) -> str:
        """요약 섹션 생성"""
        html = """
        <h2>📊 분석 요약</h2>
        <div class="summary-grid">
"""
        
        # 각 분석 결과에서 통계 추출
        if 'llm_analysis' in analysis_results:
            stats = analysis_results['llm_analysis'].get('stats', {})
            html += f"""
            <div class="summary-card">
                <h3>LLM 분석</h3>
                <div class="value">{stats.get('match_rate', 0):.1f}%</div>
                <p>{stats.get('matched_clauses', 0)}/{stats.get('total_clauses', 0)} 조항</p>
            </div>
"""
        
        if 'keyword_analysis' in analysis_results:
            stats = analysis_results['keyword_analysis'].get('stats', {})
            html += f"""
            <div class="summary-card">
                <h3>키워드 분석</h3>
                <div class="value">{stats.get('match_rate', 0):.1f}%</div>
                <p>{stats.get('matched_clauses', 0)}/{stats.get('total_clauses', 0)} 조항</p>
            </div>
"""
        
        if 'rag_analysis' in analysis_results:
            stats = analysis_results['rag_analysis'].get('stats', {})
            html += f"""
            <div class="summary-card">
                <h3>RAG 분석</h3>
                <div class="value">{stats.get('overall_score', 0):.1%}</div>
                <p>적절성 점수</p>
            </div>
"""
        
        if 'compliance_analysis' in analysis_results:
            stats = analysis_results['compliance_analysis'].get('stats', {})
            html += f"""
            <div class="summary-card">
                <h3>내용 충족도</h3>
                <div class="value">{stats.get('compliance_rate', 0):.1f}%</div>
                <p>{stats.get('compliant_clauses', 0)}/{stats.get('total_clauses', 0)} 조항</p>
            </div>
"""
        
        html += """
        </div>
"""
        return html
    
    def _generate_analysis_section(self, title: str, analysis_data: Dict) -> str:
        """일반 분석 섹션 생성"""
        html = f"""
        <h2>{title}</h2>
"""
        
        if 'analysis_df' in analysis_data and analysis_data['analysis_df'] is not None:
            df = analysis_data['analysis_df']
            if not isinstance(df, pd.DataFrame):
                df = pd.DataFrame(df)
            if not df.empty:
                html += """
        <table>
            <thead>
                <tr>
"""
                # 헤더 생성
                for col in df.columns:
                    html += f"<th>{col}</th>"
                html += """
                </tr>
            </thead>
            <tbody>
"""
                # 데이터 행 생성
                for _, row in df.iterrows():
                    html += "<tr>"
                    for col in df.columns:
                        value = str(row[col])
                        if col == "작성여부":
                            css_class = "status-success" if "✅" in value else "status-fail"
                            html += f'<td class="{css_class}">{value}</td>'
                        else:
                            html += f"<td>{value}</td>"
                    html += "</tr>"
                html += """
            </tbody>
        </table>
"""
        
        return html
    
    def _generate_rag_section(self, rag_data: Dict) -> str:
        print("[DEBUG] _generate_rag_section called with rag_data:", rag_data)
        html = """
        <h2>🤖 RAG 분석 결과</h2>
"""
        
        if 'analysis_df' in rag_data and rag_data['analysis_df'] is not None:
            df = rag_data['analysis_df']
            if not isinstance(df, pd.DataFrame):
                df = pd.DataFrame(df)
            print("[DEBUG] RAG 분석 DataFrame head:")
            print(df.head())
            print("[DEBUG] RAG 분석 DataFrame columns:", df.columns)
            print("[DEBUG] RAG 분석 DataFrame shape:", df.shape)
            if not df.empty:
                html += """
        <table>
            <thead>
                <tr>
"""
                # 헤더 생성
                for col in df.columns:
                    html += f"<th>{col}</th>"
                html += """
                </tr>
            </thead>
            <tbody>
"""
                # 데이터 행 생성
                for _, row in df.iterrows():
                    html += "<tr>"
                    for col in df.columns:
                        value = str(row[col])
                        if col == "적절성 점수":
                            try:
                                score = float(value)
                            except Exception:
                                score = 0.0
                            if score >= 0.8:
                                css_class = "score-high"
                            elif score >= 0.5:
                                css_class = "score-medium"
                            else:
                                css_class = "score-low"
                            html += f'<td class="{css_class}">{value}</td>'
                        else:
                            html += f"<td>{value}</td>"
                    html += "</tr>"
                html += """
            </tbody>
        </table>
"""
        
        return html
    
    def _generate_compliance_section(self, compliance_data: Dict) -> str:
        """내용 충족도 분석 섹션 생성"""
        html = """
        <h2>📋 내용 충족도 분석 결과</h2>
"""
        
        if 'detailed_df' in compliance_data and compliance_data['detailed_df'] is not None:
            df = compliance_data['detailed_df']
            if not isinstance(df, pd.DataFrame):
                df = pd.DataFrame(df)
            if not df.empty:
                html += """
        <table>
            <thead>
                <tr>
"""
                # 헤더 생성
                for col in df.columns:
                    html += f"<th>{col}</th>"
                html += """
                </tr>
            </thead>
            <tbody>
"""
                # 데이터 행 생성
                for _, row in df.iterrows():
                    html += "<tr>"
                    for col in df.columns:
                        value = str(row[col])
                        if col == "충족 여부":
                            css_class = "status-success" if "✅" in value else "status-fail"
                            html += f'<td class="{css_class}">{value}</td>'
                        else:
                            html += f"<td>{value}</td>"
                    html += "</tr>"
                html += """
            </tbody>
        </table>
"""
        
        return html 