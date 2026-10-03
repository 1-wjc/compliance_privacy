import fitz  # PyMuPDF
import io
import re
from openai import OpenAI
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

# Configure OpenAI
client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

def extract_text_from_pdf(uploaded_file):
    """Extract text from uploaded PDF file."""
    uploaded_file.seek(0)  # 💡 중요: 매번 읽기 전에 포인터를 앞으로 되돌림
    file_bytes = uploaded_file.read()
    if not file_bytes:
        raise ValueError("빈 파일입니다. PDF를 다시 업로드 해주세요.")
    
    doc = fitz.open(stream=io.BytesIO(file_bytes), filetype="pdf")
    text = ""
    for page in doc:
        text += page.get_text()
    return text



def validate_privacy_policy(text):
    """Validate if the uploaded file is a privacy policy using OpenAI API."""
    check_prompt = f"""다음 문서가 개인정보 처리방침 문서인지 판단해주세요. 
- 개인정보 처리방침 문서라면 "Yes"만 응답해주세요. 
- 아니라면 "No"만 응답해주세요.

내용:
\"\"\"
{text[:1500]}
\"\"\"
"""
    
    try:
        resp = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "당신은 문서 내용을 빠르게 분류하는 전문가입니다."},
                {"role": "user", "content": check_prompt}
            ],
            temperature=0
        )
        is_policy = resp.choices[0].message.content.strip()
        return is_policy == "Yes"
    except Exception as e:
        print(f"Error in validation: {str(e)}")
        # Fallback to keyword-based validation if API fails
        return validate_privacy_policy_fallback(text)

def validate_privacy_policy_fallback(text):
    """Fallback validation using keyword matching."""
    # Keywords that are typically found in privacy policies
    privacy_keywords = [
        "개인정보처리방침",
        "개인정보 보호정책",
        "개인정보 수집 및 이용",
        "개인정보 제3자 제공",
        "개인정보 보호책임자",
        "개인정보",
        "정보주체",
        "처리목적",
        "보유기간",
        "파기절차"
    ]
    
    # Convert text to lowercase for case-insensitive matching
    text_lower = text.lower()
    
    # Check for common privacy policy section headers
    section_patterns = [
        r'제\s*\d+\s*조\s*[\(（]?개인정보',
        r'개인정보\s*처리\s*목적',
        r'개인정보\s*수집\s*및\s*이용',
        r'개인정보\s*보호\s*정책'
    ]
    
    # Count matching section patterns
    section_matches = sum(1 for pattern in section_patterns if re.search(pattern, text, re.IGNORECASE))
    
    # Count matching keywords
    keyword_matches = sum(1 for keyword in privacy_keywords if keyword.lower() in text_lower)
    
    # Consider it valid if either:
    # 1. At least 2 section patterns are found, or
    # 2. At least 3 keywords are found
    return section_matches >= 2 or keyword_matches >= 3