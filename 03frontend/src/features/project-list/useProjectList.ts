/**
 * 机会数据相关的 React Query hooks
 */

import { useQuery, useInfiniteQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { opportunitiesApi } from '@/lib/api/opportunities';
import { config } from '@/lib/config';
import { useState, useMemo } from 'react';
import { projectListApi } from './api';
import { OpportunityReport } from '@/lib/types';

/**
 * 获取机会列表（分页）
 */
export function useOpportunities(params: {
  page?: number;
  size?: number;
  sort?: 'score' | 'date';
  order?: 'asc' | 'desc';
} = {}) {
  return useQuery({
    queryKey: ['opportunities', params],
    queryFn: () => opportunitiesApi.getList(params),
    staleTime: config.dataRefreshInterval,
  });
}

/**
 * 获取机会列表（无限滚动）
 */
export function useInfiniteOpportunities(params: {
  size?: number;
  sort?: 'score' | 'date';
  order?: 'asc' | 'desc';
} = {}) {
  return useInfiniteQuery({
    queryKey: ['opportunities', 'infinite', params],
    queryFn: ({ pageParam }) => 
      opportunitiesApi.getList({ ...params, page: pageParam }),
    initialPageParam: 1,
    getNextPageParam: (lastPage) => {
      if (lastPage.page < lastPage.pages) {
        return lastPage.page + 1;
      }
      return undefined;
    },
    staleTime: config.dataRefreshInterval,
  });
}

/**
 * 获取单个机会详情
 */
export function useOpportunity(id: string) {
  return useQuery({
    queryKey: ['opportunity', id],
    queryFn: () => opportunitiesApi.getById(id),
    enabled: !!id,
    staleTime: config.dataRefreshInterval,
  });
}

/**
 * 搜索机会
 */
export function useSearchOpportunities(query: string, params: {
  page?: number;
  size?: number;
} = {}) {
  return useQuery({
    queryKey: ['opportunities', 'search', query, params],
    queryFn: () => opportunitiesApi.search(query, params),
    enabled: !!query,
    staleTime: config.dataRefreshInterval,
  });
}

/**
 * 获取今日最佳机会
 */
export function useTodaysBest() {
  return useQuery({
    queryKey: ['opportunities', 'today-best'],
    queryFn: () => opportunitiesApi.getTodaysBest(),
    staleTime: config.dataRefreshInterval,
  });
}

/**
 * 获取统计数据
 */
export function useOpportunityStats() {
  return useQuery({
    queryKey: ['opportunities', 'stats'],
    queryFn: () => opportunitiesApi.getStats(),
    staleTime: config.dataRefreshInterval,
  });
}

/**
 * 触发分析任务
 */
export function useTriggerAnalysis() {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: () => opportunitiesApi.triggerAnalysis(),
    onSuccess: () => {
      // 触发成功后，使相关查询失效以刷新数据
      queryClient.invalidateQueries({ queryKey: ['opportunities'] });
      queryClient.invalidateQueries({ queryKey: ['tasks'] });
    },
  });
}

/**
 * 获取任务状态
 */
export function useTaskStatus(taskId: string | null) {
  return useQuery({
    queryKey: ['task', taskId],
    queryFn: () => opportunitiesApi.getTaskStatus(taskId!),
    enabled: !!taskId,
    refetchInterval: ({ state }) => {
      // 如果任务还在进行中，每2秒刷新一次
      if (state.data?.status === 'pending' || state.data?.status === 'processing') {
        return 2000;
      }
      return false;
    },
  });
}

// 定义排序选项，这将在我们的hook内部和外部使用
type SortOption = 'score' | 'stars' | 'created' | 'name';
type SortDirection = 'asc' | 'desc';

export interface ColumnSort {
  field: SortOption;
  direction: SortDirection;
}

/**
 * 这是一个全功能的Hook，为项目列表页面提供所有需要的数据和逻辑。
 * 它封装了数据获取、搜索、排序和数据分割的所有复杂性。
 */
export function useProjectList() {
  const [searchQuery, setSearchQuery] = useState('');
  const [leftColumnSort, setLeftColumnSort] = useState<ColumnSort>({ field: 'score', direction: 'desc' });
  const [rightColumnSort, setRightColumnSort] = useState<ColumnSort>({ field: 'stars', direction: 'desc' });

  // 1. 使用 React Query 从API获取基础数据
  const { data: rawData, isLoading, error } = useQuery({
    queryKey: ['opportunities', 'list-all'], // 使用一个固定的key来获取所有项目
    queryFn: () => projectListApi.getList({ size: 200 }), // 获取一个较大的数据集
    staleTime: config.dataRefreshInterval,
  });

  // 2. 过滤数据
  const filteredData = useMemo(() => {
    if (!rawData?.items) return [];
    
    return rawData.items.filter(opportunity =>
      searchQuery === '' ||
      opportunity.project.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      (opportunity.project.description && opportunity.project.description.toLowerCase().includes(searchQuery.toLowerCase()))
    );
  }, [rawData?.items, searchQuery]);

  // 3. 排序函数
  const sortData = (data: OpportunityReport[], sort: ColumnSort): OpportunityReport[] => {
    return [...data].sort((a, b) => {
      let aValue: any, bValue: any;
      
      switch (sort.field) {
        case 'score':
          aValue = a.final_score;
          bValue = b.final_score;
          break;
        case 'stars':
          aValue = a.project.stars_count;
          bValue = b.project.stars_count;
          break;
        case 'created':
          aValue = new Date(a.project.created_at).getTime();
          bValue = new Date(b.project.created_at).getTime();
          break;
        case 'name':
          aValue = a.project.name.toLowerCase();
          bValue = a.project.name.toLowerCase();
          break;
        default:
          return 0;
      }

      if (aValue < bValue) return sort.direction === 'asc' ? -1 : 1;
      if (aValue > bValue) return sort.direction === 'asc' ? 1 : -1;
      return 0;
    });
  };

  // 4. 分割和排序数据到两列
  const { leftColumnData, rightColumnData } = useMemo(() => {
    if (filteredData.length === 0) return { leftColumnData: [], rightColumnData: [] };
    
    const midpoint = Math.ceil(filteredData.length / 2);
    
    const leftData = sortData(filteredData.slice(0, midpoint), leftColumnSort);
    const rightData = sortData(filteredData.slice(midpoint), rightColumnSort);
    
    return { leftColumnData: leftData, rightColumnData: rightData };
  }, [filteredData, leftColumnSort, rightColumnSort]);

  // 5. 计算统计数据
  const totalCount = rawData?.total ?? 0;
  const averageScore = useMemo(() => {
    if (!rawData?.items || rawData.items.length === 0) return 0;
    const totalScore = rawData.items.reduce((sum, op) => sum + op.final_score, 0);
    return Math.round(totalScore / rawData.items.length);
  }, [rawData?.items]);

  // 6. 返回页面所需的所有内容
  return {
    searchQuery,
    setSearchQuery,
    leftColumn: {
      items: leftColumnData,
      sort: leftColumnSort,
      setSort: setLeftColumnSort,
    },
    rightColumn: {
      items: rightColumnData,
      sort: rightColumnSort,
      setSort: setRightColumnSort,
    },
    isLoading,
    error,
    totalCount,
    averageScore,
  };
} 