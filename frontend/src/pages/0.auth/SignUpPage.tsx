import { useEffect, useState } from "react";
import type { AppRoute } from "../../App";
import { checkSignupAvailability, type SignUpPayload } from "../../api/auth";
import { ApiError } from "../../api/client";
import { PasswordToggleButton } from "../../components/common/PasswordToggleButton";

interface SignUpPageProps {
  onNavigate: (route: AppRoute) => void;
}

const NO_MANAGED_DISEASE = "없음";
const DISEASES = [NO_MANAGED_DISEASE, "당뇨", "고혈압", "고지혈증", "비만", "만성신장질환"];
const SIGNUP_DRAFT_KEY = "auth.signupDraft";
const GOOGLE_SIGNUP_DRAFT_KEY = "auth.googleSignupDraft";
const SIGNUP_ERROR_KEY = "auth.signupError";

type GoogleSignupDraft = {
  id_token: string;
  email: string;
  name?: string;
  picture?: string;
  remember_me?: boolean;
};

type SignupDraft = Partial<SignUpPayload> & {
  auth_provider?: "GOOGLE";
  id_token?: string;
  remember_me?: boolean;
  managed_diseases?: string[];
};

function validatePassword(value: string) {
  if (value.length < 8) return "비밀번호는 8자 이상이어야 합니다.";
  if (!/[A-Z]/.test(value)) return "대문자를 1개 이상 포함해야 합니다.";
  if (!/[a-z]/.test(value)) return "소문자를 1개 이상 포함해야 합니다.";
  if (!/[0-9]/.test(value)) return "숫자를 1개 이상 포함해야 합니다.";
  if (!/[^a-zA-Z0-9]/.test(value)) return "특수문자를 1개 이상 포함해야 합니다.";
  return "";
}

function validateEmail(value: string) {
  return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(value);
}

function validatePhoneNumber(value: string) {
  return /^(010-\d{4}-\d{4}|010\d{8}|\+8210\d{8})$/.test(value);
}

function toSignupName(value?: string) {
  const normalized = (value ?? "")
    .replace(/[^\uAC00-\uD7A3a-zA-Z0-9\s]/g, "")
    .replace(/\s+/g, " ")
    .trim();
  return normalized.length >= 2 ? normalized.slice(0, 20) : "";
}

