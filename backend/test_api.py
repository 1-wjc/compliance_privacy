"""
Flask API 서버 테스트 스크립트
"""

import requests
import json
import sys
import os

BASE_URL = "http://127.0.0.1:8080/"

def test_health():
    """서버 상태 확인"""
    try:
        response = requests.get(f"{BASE_URL}/api/health")
        print("=== 서버 상태 확인 ===")
        print(f"Status: {response.status_code}")
        print(f"Response: {response.json()}")
        print()
    except Exception as e:
        print(f"서버 연결 실패: {e}")

def test_files():
    """파일 목록 조회 테스트"""
    try:
        response = requests.get(f"{BASE_URL}/api/files")
        print("=== 파일 목록 조회 ===")
        print(f"Status: {response.status_code}")
        print(f"Response: {response.json()}")
        print()
    except Exception as e:
        print(f"파일 목록 조회 실패: {e}")

def test_config():
    """설정 조회 테스트"""
    try:
        response = requests.get(f"{BASE_URL}/api/config")
        print("=== 설정 조회 ===")
        print(f"Status: {response.status_code}")
        print(f"Response: {response.json()}")
        print()
    except Exception as e:
        print(f"설정 조회 실패: {e}")

def test_help():
    """도움말 조회 테스트"""
    try:
        response = requests.get(f"{BASE_URL}/api/help")
        print("=== 도움말 조회 ===")
        print(f"Status: {response.status_code}")
        print(f"Response: {response.json()}")
        print()
    except Exception as e:
        print(f"도움말 조회 실패: {e}")

def test_command(command):
    """명령 처리 테스트"""
    try:
        data = {"command": command}
        response = requests.post(f"{BASE_URL}/api/command", json=data)
        print(f"=== 명령 처리: {command} ===")
        print(f"Status: {response.status_code}")
        print(f"Response: {response.json()}")
        print()
    except Exception as e:
        print(f"명령 처리 실패: {e}")

if __name__ == "__main__":
    print("Flask API 서버 테스트를 시작합니다...")
    print("=" * 50)
    
    # 기본 테스트
    test_health()
    test_files()
    test_config()
    test_help()
    
    # 명령 테스트
    test_command("파일 목록")
    test_command("설정")
    
    print("테스트 완료!") 