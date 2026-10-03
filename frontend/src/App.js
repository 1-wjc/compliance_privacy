import React, { useState } from 'react';
import FileUpload from './components/FileUpload';
import Chat from './components/Chat';
import HelpPanel from './components/HelpPanel';
import FilesPanel from './components/FilesPanel';
import ResultsPanel from './components/ResultsPanel';
import MCPDataPanel from './components/MCPDataPanel';
import ConfigPanel from './components/ConfigPanel';

const quickButtonStyle = {
  padding: '8px 12px',
  fontSize: '15px',
  background: '#007bff',
  color: 'white',
  border: 'none',
  borderRadius: '6px',
  cursor: 'pointer',
  fontWeight: 'bold',
  minWidth: '110px'
};

function App() {
  const [activePanel, setActivePanel] = useState(null); // 기본은 아무 패널도 안뜸

  const renderPanel = () => {
    switch (activePanel) {
      case 'help': return <HelpPanel />;
      case 'files': return <FilesPanel />;
      case 'results': return <ResultsPanel />;
      case 'mcp': return <MCPDataPanel />;
      case 'config': return <ConfigPanel />;
      default: return null;
    }
  };

  return (
    <div style={{ minHeight: '100vh', backgroundColor: '#f5f5f5' }}>
      {/* 헤더 */}
      <header style={{
        backgroundColor: '#2c3e50',
        color: 'white',
        padding: '20px',
        textAlign: 'center'
      }}>
        <h1 style={{ margin: 0, fontSize: '2rem' }}>
          개인정보 처리방침 자동화 분석 서비스
        </h1>
        <p style={{ margin: '10px 0 0 0', opacity: 0.8 }}>
          LangChain MCP Agent 기반
        </p>
      </header>
      <div style={{ maxWidth: 800, margin: '0 auto', padding: 24 }}>
        {/* 파일 업로드 */}
        <div style={{ marginBottom: 24 }}>
          <FileUpload />
        </div>
        {/* 채팅창 항상 위에 고정 */}
        <div style={{ marginBottom: 32 }}>
          <Chat />
        </div>
        {/* 퀵 메뉴 */}
        <div style={{ fontWeight: 'bold', fontSize: 18, marginBottom: 16, textAlign: 'center' }}>퀵 메뉴</div>
        {/* 버튼들 */}
        <div style={{ display: 'flex', flexDirection: 'row', gap: 12, justifyContent: 'center', marginBottom: 32 }}>
          <button style={quickButtonStyle} onClick={() => setActivePanel('help')}>❓ 도움말</button>
          <button style={quickButtonStyle} onClick={() => setActivePanel('files')}>📄 파일목록</button>
          <button style={quickButtonStyle} onClick={() => setActivePanel('results')}>📊 분석 결과 확인</button>
          <button style={quickButtonStyle} onClick={() => setActivePanel('mcp')}>📋 MCP 데이터 확인</button>
          <button style={quickButtonStyle} onClick={() => setActivePanel('config')}>⚙️ 설정</button>
        </div>
        {/* 선택된 패널 */}
        <div>
          {renderPanel()}
        </div>
      </div>
      {/* 푸터 */}
      <footer style={{
        backgroundColor: '#2c3e50',
        color: 'white',
        textAlign: 'center',
        padding: '20px',
        marginTop: '40px'
      }}>
        <p style={{ margin: 0, opacity: 0.8 }}>
          © 개인정보 처리방침 자동화 분석 서비스
        </p>
      </footer>
    </div>
  );
}

export default App;
