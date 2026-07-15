import axios from 'axios';
import type { SearchResponse } from '../types';

const API_BASE_URL = '/api';

export async function searchByText(text: string): Promise<SearchResponse> {
  const formData = new FormData();
  formData.append('text', text);
  const response = await axios.post<SearchResponse>(`${API_BASE_URL}/search`, formData, {
    timeout: 60000,
  });
  return response.data;
}

export async function searchByImage(file: File): Promise<SearchResponse> {
  const formData = new FormData();
  formData.append('image', file);
  const response = await axios.post<SearchResponse>(`${API_BASE_URL}/search`, formData, {
    timeout: 60000,
  });
  return response.data;
}

export async function getDemo(): Promise<SearchResponse> {
  const response = await axios.get<SearchResponse>(`${API_BASE_URL}/demo`, {
    timeout: 60000,
  });
  return response.data;
}
