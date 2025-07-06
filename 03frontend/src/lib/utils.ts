/**
 * 工具函数
 */

import { type ClassValue, clsx } from 'clsx';
import { twMerge } from 'tailwind-merge';

/**
 * 合并 className，支持条件类名和 Tailwind CSS 类名冲突处理
 */
export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

/**
 * 格式化数字，添加千位分隔符
 */
export function formatNumber(num: number): string {
  return new Intl.NumberFormat('zh-CN').format(num);
}

/**
 * 格式化日期
 */
export function formatDate(date: string | Date): string {
  const d = new Date(date);
  return new Intl.DateTimeFormat('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
  }).format(d);
}

/**
 * 格式化日期时间
 */
export function formatDateTime(date: string | Date): string {
  const d = new Date(date);
  return new Intl.DateTimeFormat('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
  }).format(d);
}

/**
 * 计算相对时间（如：3小时前）
 */
export function formatRelativeTime(date: string | Date): string {
  const d = new Date(date);
  const now = new Date();
  const diff = now.getTime() - d.getTime();
  
  const minutes = Math.floor(diff / 60000);
  const hours = Math.floor(minutes / 60);
  const days = Math.floor(hours / 24);
  
  if (days > 0) {
    return `${days}天前`;
  } else if (hours > 0) {
    return `${hours}小时前`;
  } else if (minutes > 0) {
    return `${minutes}分钟前`;
  } else {
    return '刚刚';
  }
}

/**
 * 截断文本
 */
export function truncate(text: string, maxLength: number): string {
  if (text.length <= maxLength) return text;
  return text.slice(0, maxLength) + '...';
}

/**
 * 获取评分等级
 */
export function getScoreLevel(score: number): {
  level: 'excellent' | 'good' | 'average' | 'poor';
  label: string;
  color: string;
} {
  if (score >= 90) {
    return { level: 'excellent', label: '极佳', color: 'text-green-600' };
  } else if (score >= 75) {
    return { level: 'good', label: '良好', color: 'text-blue-600' };
  } else if (score >= 60) {
    return { level: 'average', label: '一般', color: 'text-yellow-600' };
  } else {
    return { level: 'poor', label: '较差', color: 'text-red-600' };
  }
} 