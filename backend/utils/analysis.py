from openai import OpenAI
import os
from dotenv import load_dotenv
from typing import List, Dict
from .keyword_matcher import match_by_keywords
import openai
import pandas as pd
import streamlit as st
import re

# Load environment variables
load_dotenv()

# Configure OpenAI
client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

def extract_clause_number(clause):
    match = re.match(r"^\s*(\d+)", clause)
    return int(match.group(1)) if match else float('inf')

def analyze_policy_content(company_df, guideline_clauses: List[dict], version: str) -> List[dict]:
    """기업 개인정보처리방침 분석 수행
    
    Args:
        company_df: 기업 개인정보처리방침 DataFrame
        guideline_clauses: 작성지침 조항 목록
        version: 작성지침 버전
    
    Returns:
        List[dict]: 분석 결과 목록
    """
    # 기업 조항을 딕셔너리 리스트로 변환
    company_clauses = company_df.to_dict('records')
    
    # 1단계: 키워드 기반 매칭
    matched_results, unmatched_guidelines = match_by_keywords(company_clauses, guideline_clauses, version)

    st.subheader("키워드 매칭 중간 분석 결과")
    analysis_df = pd.DataFrame([
        {
            "필수 지침 조항명": item['clause'],
            "작성여부": "✅" if item['is_matched'] else "❌",
            "매칭된 기업 조항명": item.get('matched_clause_name', ''),
            "이유": item['explanation'],
            "정렬기준": extract_clause_number(item['clause'])
        }
        for item in matched_results
    ])

    analysis_df = analysis_df.sort_values(by="정렬기준").drop(columns=["정렬기준"])
    # Streamlit 관련 코드 제거
    # st.session_state.analysis_df = analysis_df
    # st.dataframe(st.session_state.analysis_df, use_container_width=True)

    final_result = []
    
    # 2단계: 매칭되지 않은 항목들에 대해 LLM 분석 수행
    for guideline in guideline_clauses:
        try:
            llm_result = analyze_with_llm(company_clauses, guideline)
            if llm_result:  # None이 아닌 경우에만 추가
                final_result.append(llm_result)
            else:
                # llm_result가 None인 경우 기본 결과 추가
                final_result.append({
                    'clause': guideline['clause'],
                    'is_matched': False,
                    'matched_clause_name': '',
                    'explanation': 'LLM 분석 실패'
                })
        except Exception as e:
            print(f"Error in LLM analysis: {str(e)}")
            final_result.append({
                'clause': guideline['clause'],
                'is_matched': False,
                'matched_clause_name': '',
                'explanation': f'LLM 분석 중 오류 발생: {str(e)}'
            })
    
    return final_result

def analyze_with_llm(company_clauses: List[dict], guideline: dict) -> dict:
    """LLM을 사용하여 단일 가이드라인 조항에 대한 분석 수행"""
    try:
        # 기업 조항들을 DataFrame 형식의 문자열로 변환
        df = pd.DataFrame(company_clauses)
        
        prompt = f"""
다음은 개인정보처리방침 작성지침의 조항과 내용입니다:

조항: {guideline['clause']}
지침 내용: {guideline['content']}

다음은 기업의 개인정보처리방침 조항과 내용입니다:

{df.to_string()}

위 지침과 기업의 개인정보처리방침을 비교하여 다음을 엄밀히 분석해주세요:
1. 하나의 가이드라인이 여러(최대 3개) 기업 조항에 관련될 수 있습니다. 이 경우 모든 기업 조항을 적어주세요.
2. 가이드라인의 조항 제목 및 본문 내용이 어떤 기업의 개인정보처리방침 조항과 그의 본문 내용과 연관이 있는지
3. 기업의 개인정보처리방침에서 해당 지침과 관련된 내용이 있는지
4. 있다면 어떤 조항과 내용이 매칭되는지
5. 매칭 여부에 대한 설명

응답은 다음 JSON 형식으로 해주세요:
{{
    "is_matched": true/false,
    "matched_clauses": [
        {{
            "clause_name": "매칭된 기업 조항명",
            "clause_content": "매칭된 기업 조항 본문 내용",
            "explanation": "이 조항이 지침과 관련 있다고 판단한 이유"
        }},
        {{
            "clause_name": "매칭된 기업 조항명",
            "clause_content": "매칭된 기업 조항 본문 내용",
            "explanation": "이 조항이 지침과 관련 있다고 판단한 이유"
        }},
        ...
    ]
}}
"""        
        # Get analysis from GPT
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "당신은 개인정보처리방침 분석 전문가입니다."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.0
        )
        
        # Parse response
        analysis = response.choices[0].message.content.strip()
        
        # Try to parse JSON response
        import json
        # Extract JSON from response
        json_start = analysis.find('{')
        json_end = analysis.rfind('}') + 1
        if json_start != -1 and json_end != -1:
            json_str = analysis[json_start:json_end]
            parsed_analysis = json.loads(json_str)
            
            return {
                'clause': guideline['clause'],
                'is_matched': parsed_analysis.get('is_matched', False),
                'matched_clauses': parsed_analysis.get('matched_clauses', [])  # 1:N 결과 받기
            }

        
        # JSON을 찾을 수 없는 경우
        return {
            'clause': guideline['clause'],
            'is_matched': False,
            'matched_clause_name': '',
            'explanation': 'LLM 응답에서 JSON을 찾을 수 없음'
        }
            
    except Exception as e:
        print(f"Error in LLM analysis: {str(e)}")
        return {
            'clause': guideline['clause'],
            'is_matched': False,
            'matched_clause_name': '',
            'explanation': f'LLM 분석 중 오류 발생: {str(e)}'
        }

