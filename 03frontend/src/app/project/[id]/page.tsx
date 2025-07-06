'use client'

import { useEffect, useState } from 'react'
import { useParams, useRouter } from 'next/navigation'
import { ArrowLeft, ExternalLink, Star, GitFork, Calendar, Users, Code, TrendingUp, AlertTriangle, Target, Lightbulb } from 'lucide-react'
import { OpportunityReport } from '@/lib/types'
import { mockOpportunities } from '@/lib/mock-data'
import { useQuery } from '@tanstack/react-query'
import { ProjectDetailView } from '@/features/project-detail/components/ProjectDetailView'
import { projectDetailApi } from '@/features/project-detail/api'

export default function ProjectDetailPage() {
  const params = useParams()
  const router = useRouter()
  const [opportunity, setOpportunity] = useState<OpportunityReport | null>(null)
  const [loading, setLoading] = useState(true)

  const { data: project, isLoading } = useQuery({ 
    queryKey: ['project', params.id],
    queryFn: () => projectDetailApi.getById(params.id),
  })

  useEffect(() => {
    // 模拟数据获取
    const projectId = params.id as string
    const foundOpportunity = mockOpportunities.find(op => op.id === projectId)
    
    setTimeout(() => {
      setOpportunity(foundOpportunity || null)
      setLoading(false)
    }, 300)
  }, [params.id])

  // 计算项目年龄
  const getProjectAge = (createdAt: string) => {
    const created = new Date(createdAt)
    const now = new Date()
    const diffTime = Math.abs(now.getTime() - created.getTime())
    const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24))
    
    if (diffDays < 30) return `${diffDays}天前`
    if (diffDays < 365) return `${Math.floor(diffDays / 30)}个月前`
    return `${Math.floor(diffDays / 365)}年前`
  }

  // 获取威胁等级
  const getThreatLevel = (score: number) => {
    if (score >= 85) return { label: 'CRITICAL', color: 'badge-danger', bg: 'bg-red-50', border: 'border-red-200' }
    if (score >= 70) return { label: 'HIGH', color: 'badge-warning', bg: 'bg-orange-50', border: 'border-orange-200' }
    if (score >= 50) return { label: 'MEDIUM', color: 'badge-primary', bg: 'bg-blue-50', border: 'border-blue-200' }
    return { label: 'LOW', color: 'badge-clean', bg: 'bg-gray-50', border: 'border-gray-200' }
  }

  if (loading) {
    return (
      <div className="min-h-screen bg-white flex items-center justify-center">
        <div className="text-center">
          <div className="text-gray-900 text-lg font-semibold mb-2">加载中...</div>
          <div className="text-gray-600 text-sm">正在获取项目详情</div>
        </div>
      </div>
    )
  }

  if (!opportunity) {
    return (
      <div className="min-h-screen bg-white flex items-center justify-center">
        <div className="text-center">
          <div className="text-gray-900 text-lg font-semibold mb-2">项目未找到</div>
          <div className="text-gray-600 text-sm mb-4">请检查项目ID是否正确</div>
          <button 
            onClick={() => router.back()}
            className="button-clean flex items-center gap-2"
          >
            <ArrowLeft className="w-4 h-4" />
            返回
          </button>
        </div>
      </div>
    )
  }

  const { project: apiProject, final_score, evaluation, market, screening, recommendation, action_items } = opportunity
  const threatLevel = getThreatLevel(final_score)

  return (
    <div className="min-h-screen bg-white">
      {/* 顶部导航 */}
      <header className="header-clean">
        <div className="max-w-7xl mx-auto px-6 py-4">
          <div className="flex items-center gap-4">
            <button 
              onClick={() => router.back()}
              className="button-clean flex items-center gap-2"
            >
              <ArrowLeft className="w-4 h-4" />
              返回
            </button>
            <div className="flex-1">
              <h1 className="text-2xl font-bold text-gray-900">{apiProject.name}</h1>
              <p className="text-sm text-gray-600">项目详细分析报告</p>
            </div>
            <div className="flex items-center gap-4">
              <span className={`badge-clean ${threatLevel.color} px-4 py-2`}>
                {threatLevel.label}
              </span>
              <div className="text-right">
                <div className="text-2xl font-bold text-gray-900">{final_score}</div>
                <div className="text-sm text-gray-500">综合评分</div>
              </div>
            </div>
          </div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-6 py-8">
        {/* 项目概览 */}
        <div className={`${threatLevel.bg} ${threatLevel.border} border rounded-lg p-6 mb-8`}>
          <div className="flex items-start justify-between mb-4">
            <div className="flex-1">
              <div className="flex items-center gap-3 mb-2">
                <h2 className="text-xl font-bold text-gray-900">{apiProject.full_name}</h2>
                <a 
                  href={apiProject.html_url} 
                  target="_blank" 
                  rel="noopener noreferrer"
                  className="text-gray-500 hover:text-brand transition-colors"
                >
                  <ExternalLink className="w-5 h-5" />
                </a>
              </div>
              <p className="text-gray-700 mb-4">{apiProject.description}</p>
              
              {/* 项目统计 */}
              <div className="flex items-center gap-6 text-sm text-gray-600">
                <div className="flex items-center gap-1">
                  <Star className="w-4 h-4" />
                  <span>{apiProject.stars_count?.toLocaleString()} Stars</span>
                </div>
                <div className="flex items-center gap-1">
                  <GitFork className="w-4 h-4" />
                  <span>{apiProject.forks_count?.toLocaleString()} Forks</span>
                </div>
                <div className="flex items-center gap-1">
                  <Calendar className="w-4 h-4" />
                  <span>创建于 {getProjectAge(apiProject.created_at)}</span>
                </div>
                {apiProject.language && (
                  <div className="flex items-center gap-1">
                    <Code className="w-4 h-4" />
                    <span>{apiProject.language}</span>
                  </div>
                )}
              </div>
            </div>
          </div>

          {/* 三维评分 */}
          <div className="grid grid-cols-3 gap-6 pt-4 border-t border-gray-200">
            <div className="text-center">
              <div className="text-3xl font-bold text-blue-600 mb-1">
                {evaluation?.business_value?.score || 0}
              </div>
              <div className="text-sm text-gray-600">商业价值</div>
            </div>
            <div className="text-center">
              <div className="text-3xl font-bold text-green-600 mb-1">
                {evaluation?.technical_quality?.score || 0}
              </div>
              <div className="text-sm text-gray-600">技术质量</div>
            </div>
            <div className="text-center">
              <div className="text-3xl font-bold text-purple-600 mb-1">
                {evaluation?.market_potential?.score || 0}
              </div>
              <div className="text-sm text-gray-600">市场潜力</div>
            </div>
          </div>
        </div>

        {/* 详细分析 */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          {/* 左列 */}
          <div className="space-y-8">
            {/* 商业价值分析 */}
            <div className="bg-blue-50 border border-blue-200 rounded-lg p-6">
              <div className="flex items-center gap-2 mb-4">
                <TrendingUp className="w-5 h-5 text-blue-600" />
                <h3 className="text-lg font-semibold text-gray-900">商业价值分析</h3>
              </div>
              <p className="text-gray-700 mb-4">{evaluation?.business_value?.description}</p>
              
              <div className="space-y-2">
                <h4 className="font-medium text-gray-900">核心亮点：</h4>
                <ul className="space-y-1">
                  {evaluation?.business_value?.highlights?.map((highlight, index) => (
                    <li key={index} className="flex items-start gap-2 text-sm text-gray-700">
                      <span className="text-blue-600 mt-1">•</span>
                      {highlight}
                    </li>
                  ))}
                </ul>
              </div>
            </div>

            {/* 技术质量分析 */}
            <div className="bg-green-50 border border-green-200 rounded-lg p-6">
              <div className="flex items-center gap-2 mb-4">
                <Code className="w-5 h-5 text-green-600" />
                <h3 className="text-lg font-semibold text-gray-900">技术质量分析</h3>
              </div>
              <p className="text-gray-700 mb-4">{evaluation?.technical_quality?.description}</p>
              
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <h4 className="font-medium text-gray-900 mb-2">技术优势：</h4>
                  <ul className="space-y-1">
                    {evaluation?.technical_quality?.strengths?.map((strength, index) => (
                      <li key={index} className="flex items-start gap-2 text-sm text-gray-700">
                        <span className="text-green-600 mt-1">✓</span>
                        {strength}
                      </li>
                    ))}
                  </ul>
                </div>
                
                <div>
                  <h4 className="font-medium text-gray-900 mb-2">改进空间：</h4>
                  <ul className="space-y-1">
                    {evaluation?.technical_quality?.weaknesses?.map((weakness, index) => (
                      <li key={index} className="flex items-start gap-2 text-sm text-gray-700">
                        <span className="text-orange-500 mt-1">!</span>
                        {weakness}
                      </li>
                    ))}
                  </ul>
                </div>
              </div>
            </div>
          </div>

          {/* 右列 */}
          <div className="space-y-8">
            {/* 市场潜力分析 */}
            <div className="bg-purple-50 border border-purple-200 rounded-lg p-6">
              <div className="flex items-center gap-2 mb-4">
                <Target className="w-5 h-5 text-purple-600" />
                <h3 className="text-lg font-semibold text-gray-900">市场潜力分析</h3>
              </div>
              <p className="text-gray-700 mb-4">{evaluation?.market_potential?.description}</p>
              
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <h4 className="font-medium text-gray-900 mb-2">市场机会：</h4>
                  <ul className="space-y-1">
                    {evaluation?.market_potential?.opportunities?.map((opportunity, index) => (
                      <li key={index} className="flex items-start gap-2 text-sm text-gray-700">
                        <span className="text-purple-600 mt-1">↗</span>
                        {opportunity}
                      </li>
                    ))}
                  </ul>
                </div>
                
                <div>
                  <h4 className="font-medium text-gray-900 mb-2">潜在风险：</h4>
                  <ul className="space-y-1">
                    {evaluation?.market_potential?.risks?.map((risk, index) => (
                      <li key={index} className="flex items-start gap-2 text-sm text-gray-700">
                        <span className="text-red-500 mt-1">⚠</span>
                        {risk}
                      </li>
                    ))}
                  </ul>
                </div>
              </div>
            </div>

            {/* 竞争分析 */}
            {market?.competitors && market.competitors.length > 0 && (
              <div className="bg-gray-50 border border-gray-200 rounded-lg p-6">
                <div className="flex items-center gap-2 mb-4">
                  <Users className="w-5 h-5 text-gray-600" />
                  <h3 className="text-lg font-semibold text-gray-900">竞争分析</h3>
                </div>
                
                <div className="space-y-4">
                  {market.competitors.map((competitor, index) => (
                    <div key={index} className="bg-white rounded-lg p-4 border border-gray-200">
                      <h4 className="font-medium text-gray-900 mb-1">{competitor.name}</h4>
                      <p className="text-sm text-gray-600 mb-2">{competitor.description}</p>
                      {competitor.market_share && (
                        <p className="text-xs text-gray-500 mb-2">市场份额: {competitor.market_share}</p>
                      )}
                      <div className="flex flex-wrap gap-1">
                        {competitor.strengths.map((strength, i) => (
                          <span key={i} className="badge-clean text-xs">{strength}</span>
                        ))}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        </div>

        {/* 底部推荐和行动计划 */}
        <div className="mt-8 grid grid-cols-1 lg:grid-cols-2 gap-8">
          {/* 推荐建议 */}
          <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-6">
            <div className="flex items-center gap-2 mb-4">
              <Lightbulb className="w-5 h-5 text-yellow-600" />
              <h3 className="text-lg font-semibold text-gray-900">推荐建议</h3>
            </div>
            <p className="text-gray-700">{recommendation}</p>
          </div>

          {/* 行动计划 */}
          <div className="bg-indigo-50 border border-indigo-200 rounded-lg p-6">
            <div className="flex items-center gap-2 mb-4">
              <AlertTriangle className="w-5 h-5 text-indigo-600" />
              <h3 className="text-lg font-semibold text-gray-900">行动计划</h3>
            </div>
            <ul className="space-y-2">
              {action_items?.map((item, index) => (
                <li key={index} className="flex items-start gap-2 text-sm text-gray-700">
                  <span className="text-indigo-600 font-bold mt-1">{index + 1}.</span>
                  {item}
                </li>
              ))}
            </ul>
          </div>
        </div>
      </main>
    </div>
  )
} 