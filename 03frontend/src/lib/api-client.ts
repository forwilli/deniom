/**
 * API 客户端
 * 封装 axios 实例，提供统一的 API 调用接口
 */

import axios, { AxiosError } from 'axios';
import { config } from '@/lib/config';

// 创建 axios 实例
export const apiClient = axios.create({
  baseURL: config.apiBaseUrl,
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// 请求拦截器
apiClient.interceptors.request.use(
  (config) => {
    // 可以在这里添加认证 token 等
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// 响应拦截器
apiClient.interceptors.response.use(
  (response) => {
    return response;
  },
  (error: AxiosError) => {
    // 统一错误处理
    if (error.response) {
      // 服务器返回错误状态码
      console.error('API Error:', error.response.status, error.response.data);
    } else if (error.request) {
      // 请求已发送但未收到响应
      console.error('Network Error:', error.message);
    } else {
      // 其他错误
      console.error('Error:', error.message);
    }
    return Promise.reject(error);
  }
);

export default apiClient; 