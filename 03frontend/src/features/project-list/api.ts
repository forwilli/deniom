/**
 * 项目列表功能 API 服务
 */
import { apiClient } from '@/lib/api-client';
import { OpportunityReport, PaginatedResponse } from '@/lib/types';
import { config } from '@/lib/config';
import { mockOpportunities, getMockPaginatedResponse } from '@/lib/mock-data';

const mockApiCall = <T>(data: T, delay = 500): Promise<T> =>
  new Promise(resolve => setTimeout(() => resolve(data), delay));

export const projectListApi = {
  async getList(params: {
    page?: number;
    size?: number;
    sort?: 'score' | 'date';
    order?: 'asc' | 'desc';
  } = {}) {
    if (config.useMockData) {
      const sorted = [...mockOpportunities].sort((a, b) => {
        if (params.sort === 'score') {
          return params.order === 'desc' ? b.final_score - a.final_score : a.final_score - b.final_score;
        }
        return params.order === 'desc' 
          ? new Date(b.created_at).getTime() - new Date(a.created_at).getTime()
          : new Date(a.created_at).getTime() - new Date(b.created_at).getTime();
      });
      const data = getMockPaginatedResponse(sorted, params.page, params.size);
      return mockApiCall(data);
    }
    const { data } = await apiClient.get<PaginatedResponse<OpportunityReport>>(
      '/projects', { params }
    );
    return data;
  },

  async search(query: string, params: {
    page?: number;
    size?: number;
  } = {}) {
    if (config.useMockData) {
      const filtered = mockOpportunities.filter(
        opp => opp.project.name.includes(query) || opp.project.description?.includes(query)
      );
      const data = getMockPaginatedResponse(filtered, params.page, params.size);
      return mockApiCall(data);
    }
    const { data } = await apiClient.get<PaginatedResponse<OpportunityReport>>(
      '/projects/search', { params: { q: query, ...params } }
    );
    return data;
  },
}; 