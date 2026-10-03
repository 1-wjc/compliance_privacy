import React, { useState, useEffect } from 'react';
import axios from 'axios';

function HelpPanel() {
  const [help, setHelp] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const fetchHelp = async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await axios.get('/api/help');
      setHelp(response.data.message);
    } catch (err) {
      setError(`도움말을 불러오는데 실패했습니다: ${err.message}`);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchHelp();
  }, []);

  if (loading) {
    return <div style={{ padding: '20px', textAlign: 'center' }}>도움말을 불러오는 중...</div>;
  }

  if (error) {
    return <div style={{ padding: '20px', color: 'red' }}>{error}</div>;
  }

  return (
    <div style={{ margin: 0, padding: 0 }}>
      <div dangerouslySetInnerHTML={{ __html: help }} />
    </div>
  );
}

export default HelpPanel; 