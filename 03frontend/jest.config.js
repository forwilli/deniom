module.exports = {
  // 使用 ts-jest 预设，让 Jest 能够理解 TypeScript
  preset: 'ts-jest',
  
  // 指定测试环境为 JSDOM，模拟浏览器环境
  testEnvironment: 'jest-environment-jsdom',
  
  // 在每个测试文件运行前执行的设置文件
  setupFilesAfterEnv: ['<rootDir>/jest.setup.js'],
  
  // 模块名称映射，用于处理 CSS、图片等非 JS 文件
  // 以及正确解析路径别名
  moduleNameMapper: {
    // 处理 CSS Modules
    '\\.css$': 'identity-obj-proxy',
    
    // 将路径别名 @/* 指向 src/*
    '^@/(.*)$': '<rootDir>/src/$1',
  },
  
  // 忽略 node_modules 和 .next 目录中的文件
  testPathIgnorePatterns: ['<rootDir>/node_modules/', '<rootDir>/.next/'],
  
  // 转换器配置，告诉 Jest 如何处理 .ts 和 .tsx 文件
  transform: {
    '^.+\\.(ts|tsx)$': ['ts-jest', {
      tsconfig: 'tsconfig.json',
    }],
  },
}; 