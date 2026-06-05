import { useState } from "react";
import type { AppRoute } from "../App";
import logoUrl from "../assets/all4health-logo.png";

interface SignUpPageProps {
  onNavigate: (route: AppRoute) => void;
}

const DISEASES = ["당뇨", "고혈압", "고지혈증", "비만", "만성신장질환"];

export function SignUpPage({ onNavigate }: SignUpPageProps) {
  const [name, setName] = useState("");
  const [gender, setGender] = useState<"male" | "female" | "">("");
  const [email, setEmail] = useState("");
  const [emailChecked, setEmailChecked] = useState(false);
  const [password, setPassword] = useState("");
  const [passwordConfirm, setPasswordConfirm] = useState("");
  const [showPw, setShowPw] = useState(false);
  const [showPwConfirm, setShowPwConfirm] = useState(false);
  const [selectedDiseases, setSelectedDiseases] = useState<string[]>([]);
  const [isLoading, setIsLoading] = useState(false);

  const toggleDisease = (d: string) => {
    setSelectedDiseases(prev => prev.includes(d) ? prev.filter(x => x !== d) : [...prev, d]);
  };

  const handleEmailCheck = () => {
    // TODO: API 연결 — GET /api/v1/auth/email-availability?email={email}
    // 응답: 200 { data: { available: bool } }
    // available: true → "사용 가능한 이메일입니다." 표시
    // available: false → 400 INVALID_EMAIL_FORMAT 또는 409 EMAIL_EXISTS
    setEmailChecked(true);
  };

  const handleNext = () => {
    setIsLoading(true);
    // TODO: API 연결 — POST /api/v1/auth/registrations
    // body: {
    //   email, password, name,
    //   gender: gender === "male" ? "M" : "F",
    //   managed_diseases: selectedDiseases.map(d => DISEASE_CODE_MAP[d]),
    //   consent_terms_version: "v1.0",
    //   consent_privacy_agreed: true,   // 약관동의 단계에서 처리
    //   consent_health_data: true,
    //   consent_marketing: false
    // }
    // 응답: 201 { data: { user_id, email, name, gender, managed_diseases } }
    // 실패: 409 EMAIL_EXISTS / 422 PASSWORD_TOO_WEAK / 422 DISEASE_SELECTION_REQUIRED
    setTimeout(() => {
      setIsLoading(false);
      onNavigate("/terms");
    }, 300);
  };

  const pwMismatch = passwordConfirm.length > 0 && password !== passwordConfirm;
  const isValid = name && gender && email && emailChecked && password && !pwMismatch && selectedDiseases.length > 0;

  return (
    <div style={{ display: "flex", minHeight: "100vh" }}>
      {/* Left - 온보딩 단계 안내 */}
      <div style={{ width: "45%", background: "#f5f5f5", padding: "48px 40px", display: "flex", flexDirection: "column", justifyContent: "center", borderRight: "1px solid #e0e0e0" }}>
        <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 24 }}>
          <img src={logoUrl} alt="All4Health" style={{ height: 28, width: "auto" }} />
          <span style={{ fontSize: 16, fontWeight: 700, color: "#1a1a1a" }}>All4Health</span>
        </div>
        <h2 style={{ fontSize: 20, fontWeight: 600, color: "#1a1a1a", lineHeight: 1.35, margin: "0 0 12px" }}>
          건강한 변화의<br />첫 걸음을 시작하세요
        </h2>
        <p style={{ fontSize: 12, color: "#555", lineHeight: 1.6, margin: "0 0 24px" }}>
          All4Health와 함께 만성질환을 예방하고<br />생활습관을 개선해보세요.
        </p>
        <hr style={{ border: "none", borderTop: "1px solid #ddd", margin: "0 0 20px" }} />
        <div style={{ display: "flex", flexDirection: "column", gap: 16 }}>
          {[
            { num: "1", title: "계정 정보 입력", desc: "이메일과 비밀번호 설정", active: true },
            { num: "2", title: "약관 동의", desc: "서비스 이용약관 동의", active: false },
            { num: "3", title: "이메일 인증", desc: "이메일 확인 및 인증", active: false },
            { num: "4", title: "건강 설문", desc: "건강 프로필 설정", active: false },
            { num: "5", title: "완료", desc: "가입 완료 및 서비스 시작", active: false },
          ].map((item) => (
            <div key={item.num} style={{ display: "flex", gap: 12, alignItems: "flex-start" }}>
              <div style={{ width: 28, height: 28, borderRadius: "50%", border: `1.5px solid ${item.active ? "#1a1a1a" : "#ddd"}`, background: item.active ? "#1a1a1a" : "#f0f0f0", display: "flex", alignItems: "center", justifyContent: "center", fontSize: 11, color: item.active ? "#fff" : "#888", flexShrink: 0 }}>{item.num}</div>
              <div>
                <div style={{ fontSize: 11, fontWeight: item.active ? 600 : 400, color: item.active ? "#1a1a1a" : "#888", marginBottom: 3 }}>{item.title}</div>
                <div style={{ fontSize: 10, color: "#aaa", lineHeight: 1.5 }}>{item.desc}</div>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Right - 회원가입 폼 */}
      <div style={{ flex: 1, padding: "48px 40px", display: "flex", flexDirection: "column", justifyContent: "center", background: "#fff", overflowY: "auto" }}>
        <div style={{ fontSize: 11, fontWeight: 500, color: "#888", letterSpacing: 0.5, textTransform: "uppercase", marginBottom: 6 }}>회원가입</div>
        <div style={{ fontSize: 12, color: "#555", marginBottom: 20 }}>아래 정보를 입력하여 계정을 만드세요</div>
        <hr style={{ border: "none", borderTop: "1px solid #e0e0e0", margin: "0 0 16px" }} />

        <div style={{ display: "flex", flexDirection: "column", gap: 14 }}>
          {/* 이름 + 성별 */}
          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 12 }}>
            <div>
              <label style={{ fontSize: 10, color: "#555", display: "block", marginBottom: 4 }}>이름</label>
              <input value={name} onChange={e => setName(e.target.value)} placeholder="홍길동"
                style={{ width: "100%", height: 34, border: "1.5px solid #ddd", borderRadius: 5, padding: "0 10px", fontSize: 11, boxSizing: "border-box", outline: "none" }} />
            </div>
            <div>
              <label style={{ fontSize: 10, color: "#555", display: "block", marginBottom: 4 }}>성별</label>
              <div style={{ display: "flex", gap: 8 }}>
                {(["male", "female"] as const).map(g => (
                  <button key={g} onClick={() => setGender(g)}
                    style={{ flex: 1, height: 34, border: `1.5px solid ${gender === g ? "#1a1a1a" : "#ddd"}`, borderRadius: 5, background: gender === g ? "#1a1a1a" : "#fff", color: gender === g ? "#fff" : "#555", fontSize: 11, cursor: "pointer" }}>
                    {g === "male" ? "남성" : "여성"}
                  </button>
                ))}
              </div>
            </div>
          </div>

          {/* 이메일 */}
          <div>
            <label style={{ fontSize: 10, color: "#555", display: "block", marginBottom: 4 }}>이메일 (필수)</label>
            <div style={{ display: "flex", gap: 8 }}>
              <input type="email" value={email} onChange={e => { setEmail(e.target.value); setEmailChecked(false); }} placeholder="example@email.com"
                style={{ flex: 1, height: 34, border: "1.5px solid #ddd", borderRadius: 5, padding: "0 10px", fontSize: 11, boxSizing: "border-box", outline: "none" }} />
              <button onClick={handleEmailCheck}
                style={{ height: 34, minWidth: 70, border: "1.5px solid #ddd", borderRadius: 5, background: "#f5f5f5", fontSize: 10, color: "#555", cursor: "pointer" }}>중복 확인</button>
            </div>
            {emailChecked && <p style={{ fontSize: 11, color: "#2e7d32", margin: "4px 0 0" }}>✓ 사용 가능한 이메일입니다.</p>}
          </div>

          {/* 비밀번호 */}
          <div>
            <label style={{ fontSize: 10, color: "#555", display: "block", marginBottom: 4 }}>비밀번호</label>
            <div style={{ position: "relative" }}>
              <input type={showPw ? "text" : "password"} value={password} onChange={e => setPassword(e.target.value)}
                placeholder="영문+숫자+특수문자 조합 8자 이상"
                style={{ width: "100%", height: 34, border: "1.5px solid #ddd", borderRadius: 5, padding: "0 36px 0 10px", fontSize: 11, boxSizing: "border-box", outline: "none" }} />
              <button onClick={() => setShowPw(!showPw)} style={{ position: "absolute", right: 10, top: "50%", transform: "translateY(-50%)", background: "none", border: "none", cursor: "pointer", fontSize: 12 }}>
                {showPw ? "🙈" : "👁"}
              </button>
            </div>
          </div>

          {/* 비밀번호 확인 */}
          <div>
            <label style={{ fontSize: 10, color: "#555", display: "block", marginBottom: 4 }}>비밀번호 확인</label>
            <div style={{ position: "relative" }}>
              <input type={showPwConfirm ? "text" : "password"} value={passwordConfirm} onChange={e => setPasswordConfirm(e.target.value)}
                placeholder="동일하게 입력"
                style={{ width: "100%", height: 34, border: `1.5px solid ${pwMismatch ? "#E24B4A" : "#ddd"}`, borderRadius: 5, padding: "0 36px 0 10px", fontSize: 11, boxSizing: "border-box", outline: "none" }} />
              <button onClick={() => setShowPwConfirm(!showPwConfirm)} style={{ position: "absolute", right: 10, top: "50%", transform: "translateY(-50%)", background: "none", border: "none", cursor: "pointer", fontSize: 12 }}>
                {showPwConfirm ? "🙈" : "👁"}
              </button>
            </div>
            {pwMismatch && <p style={{ fontSize: 11, color: "#E24B4A", margin: "4px 0 0" }}>비밀번호가 일치하지 않습니다.</p>}
          </div>

          {/* 관리 질환 선택 */}
          <div>
            <label style={{ fontSize: 10, color: "#555", display: "block", marginBottom: 4 }}>관리 대상 질환 선택 *</label>
            <p style={{ fontSize: 11, color: "#888", margin: "0 0 10px" }}>1개 이상 선택해주세요.</p>
            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 8 }}>
              {DISEASES.map(d => (
                <label key={d} style={{ display: "flex", alignItems: "center", gap: 8, cursor: "pointer" }}>
                  <input type="checkbox" checked={selectedDiseases.includes(d)} onChange={() => toggleDisease(d)}
                    style={{ width: 14, height: 14, cursor: "pointer" }} />
                  <span style={{ fontSize: 12, color: "#333" }}>{d}</span>
                </label>
              ))}
            </div>
            {selectedDiseases.length === 0 && <p style={{ fontSize: 11, color: "#E24B4A", margin: "6px 0 0" }}>관리 대상 질환을 1개 이상 선택해주세요.</p>}
          </div>

          <button onClick={handleNext} disabled={!isValid || isLoading}
            style={{ width: "100%", height: 36, background: !isValid || isLoading ? "#ccc" : "#1a1a1a", color: "#fff", border: "none", borderRadius: 8, fontSize: 13, fontWeight: 600, cursor: !isValid || isLoading ? "not-allowed" : "pointer", marginTop: 6 }}>
            {isLoading ? "처리 중..." : "다음"}
          </button>

          <div style={{ textAlign: "right" }}>
            <span style={{ fontSize: 11, color: "#888" }}>이미 계정이 있으신가요? </span>
            <button onClick={() => onNavigate("/login")} style={{ background: "none", border: "none", fontSize: 11, color: "#1a1a1a", cursor: "pointer", fontWeight: 600 }}>로그인</button>
          </div>
        </div>
      </div>
    </div>
  );
}
