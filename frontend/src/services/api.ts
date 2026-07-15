import axios from 'axios';
import type { SearchResponse } from '../types';

const API_BASE_URL = '/api';

// 通过文字搜索折纸教程
export async function searchByText(text: string): Promise<SearchResponse> {
  const formData = new FormData();
  formData.append('text', text);
  const response = await axios.post<SearchResponse>(`${API_BASE_URL}/search`, formData);
  return response.data;
}

// 通过图片搜索折纸教程
export async function searchByImage(file: File): Promise<SearchResponse> {
  const formData = new FormData();
  formData.append('image', file);
  const response = await axios.post<SearchResponse>(`${API_BASE_URL}/search`, formData);
  return response.data;
}
