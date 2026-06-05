type LoginPageProps = {
  onLogin: () => void;
};

export function LoginPage({ onLogin }: LoginPageProps) {
  return (
    <div className="auth-card">
      <h2>로그인</h2>
      <p>프론트 공통 레이아웃 예시 화면입니다. 실제 인증 API 연결은 인증/온보딩 브랜치에서 진행합니다.</p>
      <label>
        이메일
        <input placeholder="user@example.com" type="email" />
      </label>
      <label>
        비밀번호
        <input placeholder="비밀번호" type="password" />
      </label>
      <button className="primary-button" type="button" onClick={onLogin}>
        로그인 후 홈 보기
      </button>
    </div>
  );
}
