'use client';

import { useState } from 'react';
import { Search, Filter } from 'lucide-react';
import { useRouter } from 'next/navigation';

// 功能切片导入
import { useProjectList } from '@/features/project-list/useProjectList';
import { OpportunityCard } from '@/features/project-list/components/OpportunityCard';
import { SortControls } from '@/features/project-list/components/SortControls';
import { OpportunityReport } from '@/lib/types';

// UI组件
import { Input } from '@/components/ui/input';

export default function HomePage() {
  const router = useRouter();
  
  // All logic is now encapsulated in the useProjectList hook
  const {
    searchQuery,
    setSearchQuery,
    leftColumn,
    rightColumn,
    isLoading,
    error,
    totalCount,
    averageScore
  } = useProjectList();

  const handleProjectClick = (opportunity: OpportunityReport) => {
    router.push(`/project/${opportunity.id}`);
  };

  if (error) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50">
        <div className="text-center max-w-md">
          <div className="text-red-600 text-lg font-semibold mb-2">连接失败</div>
          <div className="text-gray-600 text-sm">无法连接到服务器，请稍后重试</div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-white">
      {/* 顶部导航栏 */}
      <header className="header-clean sticky top-0 z-40">
        <div className="max-w-7xl mx-auto px-6 py-4">
          <div className="flex items-center justify-between">
            {/* Logo 和标题 */}
            <div className="flex items-center gap-4">
              <div className="w-10 h-10 bg-brand rounded-lg flex items-center justify-center">
                <span className="text-white font-bold text-lg">D</span>
              </div>
              <div>
                <h1 className="text-2xl font-bold text-gray-900">
                  Deniom
                </h1>
                <p className="text-sm text-gray-600">
                  发现最有潜力的开源项目
                </p>
              </div>
            </div>

            {/* 右侧操作 */}
            <div className="flex items-center gap-4">
              <div className="text-sm text-gray-500">
                今日发现
              </div>
              <div className="text-2xl font-bold text-brand">
                {totalCount}
              </div>
            </div>
          </div>

          {/* 搜索和筛选 */}
          <div className="mt-6 flex items-center gap-4">
            <div className="relative flex-1 max-w-2xl">
              <Search className="absolute left-4 top-1/2 transform -translate-y-1/2 text-gray-400 w-5 h-5" />
              <input
                type="text"
                placeholder="搜索项目名称或描述..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="input-clean w-full pl-12 pr-4 py-3 text-gray-900 placeholder-gray-500"
              />
            </div>
            <button className="button-clean flex items-center gap-2">
              <Filter className="w-4 h-4" />
              筛选
            </button>
          </div>
        </div>
      </header>

      {/* 统计面板 */}
        <div className="max-w-7xl mx-auto px-6">
          <div className="stats-clean py-6">
            <div className="grid grid-cols-2 md:grid-cols-4 gap-6">
              <div className="text-center">
                <div className="text-3xl font-bold text-gray-900 mb-1">
                {totalCount}
                </div>
                <div className="text-sm text-gray-600">总项目数</div>
              </div>
              <div className="text-center">
                <div className="text-3xl font-bold text-blue-600 mb-1">
                {leftColumn.items.length}
                </div>
                <div className="text-sm text-gray-600">高分项目</div>
              </div>
              <div className="text-center">
                <div className="text-3xl font-bold text-green-600 mb-1">
                {rightColumn.items.length}
                </div>
                <div className="text-sm text-gray-600">热门项目</div>
              </div>
              <div className="text-center">
                <div className="text-3xl font-bold text-purple-600 mb-1">
                {averageScore}
                </div>
                <div className="text-sm text-gray-600">平均分值</div>
              </div>
            </div>
          </div>
        </div>

      {/* 主内容区域 - 无缝双列布局 */}
      <main className="max-w-7xl mx-auto">
        {isLoading ? (
          <div className="flex items-center justify-center py-20">
            <div className="text-center">
              <div className="text-gray-900 text-lg font-semibold mb-2">加载中...</div>
              <div className="text-gray-600 text-sm">正在获取最新数据</div>
            </div>
          </div>
        ) : (
          <div className="seamless-grid">
            {/* 左列 */}
            <div className="left-column">
              <SortControls 
                sort={leftColumn.sort}
                onSortChange={leftColumn.setSort}
                title="🏆 高评分项目"
                itemCount={leftColumn.items.length}
              />
              
              <div className="column-content-area">
                <div className="scrollbar-clean overflow-y-auto">
                  {leftColumn.items.map((opportunity, index) => (
                    <OpportunityCard
                      key={`left-${opportunity.id}`}
                      opportunity={opportunity}
                      rank={index + 1}
                      onClick={() => handleProjectClick(opportunity)}
                    />
                  ))}
                  {leftColumn.items.length === 0 && (
                    <div className="text-center py-12 text-gray-500">
                      暂无数据
                    </div>
                  )}
                </div>
              </div>
            </div>

            {/* 右列 */}
            <div className="right-column">
              <SortControls 
                sort={rightColumn.sort}
                onSortChange={rightColumn.setSort}
                title="⭐ 热门项目"
                itemCount={rightColumn.items.length}
              />
              
              <div className="column-content-area">
                <div className="scrollbar-clean overflow-y-auto">
                  {rightColumn.items.map((opportunity, index) => (
                    <OpportunityCard
                      key={`right-${opportunity.id}`}
                      opportunity={opportunity}
                      rank={leftColumn.items.length + index + 1}
                      onClick={() => handleProjectClick(opportunity)}
                    />
                  ))}
                  {rightColumn.items.length === 0 && (
                    <div className="text-center py-12 text-gray-500">
                      暂无数据
                    </div>
                  )}
                </div>
              </div>
            </div>
          </div>
        )}
      </main>
    </div>
  );
}
