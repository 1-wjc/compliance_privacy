import json
import os
import re

import os

def get_guideline_versions():
    """Get available guideline versions."""
    return {
        "2020년 12월": "policy_2012.md",
        "2022년 3월": "policy_2203.md",
        "2024년 4월": "policy_2404.md",
        "2025년 4월": "policy_2504.md",
    }

def process_guideline(version):
    """Process the selected guideline version without removing any clause annotations."""
    versions = get_guideline_versions()
    if version not in versions:
        raise ValueError(f"Invalid version: {version}")
        
    file_path = os.path.join("policy", versions[version])
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Guideline file not found: {file_path}")
        
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    lines = content.split('\n')
    clauses = []
    current_clause = None
    current_content = []
    
    for line in lines:
        if line.startswith('## '):
            if current_clause is not None:
                clauses.append({
                    "clause": current_clause,
                    "content": '\n'.join(current_content).strip()
                })
            current_clause = line[3:].strip()  # "## " 제거만 하고 전체 유지
            current_content = []
        else:
            if current_clause is not None:
                current_content.append(line)
    
    if current_clause is not None:
        clauses.append({
            "clause": current_clause,
            "content": '\n'.join(current_content).strip()
        })
    
    return clauses