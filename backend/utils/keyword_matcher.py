from typing import Dict, List, Tuple

def get_guideline_keywords_2020() -> dict[int, list[str]]:
    """2020 각 지침 섹션별 핵심 키워드 정의"""
    return {
        2: ["목적"],
        3: ["기간"],
        4: ["제3자 제공", "제 3자 제공"],
        5: ["파기", "폐기", "삭제"],
        6: ["위탁", "위탁처리", "위탁업체"],
        7: ["법정대리인"],
        8: ["보호책임자", "고충처리", "담당부서", "연락처"],
        9: ["인터넷", "로그", "쿠키"],
        10: ["항목", "수집 항목"],
        11: ["안전성"],
        12: ["변경", "개정", "수정"],
        13: ["열람청구"],
        14: ["권익침해", "구제방법", "피해구제"],
        15: ["가명정보", "가명처리"],
        16: ["국내대리인"],
        17: ["추가이용", "추가제공", "지속적이용", "추가"],
        18: ["영상정보처리기기"],
        19: ["자율적"]
    }


def get_guideline_keywords_2022() -> dict[int, list[str]]:
    """2022 각 지침 섹션별 핵심 키워드 정의"""
    return {
        2: ["목적"],
        3: ["기간"],
        4: ["항목", "수집 항목"],
        5: ["14세", "아동"],
        6: ["제3자 제공", "제 3자 제공"],
        7: ["위탁", "위탁처리", "위탁업체"],
        8: ["국외", "해외", "이전"],
        9: ["파기", "폐기", "삭제"],
        10: ["미이용", "휴면"],
        11: ["법정대리인"],
        12: ["안전성"],
        13: ["설치", "쿠키", "로그"],
        14: ["행태정보"],
        15: ["추가이용", "추가제공", "지속적이용", "추가"],
        16: ["가명정보", "가명처리"],
        17: ["보호책임자"],
        18: ["국내대리인"],
        19: ["열람청구"],
        20: ["권익침해", "구제방법", "피해구제","침해"],
        21: ["영상정보처리기기"],
        22: ["변경", "개정", "수정"]
    }


def get_guideline_keywords_2024() -> dict[int, list[str]]:
    """2024 각 지침 섹션별 핵심 키워드 정의"""
    return {
        2: ["목적"],
        3: ["항목"],
        4: ["14세", "아동"],
        5: ["기간"],
        6: ["파기", "폐기", "삭제"],
        7: ["제3자 제공", "제 3자 제공"],
        8: ["추가이용", "추가제공", "지속적이용", "추가"],
        9: ["위탁", "위탁처리", "위탁업체"],
        10: ["국외", "해외", "이전"],
        11: ["안전성"],
        12: ["민감정보"],
        13: ["가명정보", "가명처리"],
        14: ["설치", "쿠키", "로그"],
        15: ["행태정보"],
        16: ["법정대리인"],
        17: ["보호책임자", "담당부서", "고충처리", "고충사항"],
        18: ["국내대리인"],
        19: ["권익침해", "구제방법", "피해구제","침해"],
        20: ["고정형"],
        21: ["이동형"],
        22: ["자율적"],
        23: ["변경", "개정", "수정"]
    }


def get_guideline_keywords_2025() -> dict[int, list[str]]:
    """2025 각 지침 섹션별 핵심 키워드 정의"""
    return {
        2: ["목적"],
        3: ["항목", "수집 항목"],
        4: ["14세", "아동"],
        5: ["기간"],
        6: ["파기", "폐기", "삭제"],
        7: ["제3자 제공", "제 3자 제공"],
        8: ["추가이용", "추가제공", "판단기준", "지속적이용"],
        9: ["위탁", "위탁처리", "위탁업체"],
        10: ["국외", "해외", "이전"],
        11: ["안전성"],
        12: ["민감정보"],
        13: ["가명정보", "가명처리"],
        14: ["자동 수집", "쿠키", "로그"],
        15: ["행태정보"],
        16: ["법정대리인"],
        17: ["자동화"],
        18: ["보호책임자", "담당부서", "고충처리", "고충사항"],
        19: ["국내대리인"],
        20: ["권익침해", "구제방법", "피해구제","침해"],
        21: ["고정형"],
        22: ["이동형"],
        23: ["자율적"],
        24: ["변경", "개정", "수정"]
    }

def get_keywords_for_version(version: str) -> Dict[int, List[str]]:
    """버전에 따른 키워드 사전 반환"""
    version_map = {
        "2020년 12월": get_guideline_keywords_2020,
        "2022년 3월": get_guideline_keywords_2022,
        "2024년 4월": get_guideline_keywords_2024,
        "2025년 4월": get_guideline_keywords_2025
    }
    
    return version_map.get(version, get_guideline_keywords_2024)()  # 기본값은 2024년 버전

def match_by_keywords(company_clauses: List[dict], guideline_clauses: List[dict], version: str) -> Tuple[List[dict], List[dict]]:
    """키워드 기반 매칭 수행
    
    Returns:
        Tuple[List[dict], List[dict]]: (매칭된 결과, 매칭되지 않은 가이드라인 조항)
    """
    keywords = get_keywords_for_version(version)
    matched_results = []
    unmatched_guidelines = []
    
    # 각 가이드라인 조항에 대해
    for guideline in guideline_clauses:
        print(f"\n처리 중인 가이드라인: {guideline['clause']}")
        # 조항 번호 추출 (예: "2. 개인정보의 처리 목적" -> 2)
        try:
            # 먼저 숫자로 시작하는지 확인
            first_part = guideline['clause'].split()[0]
            if first_part.isdigit():
                clause_num = int(first_part)
            else:
                # 숫자가 아니면 첫 번째 숫자 시퀀스 추출
                clause_num = int(''.join(filter(str.isdigit, first_part)))
            print(f"추출된 조항 번호: {clause_num}")
        except (ValueError, IndexError) as e:
            print(f"조항 번호 추출 실패: {str(e)}")
            unmatched_guidelines.append(guideline)
            continue
            
        if clause_num not in keywords:
            print(f"조항 번호 {clause_num}에 대한 키워드가 없음")
            unmatched_guidelines.append(guideline)
            continue
            
        clause_keywords = keywords[clause_num]
        print(f"키워드 목록: {clause_keywords}")
        found_match = False
        
        # 각 기업 조항에 대해 키워드 매칭 시도
        for company_clause in company_clauses:
            clause_title = company_clause['조항'].lower()
            print(f"비교 중인 기업 조항: {company_clause['조항']}")
            # 키워드 중 하나라도 조항명에 포함되어 있으면 매칭
            matching_keywords = [k for k in clause_keywords if k.lower() in clause_title]
            if matching_keywords:
                print(f"매칭된 키워드: {matching_keywords}")
                matched_results.append({
                    'clause': guideline['clause'],
                    'is_matched': True,
                    'matched_clause_name': company_clause['조항'],
                    'explanation': f"조항명 키워드 매칭: {', '.join(matching_keywords)}"
                })
                found_match = True
                break
                
        if not found_match:
            print("매칭 실패")
            unmatched_guidelines.append(guideline)
            
    return matched_results, unmatched_guidelines 