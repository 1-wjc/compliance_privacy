"""
개인정보 처리방침 자동화 분석 서비스 - Flask API 서버
"""

from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import os
from datetime import datetime
import traceback
from dotenv import load_dotenv
import shutil
from werkzeug.utils import secure_filename
import base64
import io
import fitz
import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

# 환경 변수 로드
load_dotenv()

# 기존 Streamlit 함수들 임포트
from agent_langchain_mcp import (
    process_command_with_agent, 
    run_full_analysis,
    check_mcp_data, 
    clear_mcp_store,
    list_files, 
    show_config, 
    show_help, 
    show_tools
)

app = Flask(__name__)
CORS(app)  # React 프론트엔드와 통신을 위한 CORS 설정

# 환경 변수에서 설정값 가져오기
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
INPUT_FOLDER = os.getenv("INPUT_FOLDER", "input")
OUTPUT_FOLDER = os.getenv("OUTPUT_FOLDER", "output")

# 파일 업로드 설정
UPLOAD_FOLDER = INPUT_FOLDER
ALLOWED_EXTENSIONS = {'pdf'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def is_safe_filename(filename):
    import re
    # 위험한 문자나 경로 조작 시도 방지
    dangerous_patterns = [
        r'\.\.',  # 상위 디렉토리 접근 시도
        r'/',       # 경로 구분자
        r'\\',    # Windows 경로 구분자
        r':',       # Windows 드라이브 구분자
    ]
    for pattern in dangerous_patterns:
        if re.search(pattern, filename):
            return False
    # 파일명이 너무 길거나 비어있으면 안전하지 않음
    if len(filename) > 255 or len(filename.strip()) == 0:
        return False
    return True

@app.route('/api/health', methods=['GET'])
def health_check():
    """서버 상태 확인"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'openai_api_key': 'configured' if OPENAI_API_KEY else 'not_configured'
    })

@app.route('/api/upload', methods=['POST'])
def upload_file():
    """PDF 파일 업로드"""
    try:
        if 'file' not in request.files:
            return jsonify({
                'success': False,
                'message': '파일이 선택되지 않았습니다.'
            }), 400
        file = request.files['file']
        if file.filename == '':
            return jsonify({
                'success': False,
                'message': '파일이 선택되지 않았습니다.'
            }), 400
        if file and allowed_file(file.filename):
            if not is_safe_filename(file.filename):
                return jsonify({
                    'success': False,
                    'message': '파일명에 허용되지 않은 문자가 포함되어 있습니다.'
                }), 400
            # input 폴더가 없으면 생성
            if not os.path.exists(INPUT_FOLDER):
                os.makedirs(INPUT_FOLDER)
            filename = file.filename  # 원본 파일명 사용
            filepath = os.path.join(INPUT_FOLDER, filename)
            file.save(filepath)
            return jsonify({
                'success': True,
                'message': f'파일이 성공적으로 업로드되었습니다: {filename}',
                'filename': filename
            })
        else:
            return jsonify({
                'success': False,
                'message': 'PDF 파일만 업로드 가능합니다.'
            }), 400
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'파일 업로드 중 오류가 발생했습니다: {str(e)}'
        }), 500

@app.route('/api/upload_url', methods=['POST'])
def upload_url():
    """URL에서 개인정보 처리방침을 PDF로 변환 후 업로드"""
    try:
        data = request.get_json()
        url = data.get('url')
        if not url:
            return jsonify({'success': False, 'message': 'URL이 제공되지 않았습니다.'}), 400

        # Chrome 옵션 설정
        chrome_options = Options()
        chrome_options.add_argument('--headless')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--print-to-pdf-no-header')
        chrome_options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36')

        # WebDriver 초기화
        driver = webdriver.Chrome(options=chrome_options)
        driver.get(url)
        time.sleep(3)  # 페이지 로딩 대기

        # PDF로 변환
        pdf = driver.execute_cdp_cmd('Page.printToPDF', {
            'landscape': False,
            'printBackground': True,
            'paperWidth': 8.5,
            'paperHeight': 150,
            'marginTop': 0,
            'marginBottom': 0,
            'marginLeft': 0,
            'marginRight': 0
        })
        driver.quit()

        pdf_bytes = io.BytesIO(base64.b64decode(pdf['data']))

        # PDF가 정상인지 확인 (PyMuPDF)
        try:
            with fitz.open(stream=pdf_bytes, filetype='pdf') as doc:
                if doc.page_count == 0:
                    raise ValueError('PDF 페이지가 없습니다.')
        except Exception as e:
            return jsonify({'success': False, 'message': f'PDF 변환 실패: {str(e)}'}), 500

        # 파일명 생성 (도메인_날짜.pdf)
        from urllib.parse import urlparse
        domain = urlparse(url).netloc.replace('.', '_')
        now_str = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f'{domain}_{now_str}.pdf'
        if not os.path.exists(INPUT_FOLDER):
            os.makedirs(INPUT_FOLDER)
        filepath = os.path.join(INPUT_FOLDER, filename)
        pdf_bytes.seek(0)
        with open(filepath, 'wb') as f:
            f.write(pdf_bytes.read())

        return jsonify({'success': True, 'message': 'URL에서 PDF 업로드 성공', 'filename': filename})
    except Exception as e:
        return jsonify({'success': False, 'message': f'URL 업로드 중 오류: {str(e)}'}), 500

@app.route('/api/uploaded-files', methods=['GET'])
def get_uploaded_files():
    """업로드된 파일 목록 조회"""
    try:
        if not os.path.exists(INPUT_FOLDER):
            return jsonify({
                'success': True,
                'files': []
            })
        
        files = []
        for filename in os.listdir(INPUT_FOLDER):
            file_path = os.path.join(INPUT_FOLDER, filename)
            if os.path.isfile(file_path) and allowed_file(filename):
                file_size = os.path.getsize(file_path)
                files.append({
                    'name': filename,
                    'size': file_size,
                    'size_mb': round(file_size / (1024 * 1024), 2),
                    'modified': datetime.fromtimestamp(os.path.getmtime(file_path)).isoformat()
                })
        
        return jsonify({
            'success': True,
            'files': files
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'업로드된 파일 목록 조회 중 오류가 발생했습니다: {str(e)}'
        }), 500

@app.route('/api/uploaded-files/<filename>', methods=['DELETE'])
def delete_uploaded_file(filename):
    """업로드된 파일 삭제"""
    try:
        file_path = os.path.join(INPUT_FOLDER, filename)
        if os.path.exists(file_path):
            os.remove(file_path)
            return jsonify({
                'success': True,
                'message': f'파일이 성공적으로 삭제되었습니다: {filename}'
            })
        else:
            return jsonify({
                'success': False,
                'message': '파일을 찾을 수 없습니다.'
            }), 404
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'파일 삭제 중 오류가 발생했습니다: {str(e)}'
        }), 500

@app.route('/api/delete/<path:filename>', methods=['DELETE'])
def delete_output_file(filename):
    """output 하위 폴더까지 포함한 파일 삭제"""
    try:
        file_path = os.path.join(OUTPUT_FOLDER, filename)
        if os.path.exists(file_path) and os.path.isfile(file_path):
            os.remove(file_path)
            return jsonify({'success': True, 'message': f'{filename} 파일이 삭제되었습니다.'})
        else:
            return jsonify({'success': False, 'message': '파일을 찾을 수 없습니다.'}), 404
    except Exception as e:
        return jsonify({'success': False, 'message': f'파일 삭제 중 오류: {str(e)}'}), 500

@app.route('/api/download/<filename>', methods=['GET'])
def download_file(filename):
    """결과 파일 다운로드 (HTML도 무조건 다운로드)"""
    try:
        file_path = os.path.join(OUTPUT_FOLDER, filename)
        if os.path.exists(file_path):
            ext = os.path.splitext(filename)[1].lower()
            if ext in ['.html', '.htm']:
                # HTML은 무조건 다운로드
                return send_file(
                    file_path,
                    as_attachment=True,
                    download_name=filename,
                    mimetype='application/octet-stream'
                )
            # 그 외는 자동 감지
            return send_file(
                file_path,
                as_attachment=True,
                download_name=filename
            )
        else:
            return jsonify({
                'success': False,
                'message': '파일을 찾을 수 없습니다.'
            }), 404
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'파일 다운로드 중 오류가 발생했습니다: {str(e)}'
        }), 500

@app.route('/api/results', methods=['GET'])
def get_results():
    """결과 파일 목록 + 최신 HTML 보고서 미리보기 반환 (output 하위 폴더까지 모두 탐색)"""
    try:
        if not os.path.exists(OUTPUT_FOLDER):
            return jsonify({
                'success': True,
                'files': [],
                'latest_html': None
            })
        files = []
        html_files = []
        for root, dirs, filenames in os.walk(OUTPUT_FOLDER):
            for filename in filenames:
                file_path = os.path.join(root, filename)
                if os.path.isfile(file_path):
                    file_size = os.path.getsize(file_path)
                    rel_path = os.path.relpath(file_path, OUTPUT_FOLDER)
                    file_info = {
                        'name': rel_path.replace('\\', '/'),
                        'size': file_size,
                        'size_mb': round(file_size / (1024 * 1024), 2),
                        'modified': datetime.fromtimestamp(os.path.getmtime(file_path)).isoformat(),
                        'download_url': f'/api/download/{rel_path.replace('\\', '/')}'
                    }
                    files.append(file_info)
                    if filename.lower().endswith('.html'):
                        html_files.append((file_path, os.path.getmtime(file_path)))
        # 최신 HTML 파일 찾기
        latest_html = None
        if html_files:
            latest_html_file = max(html_files, key=lambda x: x[1])[0]
            try:
                with open(latest_html_file, 'r', encoding='utf-8') as f:
                    latest_html = f.read()
            except Exception as e:
                latest_html = f'<div style="color:red">HTML 파일 읽기 오류: {str(e)}</div>'
        return jsonify({
            'success': True,
            'files': files,
            'latest_html': latest_html
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'결과 파일 목록 조회 중 오류가 발생했습니다: {str(e)}'
        }), 500

@app.route('/api/command', methods=['POST'])
def command():
    """자연어 명령 처리"""
    try:
        data = request.json
        if not data or 'command' not in data:
            return jsonify({
                'success': False,
                'message': '명령어가 제공되지 않았습니다.'
            }), 400
        
        command = data['command']
        result = process_command_with_agent(command)
        
        return jsonify(result)
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'명령 처리 중 오류가 발생했습니다: {str(e)}'
        }), 500

@app.route('/api/analyze/full', methods=['POST'])
def analyze_full():
    """전체 분석 실행"""
    try:
        data = request.json or {}
        company_name = data.get('company_name')
        
        result = run_full_analysis(company_name)
        return jsonify(result)
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'전체 분석 중 오류가 발생했습니다: {str(e)}'
        }), 500

@app.route('/api/files', methods=['GET'])
def files():
    """파일 목록 조회"""
    try:
        result = list_files()
        return jsonify(result)
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'파일 목록 조회 중 오류가 발생했습니다: {str(e)}'
        }), 500

@app.route('/api/config', methods=['GET'])
def config():
    """현재 설정 표시"""
    try:
        result = show_config()
        return jsonify(result)
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'설정 조회 중 오류가 발생했습니다: {str(e)}'
        }), 500

@app.route('/api/help', methods=['GET'])
def help_():
    """도움말 표시"""
    try:
        result = show_help()
        return jsonify(result)
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'도움말 조회 중 오류가 발생했습니다: {str(e)}'
        }), 500

@app.route('/api/tools', methods=['GET'])
def tools():
    """사용 가능한 도구 목록 표시"""
    try:
        result = show_tools()
        return jsonify(result)
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'도구 목록 조회 중 오류가 발생했습니다: {str(e)}'
        }), 500

@app.route('/api/mcp/check', methods=['GET'])
def mcp_check():
    """MCP 저장소 상태 확인"""
    try:
        result = check_mcp_data()
        return jsonify(result)
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'MCP 데이터 확인 중 오류가 발생했습니다: {str(e)}'
        }), 500

@app.route('/api/mcp/clear', methods=['POST'])
def mcp_clear():
    """MCP 저장소 초기화"""
    try:
        result = clear_mcp_store()
        return jsonify(result)
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'MCP 저장소 초기화 중 오류가 발생했습니다: {str(e)}'
        }), 500

@app.route('/api/analyze/llm', methods=['POST'])
def analyze_llm():
    """LLM 분석만 실행"""
    try:
        data = request.json or {}
        company_name = data.get('company_name')
        
        command = "llm 분석해줘"
        if company_name:
            command = f"{company_name} {command}"
        
        result = process_command_with_agent(command)
        return jsonify(result)
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'LLM 분석 중 오류가 발생했습니다: {str(e)}'
        }), 500

@app.route('/api/analyze/keyword', methods=['POST'])
def analyze_keyword():
    """키워드 분석만 실행"""
    try:
        data = request.json or {}
        company_name = data.get('company_name')
        
        command = "키워드 분석해줘"
        if company_name:
            command = f"{company_name} {command}"
        
        result = process_command_with_agent(command)
        return jsonify(result)
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'키워드 분석 중 오류가 발생했습니다: {str(e)}'
        }), 500

@app.route('/api/analyze/rag', methods=['POST'])
def analyze_rag():
    """RAG 분석만 실행"""
    try:
        data = request.json or {}
        company_name = data.get('company_name')
        
        command = "rag 분석해줘"
        if company_name:
            command = f"{company_name} {command}"
        
        result = process_command_with_agent(command)
        return jsonify(result)
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'RAG 분석 중 오류가 발생했습니다: {str(e)}'
        }), 500

@app.route('/api/analyze/compliance', methods=['POST'])
def analyze_compliance():
    """충족도 분석만 실행"""
    try:
        data = request.json or {}
        company_name = data.get('company_name')
        
        command = "충족도 분석해줘"
        if company_name:
            command = f"{company_name} {command}"
        
        result = process_command_with_agent(command)
        return jsonify(result)
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'충족도 분석 중 오류가 발생했습니다: {str(e)}'
        }), 500

@app.route('/api/preview/<path:filename>', methods=['GET'])
def preview_html(filename):
    """HTML 파일 미리보기 (output 하위 폴더 지원, 보안 체크)"""
    import os
    file_path = os.path.join(OUTPUT_FOLDER, *filename.split('/'))
    abs_output = os.path.abspath(OUTPUT_FOLDER)
    abs_file = os.path.abspath(file_path)
    if not abs_file.startswith(abs_output):
        return '허용되지 않은 경로입니다.', 403
    ext = os.path.splitext(filename)[1].lower()
    if not ext in ['.html', '.htm']:
        return 'HTML 파일만 미리보기 지원', 400
    if not os.path.exists(file_path):
        return '파일을 찾을 수 없습니다.', 404
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            html = f.read()
        from flask import Response
        return Response(html, mimetype='text/html')
    except Exception as e:
        return f'파일 읽기 오류: {str(e)}', 500

if __name__ == '__main__':
    print("Flask API 서버를 시작합니다...")
    print(f"Input 폴더: {INPUT_FOLDER}")
    print(f"Output 폴더: {OUTPUT_FOLDER}")
    print(f"OpenAI API 키: {'설정됨' if OPENAI_API_KEY else '설정되지 않음'}")
    print("서버가 http://127.0.0.1:8080/ 에서 실행됩니다.")
    
    app.run(debug=True, host='0.0.0.0', port=8080) 