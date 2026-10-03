import React, { useState, useEffect } from 'react';
import axios from 'axios';

function ResultsPanel() {
  const [files, setFiles] = useState([]);
  const [previewHtml, setPreviewHtml] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  // HTML 미리보기 불러오기
  const fetchPreview = async (filename) => {
    setLoading(true);
    setError(null);
    try {
      const res = await axios.get(`/api/preview/${encodeURIComponent(filename)}`);
      setPreviewHtml(res.data || res);
    } catch (err) {
      setPreviewHtml(`<div style='color:red'>미리보기 실패: ${err.message}</div>`);
    } finally {
      setLoading(false);
    }
  };

  // 파일 목록 및 최신 미리보기 불러오기
  const fetchResults = async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await axios.get('/api/results');
      setFiles(response.data.files || []);
      // 최신 HTML 파일 자동 미리보기
      const latestHtmlFile = (response.data.files || []).filter(f => f.name.toLowerCase().endsWith('.html')).sort((a, b) => new Date(b.modified) - new Date(a.modified))[0];
      if (latestHtmlFile) {
        fetchPreview(latestHtmlFile.name);
      } else {
        setPreviewHtml(null);
      }
    } catch (err) {
      setError(`분석 결과를 불러오는데 실패했습니다: ${err.message}`);
    } finally {
      setLoading(false);
    }
  };

  // 파일 삭제 함수
  const handleDelete = async (filename) => {
    if (!window.confirm(`정말로 삭제하시겠습니까?\n${filename}`)) return;
    setLoading(true);
    setError(null);
    try {
      const res = await axios.delete(`/api/delete/${encodeURIComponent(filename)}`);
      if (res.data && res.data.success) {
        fetchResults();
      } else {
        setError(res.data && res.data.message ? res.data.message : '삭제 실패');
      }
    } catch (err) {
      setError(`삭제 중 오류: ${err.message}`);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchResults();
    // eslint-disable-next-line
  }, []);

  if (loading) return <div style={{ padding: 20, textAlign: 'center' }}>분석 결과를 불러오는 중...</div>;
  if (error) return <div style={{ padding: 20, color: 'red' }}>{error}</div>;

  // FileUpload.js의 삭제 버튼 스타일과 통일
  const deleteButtonStyle = {
    backgroundColor: '#dc3545',
    color: 'white',
    border: 'none',
    borderRadius: '4px',
    padding: '5px 10px',
    cursor: 'pointer',
    fontSize: '12px',
    whiteSpace: 'nowrap',
  };

  return (
    <div style={{ margin: 0, padding: 0 }}>
      <style>{`hr { border: none; border-top: 1.5px solid #bbb; margin: 24px 0; }`}</style>
      <div style={{ marginBottom: 32 }}>
        <h3 style={{ textAlign: 'center', margin: '16px 0 12px 0' }}>분석 결과 파일 목록</h3>
        {files.length === 0 ? (
          <div style={{ textAlign: 'center', color: '#888' }}>분석 결과 파일이 없습니다.</div>
        ) : (
          <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 15 }}>
            <thead>
              <tr style={{ background: '#f5f5f5' }}>
                <th style={{ padding: 8, borderBottom: '1px solid #ddd' }}>파일명</th>
                <th style={{ padding: 8, borderBottom: '1px solid #ddd' }}>크기</th>
                <th style={{ padding: 8, borderBottom: '1px solid #ddd' }}>수정일</th>
                <th style={{ padding: 8, borderBottom: '1px solid #ddd' }}>미리보기</th>
                <th style={{ padding: 8, borderBottom: '1px solid #ddd' }}>삭제</th>
              </tr>
            </thead>
            <tbody>
              {files
                .slice()
                .sort((a, b) => new Date(b.modified) - new Date(a.modified))
                // .DS_Store 화면에 나타나서 안 보이게 처리함
                .filter(file => file.name !== '.DS_Store' && !file.name.endsWith('/.DS_Store'))
                .map((file, idx) => (
                  <tr key={file.name} style={{ background: idx % 2 === 0 ? '#fff' : '#f9f9f9' }}>
                    <td style={{ padding: 8 }}>{file.name}</td>
                    <td style={{ padding: 8 }}>{file.size_mb} MB</td>
                    <td style={{ padding: 8 }}>{new Date(file.modified).toLocaleString()}</td>
                    <td style={{ padding: 8 }}>
                      {file.name.toLowerCase().endsWith('.html') ? (
                        <button
                          onClick={() => fetchPreview(file.name)}
                          style={{
                            padding: '6px 14px',
                            background: '#007bff',
                            color: 'white',
                            border: 'none',
                            borderRadius: '5px',
                            cursor: 'pointer',
                            fontWeight: 'bold',
                            fontSize: 14
                          }}
                        >
                          미리보기
                        </button>
                      ) : (
                        <span style={{ color: '#aaa' }}>-</span>
                      )}
                    </td>
                    <td style={{ padding: 8 }}>
                      {file.name.toLowerCase().endsWith('.html') ? (
                        <button
                          onClick={() => handleDelete(file.name)}
                          style={deleteButtonStyle}
                        >
                          삭제
                        </button>
                      ) : (
                        <span style={{ color: '#aaa' }}>-</span>
                      )}
                    </td>
                  </tr>
                ))}
            </tbody>
          </table>
        )}
      </div>
      <hr />
      <div>
        <h3 style={{ textAlign: 'center', margin: '16px 0 12px 0' }}>분석 결과 미리보기</h3>
        {previewHtml ? (
          <div style={{ border: '1px solid #eee', borderRadius: 8, padding: 16, background: '#fafbfc', minHeight: 200 }}
            dangerouslySetInnerHTML={{ __html: previewHtml }}
          />
        ) : (
          <div style={{ textAlign: 'center', color: '#888' }}>미리볼 수 있는 HTML 보고서가 없습니다.</div>
        )}
      </div>
    </div>
  );
}

export default ResultsPanel; 