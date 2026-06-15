import { useEffect, useState } from "react";
import type { AppRoute } from "../../App";
import {
  googleSignup,
  login,
  requestEmailVerification,
  requestPasswordReset,
  resetPassword,
  storeOnboardingAccessToken,
  signup,
  storeAccessToken,
  verifyEmail,
  type SignUpPayload,
  type GoogleSignUpPayload,
} from "../../api/auth";
import { ApiError } from "../../api/client";
import { getPolicyDocument, type ConsentType } from "../../api/users";
import { PasswordToggleButton } from "../../components/common/PasswordToggleButton";
import { Stepper } from "../../components/common/Stepper";
import { icons } from "../../utils/iconAssets";

// ──────────────────────────────────────────────
// 약관 동의 페이지
// ──────────────────────────────────────────────
const SIGNUP_DRAFT_KEY = "auth.signupDraft";
const GOOGLE_SIGNUP_DRAFT_KEY = "auth.googleSignupDraft";
const SIGNUP_ERROR_KEY = "auth.signupError";
const ONBOARDING_PROFILE_KEY = "auth.onboardingProfile";
const EMAIL_VERIFY_ADDRESS_KEY = "auth.emailVerifyAddress";

function saveOnboardingProfile(profile: Pick<SignUpPayload, "birth_date" | "gender"> & { managed_diseases?: string[] }) {
  const serialized = JSON.stringify(profile);
  sessionStorage.setItem(ONBOARDING_PROFILE_KEY, serialized);
  localStorage.setItem(ONBOARDING_PROFILE_KEY, serialized);
}

function saveEmailVerifyAddress(email: string) {
  sessionStorage.setItem(EMAIL_VERIFY_ADDRESS_KEY, email);
  localStorage.setItem(EMAIL_VERIFY_ADDRESS_KEY, email);
}

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

