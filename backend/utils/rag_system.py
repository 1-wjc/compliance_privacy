import os
import json
import numpy as np
from typing import List, Dict, Tuple, Optional
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import FAISS
from langchain.schema import Document
from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from langchain.text_splitter import RecursiveCharacterTextSplitter
import pandas as pd
from utils.guideline_processor import get_guideline_versions, process_guideline

class RAGSystem:
    def __init__(self, openai_api_key: str):
        self.embedding_model = OpenAIEmbeddings(openai_api_key=openai_api_key)
        self.chat_model = ChatOpenAI(temperature=0.2, openai_api_key=openai_api_key)
        self.vectorstore = None
        self.guideline_version = None
        self.guideline_clauses = None
        
    def build_guideline_vectorstore(self, guideline_version: str) -> None:
        """선택된 작성지침 버전으로 벡터 스토어를 구축합니다."""
        self.guideline_version = guideline_version
        guideline_content_all = process_guideline(guideline_version)
        
        # 필수 조항만 사용
        mandatory_clauses = []
        for item in guideline_content_all:
            clause_title = item['clause']
            if '(해당시)' not in clause_title and '(권장)' not in clause_title:
                mandatory_clauses.append(item)
        
        self.guideline_clauses = mandatory_clauses
        
        # 작성지침 조항들을 문서로 변환
        documents = []
        for clause in self.guideline_clauses:
            # 조항 제목과 내용을 결합하여 문서 생성
            content = f"조항: {clause['clause']}\n\n내용: {clause['content']}"
            doc = Document(
                page_content=content,
                metadata={
                    "clause": clause['clause'],
                    "content": clause['content'],
                    "guideline_version": guideline_version,
                    "type": "guideline"
                }
            )
            documents.append(doc)
        
        # 1단계: 작성지침 문서를 청크로 분할
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
            separators=["\n\n", "\n", " ", ""]
        )
        
        split_docs = []
        for doc in documents:
            splits = text_splitter.split_documents([doc])
            split_docs.extend(splits)
        
        # 벡터 스토어 생성
        self.vectorstore = FAISS.from_documents(split_docs, self.embedding_model)
        
    # 기업 조항들을 같은 방식으로 청크 분할 후 벡터 스토어에 추가
    def add_company_policy(self, company_df: pd.DataFrame) -> None:
        """기업 개인정보 처리방침을 벡터 스토어에 추가합니다."""
        if self.vectorstore is None:
            raise ValueError("작성지침 벡터 스토어가 먼저 구축되어야 합니다.")
        
        # 기업 조항들을 문서로 변환
        company_docs = []
        for _, row in company_df.iterrows():
            content = f"조항: {row['조항']}\n\n내용: {row['본문내용']}"
            doc = Document(
                page_content=content,
                metadata={
                    "clause": row['조항'],
                    "content": row['본문내용'],
                    "type": "company_policy"
                }
            )
            company_docs.append(doc)
        
        # 텍스트 분할
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
            separators=["\n\n", "\n", " ", ""]
        )
        
        split_company_docs = []
        for doc in company_docs:
            splits = text_splitter.split_documents([doc])
            split_company_docs.extend(splits)
        
        # 기존 벡터 스토어에 추가
        self.vectorstore.add_documents(split_company_docs)
        
    def search_similar_documents(self, query: str, k: int = 5) -> List[Document]:
        """유사한 문서들을 검색합니다."""
        if self.vectorstore is None:
            raise ValueError("벡터 스토어가 구축되지 않았습니다.")
        
        return self.vectorstore.similarity_search(query, k=k)
    
    def search_similar_documents_with_scores(self, query: str, k: int = 5) -> List[Tuple[Document, float]]:
        """유사한 문서들과 점수를 함께 검색합니다."""
        if self.vectorstore is None:
            raise ValueError("벡터 스토어가 구축되지 않았습니다.")
        
        return self.vectorstore.similarity_search_with_score(query, k=k)
    
    def evaluate_adequacy(self, company_df: pd.DataFrame) -> Dict:
        """기업 개인정보 처리방침의 적절성을 평가합니다."""
        if self.guideline_clauses is None:
            raise ValueError("작성지침이 로드되지 않았습니다.")
        
        evaluation_results = []
        total_score = 0
        max_score = len(self.guideline_clauses)
        
        for guideline_clause in self.guideline_clauses:
            # 특별한 매핑 규칙: "제목" 조항은 "개인정보 처리방침" 조항에 매핑
            if (guideline_clause['clause'].lower() in ['제목', 'title', '개인정보 처리방침'] or 
                '제목' in guideline_clause['clause'] or 
                'title' in guideline_clause['clause'].lower()):
                
                # 기업 조항에서 "개인정보 처리방침" 관련 조항 찾기
                title_match = None
                title_score = 0.0
                
                for _, row in company_df.iterrows():
                    company_clause = row['조항'].lower()
                    # 더 포괄적인 키워드 매칭
                    if any(keyword in company_clause for keyword in [
                        '개인정보 처리방침', '개인정보처리방침', '제목', 'title', 
                        '제1조', '제 1조', '1조', '1 조'
                    ]):
                        # 제목 매핑의 경우 높은 점수 부여
                        title_score = 0.9
                        title_match = {
                            'clause': row['조항'],
                            'content': row['본문내용'],
                            'similarity': title_score
                        }
                        print(f"제목 매핑 성공: '{guideline_clause['clause']}' → '{row['조항']}'")
                        break
                
                if title_match:
                    final_score = title_score
                    total_score += final_score
                    
                    evaluation_results.append({
                        'guideline_clause': guideline_clause['clause'],
                        'guideline_content': guideline_clause['content'],
                        'matched_company_clause': title_match['clause'],
                        'matched_company_content': title_match['content'],
                        'adequacy_score': final_score,
                        'embedding_similarity': title_score,
                        'company_matches_count': 1,
                        'explanation': self._generate_explanation(guideline_clause, title_match, final_score)
                    })
                    continue
                else:
                    print(f"제목 매핑 실패: '{guideline_clause['clause']}' - 적절한 기업 조항을 찾을 수 없습니다.")
            
            # 일반적인 조항들의 유사도 검색
            similar_docs_with_scores = self.search_similar_documents_with_scores(
                f"조항: {guideline_clause['clause']}\n내용: {guideline_clause['content']}", 
                k=20
            )
            
            # 기업 조항 중에서 가장 유사한 것 찾기
            best_match = None
            best_score = 0
            company_matches = []
            
            for doc, score in similar_docs_with_scores:
                if doc.metadata.get('type') == 'company_policy':
                    similarity_score = 1.0 / (1.0 + score)
                    company_matches.append({
                        'clause': doc.metadata['clause'],
                        'content': doc.metadata['content'],
                        'similarity': similarity_score
                    })
                    if similarity_score > best_score:
                        best_score = similarity_score
                        best_match = doc
            
            # 매핑 실패 시 대안적 검색 시도
            if not best_match:
                # 조항 제목만으로 재검색
                title_only_results = self.search_similar_documents_with_scores(
                    guideline_clause['clause'], k=10
                )
                
                for doc, score in title_only_results:
                    if doc.metadata.get('type') == 'company_policy':
                        similarity_score = 1.0 / (1.0 + score)
                        if similarity_score > best_score:
                            best_score = similarity_score
                            best_match = doc
                
                # 여전히 실패하면 내용만으로 재검색
                if not best_match:
                    content_only_results = self.search_similar_documents_with_scores(
                        guideline_clause['content'], k=10
                    )
                    
                    for doc, score in content_only_results:
                        if doc.metadata.get('type') == 'company_policy':
                            similarity_score = 1.0 / (1.0 + score)
                            if similarity_score > best_score:
                                best_score = similarity_score
                                best_match = doc
            
            # 매핑 실패 시 디버깅 정보 추가
            if not best_match:
                print(f"매핑 실패: {guideline_clause['clause']}")
                print(f"검색된 기업 조항 수: {len(company_matches)}")
                if company_matches:
                    print("상위 3개 기업 조항:")
                    for i, match in enumerate(company_matches[:3]):
                        print(f"  {i+1}. {match['clause']} (유사도: {match['similarity']:.3f})")
                print("---")
            
            final_score = best_score if best_match else 0.0
            total_score += final_score
            
            evaluation_results.append({
                'guideline_clause': guideline_clause['clause'],
                'guideline_content': guideline_clause['content'],
                'matched_company_clause': best_match.metadata['clause'] if best_match else None,
                'matched_company_content': best_match.metadata['content'] if best_match else None,
                'adequacy_score': final_score,
                'embedding_similarity': best_score,
                'company_matches_count': len(company_matches),
                'explanation': self._generate_explanation(guideline_clause, best_match, final_score)
            })
        
        overall_score = total_score / max_score if max_score > 0 else 0
        
        return {
            'overall_score': overall_score,
            'total_score': total_score,
            'max_score': max_score,
            'evaluation_results': evaluation_results,
            'guideline_version': self.guideline_version
        }
    
    def _generate_explanation(self, guideline_clause: Dict, matched_doc: Optional[Document], score: float) -> str:
        """적절성 평가에 대한 설명을 생성합니다."""
        if matched_doc is None:
            return f"'{guideline_clause['clause']}' 조항에 해당하는 내용을 찾을 수 없습니다."
        
        if score >= 0.8:
            return f"'{guideline_clause['clause']}' 조항이 적절하게 작성되어 있습니다."
        elif score >= 0.5:
            return f"'{guideline_clause['clause']}' 조항이 부분적으로 작성되어 있으나 개선이 필요합니다. 작성지침에 따르면: {guideline_clause['content']}"
        else:
            return f"'{guideline_clause['clause']}' 조항이 부족하거나 부적절하게 작성되어 있습니다. 작성지침에 따르면: {guideline_clause['content']}"
    
    def answer_question(self, question: str, company_df: pd.DataFrame = None) -> str:
        """사용자 질문에 답변합니다."""
        if self.vectorstore is None:
            return "작성지침이 로드되지 않았습니다. 먼저 작성지침을 선택해주세요."
        
        # 관련 문서 검색
        relevant_docs = self.search_similar_documents(question, k=5)
        
        # 컨텍스트 구성
        context = "\n\n".join([doc.page_content for doc in relevant_docs])
        
        # 프롬프트 템플릿
        prompt_template = ChatPromptTemplate.from_template("""
        당신은 개인정보 처리방침 전문가입니다. 다음 정보를 바탕으로 사용자의 질문에 답변해주세요.
        
        작성지침 버전: {guideline_version}
        
        관련 정보:
        {context}
        
        사용자 질문: {question}
        
        답변은 한국어로 작성하고, 구체적이고 실용적인 조언을 제공해주세요.
        가능하면 관련 법령이나 작성지침을 인용하여 답변해주세요.
        """)
        
        # 답변 생성
        chain = prompt_template | self.chat_model
        response = chain.invoke({
            "guideline_version": self.guideline_version,
            "context": context,
            "question": question
        })
        
        return response.content 