import axios from 'axios';
import { 
  DashboardStats, Product, ProductHistoryItem, 
  RuleConfig, ScanJobResult, ScanJobStatus 
} from '../types';

const API_BASE = '/api/v1';

export const apiClient = axios.create({
  baseURL: API_BASE,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Attach JWT token automatically
apiClient.interceptors.request.use((config) => {
  const token = localStorage.getItem('visionx_token') || localStorage.getItem('legalmetro_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Response interceptor to handle auth expiration
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      // Don't auto-redirect on login page
      if (!window.location.pathname.includes('/login')) {
        localStorage.removeItem('visionx_token');
        localStorage.removeItem('visionx_user');
        localStorage.removeItem('legalmetro_token');
        localStorage.removeItem('legalmetro_user');
        window.location.href = '/login';
      }
    }
    return Promise.reject(error);
  }
);

export const api = {
  auth: {
    login: async (email: string, password: string) => {
      const resp = await apiClient.post('/auth/login', { email, password });
      return resp.data;
    },
    getMe: async () => {
      const resp = await apiClient.get('/auth/me');
      return resp.data;
    },
  },

  products: {
    scan: async (formData: FormData) => {
      const resp = await apiClient.post('/products/scan', formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
      });
      return resp.data;
    },
    getScanStatus: async (jobId: string): Promise<ScanJobStatus> => {
      const resp = await apiClient.get(`/products/scan/${jobId}/status`);
      return resp.data;
    },
    getScanResult: async (jobId: string): Promise<ScanJobResult> => {
      const resp = await apiClient.get(`/products/scan/${jobId}/result`);
      return resp.data;
    },
    list: async (params?: { search?: string; status?: string; category?: string; skip?: number; limit?: number }): Promise<Product[]> => {
      const resp = await apiClient.get('/products', { params });
      return resp.data;
    },
    getHistory: async (productId: number): Promise<{ product: Product; inspections: ProductHistoryItem[] }> => {
      const resp = await apiClient.get(`/products/${productId}/history`);
      return resp.data;
    },
    submitQrEvidence: async (jobId: string, formData: FormData) => {
      const resp = await apiClient.post(`/products/scan/${jobId}/qr-evidence`, formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
      });
      return resp.data;
    },
    skipQrEvidence: async (jobId: string) => {
      const resp = await apiClient.post(`/products/scan/${jobId}/skip-qr-evidence`);
      return resp.data;
    },
    submitNoBatchCode: async (jobId: string) => {
      const resp = await apiClient.post(`/products/scan/${jobId}/no-batch-code`);
      return resp.data;
    },
    editField: async (jobId: string, payload: { field_key: string; new_value: string; revert?: boolean }): Promise<ScanJobResult> => {
      const resp = await apiClient.patch(`/products/scan/${jobId}/edit-field`, payload);
      return resp.data;
    },
  },

  reports: {
    generate: async (scanId: string) => {
      const resp = await apiClient.post(`/reports/${scanId}/generate`);
      return resp.data;
    },
    getPdfDownloadUrl: (scanId: string) => `${API_BASE}/reports/${scanId}/download/pdf`,
    getDocxDownloadUrl: (scanId: string) => `${API_BASE}/reports/${scanId}/download/docx`,
    attachEvidence: async (scanId: string, formData: FormData) => {
      const resp = await apiClient.post(`/reports/${scanId}/attach-evidence`, formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
      });
      return resp.data;
    },
  },

  dashboard: {
    getStats: async (): Promise<DashboardStats> => {
      const resp = await apiClient.get('/dashboard/stats');
      return resp.data;
    },
  },

  admin: {
    getRules: async (): Promise<RuleConfig[]> => {
      const resp = await apiClient.get('/admin/rules');
      return resp.data;
    },
    updateRule: async (ruleId: string, data: Partial<RuleConfig>): Promise<RuleConfig> => {
      const resp = await apiClient.put(`/admin/rules/${ruleId}`, data);
      return resp.data;
    },
  },
};
