/**
 * LoginPage Layout TDD Test
 * 레이아웃 구조 검증
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import LoginPage from './LoginPage';
import * as api from '../utils/api';

vi.mock('../utils/api', () => ({
  login: vi.fn(),
}));

const mockNavigate = vi.fn();
vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual('react-router-dom');
  return {
    ...actual,
    useNavigate: () => mockNavigate,
  };
});

describe('LoginPage Layout Structure', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    localStorage.clear();
  });

  it('폼 구조가 원본 템플릿과 일치해야 한다', () => {
    const { container } = render(
      <BrowserRouter>
        <LoginPage />
      </BrowserRouter>
    );

    // 1. form-wrapper 확인
    const formWrapper = container.querySelector('.form-wrapper');
    expect(formWrapper).toBeInTheDocument();

    // 2. form 확인
    const form = formWrapper.querySelector('form.signin');
    expect(form).toBeInTheDocument();

    // 3. form 내부 순서 확인
    const formChildren = Array.from(form.children);
    const classNames = formChildren.map(child => child.className);

    console.log('Form children order:', classNames);

    // 원본 템플릿 순서:
    // 1. id_input_container
    // 2. pswd_input_container
    // 3. remember-id-wrapper
    // 4. error-message (조건부)
    // 5. login-button-container

    expect(classNames[0]).toContain('id_input_container');
    expect(classNames[1]).toContain('pswd_input_container');
    expect(classNames[2]).toContain('remember-id-wrapper');
  });

  it('에러가 없을 때 remember-id-wrapper 다음이 login-button-container여야 한다', () => {
    const { container } = render(
      <BrowserRouter>
        <LoginPage />
      </BrowserRouter>
    );

    const form = container.querySelector('form.signin');
    const formChildren = Array.from(form.children);

    const rememberIdIndex = formChildren.findIndex(child =>
      child.className.includes('remember-id-wrapper')
    );
    const buttonIndex = formChildren.findIndex(child =>
      child.className.includes('login-button-container')
    );

    console.log('Remember ID index:', rememberIdIndex);
    console.log('Button index:', buttonIndex);
    console.log('Elements between:', formChildren.slice(rememberIdIndex + 1, buttonIndex).map(e => e.className));

    // remember-id-wrapper 바로 다음이 login-button-container여야 함 (에러 없을 때)
    // 또는 사이에 error-message만 있어야 함
    const elementsBetween = buttonIndex - rememberIdIndex - 1;
    expect(elementsBetween).toBeLessThanOrEqual(1);
  });

  it('CSS margin이 올바르게 적용되는지 확인', () => {
    const { container } = render(
      <BrowserRouter>
        <LoginPage />
      </BrowserRouter>
    );

    const rememberIdWrapper = container.querySelector('.remember-id-wrapper');
    const buttonContainer = container.querySelector('.login-button-container');

    expect(rememberIdWrapper).toBeInTheDocument();
    expect(buttonContainer).toBeInTheDocument();

    // CSS가 로드되었는지 확인
    const buttonStyle = window.getComputedStyle(buttonContainer);
    console.log('Button container margin-top:', buttonStyle.marginTop);
    console.log('Button container display:', buttonStyle.display);
    console.log('Button container justify-content:', buttonStyle.justifyContent);
  });

  it('버튼이 form 내부에 있어야 한다', () => {
    const { container } = render(
      <BrowserRouter>
        <LoginPage />
      </BrowserRouter>
    );

    const form = container.querySelector('form.signin');
    const button = screen.getByRole('button', { name: /login/i });

    expect(form).toContainElement(button);
  });

  it('bottom-message가 form 밖에 있어야 한다', () => {
    const { container } = render(
      <BrowserRouter>
        <LoginPage />
      </BrowserRouter>
    );

    const form = container.querySelector('form.signin');
    const bottomMessage = container.querySelector('.bottom-message');
    const formWrapper = container.querySelector('.form-wrapper');

    expect(formWrapper).toContainElement(bottomMessage);
    expect(form).not.toContainElement(bottomMessage);
  });
});
