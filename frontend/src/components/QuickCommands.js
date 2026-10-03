import React, { useState } from 'react';
import axios from 'axios';

function QuickCommands({ onResult }) {
  const [loading, setLoading] = useState(false);

  const handleClick = async (type) => {
    setLoading(true);
    try {
      let response;
      switch (type) {
        case 'mcp-check':
          response = await axios.get('/api/mcp/check');
          break;
        case 'mcp-clear':
          response = await axios.post('/api/mcp/clear');
          break;
        default:
          return;
      }
      onResult(response.data.message);
    } catch (error) {
      onResult(`오류가 발생했습니다: ${error.message}`);
    } finally {
      setLoading(false);
    }
  };

  const buttonStyle = {
    padding: '10px 15px',
    margin: '5px',
    backgroundColor: '#28a745',
    color: 'white',
    border: 'none',
    borderRadius: '5px',
    cursor: 'pointer',
    fontSize: '14px',
    minWidth: '120px'
  };

  const disabledButtonStyle = {
    ...buttonStyle,
    backgroundColor: '#6c757d',
    cursor: 'not-allowed'
  };

  return (
    <div style={{ padding: '20px', backgroundColor: '#f8f9fa', borderRadius: '8px', marginBottom: '20px' }}>
      <h3>빠른 명령</h3>
      <div style={{ display: 'flex', flexWrap: 'wrap', gap: '10px', justifyContent: 'center' }}>
        <button
          onClick={() => handleClick('mcp-check')}
          disabled={loading}
          style={loading ? disabledButtonStyle : buttonStyle}
        >
          📊 MCP 데이터 확인
        </button>
        <button
          onClick={() => handleClick('mcp-clear')}
          disabled={loading}
          style={loading ? disabledButtonStyle : buttonStyle}
        >
          🧹 MCP 저장소 초기화
        </button>
      </div>
      {loading && (
        <div style={{ textAlign: 'center', marginTop: '10px', color: '#666' }}>
          처리 중...
        </div>
      )}
    </div>
  );
}

export default QuickCommands; 