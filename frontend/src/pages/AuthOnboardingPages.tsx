import { useState } from "react";
import type { AppRoute } from "../App";
import { Stepper } from "../components/common/Stepper";

// ──────────────────────────────────────────────
// 약관 동의 페이지
// ──────────────────────────────────────────────
interface TermsAgreementPageProps {
  onNavigate: (route: AppRoute) => void;
}

export function TermsAgreementPage({ onNavigate }: TermsAgreementPageProps) {
  const [checked, setChecked] = useState({
    service: false,
    privacy: false,
    health: false,
    marketing: false,
  });

  const allRequired = checked.service && checked.privacy && checked.health;
  const allChecked = allRequired && checked.marketing;

  const toggleAll = () => {
    const next = !allChecked;
    setChecked({ service: next, privacy: next, health: next, marketing: next });
  };

  return (
    <div style={{ minHeight: "100vh", background: "#fafafa", display: "flex", alignItems: "center", justifyContent: "center", padding: 40 }}>
      <div style={{ width: "100%", maxWidth: 680 }}>
        <div style={{ textAlign: "center", marginBottom: 24 }}>
          <img src="/logo.png" alt="All4Health" style={{ height: 40, margin: "0 auto 16px", display: "block" }} onError={e => { (e.target as HTMLImageElement).style.display = "none"; }} />
          <h2 style={{ fontSize: 18, fontWeight: 600, color: "#1a1a1a", margin: "0 0 8px" }}>회원가입</h2>
          <p style={{ fontSize: 12, color: "#888", margin: 0 }}>서비스 이용을 위한 약관에 동의해주세요</p>
        </div>

        <Stepper steps={["계정정보", "약관동의", "이메일인증", "건강설문", "완료"]} current={1} />

        <div style={{ background: "#fff", border: "1px solid #e0e0e0", borderRadius: 10, padding: 24 }}>
          <h3 style={{ fontSize: 13, fontWeight: 600, color: "#1a1a1a", margin: "0 0 16px" }}>약관 동의</h3>

          {/* 전체 동의 */}
          <label style={{ display: "flex", alignItems: "center", gap: 8, cursor: "pointer", marginBottom: 14 }}>
            <input type="checkbox" checked={allChecked} onChange={toggleAll} style={{ width: 16, height: 16, cursor: "pointer" }} />
            <span style={{ fontSize: 13, fontWeight: 600, color: "#1a1a1a" }}>전체 동의</span>
          </label>
          <hr style={{ border: "none", borderTop: "1px solid #e0e0e0", margin: "0 0 14px" }} />

          <div style={{ display: "flex", flexDirection: "column", gap: 10 }}>
            {[
              { key: "service" as const, label: "[필수] 서비스 이용약관" },
              { key: "privacy" as const, label: "[필수] 개인정보 처리방침" },
              { key: "health" as const, label: "[필수] 건강 데이터 수집·이용 동의" },
              { key: "marketing" as const, label: "[선택] 마케팅 정보 수신 동의" },
            ].map(item => (
              <div key={item.key} style={{ display: "flex", alignItems: "center", justifyContent: "space-between" }}>
                <label style={{ display: "flex", alignItems: "center", gap: 8, cursor: "pointer" }}>
                  <input type="checkbox" checked={checked[item.key]} onChange={() => setChecked(prev => ({ ...prev, [item.key]: !prev[item.key] }))}
                    style={{ width: 14, height: 14, cursor: "pointer" }} />
                  <span style={{ fontSize: 12, color: "#333" }}>{item.label}</span>
                </label>
                <button style={{ background: "none", border: "none", fontSize: 10, color: "#888", cursor: "pointer" }}>보기</button>
              </div>
            ))}
          </div>

          <p style={{ fontSize: 11, color: "#aaa", textAlign: "right", margin: "14px 0 20px" }}>적용 약관 버전: v1.0</p>

          <button onClick={() => onNavigate("/email-verify")} disabled={!allRequired}
            style={{ width: "100%", height: 40, background: allRequired ? "#1a1a1a" : "#ccc", color: "#fff", border: "none", borderRadius: 8, fontSize: 14, fontWeight: 600, cursor: allRequired ? "pointer" : "not-allowed" }}>
            다음
          </button>
        </div>

        <p style={{ textAlign: "center", marginTop: 16, fontSize: 11, color: "#888" }}>
          이미 계정이 있으신가요? {" "}
          <button onClick={() => onNavigate("/login")} style={{ background: "none", border: "none", fontSize: 11, color: "#1a1a1a", cursor: "pointer", fontWeight: 600 }}>로그인</button>
        </p>
      </div>
    </div>
  );
}