export function SignUpPage({ onNavigate }: SignUpPageProps) {
  const [name, setName] = useState("");
  const [gender, setGender] = useState<"male" | "female" | "">("");
  const [birthDate, setBirthDate] = useState("");
  const [phoneNumber, setPhoneNumber] = useState("");
  const [email, setEmail] = useState("");
  const [emailChecked, setEmailChecked] = useState(false);
  const [password, setPassword] = useState("");
  const [passwordConfirm, setPasswordConfirm] = useState("");
  const [showPw, setShowPw] = useState(false);
  const [showPwConfirm, setShowPwConfirm] = useState(false);
  const [selectedDiseases, setSelectedDiseases] = useState<string[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [formMessage, setFormMessage] = useState("");
  const [emailServerError, setEmailServerError] = useState("");
  const [phoneServerError, setPhoneServerError] = useState("");
  const [googleDraft, setGoogleDraft] = useState<GoogleSignupDraft | null>(null);

  useEffect(() => {
    const rawGoogleDraft = sessionStorage.getItem(GOOGLE_SIGNUP_DRAFT_KEY);
    if (rawGoogleDraft) {
      try {
        const draft = JSON.parse(rawGoogleDraft) as GoogleSignupDraft;
        const safeName = toSignupName(draft.name);
        setGoogleDraft(draft);
        setName(safeName);
        setEmail(draft.email ?? "");
        setEmailChecked(Boolean(draft.email));
        if (draft.name && !safeName) {
          setFormMessage("Google 계정 이름을 회원가입 이름으로 사용할 수 없어 직접 입력해주세요.");
        }
      } catch {
        sessionStorage.removeItem(GOOGLE_SIGNUP_DRAFT_KEY);
      }
    }

    const rawDraft = sessionStorage.getItem(SIGNUP_DRAFT_KEY);
    if (rawDraft) {
      try {
        const draft = JSON.parse(rawDraft) as SignupDraft;
        setName(draft.name ?? "");
        setGender(draft.gender === "MALE" ? "male" : draft.gender === "FEMALE" ? "female" : "");
        setBirthDate(draft.birth_date ?? "");
        setPhoneNumber(draft.phone_number ?? "");
        setEmail(draft.email ?? "");
        setPassword(draft.password ?? "");
        setPasswordConfirm(draft.password ?? "");
        setSelectedDiseases(draft.managed_diseases?.length ? draft.managed_diseases : []);
        if (draft.email) setEmailChecked(true);
        if (draft.auth_provider === "GOOGLE" && draft.id_token) {
          const safeName = toSignupName(draft.name);
          setName(safeName);
          if (draft.name && !safeName) {
            setFormMessage("Google 계정 이름을 회원가입 이름으로 사용할 수 없어 직접 입력해주세요.");
          }
          setGoogleDraft({
            id_token: draft.id_token,
            email: draft.email ?? "",
            name: safeName,
            remember_me: draft.remember_me,
          });
        }
      } catch {
        sessionStorage.removeItem(SIGNUP_DRAFT_KEY);
      }
    }

    const signupError = sessionStorage.getItem(SIGNUP_ERROR_KEY);
    if (signupError) {
      if (signupError.includes("휴대폰")) {
        setPhoneServerError(signupError);
      } else if (signupError.includes("이메일")) {
        setEmailServerError(signupError);
      } else {
        setFormMessage(signupError);
      }
      sessionStorage.removeItem(SIGNUP_ERROR_KEY);
    }
  }, []);

  const toggleDisease = (d: string) => {
    setSelectedDiseases(prev => {
      if (d === NO_MANAGED_DISEASE) {
        return prev.includes(NO_MANAGED_DISEASE) ? [] : [NO_MANAGED_DISEASE];
      }
      const withoutNone = prev.filter(x => x !== NO_MANAGED_DISEASE);
      return withoutNone.includes(d) ? withoutNone.filter(x => x !== d) : [...withoutNone, d];
    });
  };

  const handleEmailCheck = () => {
    if (googleDraft) return;
    setEmailServerError("");
    if (!validateEmail(email)) {
      setEmailChecked(false);
      setFormMessage("이메일 형식을 확인해주세요.");
      return;
    }
    setFormMessage("이메일 형식이 확인되었습니다. 중복 여부는 가입 시 확인됩니다.");
    setEmailChecked(true);
  };

  const switchToEmailSignup = () => {
    sessionStorage.removeItem(GOOGLE_SIGNUP_DRAFT_KEY);
    sessionStorage.removeItem(SIGNUP_DRAFT_KEY);
    setGoogleDraft(null);
    setEmail("");
    setEmailChecked(false);
    setPassword("");
    setPasswordConfirm("");
    setFormMessage("이메일 회원가입으로 전환했습니다. 계정 정보를 다시 입력해주세요.");
  };

  const handleNext = async () => {
    const passwordError = googleDraft ? "" : validatePassword(password);
    setEmailServerError("");
    setPhoneServerError("");
    setFormMessage("");
    if (passwordError) {
      setFormMessage(passwordError);
      return;
    }
    if (!validatePhoneNumber(phoneNumber)) {
      setFormMessage("휴대폰 번호는 01012345678, 010-1234-5678, +821012345678 형식으로 입력해주세요.");
      return;
    }

    setIsLoading(true);
    try {
      await checkSignupAvailability({ email, phone_number: phoneNumber });

      const draft: SignupDraft = {
        email,
        password: googleDraft ? undefined : password,
        name,
        gender: gender === "male" ? "MALE" : "FEMALE",
        birth_date: birthDate,
        phone_number: phoneNumber,
        managed_diseases: selectedDiseases.includes(NO_MANAGED_DISEASE) ? [] : selectedDiseases,
        auth_provider: googleDraft ? "GOOGLE" : undefined,
        id_token: googleDraft?.id_token,
        remember_me: googleDraft?.remember_me,
      };
      sessionStorage.setItem(SIGNUP_DRAFT_KEY, JSON.stringify(draft));
      onNavigate("/terms");
    } catch (error) {
      if (error instanceof ApiError && error.status === 409) {
        const message = String(error.detail ?? "이미 사용 중인 이메일 또는 휴대폰 번호입니다.");
        if (message.includes("휴대폰")) {
          setPhoneServerError(message);
        } else if (message.includes("이메일")) {
          setEmailServerError(message);
        } else {
          setFormMessage(message);
        }
      } else if (error instanceof ApiError && error.status === 422) {
        setFormMessage("입력값을 확인해주세요. 이메일 또는 휴대폰 번호 형식이 올바르지 않습니다.");
      } else {
        setFormMessage("중복 확인에 실패했습니다. 백엔드 서버 연결 상태를 확인해주세요.");
      }
    } finally {
      setIsLoading(false);
    }
  };

  const pwMismatch = passwordConfirm.length > 0 && password !== passwordConfirm;
  const passwordError = googleDraft ? "" : password ? validatePassword(password) : "";
  const phoneError = phoneNumber && !validatePhoneNumber(phoneNumber);
  const isValid =
    name &&
    gender &&
    birthDate &&
    phoneNumber &&
    !phoneError &&
    email &&
    emailChecked &&
    (googleDraft || password) &&
    !passwordError &&
    (googleDraft || passwordConfirm) &&
    (googleDraft || !pwMismatch) &&
    selectedDiseases.length > 0;

  return (
    <div style={{ display: "flex", minHeight: "100vh" }}>
      {/* Left - 온보딩 단계 안내 */}
      <div style={{ width: "45%", background: "#f5f5f5", padding: "48px 40px", display: "flex", flexDirection: "column", justifyContent: "center", borderRight: "1px solid #e0e0e0" }}>
        <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 24 }}>
          <img src="/logo.png" alt="All4Health" style={{ height: 28, width: "auto" }} onError={e => { (e.target as HTMLImageElement).style.display = "none"; }} />
          <span style={{ fontSize: 16, fontWeight: 700, color: "#1a1a1a" }}>All4Health</span>
        </div>
        <h2 style={{ fontSize: 20, fontWeight: 600, color: "#1a1a1a", lineHeight: 1.35, margin: "0 0 12px" }}>
          건강한 변화의<br />첫 걸음을 시작하세요
        </h2>
        <p style={{ fontSize: 15, color: "#555", lineHeight: 1.6, margin: "0 0 24px" }}>
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
              <div style={{ width: 28, height: 28, borderRadius: "50%", border: `1.5px solid ${item.active ? "#1a1a1a" : "#ddd"}`, background: item.active ? "#1a1a1a" : "#f0f0f0", display: "flex", alignItems: "center", justifyContent: "center", fontSize: 17, color: item.active ? "#fff" : "#888", flexShrink: 0 }}>{item.num}</div>
              <div>
                <div style={{ fontSize: 17, fontWeight: item.active ? 600 : 400, color: item.active ? "#1a1a1a" : "#888", marginBottom: 3 }}>{item.title}</div>
                <div style={{ fontSize: 16, color: "#aaa", lineHeight: 1.5 }}>{item.desc}</div>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Right - 회원가입 폼 */}
      <div style={{ flex: 1, padding: "48px 40px", display: "flex", flexDirection: "column", justifyContent: "center", background: "#fff", overflowY: "auto" }}>
        <div style={{ fontSize: 17, fontWeight: 500, color: "#888", letterSpacing: 0.5, textTransform: "uppercase", marginBottom: 6 }}>회원가입</div>
        <div style={{ fontSize: 15, color: "#555", marginBottom: 20 }}>아래 정보를 입력하여 계정을 만드세요</div>
        <hr style={{ border: "none", borderTop: "1px solid #e0e0e0", margin: "0 0 16px" }} />

        <div style={{ display: "flex", flexDirection: "column", gap: 14 }}>
          {/* 이름 + 성별 */}
          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 12 }}>
            <div>
              <label style={{ fontSize: 16, color: "#555", display: "block", marginBottom: 4 }}>이름</label>
              <input value={name} onChange={e => setName(e.target.value)} placeholder="홍길동"
                style={{ width: "100%", height: 34, border: "1.5px solid #ddd", borderRadius: 5, padding: "0 10px", fontSize: 17, boxSizing: "border-box", outline: "none" }} />
            </div>
            <div>
              <label style={{ fontSize: 16, color: "#555", display: "block", marginBottom: 4 }}>성별</label>
              <div style={{ display: "flex", gap: 8 }}>
                {(["male", "female"] as const).map(g => (
                  <button key={g} onClick={() => setGender(g)}
                    style={{ flex: 1, height: 34, border: `1.5px solid ${gender === g ? "#1a1a1a" : "#ddd"}`, borderRadius: 5, background: gender === g ? "#1a1a1a" : "#fff", color: gender === g ? "#fff" : "#555", fontSize: 17, cursor: "pointer" }}>
                    {g === "male" ? "남성" : "여성"}
                  </button>
                ))}
              </div>
            </div>
          </div>

          {/* 생년월일 + 휴대폰 */}
          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 12 }}>
            <div>
              <label style={{ fontSize: 16, color: "#555", display: "block", marginBottom: 4 }}>생년월일</label>
              <input type="date" value={birthDate} onChange={e => setBirthDate(e.target.value)}
                style={{ width: "100%", height: 34, border: "1.5px solid #ddd", borderRadius: 5, padding: "0 10px", fontSize: 17, boxSizing: "border-box", outline: "none" }} />
            </div>
            <div>
              <label style={{ fontSize: 16, color: "#555", display: "block", marginBottom: 4 }}>휴대폰 번호</label>
              <input value={phoneNumber} onChange={e => { setPhoneNumber(e.target.value); setPhoneServerError(""); }} placeholder="01012345678"
                style={{ width: "100%", height: 34, border: `1.5px solid ${phoneError || phoneServerError ? "#E24B4A" : "#ddd"}`, borderRadius: 5, padding: "0 10px", fontSize: 17, boxSizing: "border-box", outline: "none" }} />
              {phoneError && <p style={{ fontSize: 17, color: "#E24B4A", margin: "4px 0 0" }}>휴대폰 번호 형식을 확인해주세요.</p>}
              {phoneServerError && <p style={{ fontSize: 17, color: "#E24B4A", margin: "4px 0 0" }}>{phoneServerError}</p>}
            </div>
          </div>

          {/* 이메일 */}
          <div>
            <label style={{ fontSize: 16, color: "#555", display: "block", marginBottom: 4 }}>이메일 (필수)</label>
            <div style={{ display: "flex", gap: 8 }}>
              <input type="email" value={email} disabled={Boolean(googleDraft)} onChange={e => { setEmail(e.target.value); setEmailChecked(false); setEmailServerError(""); }} placeholder="example@email.com"
                style={{ flex: 1, height: 34, border: `1.5px solid ${emailServerError ? "#E24B4A" : "#ddd"}`, borderRadius: 5, padding: "0 10px", fontSize: 17, boxSizing: "border-box", outline: "none", background: googleDraft ? "#fafafa" : "#fff" }} />
              {!googleDraft && (
                <button onClick={handleEmailCheck}
                  style={{ height: 34, minWidth: 70, border: "1.5px solid #ddd", borderRadius: 5, background: "#f5f5f5", fontSize: 16, color: "#555", cursor: "pointer" }}>이메일 확인</button>
              )}
            </div>
            {googleDraft && <p style={{ fontSize: 17, color: "#2e7d32", margin: "4px 0 0" }}>Google 계정 이메일로 가입합니다.</p>}
            {googleDraft && (
              <button
                type="button"
                onClick={switchToEmailSignup}
                style={{ marginTop: 6, background: "none", border: "none", color: "#555", fontSize: 16, textDecoration: "underline", cursor: "pointer", padding: 0 }}
              >
                이메일로 직접 가입하기
              </button>
            )}
            {!googleDraft && emailChecked && <p style={{ fontSize: 17, color: "#2e7d32", margin: "4px 0 0" }}>✓ 이메일 형식이 확인되었습니다.</p>}
            {emailServerError && <p style={{ fontSize: 17, color: "#E24B4A", margin: "4px 0 0" }}>{emailServerError}</p>}
          </div>

          {/* 비밀번호 */}
          {!googleDraft && (
            <div>
              <label style={{ fontSize: 16, color: "#555", display: "block", marginBottom: 4 }}>비밀번호</label>
              <div style={{ position: "relative" }}>
                <input type={showPw ? "text" : "password"} value={password} onChange={e => setPassword(e.target.value)}
                  placeholder="영문+숫자+특수문자 조합 8자 이상"
                  style={{ width: "100%", height: 34, border: "1.5px solid #ddd", borderRadius: 5, padding: "0 36px 0 10px", fontSize: 17, boxSizing: "border-box", outline: "none" }} />
                <PasswordToggleButton isVisible={showPw} onToggle={() => setShowPw(!showPw)} />
              </div>
              {passwordError && <p style={{ fontSize: 17, color: "#E24B4A", margin: "4px 0 0" }}>{passwordError}</p>}
            </div>
          )}

          {/* 비밀번호 확인 */}
          {!googleDraft && (
            <div>
              <label style={{ fontSize: 16, color: "#555", display: "block", marginBottom: 4 }}>비밀번호 확인</label>
              <div style={{ position: "relative" }}>
                <input type={showPwConfirm ? "text" : "password"} value={passwordConfirm} onChange={e => setPasswordConfirm(e.target.value)}
                  placeholder="동일하게 입력"
                  style={{ width: "100%", height: 34, border: `1.5px solid ${pwMismatch ? "#E24B4A" : "#ddd"}`, borderRadius: 5, padding: "0 36px 0 10px", fontSize: 17, boxSizing: "border-box", outline: "none" }} />
                <PasswordToggleButton isVisible={showPwConfirm} onToggle={() => setShowPwConfirm(!showPwConfirm)} />
              </div>
              {pwMismatch && <p style={{ fontSize: 17, color: "#E24B4A", margin: "4px 0 0" }}>비밀번호가 일치하지 않습니다.</p>}
            </div>
          )}

          {/* 관리 질환 선택 */}
          <div>
            <label style={{ fontSize: 16, color: "#555", display: "block", marginBottom: 4 }}>관리 대상 질환 선택 *</label>
            <p style={{ fontSize: 17, color: "#888", margin: "0 0 10px" }}>1개 이상 선택해주세요.</p>
            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 8 }}>
              {DISEASES.map(d => (
                <label key={d} style={{ display: "flex", alignItems: "center", gap: 8, cursor: "pointer" }}>
                  <input type="checkbox" checked={selectedDiseases.includes(d)} onChange={() => toggleDisease(d)}
                    style={{ width: 14, height: 14, cursor: "pointer" }} />
                  <span style={{ fontSize: 15, color: "#333" }}>{d}</span>
                </label>
              ))}
            </div>
            {selectedDiseases.length === 0 && <p style={{ fontSize: 17, color: "#E24B4A", margin: "6px 0 0" }}>관리 대상 질환을 1개 이상 선택해주세요.</p>}
          </div>

          {formMessage && <p style={{ fontSize: 17, color: formMessage.includes("확인되었습니다") ? "#2e7d32" : "#E24B4A", margin: 0 }}>{formMessage}</p>}

          <button onClick={handleNext} disabled={!isValid || isLoading}
            style={{ width: "100%", height: 36, background: !isValid || isLoading ? "#ccc" : "#1a1a1a", color: "#fff", border: "none", borderRadius: 8, fontSize: 16, fontWeight: 600, cursor: !isValid || isLoading ? "not-allowed" : "pointer", marginTop: 6 }}>
            {isLoading ? "처리 중..." : "다음"}
          </button>

          <div style={{ textAlign: "right" }}>
            <span style={{ fontSize: 17, color: "#888" }}>이미 계정이 있으신가요? </span>
            <button onClick={() => onNavigate("/login")} style={{ background: "none", border: "none", fontSize: 17, color: "#1a1a1a", cursor: "pointer", fontWeight: 600 }}>로그인</button>
          </div>
        </div>
      </div>
    </div>
  );
}
