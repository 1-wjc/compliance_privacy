import React, { useState, useRef, useEffect } from 'react';
import axios from 'axios';

function FileUpload({ onUploadSuccess }) {
  const [dragActive, setDragActive] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [message, setMessage] = useState('');
  const [uploadedFiles, setUploadedFiles] = useState([]);
  const fileInputRef = useRef(null);

  // 업로드된 파일 목록 조회
  const fetchUploadedFiles = async () => {
    try {
      const response = await axios.get('/api/uploaded-files');
      if (response.data.success) {
        setUploadedFiles(response.data.files);
      }
    } catch (error) {
      console.error('파일 목록 조회 실패:', error);
    }
  };

  // 컴포넌트 마운트 시 파일 목록 조회
  useEffect(() => {
    fetchUploadedFiles();
  }, []);

  const handleDrag = (e) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === "dragenter" || e.type === "dragover") {
      setDragActive(true);
    } else if (e.type === "dragleave") {
      setDragActive(false);
    }
  };

  const handleDrop = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
    
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      handleFiles(Array.from(e.dataTransfer.files));
    }
  };

  const handleFileInput = (e) => {
    if (e.target.files && e.target.files.length > 0) {
      handleFiles(Array.from(e.target.files));
    }
  };

  const handleFiles = async (files) => {
    const pdfFiles = files.filter(file => file.name.toLowerCase().endsWith('.pdf'));
    
    if (pdfFiles.length === 0) {
      setMessage('PDF 파일만 업로드 가능합니다.');
      return;
    }

    setUploading(true);
    setMessage('');

    let successCount = 0;
    let errorCount = 0;
    for (const file of pdfFiles) {
      const formData = new FormData();
      formData.append('file', file);

      try {
        const response = await axios.post('/api/upload', formData, {
          headers: {
            'Content-Type': 'multipart/form-data',
          },
        });

        if (response.data.success) {
          successCount++;
        } else {
          errorCount++;
        }
      } catch (error) {
        errorCount++;
      }
    }

    if (successCount > 0) {
      let msg = `${successCount}개 파일이 성공적으로 업로드되었습니다.`;
      if (errorCount > 0) {
        msg += ` (${errorCount}개 실패)`;
      }
      setMessage(msg);
      if (onUploadSuccess) {
        onUploadSuccess();
      }
      // 파일 목록 새로고침
      fetchUploadedFiles();
    } else {
      setMessage(`업로드 실패: ${errorCount}개 파일`);
    }

    setUploading(false);
  };

  const deleteFile = async (filename) => {
    try {
      const response = await axios.delete(`/api/uploaded-files/${filename}`);
      if (response.data.success) {
        setMessage(response.data.message);
        // 파일 목록 새로고침
        fetchUploadedFiles();
      } else {
        setMessage(response.data.message);
      }
    } catch (error) {
      setMessage(`삭제 실패: ${error.message}`);
    }
  };

  const openFileDialog = () => {
    fileInputRef.current.click();
  };

  return (
    <div style={{ padding: '20px', backgroundColor: '#f8f9fa', borderRadius: '8px', marginBottom: '20px' }}>
      <h3>파일 업로드</h3>
      
      <div
        style={{
          border: `2px dashed ${dragActive ? '#007bff' : '#ddd'}`,
          borderRadius: '8px',
          padding: '8px',
          textAlign: 'center',
          backgroundColor: dragActive ? '#f8f9ff' : 'white',
          cursor: 'pointer',
          transition: 'all 0.3s ease'
        }}
        onDragEnter={handleDrag}
        onDragLeave={handleDrag}
        onDragOver={handleDrag}
        onDrop={handleDrop}
        onClick={openFileDialog}
      >
        <div style={{ fontSize: '48px', marginBottom: '10px' }}>
          📄
        </div>
        <p style={{ fontSize: '16px', marginBottom: '10px' }}>
          PDF 파일들을 여기에 드래그하거나 클릭하여 선택하세요
        </p>
        <p style={{ fontSize: '14px', color: '#666' }}>
          여러 파일을 한 번에 업로드할 수 있습니다
        </p>
        
        <input
          ref={fileInputRef}
          type="file"
          accept=".pdf"
          multiple
          onChange={handleFileInput}
          style={{ display: 'none' }}
        />
      </div>

      {/* URL 입력란 추가 */}
      <div style={{ margin: '24px 0 0 0', padding: '16px', background: '#fff', borderRadius: '8px', border: '1px solid #ccc' }}>
        <form
          onSubmit={async (e) => {
            e.preventDefault();
            if (!e.target.urlInput.value) return;
            setUploading(true);
            setMessage('');
            try {
              const response = await axios.post('/api/upload_url', { url: e.target.urlInput.value });
              if (response.data.success) {
                setMessage('URL에서 개인정보 처리방침을 성공적으로 업로드했습니다.');
                if (onUploadSuccess) onUploadSuccess();
                fetchUploadedFiles();
              } else {
                setMessage('URL 업로드 실패: ' + (response.data.message || '오류'));
              }
            } catch (err) {
              setMessage('URL 업로드 중 오류 발생: ' + (err.response?.data?.message || err.message));
            }
            setUploading(false);
          }}
          style={{ display: 'flex', alignItems: 'center', gap: '8px' }}
        >
          <input
            type="text"
            name="urlInput"
            placeholder="개인정보 처리방침 URL 입력"
            style={{ flex: 1, padding: '8px', borderRadius: '4px', border: '1px solid #ccc' }}
            disabled={uploading}
          />
          <button
            type="submit"
            style={{ padding: '8px 16px', borderRadius: '4px', border: 'none', background: '#007bff', color: 'white', fontWeight: 'bold', cursor: 'pointer' }}
            disabled={uploading}
          >
            URL 업로드
          </button>
        </form>
        <div style={{ fontSize: '13px', color: '#888', marginTop: '4px' }}>
          또는 URL을 입력해 업로드할 수 있습니다
        </div>
      </div>

      {uploading && (
        <div style={{ textAlign: 'center', marginTop: '10px', color: '#007bff' }}>
          업로드 중...
        </div>
      )}

      {message && (
        <div style={{
          marginTop: '10px',
          padding: '10px',
          borderRadius: '5px',
          backgroundColor: message.includes('성공') ? '#d4edda' : '#f8d7da',
          color: message.includes('성공') ? '#155724' : '#721c24',
          border: `1px solid ${message.includes('성공') ? '#c3e6cb' : '#f5c6cb'}`
        }}>
          {message}
        </div>
      )}

      {/* 업로드된 파일 목록 */}
      {uploadedFiles.length > 0 && (
        <div style={{ marginTop: '20px' }}>
          <h4>목록</h4>
          <div style={{ maxHeight: 300, overflowY: 'auto' }}>
            {uploadedFiles.map((file, index) => (
              <div
                key={index}
                style={{
                  display: 'flex',
                  justifyContent: 'space-between',
                  alignItems: 'center',
                  padding: '10px',
                  margin: '5px 0',
                  backgroundColor: 'white',
                  borderRadius: '5px',
                  border: '1px solid #ddd'
                }}
              >
                <div style={{ flex: 1 }}>
                  <div style={{ fontWeight: 'bold', fontSize: '14px' }}>
                    {file.name}
                  </div>
                  <div style={{ fontSize: '12px', color: '#666' }}>
                    크기: {file.size_mb} MB | 
                    수정일: {new Date(file.modified).toLocaleString()}
                  </div>
                </div>
                <button
                  onClick={() => deleteFile(file.name)}
                  style={{
                    backgroundColor: '#dc3545',
                    color: 'white',
                    border: 'none',
                    borderRadius: '4px',
                    padding: '5px 10px',
                    cursor: 'pointer',
                    fontSize: '12px'
                  }}
                >
                  삭제
                </button>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

export default FileUpload; 