import { request } from './client';

export const getSettings = () => request<any>('/settings');
export const updateSettings = (settings: any) =>
  request<any>('/settings', {
    method: 'PUT',
    body: JSON.stringify(settings),
  });

export const searchFiles = (params: any) => {
  const query = new URLSearchParams();
  if (params.q) query.append('q', params.q);
  if (params.scope) query.append('scope', params.scope);
  if (params.page !== undefined) query.append('page', params.page.toString());
  if (params.page_size !== undefined) query.append('page_size', params.page_size.toString());
  
  return request<any>(`/search?${query.toString()}`);
};

export const getDashboard = () => request<any>('/dashboard');

export const getAvailableModels = (baseUrl: string, apiKey: string) => 
  request<{ models: string[] }>('/settings/models', {
    method: 'POST',
    body: JSON.stringify({ base_url: baseUrl, api_key: apiKey })
  });