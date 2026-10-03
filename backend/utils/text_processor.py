import pandas as pd
import re
import datetime
from openai import OpenAI
from dotenv import load_dotenv
import os
import fitz  # PyMuPDF

# Load environment variables
load_dotenv()

# Check for OpenAI API key
api_key = os.getenv('OPENAI_API_KEY')
if not api_key:
    raise ValueError("OpenAI API key not found. Please create a .env file with OPENAI_API_KEY=your_api_key")

# Configure OpenAI
client = OpenAI(api_key=api_key)

def extract_text_from_pdf(file):
    """Extract text from PDF file using PyMuPDF."""
    doc = fitz.open(stream=file.read(), filetype="pdf")
    text = ""
    for page in doc:
        text += page.get_text()
    return text

def convert_to_markdown(text):
    """Convert text to markdown format using GPT."""
    prompt = f"""
다음은 기업의 개인정보처리방침 원문입니다. 이 내용을 마크다운 형식으로 정리해주세요.

작성 규칙:
    1. 서문이나 도입부에 개인정보 처리방침의 목적, 법적 근거, 안내 성격의 내용이 있다면, 해당 부분을 반드시 조항으로 포함시키세요.
    - 이때 조항 제목은 무조건 '개인정보 처리방침'으로 하세요.
    - 반드시 첫 번째 조항으로 포함해 주세요.

    2. 조항 제목은 모두 `제 1조`, `제 2조`...와 같은 형식으로 되어 있으니, 이 외의 형식에 대해서 조항이라고 판단하지 마세요.

    3. 각 조항은 마크다운에서 '## 조항 제목' 형식으로 작성하세요.

    4. 조항 본문은 마크다운 코드블록(``` ```) 안에, 줄바꿈을 포함해 원문 그대로 작성하세요. (내용 수정 X)

    5. 목차는 무시하고, 본문 조항만 정리하세요.

    6. 원문의 조항 순서를 절대 변경하지 마세요.

원문:
\"\"\"
{text}
\"\"\"
"""

    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "당신은 개인정보방침 문서를 마크다운 형식으로 정리하는 비서입니다."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.0
        )
        
        markdown_text = response.choices[0].message.content.strip()
        return markdown_text
        
    except Exception as e:
        print(f"Error in markdown conversion: {str(e)}")
        return None

def create_dataframe(markdown_text, is_guideline=False):
    """Create a pandas DataFrame from markdown text."""
    if not markdown_text:
        return pd.DataFrame(columns=["조항", "본문내용"])
        
    sections = []
    
    if is_guideline:
        # 가이드라인 파일에서 실제 조항명만 추출 (숫자와 점으로 시작하는 제목만)
        titles = re.findall(r"^##\s+(\d+\.\s+.*?)(?:\s*\(의무\)|\s*\(권장\))?$", markdown_text, re.MULTILINE)
    else:
        # 기업 원문에서 모든 ## 제목 추출
        titles = re.findall(r"^##\s+(.*)", markdown_text, re.MULTILINE)
    
    bodies = re.findall(r"```(?:\w*\n)?(.*?)```", markdown_text, re.DOTALL)
    
    for title, body in zip(titles, bodies):
        sections.append({
            "조항": title.strip(),
            "본문내용": body.strip()
        })
    
    return pd.DataFrame(sections)

# 적용일자 추출 함수들
def extract_date_with_llm(text: str):
    """LLM을 이용한 적용일자 추출"""
    system_prompt = (
        "당신은 한국어 문서에서 '개인정보처리방침 적용일자'를 찾아, "
        "YYYY-MM-DD 포맷으로만 응답하는 날짜 추출 전문가입니다. "
        "문장 앞뒤에 숫자 괄호나 불필요한 텍스트가 있어도 날짜만 깔끔히 뽑아주세요. "
        "만약 적용일자가 없으면 'None'이라고만 응답하세요."
    )
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": text}
    ]
    try:
        resp = client.chat.completions.create(
            model="gpt-4o",
            messages=messages,
            temperature=0
        )
        date_str = resp.choices[0].message.content.strip()
        if date_str == "None":
            return None
        try:
            y, m, d = map(int, date_str.split("-"))
            return datetime.date(y, m, d)
        except:
            return None
    except:
        return None

def extract_date_with_regex(text: str):
    """Regex 기반 fallback 적용일자 추출"""
    patterns = [
        r'(\d{4})\s*[.\-]\s*(\d{1,2})\s*[.\-]\s*(\d{1,2})',
        r'(\d{4})\s*년\s*(\d{1,2})\s*월\s*(\d{1,2})\s*일'
    ]
    dates = []
    for pat in patterns:
        for m in re.finditer(pat, text):
            y, mo, d = map(int, m.groups())
            try:
                dates.append(datetime.date(y, mo, d))
            except:
                continue
    return max(dates) if dates else None

def select_appropriate_guideline(application_date, guidelines_dict):
    """개정일자에 맞게 가이드라인 선택"""
    guideline_dates = {
        "2020년 12월": datetime.date(2020, 12, 1),
        "2022년 3월": datetime.date(2022, 3, 1),
        "2024년 4월": datetime.date(2024, 4, 1),
        "2025년 4월": datetime.date(2025, 4, 1)
    }
    sel_guideline, sel_date = None, datetime.date(2000, 1, 1)
    for g, d in guideline_dates.items():
        if g in guidelines_dict and d <= application_date and d > sel_date:
            sel_guideline, sel_date = g, d
    return sel_guideline

def extract_application_date(text):
    """적용일자 추출 (LLM 우선, Regex fallback)"""
    # LLM으로 먼저 시도
    date_llm = extract_date_with_llm(text)
    if date_llm:
        return date_llm
    
    # Regex로 fallback
    date_regex = extract_date_with_regex(text)
    return date_regex 