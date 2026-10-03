import React, { useState, useEffect } from 'react';
import axios from 'axios';

function MCPDataPanel() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [clearMsg, setClearMsg] = useState('');

  const fetchData = async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await axios.get('/api/mcp/check');
      setData(res.data.message);
    } catch (err) {
      setError(`MCP 데이터를 불러오지 못했습니다: ${err.message}`);
    } finally {
      setLoading(false);
    }
  };

  const handleClear = async () => {
    setClearMsg('');
    try {
      const res = await axios.post('/api/mcp/clear');
      setClearMsg(res.data.message);
      fetchData();
    } catch (err) {
      setClearMsg(`초기화 실패: ${err.message}`);
    }
  };

  useEffect(() => { fetchData(); }, []);

  if (loading) return <div style={{ padding: 20, textAlign: 'center' }}>불러오는 중...</div>;
  if (error) return <div style={{ padding: 20, color: 'red' }}>{error}</div>;
  return (
    <div style={{ margin: 0, padding: 0 }}>
      <style>{`hr { border: none; border-top: 1.5px solid #bbb; margin: 24px 0; }`}</style>
      <div dangerouslySetInnerHTML={{ __html: data }} />
      <div style={{ textAlign: 'center', marginTop: 24 }}>
        <button
          onClick={handleClear}
          style={{
            backgroundColor: '#dc3545',
            color: 'white',
            border: 'none',
            borderRadius: '4px',
            padding: '8px 16px',
            cursor: 'pointer',
            fontWeight: 'bold'
          }}
        >
          MCP 저장소 초기화
        </button>
        {clearMsg && (
          <div style={{ marginTop: 12, color: clearMsg.includes('초기화') ? '#28a745' : '#dc3545' }}>{clearMsg}</div>
        )}
      </div>
    </div>
  );
}

export default MCPDataPanel; 