// ──────────────────────────────────────────────
// 이메일 인증 페이지
// ──────────────────────────────────────────────
interface EmailVerifyPageProps {
  onNavigate: (route: AppRoute) => void;
}

export function EmailVerifyPage({ onNavigate }: EmailVerifyPageProps) {
  const [resendCooldown, setResendCooldown] = useState(0);

  const handleResend = () => {
    // TODO: API 연결 — POST /api/v1/auth/email-verification-requests
    // Header: Authorization: Bearer <access_token> (필수)
    // 응답: 204 No Content
    // 재발송 시 기존 미사용 토큰 무효화 후 신규 토큰 발급
    // 429 RATE_LIMIT_EXCEEDED: 분당 1회 제한 → 60초 쿨다운 UI 표시
    setResendCooldown(60);
    const timer = setInterval(() => {
      setResendCooldown(prev => {
        if (prev <= 1) { clearInterval(timer); return 0; }
        return prev - 1;
      });
    }, 1000);
  };

  return (
    <div style={{ display: "flex", minHeight: "100vh" }}>
      {/* Left */}
      <div style={{ width: "45%", background: "#f5f5f5", padding: "48px 40px", display: "flex", flexDirection: "column", justifyContent: "center", borderRight: "1px solid #e0e0e0" }}>
        <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 24 }}>
          <img src="/logo.png" alt="All4Health" style={{ height: 28 }} onError={e => { (e.target as HTMLImageElement).style.display = "none"; }} />
          <span style={{ fontSize: 16, fontWeight: 700, color: "#1a1a1a" }}>All4Health</span>
        </div>
        <h2 style={{ fontSize: 20, fontWeight: 600, color: "#1a1a1a", margin: "0 0 12px" }}>이메일로 인증<br />링크를 보냈습니다</h2>
        <p style={{ fontSize: 12, color: "#555", lineHeight: 1.6, margin: "0 0 24px" }}>
          example@email.com 으로 인증 메일을 발송했습니다.<br />메일함을 확인하고 인증 링크를 클릭해주세요.
        </p>
        <hr style={{ border: "none", borderTop: "1px solid #ddd", margin: "0 0 20px" }} />
        {[
          { title: "메일이 오지 않았나요?", desc: "스팸 메일함도 확인해보세요" },
          { title: "링크 유효 시간", desc: "인증 링크는 발송 후 24시간 동안 유효합니다" },
          { title: "이메일 변경 필요 시", desc: "아래 '이전으로 돌아가기' 버튼을 눌러주세요" },
        ].map((item, i) => (
          <div key={i} style={{ display: "flex", gap: 12, alignItems: "flex-start", marginBottom: 16 }}>
            <div style={{ width: 28, height: 28, background: "#e0e0e0", borderRadius: 5, flexShrink: 0 }} />
            <div>
              <div style={{ fontSize: 11, fontWeight: 500, color: "#1a1a1a", marginBottom: 3 }}>{item.title}</div>
              <div style={{ fontSize: 10, color: "#888", lineHeight: 1.5 }}>{item.desc}</div>
            </div>
          </div>
        ))}
      </div>

      {/* Right */}
      <div style={{ flex: 1, padding: "48px 40px", display: "flex", flexDirection: "column", justifyContent: "center", background: "#fff" }}>
        <div style={{ fontSize: 11, fontWeight: 500, color: "#888", letterSpacing: 0.5, textTransform: "uppercase", marginBottom: 6 }}>이메일 인증</div>
        <div style={{ fontSize: 12, color: "#555", marginBottom: 20 }}>아래 절차에 따라 인증을 완료해주세요</div>
        <hr style={{ border: "none", borderTop: "1px solid #e0e0e0", margin: "0 0 20px" }} />

        <div style={{ display: "flex", flexDirection: "column", alignItems: "center", marginBottom: 24 }}>
          <div style={{ width: 56, height: 56, borderRadius: "50%", background: "#f0f0f0", display: "flex", alignItems: "center", justifyContent: "center", marginBottom: 14, fontSize: 24 }}>📧</div>
          <p style={{ fontSize: 12, color: "#555", textAlign: "center" }}>example@email.com 으로 인증 메일을 발송했습니다</p>
        </div>

        <div style={{ background: "#fff", border: "1px solid #e0e0e0", borderRadius: 8, padding: 16, marginBottom: 20 }}>
          <div style={{ fontSize: 11, fontWeight: 500, color: "#555", marginBottom: 12 }}>인증 절차</div>
          <hr style={{ border: "none", borderTop: "1px solid #eee", margin: "0 0 10px" }} />
          {["이메일 수신 확인", "인증 링크 클릭", "인증 완료"].map((step, i) => (
            <div key={step} style={{ display: "flex", alignItems: "center", gap: 10, padding: "8px 0" }}>
              <div style={{ width: 16, height: 16, borderRadius: "50%", border: `1.5px solid ${i === 0 ? "#1a1a1a" : "#ddd"}`, display: "flex", alignItems: "center", justifyContent: "center", fontSize: 9, flexShrink: 0 }} />
              <span style={{ fontSize: 11, color: "#333" }}>{step}</span>
            </div>
          ))}
        </div>

        <button onClick={handleResend} disabled={resendCooldown > 0}
          style={{ width: "100%", height: 36, border: "1.5px solid #ddd", borderRadius: 8, background: "#fff", fontSize: 12, color: resendCooldown > 0 ? "#aaa" : "#333", cursor: resendCooldown > 0 ? "not-allowed" : "pointer", marginBottom: 10 }}>
          {resendCooldown > 0 ? `재발송 가능까지 ${resendCooldown}초` : "이메일 재발송"}
        </button>
        <button onClick={() => onNavigate("/signup")}
          style={{ width: "100%", height: 36, border: "1.5px solid #ddd", borderRadius: 8, background: "#fff", fontSize: 12, color: "#333", cursor: "pointer", marginBottom: 20 }}>
          이전으로 돌아가기
        </button>

        {/* 개발용: 인증 완료 시뮬레이션 */}
        <button onClick={() => onNavigate("/health-survey")}
          style={{ width: "100%", height: 36, background: "#1a1a1a", color: "#fff", border: "none", borderRadius: 8, fontSize: 12, cursor: "pointer", marginBottom: 16 }}>
          [개발용] 인증 완료 → 다음 단계
        </button>

        <p style={{ textAlign: "center", fontSize: 11, color: "#888", cursor: "pointer", margin: 0 }}
          onClick={() => onNavigate("/login")}>로그인으로 돌아가기</p>
      </div>
    </div>
  );
}

