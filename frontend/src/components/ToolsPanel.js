import React, { useState, useEffect } from 'react';
import axios from 'axios';

function ToolsPanel({ onBack }) {
  const [tools, setTools] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const fetchTools = async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await axios.get('/api/tools');
      setTools(response.data.message);
    } catch (err) {
      setError(`도구 목록을 불러오는데 실패했습니다: ${err.message}`);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchTools();
  }, []);

  if (loading) {
    return (
      <div style={{ padding: '20px', textAlign: 'center' }}>
        도구 목록을 불러오는 중...
      </div>
    );
  }

  if (error) {
    return (
      <div style={{ padding: '20px', color: 'red' }}>
        <h3>도구 목록</h3>
        <p>{error}</p>
        <button 
          onClick={fetchTools}
          style={{
            padding: '8px 16px',
            backgroundColor: '#007bff',
            color: 'white',
            border: 'none',
            borderRadius: '4px',
            cursor: 'pointer'
          }}
        >
          다시 시도
        </button>
      </div>
    );
  }

  return (
    <div style={{ padding: '20px', backgroundColor: '#f8f9fa', borderRadius: '8px', marginBottom: '20px' }}>
      <h3>도구 목록</h3>
      <div style={{ 
        backgroundColor: 'white', 
        padding: '15px', 
        borderRadius: '6px',
        border: '1px solid #dee2e6',
        maxHeight: '400px',
        overflowY: 'auto'
      }}>
        <pre style={{ 
          whiteSpace: 'pre-wrap', 
          wordWrap: 'break-word',
          fontSize: '14px',
          lineHeight: '1.5',
          margin: 0
        }}>
          {tools}
        </pre>
      </div>
      <button onClick={onBack} style={{ marginTop: '10px', padding: '8px 16px', backgroundColor: '#6c757d', color: 'white', border: 'none', borderRadius: '4px', cursor: 'pointer' }}>메인 화면으로 돌아가기</button>
    </div>
  );
}

export default ToolsPanel; 