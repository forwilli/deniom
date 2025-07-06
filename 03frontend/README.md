# Deniom Web Frontend

🚀 **现代化的商业机会发现平台前端**

基于 Next.js 14 构建的现代化 Web 应用，采用清爽的白色背景设计风格，类似 Product Hunt 的用户体验。

## ✨ 设计特色

### 🎨 视觉设计
- **现代白色背景** - 清爽简洁的设计语言
- **玻璃拟物化** - 半透明卡片与微妙阴影
- **Product Hunt 风格** - 熟悉的产品展示界面
- **双列响应式布局** - 桌面端双列，移动端自适应

### 🏆 核心功能
- **智能排序** - 每列独立按评分、Stars、时间、名称排序
- **实时搜索** - 项目名称和描述的即时过滤
- **统计面板** - 项目总数、分类统计、平均分值展示
- **详情弹窗** - 完整的项目分析报告查看

### 🎯 交互体验
- **悬停效果** - 卡片轻微上浮与边框变化
- **品牌色彩** - 橙红色主题色 (#ff6154)
- **现代化按钮** - 清晰的状态反馈
- **优雅滚动** - 自定义滚动条样式

## 🛠 技术栈

- **Next.js 14** - App Router + TypeScript
- **Tailwind CSS 3.4** - 原子化CSS框架
- **React Query** - 数据获取与缓存
- **Lucide React** - 现代化图标库
- **Radix UI** - 无障碍组件基础

## 🚀 快速开始

```bash
# 安装依赖
npm install

# 启动开发服务器
npm run dev

# 构建生产版本
npm run build
```

## 📱 界面预览

### 主页面
- 🏠 **顶部导航栏** - Logo、标题、搜索框、筛选按钮
- 📊 **统计面板** - 总项目数、高分项目、热门项目、平均分值
- 📋 **双列布局** - 高评分项目 vs 热门项目

### 项目卡片
- 🏷️ **排名标识** - 左上角数字排名
- ⭐ **项目信息** - 名称、描述、Stars、Forks、创建时间
- 🎯 **威胁等级** - CRITICAL/HIGH/MEDIUM/LOW 标签
- 📈 **三维评分** - 商业、技术、市场分值展示
- 🏷️ **标签系统** - 编程语言、NEW标签、ID编码

## 🎨 设计系统

### 颜色方案
```css
/* 主要颜色 */
--brand: #ff6154;           /* 品牌橙红色 */
--background: #ffffff;      /* 纯白背景 */
--foreground: #111827;      /* 深灰文字 */
--muted: #f9fafb;          /* 浅灰背景 */
--border: #e5e7eb;         /* 边框颜色 */

/* 功能颜色 */
--success: #10b981;        /* 成功绿色 */
--warning: #f59e0b;        /* 警告橙色 */
--danger: #ef4444;         /* 危险红色 */
--info: #3b82f6;          /* 信息蓝色 */
```

### 组件样式
- **card-modern** - 现代化卡片样式
- **button-modern** - 现代化按钮样式
- **input-modern** - 现代化输入框样式
- **badge-modern** - 现代化徽章样式

## 📂 项目结构

```
denoim-web/
├── app/                    # Next.js App Router
│   ├── globals.css        # 全局样式
│   ├── layout.tsx         # 根布局
│   ├── page.tsx           # 主页面
│   └── providers.tsx      # React Query Provider
├── components/            # React 组件
│   ├── ui/               # 基础 UI 组件
│   ├── opportunity-card.tsx    # 项目卡片
│   └── opportunity-detail.tsx  # 项目详情
├── lib/                  # 工具库
│   ├── api/             # API 客户端
│   ├── hooks/           # React Hooks
│   ├── types/           # TypeScript 类型
│   ├── config.ts        # 配置文件
│   ├── mock-data.ts     # 模拟数据
│   └── utils.ts         # 工具函数
└── public/              # 静态资源
```

## 🔧 配置说明

### 模拟数据模式
在 `lib/config.ts` 中设置 `useMockData: true` 可启用模拟数据模式，无需后端即可查看完整界面效果。

### API 端点
后端 API 地址配置在 `lib/config.ts` 中的 `API_BASE_URL`。

## 🌟 特色功能

### 双列排序系统
- 左列：高评分项目（按综合评分排序）
- 右列：热门项目（按 Stars 数排序）
- 每列支持独立的排序方式切换

### 威胁等级系统
根据项目综合评分自动分配威胁等级：
- **CRITICAL** (85+) - 红色标签
- **HIGH** (70-84) - 橙色标签  
- **MEDIUM** (50-69) - 蓝色标签
- **LOW** (<50) - 灰色标签

### 响应式设计
- 桌面端：双列布局
- 平板端：双列布局（稍窄）
- 移动端：单列布局

---

🎯 **目标：打造最优雅的商业机会发现平台界面**
