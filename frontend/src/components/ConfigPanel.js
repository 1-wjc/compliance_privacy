import React, { useState, useEffect } from 'react';
import axios from 'axios';

function ConfigPanel() {
  const [config, setConfig] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const fetchConfig = async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await axios.get('/api/config');
      setConfig(response.data.message);
    } catch (err) {
      setError(`설정을 불러오는데 실패했습니다: ${err.message}`);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchConfig();
  }, []);

  if (loading) return <div style={{ padding: 20, textAlign: 'center' }}>설정을 불러오는 중...</div>;
  if (error) return <div style={{ padding: 20, color: 'red' }}>{error}</div>;
  return (
    <div style={{ margin: 0, padding: 0 }}>
      <style>{`hr { border: none; border-top: 1.5px solid #bbb; margin: 24px 0; }`}</style>
      <div dangerouslySetInnerHTML={{ __html: config }} />
    </div>
  );
}

export default ConfigPanel; 