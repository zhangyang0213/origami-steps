import { useState, useRef, type DragEvent, type ChangeEvent } from 'react';
import { Upload, Search, Image as ImageIcon, Type } from 'lucide-react';
import { searchByText, searchByImage } from '../services/api';
import type { SearchResponse } from '../types';
import './InputPanel.css';

type InputMode = 'image' | 'text';

interface InputPanelProps {
  onSearchResult: (result: SearchResponse) => void;
  onLoadingChange: (loading: boolean) => void;
}

function InputPanel({ onSearchResult, onLoadingChange }: InputPanelProps) {
  const [mode, setMode] = useState<InputMode>('text');
  const [textInput, setTextInput] = useState('');
  const [imageFile, setImageFile] = useState<File | null>(null);
  const [imagePreview, setImagePreview] = useState<string | null>(null);
  const [isDragging, setIsDragging] = useState(false);
  const [loading, setLoading] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  // 处理图片拖拽
  const handleDragOver = (e: DragEvent) => {
    e.preventDefault();
    setIsDragging(true);
  };

  const handleDragLeave = (e: DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
  };

  const handleDrop = (e: DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
    const file = e.dataTransfer.files[0];
    if (file && file.type.startsWith('image/')) {
      setImageFile(file);
      setImagePreview(URL.createObjectURL(file));
    }
  };

  // 处理图片选择
  const handleFileChange = (e: ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      setImageFile(file);
      setImagePreview(URL.createObjectURL(file));
    }
  };

  // 清除已选图片
  const clearImage = () => {
    setImageFile(null);
    setImagePreview(null);
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  };

  // 提交搜索
  const handleSubmit = async () => {
    if (mode === 'text' && !textInput.trim()) return;
    if (mode === 'image' && !imageFile) return;

    setLoading(true);
    onLoadingChange(true);

    try {
      let result: SearchResponse;
      if (mode === 'text') {
        result = await searchByText(textInput.trim());
      } else {
        result = await searchByImage(imageFile!);
      }
      onSearchResult(result);
    } catch (error) {
      console.error('搜索失败:', error);
    } finally {
      setLoading(false);
      onLoadingChange(false);
    }
  };

  return (
    <div className="input-panel">
      <div className="input-panel__header">
        <h2 className="input-panel__title">🦢 折纸步骤分解</h2>
        <p className="input-panel__subtitle">输入折纸名称或上传图片，自动分解步骤</p>
      </div>

      {/* 模式切换标签 */}
      <div className="input-panel__tabs">
        <button
          className={`input-panel__tab ${mode === 'text' ? 'active' : ''}`}
          onClick={() => setMode('text')}
        >
          <Type size={16} />
          文字输入
        </button>
        <button
          className={`input-panel__tab ${mode === 'image' ? 'active' : ''}`}
          onClick={() => setMode('image')}
        >
          <ImageIcon size={16} />
          图片上传
        </button>
      </div>

      {/* 文字输入模式 */}
      {mode === 'text' && (
        <div className="input-panel__text-area">
          <input
            type="text"
            className="input-panel__text-input"
            placeholder="输入折纸名称，如：纸鹤、玫瑰、青蛙..."
            value={textInput}
            onChange={(e) => setTextInput(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && handleSubmit()}
          />
        </div>
      )}

      {/* 图片上传模式 */}
      {mode === 'image' && (
        <div className="input-panel__image-area">
          {imagePreview ? (
            <div className="input-panel__preview">
              <img src={imagePreview} alt="预览" />
              <button className="input-panel__clear-btn" onClick={clearImage}>✕</button>
            </div>
          ) : (
            <div
              className={`input-panel__dropzone ${isDragging ? 'dragging' : ''}`}
              onDragOver={handleDragOver}
              onDragLeave={handleDragLeave}
              onDrop={handleDrop}
              onClick={() => fileInputRef.current?.click()}
            >
              <Upload size={32} className="input-panel__dropzone-icon" />
              <p>拖拽图片到此处，或点击上传</p>
              <span className="input-panel__dropzone-hint">支持 JPG、PNG、WebP 格式</span>
            </div>
          )}
          <input
            ref={fileInputRef}
            type="file"
            accept="image/*"
            onChange={handleFileChange}
            className="input-panel__file-input"
          />
        </div>
      )}

      {/* 提交按钮 */}
      <button
        className="input-panel__submit-btn"
        onClick={handleSubmit}
        disabled={loading || (mode === 'text' ? !textInput.trim() : !imageFile)}
      >
        {loading ? (
          <span className="input-panel__spinner" />
        ) : (
          <Search size={18} />
        )}
        {loading ? '搜索中...' : '开始分解'}
      </button>
    </div>
  );
}

export default InputPanel;
