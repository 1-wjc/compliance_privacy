import React, { useState } from 'react';
import axios from 'axios';

function Chat() {
  const [input, setInput] = useState('');
  const [history, setHistory] = useState([]);
  const [loading, setLoading] = useState(false);

  // 빠른 분석 핸들러
  const handleQuickAnalysis = (type) => {
    if (loading) return;
    let command = '';
    switch (type) {
      case 'llm':
        command = 'LLM 분석 실행';
        break;
      case 'keyword_llm':
        command = 'Keyword+LLM 분석 실행';
        break;
      case 'rag':
        command = 'RAG 분석 실행';
        break;
      case 'satisfaction':
        command = '충족도 분석 실행';
        break;
      default:
        return;
    }
    setInput(command);
    sendCommand(command);
  };

  const sendCommand = async (customInput) => {
    const commandToSend = customInput !== undefined ? customInput : input;
    if (typeof commandToSend !== 'string' || !commandToSend.trim()) return;
    
    const userMessage = { role: 'user', content: commandToSend, timestamp: new Date().toLocaleTimeString() };
    setHistory(prev => [...prev, userMessage]);
    setLoading(true);
    
    try {
      const response = await axios.post('/api/command', { command: commandToSend });
      const assistantMessage = { 
        role: 'assistant', 
        content: response.data.message, 
        timestamp: new Date().toLocaleTimeString() 
      };
      setHistory(prev => [...prev, assistantMessage]);
    } catch (error) {
      const errorMessage = { 
        role: 'assistant', 
        content: `오류가 발생했습니다: ${error.message}`, 
        timestamp: new Date().toLocaleTimeString() 
      };
      setHistory(prev => [...prev, errorMessage]);
    } finally {
      setLoading(false);
      setInput('');
    }
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendCommand();
    }
  };

  return (
    <div style={{ maxWidth: '750px', margin: '0 auto', padding: '5px' }}>
      <h4>💬</h4>
      
      {/* 채팅 히스토리 */}
      <div 
        style={{ 
          height: '250px', 
          border: '1px solid #ddd', 
          borderRadius: '8px',
          padding: '15px',
          marginBottom: '15px',
          overflowY: 'auto',
          backgroundColor: '#f9f9f9',
          position: 'relative'
        }}
      >
        {history.length === 0 && (
          <div style={{
            position: 'absolute',
            top: '50%',
            left: '50%',
            transform: 'translate(-50%, -50%)',
            color: '#666',
            textAlign: 'center',
            width: '100%'
          }}>
            <div>명령을 입력하여 대화를 시작하세요</div>
            <div style={{ marginTop: 24, fontWeight: 'bold', fontSize: 16 }}>빠른 실행</div>
            <div style={{ marginTop: 16, display: 'flex', flexDirection: 'row', gap: 10, justifyContent: 'center' }}>
              <button
                onClick={() => handleQuickAnalysis('llm')}
                style={{
                  padding: '8px 14px',
                  borderRadius: '6px',
                  border: '1px solid #87cefa',
                  background: '#87cefa',
                  color: '#222',
                  cursor: 'pointer',
                  fontSize: '14px',
                  minWidth: '90px',
                  transition: 'background 0.2s',
                }}
                onMouseOver={e => e.currentTarget.style.background = '#e0ffff'}
                onMouseOut={e => e.currentTarget.style.background = '#87cefa'}
              >LLM 분석</button>
              <button
                onClick={() => handleQuickAnalysis('keyword_llm')}
                style={{
                  padding: '8px 14px',
                  borderRadius: '6px',
                  border: '1px solid #87cefa',
                  background: '#87cefa',
                  color: '#222',
                  cursor: 'pointer',
                  fontSize: '14px',
                  minWidth: '120px',
                  transition: 'background 0.2s',
                }}
                onMouseOver={e => e.currentTarget.style.background = '#e0ffff'}
                onMouseOut={e => e.currentTarget.style.background = '#87cefa'}
              >Keyword+LLM 분석</button>
              <button
                onClick={() => handleQuickAnalysis('rag')}
                style={{
                  padding: '8px 14px',
                  borderRadius: '6px',
                  border: '1px solid #87cefa',
                  background: '#87cefa',
                  color: '#222',
                  cursor: 'pointer',
                  fontSize: '14px',
                  minWidth: '90px',
                  transition: 'background 0.2s',
                }}
                onMouseOver={e => e.currentTarget.style.background = '#e0ffff'}
                onMouseOut={e => e.currentTarget.style.background = '#87cefa'}
              >RAG 분석</button>
              <button
                onClick={() => handleQuickAnalysis('satisfaction')}
                style={{
                  padding: '8px 14px',
                  borderRadius: '6px',
                  border: '1px solid #87cefa',
                  background: '#87cefa',
                  color: '#222',
                  cursor: 'pointer',
                  fontSize: '14px',
                  minWidth: '110px',
                  transition: 'background 0.2s',
                }}
                onMouseOver={e => e.currentTarget.style.background = '#e0ffff'}
                onMouseOut={e => e.currentTarget.style.background = '#87cefa'}
              >충족도 분석</button>
            </div>
          </div>
        )}
        
        {history.map((message, index) => (
          <div 
            key={index} 
            style={{ 
              marginBottom: '10px',
              textAlign: message.role === 'user' ? 'right' : 'left'
            }}
          >
            <div 
              style={{
                display: 'inline-block',
                maxWidth: '70%',
                padding: '10px 15px',
                borderRadius: '15px',
                backgroundColor: message.role === 'user' ? '#007bff' : '#e9ecef',
                color: message.role === 'user' ? 'white' : 'black',
                wordWrap: 'break-word'
              }}
            >
              <div style={{ fontSize: '12px', marginBottom: '5px', opacity: 0.7 }}>
                {message.timestamp}
              </div>
              <div>{message.content}</div>
            </div>
          </div>
        ))}
        
        {loading && (
          <div style={{ textAlign: 'center', color: '#666', fontStyle: 'italic' }}>
            처리 중...
          </div>
        )}
      </div>
      
      {/* 입력 필드 */}
      <div style={{ display: 'flex', gap: '10px' }}>
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyPress={handleKeyPress}
          placeholder="명령을 입력하세요 (예: ㅇㅇ카드 분석해줘, 파일 목록, 설정)"
          disabled={loading}
          style={{
            flex: 1,
            padding: '12px',
            border: '1px solid #ddd',
            borderRadius: '6px',
            fontSize: '14px'
          }}
        />
        <button
          onClick={sendCommand}
          disabled={loading || !input.trim()}
          style={{
            padding: '12px 20px',
            backgroundColor: '#007bff',
            color: 'white',
            border: 'none',
            borderRadius: '6px',
            cursor: 'pointer',
            fontSize: '14px'
          }}
        >
          {loading ? '처리중...' : '전송'}
        </button>
      </div>
    </div>
  );
}

export default Chat; 