function getApiErrorMessage(error: unknown, fallback: string) {
  if (!(error instanceof ApiError)) return fallback;
  if (typeof error.detail === "string") return error.detail;
  if (Array.isArray(error.detail)) return "입력값을 확인해주세요.";
  if (error.detail && typeof error.detail === "object") {
    const detail = error.detail as { message?: unknown; code?: unknown };
    if (typeof detail.message === "string") return detail.message;
  }
  return fallback;
}

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
  const [policyModal, setPolicyModal] = useState<{ title: string; content: string } | null>(null);
  const [isPolicyLoading, setIsPolicyLoading] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [submitMessage, setSubmitMessage] = useState("");

  const allRequired = checked.service && checked.privacy && checked.health;
  const allChecked = allRequired && checked.marketing;

  const toggleAll = () => {
    const next = !allChecked;
    setChecked({ service: next, privacy: next, health: next, marketing: next });
  };

  const openPolicy = async (type: ConsentType) => {
    setIsPolicyLoading(true);
    setPolicyModal({ title: "약관을 불러오는 중입니다.", content: "" });
    try {
      const document = await getPolicyDocument(type);
      setPolicyModal({ title: document.title, content: document.content });
    } catch {
      setPolicyModal({
        title: "약관 전문",
        content: "약관 내용을 불러오지 못했습니다. 잠시 후 다시 시도해주세요.",
      });
    } finally {
      setIsPolicyLoading(false);
    }
  };

  const handleSubmit = async () => {
    if (!allRequired || isSubmitting) return;

    const rawDraft = sessionStorage.getItem(SIGNUP_DRAFT_KEY);
    if (!rawDraft) {
      setSubmitMessage("회원가입 정보가 없습니다. 계정 정보 입력부터 다시 진행해주세요.");
      return;
    }

    setIsSubmitting(true);
    setSubmitMessage("");
    try {
      const parsedDraft = JSON.parse(rawDraft) as SignupDraft;
      const { managed_diseases: _managedDiseases, ...draft } = parsedDraft;
      if (parsedDraft.auth_provider === "GOOGLE") {
        if (!parsedDraft.id_token || !parsedDraft.name || !parsedDraft.gender || !parsedDraft.birth_date || !parsedDraft.phone_number) {
          setSubmitMessage("Google 가입 정보가 부족합니다. 계정 정보 입력부터 다시 진행해주세요.");
          return;
        }
        const payload: GoogleSignUpPayload = {
          id_token: parsedDraft.id_token,
          name: parsedDraft.name,
          gender: parsedDraft.gender,
          birth_date: parsedDraft.birth_date,
          phone_number: parsedDraft.phone_number,
          managed_diseases: _managedDiseases ?? [],
          consent_terms_version: "v1.0",
          consent_privacy_agreed: checked.privacy,
          consent_health_data: checked.health,
          consent_marketing: checked.marketing,
          remember_me: parsedDraft.remember_me,
        };
        let loginResponse;
        try {
          loginResponse = await googleSignup(payload);
        } catch (error) {
          if (
            error instanceof ApiError &&
            error.status === 401 &&
            String(error.detail ?? "").includes("Google")
          ) {
            sessionStorage.removeItem(SIGNUP_DRAFT_KEY);
            sessionStorage.removeItem(GOOGLE_SIGNUP_DRAFT_KEY);
            setSubmitMessage("Google 인증 시간이 만료되었습니다. 로그인 화면에서 Google 계정으로 다시 시작해주세요.");
            return;
          }
          throw error;
        }
        storeAccessToken(loginResponse.access_token, Boolean(parsedDraft.remember_me));
        saveOnboardingProfile({
          birth_date: payload.birth_date,
          gender: payload.gender,
          managed_diseases: _managedDiseases ?? [],
        });
        sessionStorage.removeItem(SIGNUP_DRAFT_KEY);
        sessionStorage.removeItem(GOOGLE_SIGNUP_DRAFT_KEY);
        onNavigate("/health-survey");
        return;
      }

      const payload: SignUpPayload = {
        ...(draft as SignUpPayload),
        managed_diseases: _managedDiseases ?? [],
        consent_terms_version: "v1.0",
        consent_privacy_agreed: checked.privacy,
        consent_health_data: checked.health,
        consent_marketing: checked.marketing,
      };
      await signup(payload);

      let loginResponse;
      try {
        loginResponse = await login({
          email: payload.email,
          password: payload.password,
          remember_me: false,
        });
      } catch (error) {
        setSubmitMessage(
          `회원가입은 완료됐지만 자동 로그인에 실패했습니다. 로그인 화면에서 다시 로그인해주세요. (${getApiErrorMessage(error, "자동 로그인 실패")})`,
        );
        return;
      }

      storeAccessToken(loginResponse.access_token);
      storeOnboardingAccessToken(loginResponse.access_token);
      saveEmailVerifyAddress(payload.email);
      saveOnboardingProfile({
        birth_date: payload.birth_date,
        gender: payload.gender,
        managed_diseases: _managedDiseases ?? [],
      });
      await requestEmailVerification();
      sessionStorage.removeItem(SIGNUP_DRAFT_KEY);
      onNavigate("/email-verify");
    } catch (error) {
      if (error instanceof ApiError && error.status === 409) {
        const message = String(error.detail ?? "이미 사용 중인 이메일 또는 휴대폰 번호입니다.");
        sessionStorage.setItem(SIGNUP_ERROR_KEY, message);
        onNavigate("/signup");
      } else if (error instanceof ApiError && error.status === 422) {
        const message = "입력값을 확인해주세요. 비밀번호, 생년월일, 휴대폰 번호 형식이 필요 조건과 맞아야 합니다.";
        sessionStorage.setItem(SIGNUP_ERROR_KEY, message);
        onNavigate("/signup");
      } else {
        setSubmitMessage(getApiErrorMessage(error, "회원가입 처리에 실패했습니다. 잠시 후 다시 시도해주세요."));
      }
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div style={{ minHeight: "100vh", background: "#fafafa", display: "flex", alignItems: "center", justifyContent: "center", padding: 40 }}>
      <div style={{ width: "100%", maxWidth: 680 }}>
        <div style={{ textAlign: "center", marginBottom: 24 }}>
          <img src="/logo.png" alt="All4Health" style={{ height: 40, margin: "0 auto 16px", display: "block" }} onError={e => { (e.target as HTMLImageElement).style.display = "none"; }} />
          <h2 style={{ fontSize: 18, fontWeight: 600, color: "#1a1a1a", margin: "0 0 8px" }}>회원가입</h2>
          <p style={{ fontSize: 15, color: "#888", margin: 0 }}>서비스 이용을 위한 약관에 동의해주세요</p>
        </div>

        <Stepper steps={["계정정보", "약관동의", "이메일인증", "건강설문", "완료"]} current={1} />

        <div style={{ background: "#fff", border: "1px solid #e0e0e0", borderRadius: 10, padding: 24 }}>
          <h3 style={{ fontSize: 16, fontWeight: 600, color: "#1a1a1a", margin: "0 0 16px" }}>약관 동의</h3>

          {/* 전체 동의 */}
          <label style={{ display: "flex", alignItems: "center", gap: 8, cursor: "pointer", marginBottom: 14 }}>
            <input type="checkbox" checked={allChecked} onChange={toggleAll} style={{ width: 16, height: 16, cursor: "pointer" }} />
            <span style={{ fontSize: 16, fontWeight: 600, color: "#1a1a1a" }}>전체 동의</span>
          </label>
          <hr style={{ border: "none", borderTop: "1px solid #e0e0e0", margin: "0 0 14px" }} />

          <div style={{ display: "flex", flexDirection: "column", gap: 10 }}>
            {[
              { key: "service" as const, label: "[필수] 서비스 이용약관", policyType: "TOS" as const },
              { key: "privacy" as const, label: "[필수] 개인정보 처리방침", policyType: "PRIVACY" as const },
              { key: "health" as const, label: "[필수] 건강 데이터 수집·이용 동의", policyType: "HEALTH_DATA" as const },
              { key: "marketing" as const, label: "[선택] 마케팅 정보 수신 동의", policyType: "MARKETING" as const },
            ].map(item => (
              <div key={item.key} style={{ display: "flex", alignItems: "center", justifyContent: "space-between" }}>
                <label style={{ display: "flex", alignItems: "center", gap: 8, cursor: "pointer" }}>
                  <input type="checkbox" checked={checked[item.key]} onChange={() => setChecked(prev => ({ ...prev, [item.key]: !prev[item.key] }))}
                    style={{ width: 14, height: 14, cursor: "pointer" }} />
                  <span style={{ fontSize: 15, color: "#333" }}>{item.label}</span>
                </label>
                <button
                  type="button"
                  onClick={() => openPolicy(item.policyType)}
                  style={{ background: "none", border: "none", fontSize: 16, color: "#888", cursor: "pointer" }}
                >
                  보기
                </button>
              </div>
            ))}
          </div>

          <p style={{ fontSize: 17, color: "#aaa", textAlign: "right", margin: "14px 0 20px" }}>적용 약관 버전: v1.0</p>

          {submitMessage && <p style={{ fontSize: 17, color: "#E24B4A", margin: "0 0 10px" }}>{submitMessage}</p>}
          <button onClick={handleSubmit} disabled={!allRequired || isSubmitting}
            style={{ width: "100%", height: 40, background: allRequired && !isSubmitting ? "#1a1a1a" : "#ccc", color: "#fff", border: "none", borderRadius: 8, fontSize: 17, fontWeight: 600, cursor: allRequired && !isSubmitting ? "pointer" : "not-allowed" }}>
            {isSubmitting ? "가입 및 인증 메일 발송 중..." : "가입하고 인증 메일 받기"}
          </button>
        </div>

        <p style={{ textAlign: "center", marginTop: 16, fontSize: 17, color: "#888" }}>
          이미 계정이 있으신가요? {" "}
          <button onClick={() => onNavigate("/login")} style={{ background: "none", border: "none", fontSize: 17, color: "#1a1a1a", cursor: "pointer", fontWeight: 600 }}>로그인</button>
        </p>
      </div>
      {policyModal && (
        <div style={{ position: "fixed", inset: 0, background: "rgba(0,0,0,0.35)", display: "flex", alignItems: "center", justifyContent: "center", padding: 24, zIndex: 1000 }}>
          <div style={{ width: "100%", maxWidth: 560, maxHeight: "80vh", background: "#fff", borderRadius: 12, padding: 24, overflow: "auto" }}>
            <h3 style={{ fontSize: 16, fontWeight: 700, margin: "0 0 12px" }}>{policyModal.title}</h3>
            <div style={{ whiteSpace: "pre-wrap", fontSize: 15, lineHeight: 1.7, color: "#444", minHeight: 120 }}>
              {isPolicyLoading ? "약관을 불러오는 중입니다." : policyModal.content}
            </div>
            <button
              type="button"
              onClick={() => setPolicyModal(null)}
              style={{ width: "100%", height: 38, marginTop: 18, border: "none", borderRadius: 8, background: "#1a1a1a", color: "#fff", fontSize: 16, cursor: "pointer" }}
            >
              확인
            </button>
          </div>
        </div>
      )}
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
  const [message, setMessage] = useState("");
  const [verifyStatus, setVerifyStatus] = useState<"IDLE" | "VERIFYING" | "SUCCESS" | "FAILED">("IDLE");
  const [targetEmail, setTargetEmail] = useState("");
  const verificationToken = new URLSearchParams(window.location.search).get("token");
  const isLocalDev = import.meta.env.DEV;

  useEffect(() => {
    setTargetEmail(sessionStorage.getItem(EMAIL_VERIFY_ADDRESS_KEY) ?? localStorage.getItem(EMAIL_VERIFY_ADDRESS_KEY) ?? "");
  }, []);

  useEffect(() => {
    if (!verificationToken) return;
    setVerifyStatus("VERIFYING");
    verifyEmail(verificationToken)
      .then(() => {
        setVerifyStatus("SUCCESS");
        setMessage("이메일 인증이 완료되었습니다.");
        sessionStorage.removeItem(EMAIL_VERIFY_ADDRESS_KEY);
        localStorage.removeItem(EMAIL_VERIFY_ADDRESS_KEY);
      })
      .catch(() => {
        setVerifyStatus("FAILED");
        setMessage("인증 링크가 만료되었거나 유효하지 않습니다. 인증 메일을 다시 요청해주세요.");
      });
  }, [verificationToken]);

  const startCooldown = () => {
    setResendCooldown(60);
    const timer = window.setInterval(() => {
      setResendCooldown(prev => {
        if (prev <= 1) {
          window.clearInterval(timer);
          return 0;
        }
        return prev - 1;
      });
    }, 1000);
  };

  const handleResend = async () => {
    setMessage("");
    try {
      await requestEmailVerification();
      setMessage("인증 메일을 다시 발송했습니다.");
      startCooldown();
    } catch (error) {
      setMessage(getApiErrorMessage(error, "인증 메일 재발송에 실패했습니다. 로그인 상태를 확인해주세요."));
    }
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
        <p style={{ fontSize: 15, color: "#555", lineHeight: 1.6, margin: "0 0 24px" }}>
          {targetEmail || "가입한 이메일"} 으로 인증 메일을 발송했습니다.<br />메일함을 확인하고 인증 링크를 클릭해주세요.
        </p>
        <hr style={{ border: "none", borderTop: "1px solid #ddd", margin: "0 0 20px" }} />
        {[
          { title: "메일이 오지 않았나요?", desc: "스팸 메일함도 확인해보세요", icon: icons.emailMissing },
          { title: "링크 유효 시간", desc: "인증 링크는 발송 후 24시간 동안 유효합니다", icon: icons.linkValidTime },
          { title: "이메일 변경 필요 시", desc: "아래 '이전으로 돌아가기' 버튼을 눌러주세요", icon: icons.emailChange },
        ].map((item, i) => (
          <div key={i} style={{ display: "flex", gap: 12, alignItems: "flex-start", marginBottom: 16 }}>
            <div style={{ width: 28, height: 28, background: "#4da463", borderRadius: 5, flexShrink: 0, display: "flex", alignItems: "center", justifyContent: "center", overflow: "hidden" }}>
              <img src={item.icon} alt="" aria-hidden="true" style={{ width: 24, height: 24, objectFit: "contain" }} />
            </div>
            <div>
              <div style={{ fontSize: 17, fontWeight: 500, color: "#1a1a1a", marginBottom: 3 }}>{item.title}</div>
              <div style={{ fontSize: 16, color: "#888", lineHeight: 1.5 }}>{item.desc}</div>
            </div>
          </div>
        ))}
      </div>

      {/* Right */}
      <div style={{ flex: 1, padding: "48px 40px", display: "flex", flexDirection: "column", justifyContent: "center", background: "#fff" }}>
        <div style={{ fontSize: 17, fontWeight: 500, color: "#888", letterSpacing: 0.5, textTransform: "uppercase", marginBottom: 6 }}>이메일 인증</div>
        <div style={{ fontSize: 15, color: "#555", marginBottom: 20 }}>
          {verificationToken ? "인증 링크를 확인하고 있습니다" : "아래 절차에 따라 인증을 완료해주세요"}
        </div>
        <hr style={{ border: "none", borderTop: "1px solid #e0e0e0", margin: "0 0 20px" }} />

        <div style={{ display: "flex", flexDirection: "column", alignItems: "center", marginBottom: 24 }}>
          <div style={{ width: 56, height: 56, borderRadius: "50%", background: "#f0f0f0", display: "flex", alignItems: "center", justifyContent: "center", marginBottom: 14, fontSize: 24 }}>📧</div>
          <p style={{ fontSize: 15, color: "#555", textAlign: "center" }}>
            {verifyStatus === "VERIFYING"
              ? "이메일 인증을 처리하는 중입니다."
              : verifyStatus === "SUCCESS"
                ? "이메일 인증이 완료되었습니다."
                : "인증 메일을 확인하고 링크를 클릭해주세요."}
          </p>
        </div>

        <div style={{ background: "#fff", border: "1px solid #e0e0e0", borderRadius: 8, padding: 16, marginBottom: 20 }}>
          <div style={{ fontSize: 17, fontWeight: 500, color: "#555", marginBottom: 12 }}>인증 절차</div>
          <hr style={{ border: "none", borderTop: "1px solid #eee", margin: "0 0 10px" }} />
          {["이메일 수신 확인", "인증 링크 클릭", "인증 완료"].map((step, i) => (
            <div key={step} style={{ display: "flex", alignItems: "center", gap: 10, padding: "8px 0" }}>
              <div style={{ width: 16, height: 16, borderRadius: "50%", border: `1.5px solid ${i === 0 ? "#1a1a1a" : "#ddd"}`, display: "flex", alignItems: "center", justifyContent: "center", fontSize: 9, flexShrink: 0 }} />
              <span style={{ fontSize: 17, color: "#333" }}>{step}</span>
            </div>
          ))}
        </div>

        <button onClick={handleResend} disabled={resendCooldown > 0 || verifyStatus === "SUCCESS"}
          style={{ width: "100%", height: 36, border: "1.5px solid #ddd", borderRadius: 8, background: "#fff", fontSize: 15, color: resendCooldown > 0 ? "#aaa" : "#333", cursor: resendCooldown > 0 ? "not-allowed" : "pointer", marginBottom: 10 }}>
          {resendCooldown > 0 ? `재발송 가능까지 ${resendCooldown}초` : "이메일 재발송"}
        </button>
        {message && <p style={{ fontSize: 17, color: message.includes("실패") ? "#E24B4A" : "#2e7d32", margin: "0 0 10px" }}>{message}</p>}
        {isLocalDev && verifyStatus !== "SUCCESS" && (
          <div style={{ border: "1px solid #f0d58c", background: "#fff8e1", borderRadius: 8, padding: 12, marginBottom: 10 }}>
            <p style={{ fontSize: 17, color: "#6d5400", lineHeight: 1.6, margin: "0 0 8px" }}>
              로컬 개발 환경에서 SMTP를 설정하지 않은 경우 인증 메일을 받을 수 없습니다. 화면 흐름 확인이 필요할 때만 건강 설문으로 이동하세요.
            </p>
            <button
              type="button"
              onClick={() => onNavigate("/health-survey")}
              style={{ width: "100%", height: 34, border: "none", borderRadius: 8, background: "#8A6D00", color: "#fff", fontSize: 15, cursor: "pointer" }}
            >
              로컬 테스트용: 건강 설문으로 이동
            </button>
          </div>
        )}
        <button onClick={() => onNavigate("/signup")}
          style={{ width: "100%", height: 36, border: "1.5px solid #ddd", borderRadius: 8, background: "#fff", fontSize: 15, color: "#333", cursor: "pointer", marginBottom: 20 }}>
          이전으로 돌아가기
        </button>

        {verifyStatus === "SUCCESS" && (
          <button onClick={() => onNavigate("/health-survey")}
            style={{ width: "100%", height: 36, background: "#1a1a1a", color: "#fff", border: "none", borderRadius: 8, fontSize: 15, cursor: "pointer", marginBottom: 16 }}>
            건강 설문으로 이동
          </button>
        )}

        <p style={{ textAlign: "center", fontSize: 17, color: "#888", cursor: "pointer", margin: 0 }}
          onClick={() => onNavigate("/login")}>로그인으로 돌아가기</p>
      </div>
      {(verifyStatus === "SUCCESS" || verifyStatus === "FAILED") && (
        <div style={{ position: "fixed", inset: 0, background: "rgba(0,0,0,0.35)", display: "flex", alignItems: "center", justifyContent: "center", padding: 24 }}>
          <div style={{ width: "100%", maxWidth: 420, background: "#fff", borderRadius: 12, padding: 28, textAlign: "center", boxShadow: "0 18px 50px rgba(0,0,0,0.18)" }}>
            <div
              style={{
                width: 56,
                height: 56,
                borderRadius: "50%",
                background: verifyStatus === "SUCCESS" ? "#2e7d32" : "#E24B4A",
                color: "#fff",
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                margin: "0 auto 18px",
                fontSize: 24,
                fontWeight: 700,
              }}
            >
              {verifyStatus === "SUCCESS" ? "✓" : "!"}
            </div>
            <h3 style={{ fontSize: 18, fontWeight: 700, color: "#1a1a1a", margin: "0 0 8px" }}>
              {verifyStatus === "SUCCESS" ? "이메일 인증 완료" : "이메일 인증 실패"}
            </h3>
            <p style={{ fontSize: 16, color: "#555", lineHeight: 1.6, margin: "0 0 22px" }}>
              {verifyStatus === "SUCCESS"
                ? "이메일 인증이 완료되었습니다. 이제 건강 설문을 입력하고 서비스를 시작할 수 있습니다."
                : "인증 링크가 만료되었거나 유효하지 않습니다. 인증 메일을 다시 요청해주세요."}
            </p>
            {verifyStatus === "SUCCESS" ? (
              <button
                type="button"
                onClick={() => onNavigate("/health-survey")}
                style={{ width: "100%", height: 40, border: "none", borderRadius: 8, background: "#1a1a1a", color: "#fff", fontSize: 17, fontWeight: 600, cursor: "pointer" }}
              >
                건강 설문으로 이동
              </button>
            ) : (
              <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
                <button
                  type="button"
                  onClick={handleResend}
                  disabled={resendCooldown > 0}
                  style={{ width: "100%", height: 40, border: "none", borderRadius: 8, background: resendCooldown > 0 ? "#ccc" : "#1a1a1a", color: "#fff", fontSize: 17, fontWeight: 600, cursor: resendCooldown > 0 ? "not-allowed" : "pointer" }}
                >
                  {resendCooldown > 0 ? `재발송 가능까지 ${resendCooldown}초` : "인증 메일 재발송"}
                </button>
                <button
                  type="button"
                  onClick={() => onNavigate("/login")}
                  style={{ width: "100%", height: 40, border: "1.5px solid #ddd", borderRadius: 8, background: "#fff", color: "#333", fontSize: 16, cursor: "pointer" }}
                >
                  로그인으로 돌아가기
                </button>
              </div>
            )}
          </div>
        </div>
      )}
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
  const resetToken = new URLSearchParams(window.location.search).get("token");
  const [step, setStep] = useState<1 | 2 | 3 | 4>(resetToken ? 3 : 1);
  const [email, setEmail] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [showPw, setShowPw] = useState(false);
  const [showConfirm, setShowConfirm] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [errorMessage, setErrorMessage] = useState("");

  const pwMismatch = confirmPassword.length > 0 && newPassword !== confirmPassword;
  const passwordError = newPassword ? validatePassword(newPassword) : "";
  const resetPasswordInvalid = !newPassword || !confirmPassword || Boolean(passwordError) || pwMismatch;

  const ProcessGuide = () => (
    <div style={{ width: "45%", background: "#f5f5f5", padding: "48px 40px", display: "flex", flexDirection: "column", justifyContent: "center", borderRight: "1px solid #e0e0e0" }}>
      <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 24 }}>
        <span style={{ fontSize: 16, fontWeight: 700, color: "#1a1a1a" }}>All4Health</span>
      </div>
      <h2 style={{ fontSize: 20, fontWeight: 600, color: "#1a1a1a", margin: "0 0 12px" }}>비밀번호를<br />재설정합니다</h2>
      <p style={{ fontSize: 15, color: "#555", lineHeight: 1.6, margin: "0 0 8px" }}>재설정 링크는 발송 후 1시간 동안 유효합니다.</p>
      <hr style={{ border: "none", borderTop: "1px solid #ddd", margin: "20px 0" }} />
      {[
        { num: "1", title: "이메일 입력", desc: "가입 시 사용한 이메일 주소를 입력하세요" },
        { num: "2", title: "인증 메일 확인", desc: "받은편지함에서 재설정 링크를 클릭하세요" },
        { num: "3", title: "새 비밀번호 설정", desc: "안전한 새 비밀번호로 계정을 보호하세요" },
      ].map((item, i) => (
        <div key={item.num} style={{ display: "flex", gap: 12, alignItems: "flex-start", marginBottom: 16 }}>
          <div style={{ width: 28, height: 28, borderRadius: "50%", border: "1.5px solid #ddd", background: step - 1 > i ? "#1a1a1a" : "#f0f0f0", display: "flex", alignItems: "center", justifyContent: "center", fontSize: 17, color: step - 1 > i ? "#fff" : "#888", flexShrink: 0 }}>
            {step - 1 > i ? "✓" : item.num}
          </div>
          <div>
            <div style={{ fontSize: 17, fontWeight: 500, color: "#1a1a1a", marginBottom: 3 }}>{item.title}</div>
            <div style={{ fontSize: 16, color: "#888", lineHeight: 1.5 }}>{item.desc}</div>
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
          <p style={{ fontSize: 15, color: "#555", lineHeight: 1.6, margin: "0 0 24px" }}>새 비밀번호로 로그인해주세요.</p>
          <button onClick={() => onNavigate("/login")}
            style={{ width: "100%", height: 40, background: "#1a1a1a", color: "#fff", border: "none", borderRadius: 8, fontSize: 17, fontWeight: 600, cursor: "pointer" }}>
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
        <div style={{ fontSize: 17, fontWeight: 500, color: "#888", letterSpacing: 0.5, textTransform: "uppercase", marginBottom: 6 }}>비밀번호 재설정</div>
        <hr style={{ border: "none", borderTop: "1px solid #e0e0e0", margin: "16px 0" }} />

        {step === 1 && (
          <div style={{ display: "flex", flexDirection: "column", gap: 14 }}>
            <div style={{ fontSize: 15, color: "#555", marginBottom: 4 }}>가입 시 사용한 이메일 주소를 입력하세요</div>
            <div>
              <label style={{ fontSize: 16, color: "#555", display: "block", marginBottom: 4 }}>이메일</label>
              <input type="email" value={email} onChange={e => setEmail(e.target.value)} placeholder="example@email.com"
                style={{ width: "100%", height: 34, border: "1.5px solid #ddd", borderRadius: 5, padding: "0 10px", fontSize: 17, boxSizing: "border-box", outline: "none" }} />
              <p style={{ fontSize: 17, color: "#aaa", margin: "4px 0 0" }}>가입된 이메일이 아니더라도 동일한 안내를 드립니다.</p>
            </div>
            <button
              onClick={async () => {
                setErrorMessage("");
                if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) {
                  setErrorMessage("이메일 입력이 잘못되었습니다.");
                  return;
                }
                setIsSubmitting(true);
                try {
                  await requestPasswordReset(email);
                  setStep(2);
                } catch (error) {
                  setErrorMessage(getApiErrorMessage(error, "메일 발송 요청에 실패했습니다. 잠시 후 다시 시도해주세요."));
                } finally {
                  setIsSubmitting(false);
                }
              }}
              disabled={!email || isSubmitting}
              style={{ width: "100%", height: 36, background: email ? "#1a1a1a" : "#ccc", color: "#fff", border: "none", borderRadius: 8, fontSize: 16, fontWeight: 600, cursor: email ? "pointer" : "not-allowed" }}>
              {isSubmitting ? "발송 중..." : "인증 메일 발송"}
            </button>
            {errorMessage && <p style={{ fontSize: 17, color: "#E24B4A", margin: 0 }}>{errorMessage}</p>}
            <hr style={{ border: "none", borderTop: "1px solid #eee" }} />
            <p style={{ textAlign: "center", fontSize: 17, color: "#888", cursor: "pointer" }} onClick={() => onNavigate("/login")}>로그인으로 돌아가기</p>
          </div>
        )}

        {step === 2 && (
          <div style={{ display: "flex", flexDirection: "column", gap: 14 }}>
            <div style={{ fontSize: 15, color: "#555" }}>이메일을 확인해주세요</div>
            <p style={{ fontSize: 16, color: "#333", lineHeight: 1.6, margin: 0 }}>
              {email}으로 재설정 링크를 발송했습니다. 메일함을 확인하고 링크를 클릭해주세요.
            </p>
            <p style={{ fontSize: 17, color: "#aaa", margin: 0 }}>링크는 발송 후 1시간 동안 유효합니다. 스팸 메일함도 확인해보세요.</p>
            <button
              onClick={async () => {
                try {
                  await requestPasswordReset(email);
                } catch (error) {
                  setErrorMessage(getApiErrorMessage(error, "이메일 재발송에 실패했습니다."));
                }
              }}
              style={{ width: "100%", height: 36, background: "#1a1a1a", color: "#fff", border: "none", borderRadius: 8, fontSize: 16, cursor: "pointer" }}
            >
              이메일 재발송
            </button>
            <hr style={{ border: "none", borderTop: "1px solid #eee" }} />
            <p style={{ textAlign: "center", fontSize: 17, color: "#888", cursor: "pointer" }} onClick={() => onNavigate("/login")}>로그인으로 돌아가기</p>
          </div>
        )}

        {step === 3 && (
          <div style={{ display: "flex", flexDirection: "column", gap: 14 }}>
            <div style={{ fontSize: 15, color: "#555" }}>새 비밀번호를 입력해주세요</div>
            <div>
              <label style={{ fontSize: 16, color: "#555", display: "block", marginBottom: 4 }}>새 비밀번호</label>
              <div style={{ position: "relative" }}>
                <input type={showPw ? "text" : "password"} value={newPassword} onChange={e => setNewPassword(e.target.value)} placeholder="영문+숫자+특수문자 조합 8자 이상"
                  style={{ width: "100%", height: 34, border: `1.5px solid ${passwordError ? "#E24B4A" : "#ddd"}`, borderRadius: 5, padding: "0 36px 0 10px", fontSize: 17, boxSizing: "border-box", outline: "none" }} />
                <PasswordToggleButton isVisible={showPw} onToggle={() => setShowPw(!showPw)} />
              </div>
              {passwordError && <p style={{ fontSize: 17, color: "#E24B4A", margin: "4px 0 0" }}>{passwordError}</p>}
            </div>
            <div>
              <label style={{ fontSize: 16, color: "#555", display: "block", marginBottom: 4 }}>새 비밀번호 확인</label>
              <div style={{ position: "relative" }}>
                <input type={showConfirm ? "text" : "password"} value={confirmPassword} onChange={e => setConfirmPassword(e.target.value)} placeholder="동일하게 입력"
                  style={{ width: "100%", height: 34, border: `1.5px solid ${pwMismatch ? "#E24B4A" : "#ddd"}`, borderRadius: 5, padding: "0 36px 0 10px", fontSize: 17, boxSizing: "border-box", outline: "none" }} />
                <PasswordToggleButton isVisible={showConfirm} onToggle={() => setShowConfirm(!showConfirm)} />
              </div>
              {pwMismatch && <p style={{ fontSize: 17, color: "#E24B4A", margin: "4px 0 0" }}>비밀번호가 일치하지 않습니다.</p>}
            </div>
            <button
              onClick={async () => {
                if (!resetToken) {
                  setErrorMessage("메일의 재설정 링크로 접속해야 비밀번호를 변경할 수 있습니다.");
                  return;
                }
                if (passwordError) {
                  setErrorMessage(passwordError);
                  return;
                }
                setErrorMessage("");
                setIsSubmitting(true);
                try {
                  await resetPassword(resetToken, newPassword, confirmPassword);
                  setStep(4);
                } catch (error) {
                  const message =
                    error instanceof ApiError && error.status === 410
                      ? "재설정 링크가 만료되었습니다. 다시 요청해주세요."
                      : "비밀번호 변경에 실패했습니다. 입력값을 확인해주세요.";
                  setErrorMessage(message);
                } finally {
                  setIsSubmitting(false);
                }
              }}
              disabled={resetPasswordInvalid || isSubmitting}
              style={{ width: "100%", height: 36, background: resetPasswordInvalid ? "#ccc" : "#1a1a1a", color: "#fff", border: "none", borderRadius: 8, fontSize: 16, fontWeight: 600, cursor: resetPasswordInvalid ? "not-allowed" : "pointer" }}>
              {isSubmitting ? "변경 중..." : "비밀번호 변경하기"}
            </button>
            {errorMessage && <p style={{ fontSize: 17, color: "#E24B4A", margin: 0 }}>{errorMessage}</p>}
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
  const nextActions: Array<{ icon: string; label: string; route: AppRoute }> = [
    { icon: "🎯", label: "건강 목표 설정하기", route: "/health/goal" },
    { icon: "📊", label: "추가 건강 수치 입력하기", route: "/health/vitals/input" },
    { icon: "🏆", label: "챌린지 참여하기", route: "/challenges/list" },
  ];

  return (
    <div style={{ minHeight: "100vh", background: "#fafafa", display: "flex", alignItems: "center", justifyContent: "center", padding: 40 }}>
      <div style={{ width: "100%", maxWidth: 680 }}>
        <div style={{ textAlign: "center", marginBottom: 24 }}>
          <img src="/logo.png" alt="All4Health" style={{ height: 40, margin: "0 auto 16px", display: "block" }} onError={e => { (e.target as HTMLImageElement).style.display = "none"; }} />
        </div>

        <Stepper steps={["계정정보", "약관동의", "이메일인증", "건강설문", "완료"]} current={4} />

        <div style={{ background: "#fff", border: "1px solid #e0e0e0", borderRadius: 10, padding: 28, textAlign: "center" }}>
          <div style={{ width: 72, height: 72, borderRadius: "50%", background: "#f0f0f0", border: "2px solid #ddd", margin: "0 auto 20px", display: "flex", alignItems: "center", justifyContent: "center", fontSize: 32 }}>✓</div>
          <div style={{ display: "inline-block", padding: "4px 12px", background: "#2e7d32", borderRadius: 12, fontSize: 17, color: "#fff", marginBottom: 14 }}>✓ 이메일 인증 완료</div>
          <h2 style={{ fontSize: 20, fontWeight: 600, color: "#1a1a1a", margin: "0 0 10px" }}>가입이 완료되었습니다!</h2>
          <p style={{ fontSize: 15, color: "#888", margin: "0 0 24px" }}>All4Health와 함께 건강한 생활을 시작해보세요.</p>

          <hr style={{ border: "none", borderTop: "1px solid #e0e0e0", margin: "0 0 20px" }} />

          <div style={{ textAlign: "left", marginBottom: 24 }}>
            <p style={{ fontSize: 17, color: "#888", marginBottom: 12 }}>다음 단계로 진행하세요:</p>
            {nextActions.map(item => (
              <button
                key={item.label}
                type="button"
                onClick={() => onNavigate(item.route)}
                style={{ width: "100%", padding: "12px 16px", border: "1.5px solid #e0e0e0", borderRadius: 8, background: "#fafafa", display: "flex", alignItems: "center", justifyContent: "space-between", cursor: "pointer", marginBottom: 8, textAlign: "left" }}
              >
                <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
                  <span style={{ fontSize: 16 }}>{item.icon}</span>
                  <span style={{ fontSize: 17, fontWeight: 500, color: "#1a1a1a" }}>{item.label}</span>
                </div>
                <span style={{ fontSize: 16, color: "#aaa" }}>›</span>
              </button>
            ))}
          </div>

          <button onClick={() => onNavigate("/home")}
            style={{ width: "100%", height: 40, background: "#1a1a1a", color: "#fff", border: "none", borderRadius: 8, fontSize: 17, fontWeight: 600, cursor: "pointer" }}>
            홈으로 이동
          </button>
        </div>
      </div>
    </div>
  );
}
