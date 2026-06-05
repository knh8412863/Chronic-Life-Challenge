import { useState } from "react";
import type { AppRoute } from "../App";
import logoUrl from "../assets/all4health-logo.png";

interface LoginPageProps {
  onLogin: () => void;
  onNavigate?: (route: AppRoute) => void;
}

export function LoginPage({ onLogin, onNavigate }: LoginPageProps) {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [errorCount, setErrorCount] = useState(0); // 0: 기본, 3: 3회남음, 1: 1회남음, -1: 잠금
  const [isLoading, setIsLoading] = useState(false);

  const handleLogin = async () => {
    setIsLoading(true);
    // TODO: API 연결 — POST /api/v1/auth/sessions
    // body: { email, password, remember_me: false }
    // 응답: 200 { data: { access_token, token_type, expires_in: 900 } }
    // Access Token은 sessionStorage에 저장 (localStorage 저장 금지, NFR-SEC-001)
    // 실패 시: 401 INVALID_CREDENTIALS → detail.remaining_attempts로 남은 횟수 표시
    // 5회 초과 시: 429 RATE_LIMIT_EXCEEDED → 잠금 화면 표시
    setTimeout(() => {
      setIsLoading(false);
      onLogin();
    }, 500);
  };

  const BrandPanel = () => (
    <div style={{
      width: "45%", background: "#f5f5f5", padding: "48px 40px",
      display: "flex", flexDirection: "column", justifyContent: "center",
      borderRight: "1px solid #e0e0e0"
    }}>
      <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 24 }}>
        <img src={logoUrl} alt="All4Health" style={{ height: 28, width: "auto" }} />
        <span style={{ fontSize: 16, fontWeight: 700, color: "#1a1a1a" }}>All4Health</span>
      </div>
      <h2 style={{ fontSize: 20, fontWeight: 600, color: "#1a1a1a", lineHeight: 1.35, margin: "0 0 12px" }}>
        건강한 내일을<br />지금 시작하세요
      </h2>
      <p style={{ fontSize: 12, color: "#555", lineHeight: 1.6, margin: "0 0 24px" }}>
        AI 기반 만성질환 관리와 생활습관 챌린지로<br />더 건강한 삶을 만들어 드립니다.
      </p>
      <hr style={{ border: "none", borderTop: "1px solid #ddd", margin: "0 0 20px" }} />
      <div style={{ display: "flex", flexDirection: "column", gap: 16 }}>
        {[
          { title: "AI 기반 질환 위험 예측", desc: "혈압·혈당 데이터로 위험도를 분석합니다" },
          { title: "매일 달성하는 건강 챌린지", desc: "작은 습관이 큰 변화를 만듭니다" },
          { title: "개인 맞춤 건강 가이드", desc: "나에게 맞는 식단·운동 조언을 제공합니다" }
        ].map((item, i) => (
          <div key={i} style={{ display: "flex", gap: 12, alignItems: "flex-start" }}>
            <div style={{ width: 28, height: 28, background: "#e0e0e0", borderRadius: 5, flexShrink: 0 }} />
            <div>
              <div style={{ fontSize: 11, fontWeight: 500, color: "#1a1a1a", marginBottom: 3 }}>{item.title}</div>
              <div style={{ fontSize: 10, color: "#888", lineHeight: 1.5 }}>{item.desc}</div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );

  // 계정 잠금 상태
  if (errorCount === -1) {
    return (
      <div style={{ display: "flex", height: "100vh" }}>
        <BrandPanel />
        <div style={{ flex: 1, padding: "48px 40px", display: "flex", flexDirection: "column", justifyContent: "center", background: "#fff", overflowY: "auto" }}>
          <div style={{ fontSize: 11, fontWeight: 500, color: "#888", letterSpacing: 0.5, textTransform: "uppercase", marginBottom: 6 }}>로그인</div>
          <hr style={{ border: "none", borderTop: "1px solid #e0e0e0", margin: "16px 0" }} />
          <div style={{ display: "flex", flexDirection: "column", gap: 14 }}>
            <div>
              <label style={{ fontSize: 10, color: "#555", display: "block", marginBottom: 4 }}>이메일</label>
              <input disabled value={email} style={{ width: "100%", height: 34, border: "0.5px solid #e0e0e0", borderRadius: 5, padding: "0 10px", fontSize: 11, opacity: 0.6, background: "#fafafa", boxSizing: "border-box" }} />
            </div>
            <div>
              <label style={{ fontSize: 10, color: "#555", display: "block", marginBottom: 4 }}>비밀번호</label>
              <input disabled type="password" style={{ width: "100%", height: 34, border: "0.5px solid #e0e0e0", borderRadius: 5, padding: "0 10px", fontSize: 11, opacity: 0.6, background: "#fafafa", boxSizing: "border-box" }} />
            </div>
            <div style={{ background: "#fff8f7", border: "0.5px solid #f5b7b1", borderRadius: 12, padding: "16px 18px" }}>
              <div style={{ display: "flex", alignItems: "flex-start", gap: 10, marginBottom: 12 }}>
                <span style={{ fontSize: 18, color: "#e87b72" }}>⏱</span>
                <div>
                  <div style={{ fontSize: 14, fontWeight: 500, color: "#c0392b" }}>로그인 요청이 잠시 제한되었습니다</div>
                  <div style={{ fontSize: 12, color: "#c0392b", marginTop: 4, lineHeight: 1.6 }}>짧은 시간 내 로그인 시도가 반복되었습니다. 잠시 후 다시 시도해주세요.</div>
                </div>
              </div>
              <button onClick={() => onNavigate?.("/password-reset")} style={{ width: "100%", height: 34, border: "0.5px solid #e87b72", borderRadius: 8, background: "#fff", color: "#c0392b", fontSize: 11, cursor: "pointer", marginBottom: 8 }}>비밀번호 재설정</button>
            </div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div style={{ display: "flex", height: "100vh" }}>
      <BrandPanel />
      <div style={{ flex: 1, padding: "48px 40px", display: "flex", flexDirection: "column", justifyContent: "center", background: "#fff", overflowY: "auto" }}>
        <div style={{ fontSize: 11, fontWeight: 500, color: "#888", letterSpacing: 0.5, textTransform: "uppercase", marginBottom: 6 }}>로그인</div>
        <div style={{ fontSize: 12, color: "#555", marginBottom: 20 }}>계정에 로그인하여 건강 관리를 시작하세요</div>
        <hr style={{ border: "none", borderTop: "1px solid #e0e0e0", margin: "0 0 16px" }} />

        <div style={{ display: "flex", flexDirection: "column", gap: 14 }}>
          <div>
            <label style={{ fontSize: 10, color: "#555", display: "block", marginBottom: 4 }}>이메일</label>
            <input
              type="email" value={email} onChange={e => setEmail(e.target.value)}
              placeholder="example@email.com"
              style={{ width: "100%", height: 34, border: `1.5px solid ${errorCount > 0 ? "#E24B4A" : "#ddd"}`, borderRadius: 5, padding: "0 10px", fontSize: 11, boxSizing: "border-box", outline: "none" }}
            />
          </div>
          <div>
            <label style={{ fontSize: 10, color: "#555", display: "block", marginBottom: 4 }}>비밀번호</label>
            <div style={{ position: "relative" }}>
              <input
                type={showPassword ? "text" : "password"} value={password} onChange={e => setPassword(e.target.value)}
                placeholder="비밀번호 입력"
                style={{ width: "100%", height: 34, border: `1.5px solid ${errorCount > 0 ? "#E24B4A" : "#ddd"}`, borderRadius: 5, padding: "0 36px 0 10px", fontSize: 11, boxSizing: "border-box", outline: "none" }}
              />
              <button onClick={() => setShowPassword(!showPassword)}
                style={{ position: "absolute", right: 10, top: "50%", transform: "translateY(-50%)", background: "none", border: "none", cursor: "pointer", fontSize: 12, color: "#888" }}>
                {showPassword ? "🙈" : "👁"}
              </button>
            </div>
            {errorCount === 3 && <p style={{ fontSize: 12, color: "#E24B4A", margin: "4px 0 0" }}>이메일 또는 비밀번호가 올바르지 않습니다. (3회 시도 남음)</p>}
          </div>

          {errorCount === 1 && (
            <div style={{ background: "#FFF8E1", border: "1.5px solid #F39C12", borderRadius: 6, padding: "12px 14px" }}>
              <div style={{ display: "flex", alignItems: "flex-start", gap: 10 }}>
                <div style={{ width: 18, height: 18, borderRadius: "50%", background: "#F39C12", color: "#fff", display: "flex", alignItems: "center", justifyContent: "center", fontSize: 11, flexShrink: 0 }}>!</div>
                <div>
                  <div style={{ fontSize: 12, fontWeight: 600, color: "#D68910", marginBottom: 4 }}>계정 잠금까지 1회 남았습니다</div>
                  <div style={{ fontSize: 11, color: "#856404", lineHeight: 1.5 }}>한 번 더 실패하면 계정이 일시적으로 잠깁니다.</div>
                </div>
              </div>
            </div>
          )}

          <button
            onClick={handleLogin} disabled={isLoading || !email || !password}
            style={{ width: "100%", height: 36, background: isLoading || !email || !password ? "#ccc" : "#1a1a1a", color: "#fff", border: "none", borderRadius: 8, fontSize: 13, fontWeight: 600, cursor: isLoading || !email || !password ? "not-allowed" : "pointer" }}>
            {isLoading ? "로그인 중..." : "로그인"}
          </button>
        </div>

        <div style={{ display: "flex", justifyContent: "space-between", marginTop: 16 }}>
          <button onClick={() => onNavigate?.("/password-reset")} style={{ background: "none", border: "none", fontSize: 11, color: "#888", cursor: "pointer" }}>비밀번호를 잊으셨나요?</button>
          <button onClick={() => onNavigate?.("/signup")} style={{ background: "none", border: "none", fontSize: 11, color: "#888", cursor: "pointer" }}>회원가입</button>
        </div>
      </div>
    </div>
  );
}