def analyze_policy_content_old(df, guideline_content):
    """Analyze policy content against guidelines."""
    results = []
    
    for guideline in guideline_content:
        # Create prompt for analysis
        prompt = f"""
다음은 개인정보처리방침 작성지침의 조항과 내용입니다:

조항: {guideline['clause']}
지침 내용: {guideline['content']}

다음은 기업의 개인정보처리방침 조항과 내용입니다:

{df.to_string()}

위 지침과 기업의 개인정보처리방침을 비교하여 다음을 엄밀히 분석해주세요:
1. 기업의 개인정보처리방침에서 해당 지침과 관련된 내용이 있는지
2. 있다면 어떤 조항과 내용이 매칭되는지
3. 매칭 여부에 대한 설명



응답은 다음 JSON 형식으로 해주세요:
{{
    "is_matched": true/false,
    "matched_clause_name": "매칭된 기업 조항명만",
    "matched_clause_content": "매칭된 기업 조항의 본문 내용만",
    "explanation": "매칭 여부에 대한 설명"
}}
"""
        
        try:
            # Get analysis from GPT
            response = client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": "당신은 개인정보처리방침 분석 전문가입니다."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.0
            )
            
            # Parse response
            analysis = response.choices[0].message.content.strip()
            
            # Try to parse JSON response
            try:
                import json
                # Extract JSON from response
                json_start = analysis.find('{')
                json_end = analysis.rfind('}') + 1
                if json_start != -1 and json_end != -1:
                    json_str = analysis[json_start:json_end]
                    parsed_analysis = json.loads(json_str)
                    
                    # Extract matched clause name from matched_text
                    matched_clause_name = parsed_analysis.get('matched_clause_name', '')
                    matched_clause_content = parsed_analysis.get('matched_clause_content', '')
                    
                    results.append({
                        "clause": guideline['clause'],
                        "guideline_content": guideline['content'][:200] + "...",
                        "is_matched": parsed_analysis.get('is_matched', False),
                        "matched_clause_name": matched_clause_name,
                        "matched_clause_content": matched_clause_content,
                        "explanation": parsed_analysis.get('explanation', '')
                    })
                else:
                    # Fallback to old parsing method
                    results.append({
                        "clause": guideline['clause'],
                        "guideline_content": guideline['content'][:200] + "...",
                        "is_matched": "true" in analysis.lower(),
                        "matched_clause_name": "",
                        "matched_clause_content": "",
                        "explanation": analysis.split('"explanation": "')[1].split('"')[0] if '"explanation": "' in analysis else ""
                    })
            except:
                # Fallback to old parsing method
                results.append({
                    "clause": guideline['clause'],
                    "guideline_content": guideline['content'][:200] + "...",
                    "is_matched": "true" in analysis.lower(),
                    "matched_clause_name": "",
                    "matched_clause_content": "",
                    "explanation": analysis.split('"explanation": "')[1].split('"')[0] if '"explanation": "' in analysis else ""
                })
            
        except Exception as e:
            print(f"Error in analysis: {str(e)}")
            results.append({
                "clause": guideline['clause'],
                "guideline_content": guideline['content'][:200] + "...",
                "is_matched": False,
                "matched_clause_name": "",
                "matched_clause_content": "",
                "explanation": f"분석 중 오류 발생: {str(e)}"
            })
    
    return results 

