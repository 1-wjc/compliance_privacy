const navButtonStyle = {
  padding: '10px 15px',
  margin: '5px',
  backgroundColor: '#007bff',
  color: 'white',
  border: 'none',
  borderRadius: '5px',
  cursor: 'pointer',
  fontSize: '14px'
};

function NavBar({ setCurrentPanel }) {
  return (
    <nav style={{ display: 'flex', gap: '10px', padding: '10px', background: '#f0f0f0', justifyContent: 'center' }}>
      <button style={navButtonStyle} onClick={() => setCurrentPanel('files')}>📄 파일목록</button>
      <button style={navButtonStyle} onClick={() => setCurrentPanel('results')}>📊 분석 결과 확인</button>
      <button style={navButtonStyle} onClick={() => setCurrentPanel('mcp')}>📋 MCP 데이터 확인</button>
      <button style={navButtonStyle} onClick={() => setCurrentPanel('config')}>⚙️ 설정</button>
      <button style={navButtonStyle} onClick={() => setCurrentPanel('help')}>❓ 도움말</button>
      <button style={navButtonStyle} onClick={() => setCurrentPanel('tools')}>🛠️ 도구목록</button>
    </nav>
  );
}

export default NavBar; 