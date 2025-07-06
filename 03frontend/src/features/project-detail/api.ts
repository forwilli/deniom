/**
 * 项目详情功能 API 服务
 */
import { apiClient } from '@/lib/api-client';
import { OpportunityReport } from '@/lib/types';
import { config } from '@/lib/config';
import { mockOpportunities } from '@/lib/mock-data';

const mockApiCall = <T>(data: T, delay = 500): Promise<T> =>
  new Promise(resolve => setTimeout(() => resolve(data), delay));

export const projectDetailApi = {
  async getById(id: string) {
    if (config.useMockData) {
      const opportunity = mockOpportunities.find(op => op.id === id);
      if (!opportunity) throw new Error("Opportunity not found");
      return mockApiCall(opportunity);
    }
    const { data } = await apiClient.get<OpportunityReport>(
      `/projects/${id}`
    );
    return data;
  },
}; 