def analyze_phased_content(company_df, guideline_clauses, guideline_version):
    """
    rule → LLM → RAG 분석 순서로 조합하는 실험용 함수입니다.
    """
    results = []

    for clause in guideline_clauses:
        clause_title = clause["clause"]
        clause_content = clause.get("content", "")

        matched_by_rule = False
        matched_clauses = []

        # 1단계: rulebase 키워드 매칭 예시
        if "목적" in clause_content:
            matched_by_rule = True
            matched_clauses.append({
                "clause_name": "제1조 개인정보의 처리 목적",
                "explanation": "키워드 '목적'과 매칭됨"
            })

        # 2단계: LLM 예시 (rule 실패시)
        if not matched_by_rule:
            matched_clauses.append({
                "clause_name": "제X조 예시",
                "explanation": "LLM 결과: 의미 유사"
            })

        results.append({
            "clause": clause_title,
            "is_matched": True if matched_clauses else False,
            "matched_clauses": matched_clauses
        })

    return results

# utils/analysis.py
def analyze_content_compliance(company_df, guideline_clauses, selected_version):
    results = []

    for clause in guideline_clauses:
        clause_name = clause['clause']
        clause_content = clause['content']

        # 가장 유사한 기업 조항 선택
        matched_clause = None
        for row in company_df.itertuples():
            if clause_name.split()[0] in row.조항:
                matched_clause = row
                break

        if matched_clause:
            related_content = matched_clause.본문
            is_compliant = clause_content[:30] in related_content  # 예시 조건
            detailed_explanation = f"'{clause_name}' 내용 일부가 포함됨" if is_compliant else "요구사항이 충분히 반영되지 않음"
            quoted_sentences_by_clause = {
                matched_clause.조항: [{"sentence": related_content, "relevance": "중간"}]
            }
        else:
            related_content = ""
            is_compliant = False
            detailed_explanation = "관련 기업 조항 없음"
            quoted_sentences_by_clause = {}

        results.append({
            "clause": clause_name,
            "is_compliant": is_compliant,
            "related_content": related_content,
            "detailed_explanation": detailed_explanation,
            "quoted_sentences_by_clause": quoted_sentences_by_clause,
        })

    return results

def analyze_policy_write_only(company_df, guideline_clauses: List[dict], version: str) -> List[dict]:
    """
    Phased 탭 전용: 키워드 중간 출력 없이
    1) match_by_keywords → matched_results, unmatched_guidelines 반환
    2) unmatched_guidelines → LLM 분석
    """
    company_clauses = company_df.to_dict('records')
    matched_results, unmatched_guidelines = match_by_keywords(company_clauses, guideline_clauses, version)

    final_results = matched_results.copy()
    for guideline in unmatched_guidelines:
        try:
            llm_res = analyze_with_llm(company_clauses, guideline)
            final_results.append(llm_res or {
                'clause': guideline['clause'],
                'is_matched': False,
                'matched_clause_name': '',
                'explanation': 'LLM 분석 실패'
            })
        except Exception as e:
            final_results.append({
                'clause': guideline['clause'],
                'is_matched': False,
                'matched_clause_name': '',
                'explanation': f'LLM 분석 중 오류: {e}'
            })

    return final_results

# ----- [다른 사람 코드, phased 전용] -----

def analyze_policy_content_phased(company_df, guideline_clauses: List[dict], version: str) -> List[dict]:
    """기업 개인정보처리방침 분석 수행 (phased 전용)"""
    company_clauses = company_df.to_dict('records')
    matched_results, unmatched_guidelines = match_by_keywords(company_clauses, guideline_clauses, version)
    for guideline in unmatched_guidelines:
        try:
            llm_result = analyze_with_llm_phased(company_clauses, guideline)
            if llm_result:
                matched_results.append(llm_result)
            else:
                matched_results.append({
                    'clause': guideline['clause'],
                    'is_matched': False,
                    'matched_clause_name': '',
                    'explanation': 'LLM 분석 실패'
                })
        except Exception as e:
            print(f"Error in LLM analysis: {str(e)}")
            matched_results.append({
                'clause': guideline['clause'],
                'is_matched': False,
                'matched_clause_name': '',
                'explanation': f'LLM 분석 중 오류 발생: {str(e)}'
            })
    return matched_results

