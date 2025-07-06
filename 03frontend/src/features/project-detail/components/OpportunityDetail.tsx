/**
 * 机会详情组件
 * 在弹窗中展示完整的商业机会分析报告
 */

import React from 'react';
import { ExternalLink, Star, GitFork, Calendar, TrendingUp, Shield, Target, AlertTriangle, Zap, Users, Code, Globe } from 'lucide-react';
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '@/components/ui/dialog';
import { Badge } from '@/components/ui/badge';
import { OpportunityReport } from '@/lib/types';
import { formatNumber, formatDateTime, getScoreLevel } from '@/lib/utils';

interface OpportunityDetailProps {
  opportunity: OpportunityReport | null;
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

export function OpportunityDetail({ opportunity, open, onOpenChange }: OpportunityDetailProps) {
  if (!opportunity) return null;

  const { project, screening, evaluation, market, final_score, recommendation, action_items } = opportunity;
  const scoreLevel = getScoreLevel(final_score);

  const getThreatLevelColor = (score: number) => {
    if (score >= 90) return 'text-red-400 border-red-400/30 bg-red-400/10';
    if (score >= 80) return 'text-orange-400 border-orange-400/30 bg-orange-400/10';
    if (score >= 70) return 'text-yellow-400 border-yellow-400/30 bg-yellow-400/10';
    return 'text-green-400 border-green-400/30 bg-green-400/10';
  };

  const getScoreIcon = (score: number) => {
    if (score >= 90) return <Zap className="h-5 w-5" />;
    if (score >= 80) return <Target className="h-5 w-5" />;
    if (score >= 70) return <Shield className="h-5 w-5" />;
    return <TrendingUp className="h-5 w-5" />;
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="glass-card max-w-4xl max-h-[90vh] overflow-y-auto scrollbar-cyber border-white/20">
        <DialogHeader className="border-b border-white/10 pb-6">
          <div className="flex items-start justify-between">
            <div className="flex-1">
              <DialogTitle className="text-2xl font-bold font-mono mb-2 text-foreground">
                <span className="text-primary">{project.owner}</span>
                <span className="text-muted-foreground mx-2">/</span>
                <span>{project.name}</span>
              </DialogTitle>
              <p className="text-muted-foreground text-sm font-mono tracking-wider">
                实体ID: #{opportunity.id.toString().padStart(4, '0')} | 威胁等级分析报告
              </p>
            </div>
            
            <div className={`flex items-center gap-2 px-4 py-2 rounded-lg border font-mono ${getThreatLevelColor(final_score)}`}>
              {getScoreIcon(final_score)}
              <span className="text-lg font-bold">{final_score}</span>
              <span className="text-xs">威胁等级</span>
            </div>
          </div>
        </DialogHeader>

        <div className="space-y-8 pt-6">
          {/* 项目基础信息 */}
          <div className="glass-card p-6 rounded-lg">
            <h3 className="text-lg font-bold font-mono text-primary mb-4 flex items-center gap-2">
              <Globe className="h-5 w-5" />
              实体基础信息
            </h3>
            
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div>
                <p className="text-sm text-muted-foreground mb-4 leading-relaxed">
                  {project.description || '未知实体特征描述'}
                </p>
                
                <div className="flex flex-wrap gap-2 mb-4">
                  {project.topics.map((topic: string) => (
                    <Badge key={topic} variant="outline" className="text-xs font-mono bg-primary/10 border-primary/30 text-primary">
                      {topic}
                    </Badge>
                  ))}
                </div>

                <a
                  href={project.html_url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="cyber-button inline-flex items-center gap-2 px-4 py-2 text-sm font-mono"
                >
                  <ExternalLink className="h-4 w-4" />
                  访问实体源代码
                </a>
              </div>

              <div className="space-y-4">
                <div className="grid grid-cols-2 gap-4">
                  <div className="glass-card p-4 rounded text-center">
                    <div className="flex items-center justify-center gap-2 text-yellow-400 mb-2">
                      <Star className="h-4 w-4" />
                      <span className="text-xl font-bold font-mono">{formatNumber(project.stars_count)}</span>
                    </div>
                    <p className="text-xs text-muted-foreground font-mono">能量值</p>
                  </div>
                  
                  <div className="glass-card p-4 rounded text-center">
                    <div className="flex items-center justify-center gap-2 text-blue-400 mb-2">
                      <GitFork className="h-4 w-4" />
                      <span className="text-xl font-bold font-mono">{formatNumber(project.forks_count)}</span>
                    </div>
                    <p className="text-xs text-muted-foreground font-mono">分叉数</p>
                  </div>
                </div>

                <div className="glass-card p-4 rounded">
                  <div className="flex items-center justify-center gap-2 mb-2">
                    <Code className="h-4 w-4 text-primary" />
                    <span className="font-mono text-primary">{project.language || 'UNKNOWN'}</span>
                  </div>
                  <p className="text-xs text-muted-foreground font-mono text-center">主要协议</p>
                </div>

                <div className="text-xs text-muted-foreground font-mono space-y-1">
                  <div className="flex items-center gap-2">
                    <Calendar className="h-3 w-3" />
                    <span>创建: {new Date(project.created_at).toLocaleDateString()}</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <Calendar className="h-3 w-3" />
                    <span>更新: {new Date(project.updated_at).toLocaleDateString()}</span>
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* 筛选结果 */}
          <section>
            <h3 className="text-lg font-semibold mb-3">初步筛选</h3>
            <div className="bg-muted/50 rounded-lg p-4">
              <div className="flex items-center justify-between mb-2">
                <span className="font-medium">潜力评分：{screening.score}/100</span>
                <Badge variant={screening.has_potential ? 'success' : 'destructive'}>
                  {screening.has_potential ? '通过筛选' : '未通过'}
                </Badge>
              </div>
              <p className="text-sm text-muted-foreground">{screening.reason}</p>
            </div>
          </section>

          {/* 深度评估 */}
          <div className="glass-card p-6 rounded-lg">
            <h3 className="text-lg font-bold font-mono text-primary mb-4 flex items-center gap-2">
              <Target className="h-5 w-5" />
              深度神经网络评估
            </h3>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-6">
              <div className="glass-card p-4 rounded">
                <h4 className="font-mono text-sm text-yellow-400 mb-2">商业价值</h4>
                <div className="text-2xl font-bold font-mono mb-2 neon-glow text-yellow-400">
                  {evaluation.business_value.score}
                </div>
                <p className="text-xs text-muted-foreground">{evaluation.business_value.description}</p>
              </div>

              <div className="glass-card p-4 rounded">
                <h4 className="font-mono text-sm text-blue-400 mb-2">技术质量</h4>
                <div className="text-2xl font-bold font-mono mb-2 neon-glow text-blue-400">
                  {evaluation.technical_quality.score}
                </div>
                <p className="text-xs text-muted-foreground">{evaluation.technical_quality.description}</p>
              </div>

              <div className="glass-card p-4 rounded">
                <h4 className="font-mono text-sm text-green-400 mb-2">市场潜力</h4>
                <div className="text-2xl font-bold font-mono mb-2 neon-glow text-green-400">
                  {evaluation.market_potential.score}
                </div>
                <p className="text-xs text-muted-foreground">{evaluation.market_potential.description}</p>
              </div>
            </div>

            <div className="space-y-4">
              {evaluation.business_value.highlights.length > 0 && (
                <div>
                  <h4 className="font-mono text-sm text-primary mb-2">🔍 商业亮点</h4>
                  <ul className="space-y-1">
                    {evaluation.business_value.highlights.map((highlight: string, index: number) => (
                      <li key={index} className="text-sm text-muted-foreground flex items-start gap-2">
                        <span className="text-primary mt-0.5">•</span>
                        <span>{highlight}</span>
                      </li>
                    ))}
                  </ul>
                </div>
              )}

              {evaluation.technical_quality.strengths.length > 0 && (
                <div>
                  <h4 className="font-mono text-sm text-primary mb-2">⚡ 技术优势</h4>
                  <ul className="space-y-1">
                    {evaluation.technical_quality.strengths.map((strength: string, index: number) => (
                      <li key={index} className="text-sm text-muted-foreground flex items-start gap-2">
                        <span className="text-green-400 mt-0.5">+</span>
                        <span>{strength}</span>
                      </li>
                    ))}
                  </ul>
                </div>
              )}

              {evaluation.technical_quality.weaknesses.length > 0 && (
                <div>
                  <h4 className="font-mono text-sm text-primary mb-2">⚠️ 技术风险</h4>
                  <ul className="space-y-1">
                    {evaluation.technical_quality.weaknesses.map((weakness: string, index: number) => (
                      <li key={index} className="text-sm text-muted-foreground flex items-start gap-2">
                        <span className="text-orange-400 mt-0.5">-</span>
                        <span>{weakness}</span>
                      </li>
                    ))}
                  </ul>
                </div>
              )}
            </div>

            <div className="border-t border-white/10 pt-4 mt-6">
              <h4 className="font-mono text-sm text-primary mb-2">📊 综合评估</h4>
              <p className="text-sm text-foreground leading-relaxed">{evaluation.summary}</p>
            </div>
          </div>

          {/* 市场洞察 */}
          {market && (
            <div className="glass-card p-6 rounded-lg">
              <h3 className="text-lg font-bold font-mono text-primary mb-4 flex items-center gap-2">
                <Users className="h-5 w-5" />
                宇宙生态分析
              </h3>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                {market.competitors.length > 0 && (
                  <div>
                    <h4 className="font-mono text-sm text-primary mb-3">🎯 竞争实体</h4>
                    <div className="space-y-3">
                      {market.competitors.slice(0, 3).map((competitor, index: number) => (
                        <div key={index} className="glass-card p-3 rounded">
                          <h5 className="font-mono text-sm font-bold text-foreground mb-1">{competitor.name}</h5>
                          <p className="text-xs text-muted-foreground mb-2">{competitor.description}</p>
                          {competitor.market_share && (
                            <Badge variant="outline" className="text-xs">
                              市场份额: {competitor.market_share}
                            </Badge>
                          )}
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                <div className="space-y-4">
                  {market.market_trends.length > 0 && (
                    <div>
                      <h4 className="font-mono text-sm text-primary mb-2">📈 市场趋势</h4>
                      <ul className="space-y-1">
                        {market.market_trends.map((trend: string, index: number) => (
                          <li key={index} className="text-sm text-muted-foreground flex items-start gap-2">
                            <span className="text-primary mt-0.5">→</span>
                            <span>{trend}</span>
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}

                  {market.opportunity_gaps.length > 0 && (
                    <div>
                      <h4 className="font-mono text-sm text-primary mb-2">🚀 机会缺口</h4>
                      <ul className="space-y-1">
                        {market.opportunity_gaps.map((gap: string, index: number) => (
                          <li key={index} className="text-sm text-muted-foreground flex items-start gap-2">
                            <span className="text-green-400 mt-0.5">◆</span>
                            <span>{gap}</span>
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}
                </div>
              </div>

              {market.positioning_strategy && (
                <div className="border-t border-white/10 pt-4 mt-6">
                  <h4 className="font-mono text-sm text-primary mb-2">🎯 定位策略</h4>
                  <p className="text-sm text-foreground leading-relaxed">{market.positioning_strategy}</p>
                </div>
              )}
            </div>
          )}

          {/* 综合建议 */}
          <div className="glass-card p-6 rounded-lg">
            <h3 className="text-lg font-bold font-mono text-primary mb-4 flex items-center gap-2">
              <Zap className="h-5 w-5" />
              行动指令
            </h3>

            <div className="space-y-4">
              <div>
                <h4 className="font-mono text-sm text-primary mb-2">🎯 推荐策略</h4>
                <p className="text-sm text-foreground leading-relaxed bg-primary/5 p-3 rounded border border-primary/20">
                  {recommendation}
                </p>
              </div>

              {action_items.length > 0 && (
                <div>
                  <h4 className="font-mono text-sm text-primary mb-2">⚡ 执行清单</h4>
                  <ul className="space-y-2">
                    {action_items.map((item: string, index: number) => (
                      <li key={index} className="text-sm text-foreground flex items-start gap-2 p-2 glass-card rounded">
                        <span className="text-primary font-mono text-xs mt-0.5">[{(index + 1).toString().padStart(2, '0')}]</span>
                        <span>{item}</span>
                      </li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          </div>
        </div>
      </DialogContent>
    </Dialog>
  );
} 