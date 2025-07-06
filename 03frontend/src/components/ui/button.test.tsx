import React from 'react';
import { render, screen } from '@testing-library/react';
import { Button } from './button'; // 确保 Button 组件可以从这里导入

describe('Button Component', () => {
  it('应该能被成功渲染并显示正确的文本', () => {
    // 渲染 Button 组件
    render(<Button>Click Me</Button>);
    
    // 使用 screen.getByText 查找包含 "Click Me" 文本的元素
    // getByRole 也是一个很好的选择，可以查找 role="button" 的元素
    const buttonElement = screen.getByText(/click me/i);
    
    // 断言：确认按钮元素存在于文档中
    expect(buttonElement).toBeInTheDocument();
    
    // 断言：确认元素的 role 是 button
    expect(buttonElement).toHaveRole('button');
  });

  it('应该能被正确禁用', () => {
    // 渲染一个被禁用的 Button 组件
    render(<Button disabled>Disabled Button</Button>);
    
    const buttonElement = screen.getByText(/disabled button/i);
    
    // 断言：确认按钮是被禁用的
    expect(buttonElement).toBeDisabled();
  });
}); 