def analyze_with_llm_phased(company_clauses: List[dict], guideline: dict) -> dict:
    """LLM을 사용하여 단일 가이드라인 조항에 대한 분석 수행 (phased 전용)"""
    try:
        df = pd.DataFrame(company_clauses)
        prompt = f"""
다음은 개인정보처리방침 작성지침의 조항과 내용입니다:

조항: {guideline['clause']}
지침 내용: {guideline['content']}

다음은 기업의 개인정보처리방침 조항과 내용입니다:

{df.to_string()}

위 지침과 기업의 개인정보처리방침을 비교하여 다음을 엄밀히 분석해주세요:
1. 기업의 개인정보처리방침에서 해당 지침과 관련된 내용이 있는지
2. 있다면 어떤 조항과 내용이 매칭되는지
3. 매칭 여부에 대한 설명

응답은 다음 JSON 형식으로 해주세요:
{{
    "is_matched": true/false,
    "matched_clause_name": "매칭된 기업 조항명만",
    "matched_clause_content": "매칭된 기업 조항의 본문 내용만",
    "explanation": "매칭 여부에 대한 설명"
}}
"""
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "당신은 개인정보처리방침 분석 전문가입니다."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.0
        )
        analysis = response.choices[0].message.content.strip()
        import json
        json_start = analysis.find('{')
        json_end = analysis.rfind('}') + 1
        if json_start != -1 and json_end != -1:
            json_str = analysis[json_start:json_end]
            parsed_analysis = json.loads(json_str)
            return {
                'clause': guideline['clause'],
                'is_matched': parsed_analysis.get('is_matched', False),
                'matched_clause_name': parsed_analysis.get('matched_clause_name', ''),
                'explanation': parsed_analysis.get('explanation', 'LLM 분석 결과 매칭되지 않음')
            }
        return {
            'clause': guideline['clause'],
            'is_matched': False,
            'matched_clause_name': '',
            'explanation': 'LLM 응답에서 JSON을 찾을 수 없음'
        }
    except Exception as e:
        print(f"Error in LLM analysis: {str(e)}")
        return {
            'clause': guideline['clause'],
            'is_matched': False,
            'matched_clause_name': '',
            'explanation': f'LLM 분석 중 오류 발생: {str(e)}'
        }

def analyze_content_compliance_phased(company_df, guideline_clauses: List[dict], version: str) -> List[dict]:
    """내용 충족 여부 분석 수행 (phased 전용)"""
    # 타입 체크 및 변환
    if hasattr(company_df, 'to_dict'):
        # DataFrame인 경우
        company_clauses = company_df.to_dict('records')
    elif isinstance(company_df, list):
        # 이미 리스트인 경우
        company_clauses = company_df
    else:
        # 기타 타입인 경우 DataFrame으로 변환 후 딕셔너리 리스트로 변환
        import pandas as pd
        company_clauses = pd.DataFrame(company_df).to_dict('records')
    
    compliance_results = []
    for guideline in guideline_clauses:
        try:
            result = analyze_content_compliance_with_llm_phased(company_clauses, guideline)
            if result:
                compliance_results.append(result)
            else:
                compliance_results.append({
                    'clause': guideline['clause'],
                    'is_compliant': False,
                    'related_content': '',
                    'quoted_sentences_by_clause': {},
                    'detailed_explanation': 'LLM 분석 실패'
                })
        except Exception as e:
            print(f"Error in content compliance analysis: {str(e)}")
            compliance_results.append({
                'clause': guideline['clause'],
                'is_compliant': False,
                'related_content': '',
                'quoted_sentences_by_clause': {},
                'detailed_explanation': f'분석 중 오류 발생: {str(e)}'
            })
    return compliance_results

