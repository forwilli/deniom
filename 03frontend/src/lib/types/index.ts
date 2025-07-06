/**
 * 类型定义文件
 * 定义所有前端使用的数据类型
 */

// 项目分析阶段
export enum AnalysisPhase {
  SCREENING = 'screening',      // 宽基筛选
  EVALUATION = 'evaluation',    // 深度评估
  MARKET = 'market',           // 市场洞察
  SYNTHESIS = 'synthesis'      // 顶尖合成
}

// GitHub 项目基础信息
export interface GithubProject {
  id: number;
  owner: string;
  name: string;
  full_name: string;
  description: string | null;
  html_url: string;
  stars_count: number;
  forks_count: number;
  language: string | null;
  created_at: string;
  updated_at: string;
  pushed_at: string;
  topics: string[];
}

// 筛选结果
export interface ScreeningResult {
  project_id: number;
  has_potential: boolean;
  reason: string;
  score: number;
  screened_at: string;
}

// 深度评估结果
export interface EvaluationResult {
  project_id: number;
  business_value: {
    score: number;
    description: string;
    highlights: string[];
  };
  technical_quality: {
    score: number;
    description: string;
    strengths: string[];
    weaknesses: string[];
  };
  market_potential: {
    score: number;
    description: string;
    opportunities: string[];
    risks: string[];
  };
  overall_score: number;
  summary: string;
  evaluated_at: string;
}

// 市场洞察结果
export interface MarketInsight {
  project_id: number;
  competitors: Array<{
    name: string;
    description: string;
    market_share?: string;
    strengths: string[];
  }>;
  market_trends: string[];
  opportunity_gaps: string[];
  positioning_strategy: string;
  insights_at: string;
}

// 综合分析结果（最终产出）
export interface OpportunityReport {
  id: string;
  project: GithubProject;
  screening: ScreeningResult;
  evaluation: EvaluationResult;
  market: MarketInsight;
  final_score: number;
  recommendation: string;
  action_items: string[];
  created_at: string;
  updated_at: string;
}

// API 分页响应
export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  size: number;
  pages: number;
}

// API 错误响应
export interface ApiError {
  detail: string;
  code?: string;
  timestamp: string;
} 