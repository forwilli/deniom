/**
 * 前端模拟数据 (Mock Data)
 * 用于在没有后端连接的情况下进行 UI 开发和测试。
 */

import { OpportunityReport, PaginatedResponse } from "./types";

// 基础的 GitHub 项目模拟数据生成器
const createMockGithubProject = (id: number): OpportunityReport['project'] => ({
  id,
  owner: `owner-${id}`,
  name: `project-fusion-core-${id}`,
  full_name: `owner-${id}/project-fusion-core-${id}`,
  description: `这是一个关于未来科技的融合核心项目，旨在探索量子计算与生物工程的交叉领域，为星际殖民提供可持续能源方案。项目 #${id}`,
  html_url: `https://github.com/owner-${id}/project-fusion-core-${id}`,
  stars_count: Math.floor(Math.random() * 2000) + 50,
  forks_count: Math.floor(Math.random() * 500),
  language: ['TypeScript', 'Rust', 'Python', 'Go'][id % 4],
  created_at: new Date(Date.now() - Math.random() * 30 * 24 * 60 * 60 * 1000).toISOString(),
  updated_at: new Date().toISOString(),
  pushed_at: new Date().toISOString(),
  topics: ['ai', 'cybernetics', 'neuro-interface', 'quantum-computing', 'fusion-energy'],
});

// 完整的商业机会报告模拟数据生成器
export const createMockOpportunity = (id: number): OpportunityReport => {
  const final_score = Math.floor(Math.random() * 50) + 50;
  return {
    id: `opp_${id}`,
    project: createMockGithubProject(id),
    screening: {
      project_id: id,
      has_potential: final_score > 60,
      reason: "该项目因其独特的市场切入点和强大的技术背景被初步筛选通过。",
      score: Math.floor(Math.random() * 40) + 60,
      screened_at: new Date().toISOString(),
    },
    evaluation: {
      project_id: id,
      business_value: {
        score: Math.floor(Math.random() * 20) + 75,
        description: "项目在解决能源危机方面展现出巨大的商业潜力，可能颠覆现有能源市场格局。",
        highlights: [
          "独特的聚变能源方案",
          "潜在的万亿级市场",
          "符合全球可持续发展趋势",
        ],
      },
      technical_quality: {
        score: Math.floor(Math.random() * 20) + 70,
        description: "代码结构清晰，采用了前沿的 Rust 和 AI 模型，但文档相对匮乏。",
        strengths: ["高性能的 Rust 后端", "创新的 AI 算法"],
        weaknesses: ["文档不完善", "需要更多单元测试"],
      },
      market_potential: {
        score: Math.floor(Math.random() * 20) + 80,
        description: "虽然面临来自传统能源巨头的竞争，但其技术突破性强，有望开辟全新赛道。",
        opportunities: ["新能源政策扶持", "技术爱好者的早期采用"],
        risks: ["高昂的研发成本", "技术实现周期长"],
      },
      overall_score: final_score,
      summary: "一个高风险、高回报的颠覆性项目，值得重点关注。",
      evaluated_at: new Date().toISOString(),
    },
    market: {
      project_id: id,
      competitors: [
        { name: "Stark Industries", description: "传统能源与军工巨头", strengths: ["资金雄厚", "市场渠道广"] },
        { name: "Cyberdyne Systems", description: "专注于 AI 与机器人技术", strengths: ["AI技术领先"] },
      ],
      market_trends: ["去中心化能源网络", "AI 驱动的科研加速"],
      opportunity_gaps: ["针对个人消费级的小型能源方案市场空白"],
      positioning_strategy: "建议定位为下一代清洁能源的'特斯拉'，通过技术极客和环保主义者社群进行早期推广。",
      insights_at: new Date().toISOString(),
    },
    final_score,
    recommendation: "强烈推荐，建议立即进行技术验证和原型开发，并寻求天使轮融资。",
    action_items: [
      "组建核心技术团队进行为期3个月的技术攻坚。",
      "撰写商业计划书，接触早期风险投资机构。",
      "发布技术白皮书，吸引社区关注。",
    ],
    created_at: new Date(Date.now() - Math.random() * 14 * 24 * 60 * 60 * 1000).toISOString(),
    updated_at: new Date().toISOString(),
  };
};

// 创建一个包含50个模拟机会的列表
export const mockOpportunities: OpportunityReport[] = Array.from(
  { length: 50 },
  (_, i) => createMockOpportunity(i + 1)
);

// 模拟统计数据
export const mockStats = {
  total_opportunities: 1337,
  today_count: 42,
  average_score: 88.4,
  top_languages: [
    { language: "Rust", count: 15 },
    { language: "Python", count: 12 },
    { language: "TypeScript", count: 10 },
  ],
};

// 模拟分页响应
export const getMockPaginatedResponse = <T>(
  items: T[],
  page: number = 1,
  size: number = 20
): PaginatedResponse<T> => {
  const start = (page - 1) * size;
  const end = start + size;
  const paginatedItems = items.slice(start, end);
  const total = items.length;
  const pages = Math.ceil(total / size);

  return {
    items: paginatedItems,
    total,
    page,
    size,
    pages,
  };
}; 