// ──────────────────────────────────────────────
// 비밀번호 재설정 페이지 (1~4단계 통합)
// ──────────────────────────────────────────────
interface PasswordResetPageProps {
  onNavigate: (route: AppRoute) => void;
}

export function PasswordResetPage({ onNavigate }: PasswordResetPageProps) {
  const [step, setStep] = useState<1 | 2 | 3 | 4>(1);
  const [email, setEmail] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [showPw, setShowPw] = useState(false);
  const [showConfirm, setShowConfirm] = useState(false);

  const pwMismatch = confirmPassword.length > 0 && newPassword !== confirmPassword;

  const ProcessGuide = () => (
    <div style={{ width: "45%", background: "#f5f5f5", padding: "48px 40px", display: "flex", flexDirection: "column", justifyContent: "center", borderRight: "1px solid #e0e0e0" }}>
      <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 24 }}>
        <span style={{ fontSize: 16, fontWeight: 700, color: "#1a1a1a" }}>All4Health</span>
      </div>
      <h2 style={{ fontSize: 20, fontWeight: 600, color: "#1a1a1a", margin: "0 0 12px" }}>비밀번호를<br />재설정합니다</h2>
      <p style={{ fontSize: 12, color: "#555", lineHeight: 1.6, margin: "0 0 8px" }}>재설정 링크는 발송 후 1시간 동안 유효합니다.</p>
      <hr style={{ border: "none", borderTop: "1px solid #ddd", margin: "20px 0" }} />
      {[
        { num: "1", title: "이메일 입력", desc: "가입 시 사용한 이메일 주소를 입력하세요" },
        { num: "2", title: "인증 메일 확인", desc: "받은편지함에서 재설정 링크를 클릭하세요" },
        { num: "3", title: "새 비밀번호 설정", desc: "안전한 새 비밀번호로 계정을 보호하세요" },
      ].map((item, i) => (
        <div key={item.num} style={{ display: "flex", gap: 12, alignItems: "flex-start", marginBottom: 16 }}>
          <div style={{ width: 28, height: 28, borderRadius: "50%", border: "1.5px solid #ddd", background: step - 1 > i ? "#1a1a1a" : "#f0f0f0", display: "flex", alignItems: "center", justifyContent: "center", fontSize: 11, color: step - 1 > i ? "#fff" : "#888", flexShrink: 0 }}>
            {step - 1 > i ? "✓" : item.num}
          </div>
          <div>
            <div style={{ fontSize: 11, fontWeight: 500, color: "#1a1a1a", marginBottom: 3 }}>{item.title}</div>
            <div style={{ fontSize: 10, color: "#888", lineHeight: 1.5 }}>{item.desc}</div>
          </div>
        </div>
      ))}
    </div>
  );

  if (step === 4) {
    return (
      <div style={{ minHeight: "100vh", display: "flex", alignItems: "center", justifyContent: "center", background: "#fff" }}>
        <div style={{ textAlign: "center", maxWidth: 360, padding: "48px 40px" }}>
          <div style={{ width: 56, height: 56, borderRadius: "50%", background: "#2e7d32", margin: "0 auto 20px", display: "flex", alignItems: "center", justifyContent: "center", fontSize: 24, color: "#fff" }}>✓</div>
          <h2 style={{ fontSize: 20, fontWeight: 600, color: "#1a1a1a", margin: "0 0 8px" }}>비밀번호가 변경되었습니다</h2>
          <p style={{ fontSize: 12, color: "#555", lineHeight: 1.6, margin: "0 0 24px" }}>새 비밀번호로 로그인해주세요.</p>
          <button onClick={() => onNavigate("/login")}
            style={{ width: "100%", height: 40, background: "#1a1a1a", color: "#fff", border: "none", borderRadius: 8, fontSize: 14, fontWeight: 600, cursor: "pointer" }}>
            로그인하러 가기
          </button>
        </div>
      </div>
    );
  }

  return (
    <div style={{ display: "flex", minHeight: "100vh" }}>
      <ProcessGuide />
      <div style={{ flex: 1, padding: "48px 40px", display: "flex", flexDirection: "column", justifyContent: "center", background: "#fff" }}>
        <div style={{ fontSize: 11, fontWeight: 500, color: "#888", letterSpacing: 0.5, textTransform: "uppercase", marginBottom: 6 }}>비밀번호 재설정</div>
        <hr style={{ border: "none", borderTop: "1px solid #e0e0e0", margin: "16px 0" }} />

        {step === 1 && (
          <div style={{ display: "flex", flexDirection: "column", gap: 14 }}>
            <div style={{ fontSize: 12, color: "#555", marginBottom: 4 }}>가입 시 사용한 이메일 주소를 입력하세요</div>
            <div>
              <label style={{ fontSize: 10, color: "#555", display: "block", marginBottom: 4 }}>이메일</label>
              <input type="email" value={email} onChange={e => setEmail(e.target.value)} placeholder="example@email.com"
                style={{ width: "100%", height: 34, border: "1.5px solid #ddd", borderRadius: 5, padding: "0 10px", fontSize: 11, boxSizing: "border-box", outline: "none" }} />
              <p style={{ fontSize: 11, color: "#aaa", margin: "4px 0 0" }}>가입된 이메일이 아니더라도 동일한 안내를 드립니다.</p>
            </div>
            <button onClick={() => setStep(2)} disabled={!email}
              style={{ width: "100%", height: 36, background: email ? "#1a1a1a" : "#ccc", color: "#fff", border: "none", borderRadius: 8, fontSize: 13, fontWeight: 600, cursor: email ? "pointer" : "not-allowed" }}>
              {/* TODO: API 연결 — POST /api/v1/auth/password-reset-requests */}
              {/* body: { email } / 응답: 204 No Content (미가입 이메일도 동일 응답, 가입 여부 비노출) */}
              {/* 재설정 토큰 유효시간 30분 / 429 RATE_LIMIT_EXCEEDED: 분당 3회/IP 제한 */}
              인증 메일 발송
            </button>
            <hr style={{ border: "none", borderTop: "1px solid #eee" }} />
            <p style={{ textAlign: "center", fontSize: 11, color: "#888", cursor: "pointer" }} onClick={() => onNavigate("/login")}>로그인으로 돌아가기</p>
          </div>
        )}

        {step === 2 && (
          <div style={{ display: "flex", flexDirection: "column", gap: 14 }}>
            <div style={{ fontSize: 12, color: "#555" }}>이메일을 확인해주세요</div>
            <p style={{ fontSize: 13, color: "#333", lineHeight: 1.6, margin: 0 }}>
              {email}으로 재설정 링크를 발송했습니다. 메일함을 확인하고 링크를 클릭해주세요.
            </p>
            <p style={{ fontSize: 11, color: "#aaa", margin: 0 }}>링크는 발송 후 1시간 동안 유효합니다. 스팸 메일함도 확인해보세요.</p>
            <button onClick={() => {}} style={{ width: "100%", height: 36, background: "#1a1a1a", color: "#fff", border: "none", borderRadius: 8, fontSize: 13, cursor: "pointer" }}>이메일 재발송</button>
            {/* 개발용 */}
            <button onClick={() => setStep(3)} style={{ width: "100%", height: 36, border: "1.5px solid #ddd", borderRadius: 8, background: "#fff", fontSize: 12, cursor: "pointer" }}>[개발용] 링크 클릭 → 다음 단계</button>
            <hr style={{ border: "none", borderTop: "1px solid #eee" }} />
            <p style={{ textAlign: "center", fontSize: 11, color: "#888", cursor: "pointer" }} onClick={() => onNavigate("/login")}>로그인으로 돌아가기</p>
          </div>
        )}

        {step === 3 && (
          <div style={{ display: "flex", flexDirection: "column", gap: 14 }}>
            <div style={{ fontSize: 12, color: "#555" }}>새 비밀번호를 입력해주세요</div>
            <div>
              <label style={{ fontSize: 10, color: "#555", display: "block", marginBottom: 4 }}>새 비밀번호</label>
              <div style={{ position: "relative" }}>
                <input type={showPw ? "text" : "password"} value={newPassword} onChange={e => setNewPassword(e.target.value)} placeholder="영문+숫자+특수문자 조합 8자 이상"
                  style={{ width: "100%", height: 34, border: "1.5px solid #ddd", borderRadius: 5, padding: "0 36px 0 10px", fontSize: 11, boxSizing: "border-box", outline: "none" }} />
                <button onClick={() => setShowPw(!showPw)} style={{ position: "absolute", right: 10, top: "50%", transform: "translateY(-50%)", background: "none", border: "none", cursor: "pointer", fontSize: 12 }}>{showPw ? "🙈" : "👁"}</button>
              </div>
            </div>
            <div>
              <label style={{ fontSize: 10, color: "#555", display: "block", marginBottom: 4 }}>새 비밀번호 확인</label>
              <div style={{ position: "relative" }}>
                <input type={showConfirm ? "text" : "password"} value={confirmPassword} onChange={e => setConfirmPassword(e.target.value)} placeholder="동일하게 입력"
                  style={{ width: "100%", height: 34, border: `1.5px solid ${pwMismatch ? "#E24B4A" : "#ddd"}`, borderRadius: 5, padding: "0 36px 0 10px", fontSize: 11, boxSizing: "border-box", outline: "none" }} />
                <button onClick={() => setShowConfirm(!showConfirm)} style={{ position: "absolute", right: 10, top: "50%", transform: "translateY(-50%)", background: "none", border: "none", cursor: "pointer", fontSize: 12 }}>{showConfirm ? "🙈" : "👁"}</button>
              </div>
              {pwMismatch && <p style={{ fontSize: 11, color: "#E24B4A", margin: "4px 0 0" }}>비밀번호가 일치하지 않습니다.</p>}
            </div>
            <button onClick={() => setStep(4)} disabled={!newPassword || !confirmPassword || pwMismatch}
              style={{ width: "100%", height: 36, background: !newPassword || !confirmPassword || pwMismatch ? "#ccc" : "#1a1a1a", color: "#fff", border: "none", borderRadius: 8, fontSize: 13, fontWeight: 600, cursor: !newPassword || !confirmPassword || pwMismatch ? "not-allowed" : "pointer" }}>
              {/* TODO: API 연결 — POST /api/v1/auth/password-resets */}
              {/* body: { token (URL 파라미터), new_password, new_password_confirm } */}
              {/* 응답: 204 No Content / 재설정 완료 시 기존 Refresh Token 세션 전체 무효화 */}
              {/* 410 TOKEN_EXPIRED: 토큰 만료(30분) / 422 PASSWORD_MISMATCH */}
              비밀번호 변경하기
            </button>
          </div>
        )}
      </div>
    </div>
  );
}

