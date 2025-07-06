/**
 * 前端配置文件
 */

export const config = {
  // 控制是否使用模拟数据。设置为 true 时，所有 API 请求将返回本地 mock 数据。
  useMockData: true,

  // API 基础 URL
  apiBaseUrl: process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000',
  
  // 分页配置
  defaultPageSize: 20,
  
  // 数据刷新间隔（毫秒）
  dataRefreshInterval: 5 * 60 * 1000, // 5分钟
  
  // 日期格式
  dateFormat: 'yyyy-MM-dd',
  dateTimeFormat: 'yyyy-MM-dd HH:mm:ss',
} as const; 