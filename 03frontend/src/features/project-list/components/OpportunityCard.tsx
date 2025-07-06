/**
 * 机会卡片组件
 * 在列表中展示商业机会的核心信息
 */

import React from 'react'
import { Star, GitFork, Calendar, ExternalLink, TrendingUp, Users, Code } from 'lucide-react'
import { Badge } from '@/components/ui/badge'
import { OpportunityReport } from '@/lib/types'
import { formatNumber } from '@/lib/utils'

interface OpportunityCardProps {
  opportunity: OpportunityReport
  rank?: number
  onClick: () => void
}

export function OpportunityCard({ opportunity, rank, onClick }: OpportunityCardProps) {
  const { project, final_score, evaluation } = opportunity

  // 计算项目年龄
  const getProjectAge = (createdAt: string) => {
    const created = new Date(createdAt)
    const now = new Date()
    const diffTime = Math.abs(now.getTime() - created.getTime())
    const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24))
    
    if (diffDays < 30) return `${diffDays}天`
    if (diffDays < 365) return `${Math.floor(diffDays / 30)}月`
    return `${Math.floor(diffDays / 365)}年`
  }

  // 获取威胁等级
  const getThreatLevel = (score: number) => {
    if (score >= 85) return { label: 'CRITICAL', color: 'badge-danger' }
    if (score >= 70) return { label: 'HIGH', color: 'badge-warning' }
    if (score >= 50) return { label: 'MEDIUM', color: 'badge-primary' }
    return { label: 'LOW', color: 'badge-modern' }
  }

  const threatLevel = getThreatLevel(final_score)

  return (
    <div
      onClick={onClick}
      className="card-modern p-6 cursor-pointer group relative"
    >
      {/* 排名标识 */}
      {rank && (
        <div className="product-rank absolute -top-2 -left-2">
          {rank}
        </div>
      )}

      {/* 顶部信息 */}
      <div className="flex items-start justify-between mb-4">
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-3 mb-2">
            <h3 className="text-lg font-bold text-gray-900 truncate group-hover:text-brand transition-colors">
              {project.name}
            </h3>
            {/* NEW 标签 */}
            {(() => {
              const daysSinceCreated = Math.ceil((new Date().getTime() - new Date(project.created_at).getTime()) / (1000 * 60 * 60 * 24))
              return daysSinceCreated <= 7 ? (
                <span className="badge-success px-2 py-1 text-xs">NEW</span>
              ) : null
            })()}
          </div>
          
          <p className="text-sm text-gray-600 line-clamp-2 mb-3">
            {project.description || '暂无描述'}
          </p>

          {/* 项目统计 */}
          <div className="flex items-center gap-4 text-sm text-gray-500">
            <div className="flex items-center gap-1">
              <Star className="w-4 h-4" />
              <span>{project.stars_count?.toLocaleString() || 0}</span>
            </div>
            <div className="flex items-center gap-1">
              <GitFork className="w-4 h-4" />
              <span>{project.forks_count?.toLocaleString() || 0}</span>
            </div>
            <div className="flex items-center gap-1">
              <Calendar className="w-4 h-4" />
              <span>{getProjectAge(project.created_at)}</span>
            </div>
          </div>
        </div>

        {/* 威胁等级 */}
        <div className="ml-4">
          <div className={`badge-modern ${threatLevel.color} px-3 py-1 text-xs font-semibold`}>
            {threatLevel.label}
          </div>
        </div>
      </div>

      {/* 评估分数区域 */}
      <div className="border-t border-gray-100 pt-4">
        <div className="flex items-center justify-between mb-3">
          <span className="text-sm font-medium text-gray-700">综合评分</span>
          <div className="flex items-center gap-2">
            <div className="text-2xl font-bold text-gray-900">
              {final_score}
            </div>
            <div className="text-xs text-gray-500">/100</div>
          </div>
        </div>

        {/* 三维评分 */}
        <div className="grid grid-cols-3 gap-3">
          <div className="text-center">
            <div className="text-lg font-semibold text-blue-600">
              {evaluation?.business_value?.score || 0}
            </div>
            <div className="text-xs text-gray-500">商业</div>
          </div>
          <div className="text-center">
            <div className="text-lg font-semibold text-green-600">
              {evaluation?.technical_quality?.score || 0}
            </div>
            <div className="text-xs text-gray-500">技术</div>
          </div>
          <div className="text-center">
            <div className="text-lg font-semibold text-purple-600">
              {evaluation?.market_potential?.score || 0}
            </div>
            <div className="text-xs text-gray-500">市场</div>
          </div>
        </div>
      </div>

      {/* 底部标签区域 */}
      <div className="flex items-center justify-between mt-4 pt-4 border-t border-gray-100">
        <div className="flex items-center gap-2">
          {/* 语言标签 */}
          {project.language && (
            <span className="badge-modern px-2 py-1 text-xs">
              {project.language}
            </span>
          )}
          
          {/* ID 编码 */}
          <span className="text-xs text-gray-400 font-mono">
            #{project.id?.toString().slice(-6) || 'UNKNOWN'}
          </span>
        </div>

        {/* 查看详情 */}
        <div className="flex items-center gap-1 text-xs text-gray-500 group-hover:text-brand transition-colors">
          <span>查看详情</span>
          <ExternalLink className="w-3 h-3" />
        </div>
      </div>
    </div>
  )
} 