// ──────────────────────────────────────────────
// 온보딩 완료 페이지
// ──────────────────────────────────────────────
interface OnboardingCompletePageProps {
  onNavigate: (route: AppRoute) => void;
}

export function OnboardingCompletePage({ onNavigate }: OnboardingCompletePageProps) {
  return (
    <div style={{ minHeight: "100vh", background: "#fafafa", display: "flex", alignItems: "center", justifyContent: "center", padding: 40 }}>
      <div style={{ width: "100%", maxWidth: 680 }}>
        <div style={{ textAlign: "center", marginBottom: 24 }}>
          <img src="/logo.png" alt="All4Health" style={{ height: 40, margin: "0 auto 16px", display: "block" }} onError={e => { (e.target as HTMLImageElement).style.display = "none"; }} />
        </div>

        <Stepper steps={["계정정보", "약관동의", "이메일인증", "건강설문", "완료"]} current={4} />

        <div style={{ background: "#fff", border: "1px solid #e0e0e0", borderRadius: 10, padding: 28, textAlign: "center" }}>
          <div style={{ width: 72, height: 72, borderRadius: "50%", background: "#f0f0f0", border: "2px solid #ddd", margin: "0 auto 20px", display: "flex", alignItems: "center", justifyContent: "center", fontSize: 32 }}>✓</div>
          <div style={{ display: "inline-block", padding: "4px 12px", background: "#2e7d32", borderRadius: 12, fontSize: 11, color: "#fff", marginBottom: 14 }}>✓ 이메일 인증 완료</div>
          <h2 style={{ fontSize: 20, fontWeight: 600, color: "#1a1a1a", margin: "0 0 10px" }}>가입이 완료되었습니다!</h2>
          <p style={{ fontSize: 12, color: "#888", margin: "0 0 24px" }}>All4Health와 함께 건강한 생활을 시작해보세요.</p>

          <hr style={{ border: "none", borderTop: "1px solid #e0e0e0", margin: "0 0 20px" }} />

          <div style={{ textAlign: "left", marginBottom: 24 }}>
            <p style={{ fontSize: 11, color: "#888", marginBottom: 12 }}>다음 단계로 진행하세요:</p>
            {[
              { icon: "🎯", label: "건강 목표 설정하기" },
              { icon: "📊", label: "추가 건강 수치 입력하기" },
              { icon: "🏆", label: "챌린지 참여하기" },
            ].map(item => (
              <div key={item.label} style={{ padding: "12px 16px", border: "1.5px solid #e0e0e0", borderRadius: 8, background: "#fafafa", display: "flex", alignItems: "center", justifyContent: "space-between", cursor: "pointer", marginBottom: 8 }}>
                <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
                  <span style={{ fontSize: 16 }}>{item.icon}</span>
                  <span style={{ fontSize: 14, fontWeight: 500, color: "#1a1a1a" }}>{item.label}</span>
                </div>
                <span style={{ fontSize: 16, color: "#aaa" }}>›</span>
              </div>
            ))}
          </div>

          <button onClick={() => onNavigate("/home")}
            style={{ width: "100%", height: 40, background: "#1a1a1a", color: "#fff", border: "none", borderRadius: 8, fontSize: 14, fontWeight: 600, cursor: "pointer" }}>
            홈으로 이동
          </button>
        </div>
      </div>
    </div>
  );
}