def analyze_content_compliance_with_llm_phased(company_clauses: List[dict], guideline: dict) -> dict:
    """LLM을 사용하여 단일 가이드라인 조항의 내용 충족도 분석 (phased 전용)"""
    try:
        df = pd.DataFrame(company_clauses)
        prompt = f"""
다음은 개인정보처리방침 작성지침의 조항과 내용입니다:

조항: {guideline['clause']}
지침 내용: {guideline['content']}

다음은 기업의 개인정보처리방침 조항과 내용입니다:

{df.to_string()}

위 지침과 기업의 개인정보처리방침을 비교하여 다음을 상세히 분석해주세요:

1. 기업의 개인정보처리방침 전체에서 해당 지침과 관련된 모든 문장들을 찾아서 수정하지 않고 그대로 인용
2. 각 조항별로 관련 문장들을 그룹화하여 인용
3. 지침의 필수 요구사항이 충족되었는지 판단 (권장되는 사항은 충족되지 않아도 됨)
4. 부족한 부분이나 개선이 필요한 부분에 대한 상세한 설명

응답은 다음 JSON 형식으로 해주세요:
{{
    "is_compliant": true/false,
    "related_content": "관련된 기업 조항명들 (쉼표로 구분)",
    "quoted_sentences_by_clause": {{
        "조항명1": [
            {{
                "sentence": "인용된 문장1",
                "relevance": "해당 문장이 지침의 어떤 부분과 관련되는지 설명"
            }},
            {{
                "sentence": "인용된 문장2", 
                "relevance": "해당 문장이 지침의 어떤 부분과 관련되는지 설명"
            }}
        ],
        "조항명2": [
            {{
                "sentence": "인용된 문장",
                "relevance": "해당 문장이 지침의 어떤 부분과 관련되는지 설명"
            }}
        ]
    }},
    "detailed_explanation": "충족 여부에 대한 상세한 설명과 개선 방안"
}}
"""
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "당신은 개인정보처리방침 내용 분석 전문가입니다. 지침의 필수 요구사항이 기업 정책에서 충족되었는지 엄격히 판단해주세요. 기업의 모든 조항에서 관련 문장을 찾아 인용하고, 조항별로 그룹화하여 제시하세요."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.0
        )
        analysis = response.choices[0].message.content.strip()
        import json
        json_start = analysis.find('{')
        json_end = analysis.rfind('}') + 1
        if json_start != -1 and json_end != -1:
            json_str = analysis[json_start:json_end]
            parsed_analysis = json.loads(json_str)
            return {
                'clause': guideline['clause'],
                'is_compliant': parsed_analysis.get('is_compliant', False),
                'related_content': parsed_analysis.get('related_content', ''),
                'quoted_sentences_by_clause': parsed_analysis.get('quoted_sentences_by_clause', {}),
                'detailed_explanation': parsed_analysis.get('detailed_explanation', 'LLM 분석 결과를 파싱할 수 없음')
            }
        return {
            'clause': guideline['clause'],
            'is_compliant': False,
            'related_content': '',
            'quoted_sentences_by_clause': {},
            'detailed_explanation': 'LLM 응답에서 JSON을 찾을 수 없음'
        }
    except Exception as e:
        print(f"Error in content compliance LLM analysis: {str(e)}")
        return {
            'clause': guideline['clause'],
            'is_compliant': False,
            'related_content': '',
            'quoted_sentences_by_clause': {},
            'detailed_explanation': f'LLM 분석 중 오류 발생: {str(e)}'
        }

# ----- [끝] -----

# (여기에 기존 코드)

# ---- 아래 추가 ----
def analyze_policy_content_phased(company_df, guideline_clauses: List[dict], version: str) -> List[dict]:
    """기업 개인정보처리방침 분석 수행 (phased 전용)"""
    company_clauses = company_df.to_dict('records')
    matched_results, unmatched_guidelines = match_by_keywords(company_clauses, guideline_clauses, version)
    for guideline in unmatched_guidelines:
        try:
            llm_result = analyze_with_llm_phased(company_clauses, guideline)
            if llm_result:
                matched_results.append(llm_result)
            else:
                matched_results.append({
                    'clause': guideline['clause'],
                    'is_matched': False,
                    'matched_clause_name': '',
                    'explanation': 'LLM 분석 실패'
                })
        except Exception as e:
            print(f"Error in LLM analysis: {str(e)}")
            matched_results.append({
                'clause': guideline['clause'],
                'is_matched': False,
                'matched_clause_name': '',
                'explanation': f'LLM 분석 중 오류 발생: {str(e)}'
            })
    return matched_results
# ---- 위 코드 추가 ----
