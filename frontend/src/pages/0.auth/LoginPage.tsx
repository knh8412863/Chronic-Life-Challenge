import { useCallback, useEffect, useRef, useState } from "react";
import type { AppRoute } from "../../App";
import { ApiError } from "../../api/client";
import { googleLogin, login, storeAccessToken } from "../../api/auth";
import { getLatestHealthSurveyInput } from "../../api/predictions";
import { getCurrentUser } from "../../api/users";
import { PasswordToggleButton } from "../../components/common/PasswordToggleButton";
import { icons } from "../../utils/iconAssets";

interface LoginPageProps {
  onLogin: () => void;
  onNavigate?: (route: AppRoute) => void;
}

type GoogleCredentialResponse = {
  credential?: string;
};

const GOOGLE_SIGNUP_DRAFT_KEY = "auth.googleSignupDraft";
const ONBOARDING_PROFILE_KEY = "auth.onboardingProfile";

function extractRemainingAttempts(detail: unknown): number | null {
  if (typeof detail !== "string") return null;
  const match = detail.match(/\((\d+)회 시도 남음\)/);
  return match ? Number(match[1]) : null;
}

function decodeGoogleCredential(credential: string): { email?: string; name?: string; picture?: string } {
  try {
    const payload = credential.split(".")[1];
    const normalized = payload.replace(/-/g, "+").replace(/_/g, "/");
    const decoded = JSON.parse(window.atob(normalized.padEnd(Math.ceil(normalized.length / 4) * 4, "=")));
    return {
      email: typeof decoded.email === "string" ? decoded.email : undefined,
      name: typeof decoded.name === "string" ? decoded.name : undefined,
      picture: typeof decoded.picture === "string" ? decoded.picture : undefined,
    };
  } catch {
    return {};
  }
}

function toSignupName(value?: string) {
  const normalized = (value ?? "")
    .replace(/[^\uAC00-\uD7A3a-zA-Z0-9\s]/g, "")
    .replace(/\s+/g, " ")
    .trim();
  return normalized.length >= 2 ? normalized.slice(0, 20) : "";
}

declare global {
  interface Window {
    google?: {
      accounts?: {
        id?: {
          initialize: (config: {
            client_id: string;
            callback: (response: GoogleCredentialResponse) => void;
          }) => void;
          renderButton: (parent: HTMLElement, options: Record<string, string | number | boolean>) => void;
        };
      };
    };
  }
}

export function LoginPage({ onLogin, onNavigate }: LoginPageProps) {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [errorCount, setErrorCount] = useState(0); // 0: 기본, 양수: 남은 횟수, -1: 잠금
  const [rememberMe, setRememberMe] = useState(false);
  const [errorMessage, setErrorMessage] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [isGoogleLoading, setIsGoogleLoading] = useState(false);
  const googleButtonRef = useRef<HTMLDivElement | null>(null);
  const googleClientId = import.meta.env.VITE_GOOGLE_CLIENT_ID as string | undefined;

  const handleLogin = async () => {
    if (!email || !password) return;
    setIsLoading(true);
    setErrorMessage("");
    try {
      const response = await login({ email, password, remember_me: rememberMe });
      storeAccessToken(response.access_token, rememberMe);
      setErrorCount(0);
      onLogin();
    } catch (error) {
      if (error instanceof ApiError) {
        if (error.status === 423 || error.status === 429) {
          setErrorCount(-1);
          setErrorMessage(
            error.message ||
            "비밀번호 입력 실패가 반복되어 계정이 일시적으로 잠겼습니다. 잠시 후 다시 시도해주세요.",
          );
          return;
        }

        const remainingAttempts = extractRemainingAttempts(error.detail);
        if (remainingAttempts !== null) {
          setErrorCount(remainingAttempts > 0 ? remainingAttempts : -1);
          setErrorMessage(error.message);
          return;
        }

        setErrorCount(0);
        setErrorMessage(error.message || "이메일 또는 비밀번호가 올바르지 않습니다.");
      } else {
        setErrorCount(0);
        setErrorMessage("이메일 또는 비밀번호가 올바르지 않습니다.");
      }
    } finally {
      setIsLoading(false);
    }
  };

  const handleGoogleCredential = useCallback(
    async (response: GoogleCredentialResponse) => {
      if (!response.credential) {
        setErrorMessage("Google 인증 정보를 받지 못했습니다. 다시 시도해 주세요.");
        return;
      }

      setIsGoogleLoading(true);
      setErrorMessage("");
      try {
        const loginResponse = await googleLogin({
          id_token: response.credential,
          remember_me: rememberMe,
        });
        storeAccessToken(loginResponse.access_token, rememberMe);
        try {
          await getLatestHealthSurveyInput(loginResponse.access_token);
        } catch (error) {
          if (error instanceof ApiError && error.status === 404) {
            const user = await getCurrentUser(loginResponse.access_token);
            const onboardingProfile = JSON.stringify({
              birth_date: user.birthday,
              gender: user.gender,
              managed_diseases: user.managed_diseases,
            });
            sessionStorage.setItem(ONBOARDING_PROFILE_KEY, onboardingProfile);
            localStorage.setItem(ONBOARDING_PROFILE_KEY, onboardingProfile);
            onNavigate?.("/health-survey");
            return;
          }
        }
        setErrorCount(0);
        onLogin();
      } catch (error) {
        if (error instanceof ApiError) {
          if (error.status === 404) {
            const profile = decodeGoogleCredential(response.credential);
            sessionStorage.setItem(
              GOOGLE_SIGNUP_DRAFT_KEY,
              JSON.stringify({
                id_token: response.credential,
                email: profile.email ?? "",
                name: toSignupName(profile.name),
                picture: profile.picture ?? "",
                remember_me: rememberMe,
              }),
            );
            onNavigate?.("/signup");
            return;
          }
          setErrorMessage(error.message || "Google 로그인에 실패했습니다.");
        } else {
          setErrorMessage("Google 로그인에 실패했습니다.");
        }
      } finally {
        setIsGoogleLoading(false);
      }
    },
    [onLogin, onNavigate, rememberMe],
  );

  useEffect(() => {
    const container = googleButtonRef.current;
    if (!googleClientId || !container) return;

    const renderGoogleButton = () => {
      const googleId = window.google?.accounts?.id;
      if (!googleId || !googleButtonRef.current) return;

      googleButtonRef.current.innerHTML = "";
      googleId.initialize({
        client_id: googleClientId,
        callback: handleGoogleCredential,
      });
      googleId.renderButton(googleButtonRef.current, {
        theme: "outline",
        size: "large",
        type: "standard",
        shape: "rectangular",
        text: "continue_with",
        width: 320,
      });
    };

    if (window.google?.accounts?.id) {
      renderGoogleButton();
      return;
    }

    const existingScript = document.querySelector<HTMLScriptElement>("script[data-google-identity]");
    if (existingScript) {
      existingScript.addEventListener("load", renderGoogleButton, { once: true });
      return () => existingScript.removeEventListener("load", renderGoogleButton);
    }

    const script = document.createElement("script");
    script.src = "https://accounts.google.com/gsi/client";
    script.async = true;
    script.defer = true;
    script.dataset.googleIdentity = "true";
    script.addEventListener("load", renderGoogleButton, { once: true });
    document.head.appendChild(script);

    return () => script.removeEventListener("load", renderGoogleButton);
  }, [googleClientId, handleGoogleCredential]);

  const BrandPanel = () => (
    <div style={{
      width: "45%", background: "#f5f5f5", padding: "48px 40px",
      display: "flex", flexDirection: "column", justifyContent: "center",
      borderRight: "1px solid #e0e0e0"
    }}>
      <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 24 }}>
        <img src="/logo.png" alt="All4Health" style={{ height: 28, width: "auto" }}
          onError={(e) => { (e.target as HTMLImageElement).style.display = "none"; }} />
        <span style={{ fontSize: 16, fontWeight: 700, color: "#1a1a1a" }}>All4Health</span>
      </div>
      <h2 style={{ fontSize: 20, fontWeight: 600, color: "#1a1a1a", lineHeight: 1.35, margin: "0 0 12px" }}>
        건강한 내일을<br />지금 시작하세요
      </h2>
      <p style={{ fontSize: 15, color: "#555", lineHeight: 1.6, margin: "0 0 24px" }}>
        AI 기반 만성질환 관리와 생활습관 챌린지로<br />더 건강한 삶을 만들어 드립니다.
      </p>
      <hr style={{ border: "none", borderTop: "1px solid #ddd", margin: "0 0 20px" }} />
      <div style={{ display: "flex", flexDirection: "column", gap: 16 }}>
        {[
          { title: "AI 기반 질환 위험 예측", desc: "혈압·혈당 데이터로 위험도를 분석합니다", icon: icons.aiRisk },
          { title: "매일 달성하는 건강 챌린지", desc: "작은 습관이 큰 변화를 만듭니다", icon: icons.healthChallenge },
          { title: "개인 맞춤 건강 가이드", desc: "나에게 맞는 식단·운동 조언을 제공합니다", icon: icons.healthGuide }
        ].map((item, i) => (
          <div key={i} style={{ display: "flex", gap: 12, alignItems: "flex-start" }}>
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
    </div>
  );

  // 계정 잠금 상태
  if (errorCount === -1) {
    return (
      <div style={{ display: "flex", height: "100vh" }}>
        <BrandPanel />
        <div style={{ flex: 1, padding: "48px 40px", display: "flex", flexDirection: "column", justifyContent: "center", background: "#fff", overflowY: "auto" }}>
          <div style={{ fontSize: 17, fontWeight: 500, color: "#888", letterSpacing: 0.5, textTransform: "uppercase", marginBottom: 6 }}>로그인</div>
          <hr style={{ border: "none", borderTop: "1px solid #e0e0e0", margin: "16px 0" }} />
          <div style={{ display: "flex", flexDirection: "column", gap: 14 }}>
            <div>
              <label style={{ fontSize: 16, color: "#555", display: "block", marginBottom: 4 }}>이메일</label>
              <input disabled value={email} style={{ width: "100%", height: 34, border: "0.5px solid #e0e0e0", borderRadius: 5, padding: "0 10px", fontSize: 17, opacity: 0.6, background: "#fafafa", boxSizing: "border-box" }} />
            </div>
            <div>
              <label style={{ fontSize: 16, color: "#555", display: "block", marginBottom: 4 }}>비밀번호</label>
              <input disabled type="password" style={{ width: "100%", height: 34, border: "0.5px solid #e0e0e0", borderRadius: 5, padding: "0 10px", fontSize: 17, opacity: 0.6, background: "#fafafa", boxSizing: "border-box" }} />
            </div>
            <div style={{ background: "#fff8f7", border: "0.5px solid #f5b7b1", borderRadius: 12, padding: "16px 18px" }}>
              <div style={{ display: "flex", alignItems: "flex-start", gap: 10, marginBottom: 12 }}>
                <span style={{ fontSize: 18, color: "#e87b72" }}>⏱</span>
                <div>
                  <div style={{ fontSize: 17, fontWeight: 500, color: "#c0392b" }}>계정이 일시적으로 잠겼습니다</div>
                  <div style={{ fontSize: 15, color: "#c0392b", marginTop: 4, lineHeight: 1.6 }}>
                    {errorMessage || "비밀번호 입력 실패가 반복되었습니다. 잠시 후 다시 시도하거나 비밀번호를 재설정해주세요."}
                  </div>
                </div>
              </div>
              <button onClick={() => onNavigate?.("/password-reset")} style={{ width: "100%", height: 34, border: "0.5px solid #e87b72", borderRadius: 8, background: "#fff", color: "#c0392b", fontSize: 17, cursor: "pointer", marginBottom: 8 }}>비밀번호 재설정</button>
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
        <div style={{ fontSize: 17, fontWeight: 500, color: "#888", letterSpacing: 0.5, textTransform: "uppercase", marginBottom: 6 }}>로그인</div>
        <div style={{ fontSize: 15, color: "#555", marginBottom: 20 }}>계정에 로그인하여 건강 관리를 시작하세요</div>
        <hr style={{ border: "none", borderTop: "1px solid #e0e0e0", margin: "0 0 16px" }} />

        <div style={{ display: "flex", flexDirection: "column", gap: 14 }}>
          <div>
            <label style={{ fontSize: 16, color: "#555", display: "block", marginBottom: 4 }}>이메일</label>
            <input
              type="email" value={email} onChange={e => setEmail(e.target.value)}
              placeholder="example@email.com"
              style={{ width: "100%", height: 34, border: `1.5px solid ${errorCount > 0 ? "#E24B4A" : "#ddd"}`, borderRadius: 5, padding: "0 10px", fontSize: 17, boxSizing: "border-box", outline: "none" }}
            />
          </div>
          <div>
            <label style={{ fontSize: 16, color: "#555", display: "block", marginBottom: 4 }}>비밀번호</label>
            <div style={{ position: "relative" }}>
              <input
                type={showPassword ? "text" : "password"} value={password} onChange={e => setPassword(e.target.value)}
                placeholder="비밀번호 입력"
                style={{ width: "100%", height: 34, border: `1.5px solid ${errorCount > 0 ? "#E24B4A" : "#ddd"}`, borderRadius: 5, padding: "0 36px 0 10px", fontSize: 17, boxSizing: "border-box", outline: "none" }}
              />
              <PasswordToggleButton isVisible={showPassword} onToggle={() => setShowPassword(!showPassword)} />
            </div>
            {errorMessage && errorCount !== 1 && (
              <p style={{ fontSize: 15, color: "#E24B4A", margin: "4px 0 0" }}>{errorMessage}</p>
            )}
          </div>

          {errorCount === 1 && (
            <div style={{ background: "#FFF8E1", border: "1.5px solid #F39C12", borderRadius: 6, padding: "12px 14px" }}>
              <div style={{ display: "flex", alignItems: "flex-start", gap: 10 }}>
                <div style={{ width: 18, height: 18, borderRadius: "50%", background: "#F39C12", color: "#fff", display: "flex", alignItems: "center", justifyContent: "center", fontSize: 17, flexShrink: 0 }}>!</div>
                <div>
                  <div style={{ fontSize: 15, fontWeight: 600, color: "#D68910", marginBottom: 4 }}>계정 잠금까지 1회 남았습니다</div>
                  <div style={{ fontSize: 17, color: "#856404", lineHeight: 1.5 }}>한 번 더 실패하면 계정이 일시적으로 잠깁니다.</div>
                </div>
              </div>
            </div>
          )}

          <label style={{ display: "flex", alignItems: "center", gap: 8, fontSize: 17, color: "#555", cursor: "pointer" }}>
            <input
              type="checkbox"
              checked={rememberMe}
              onChange={(e) => setRememberMe(e.target.checked)}
              style={{ width: 14, height: 14, cursor: "pointer" }}
            />
            로그인 상태 유지
          </label>

          <button
            onClick={handleLogin} disabled={isLoading || !email || !password}
            style={{ width: "100%", height: 36, background: isLoading || !email || !password ? "#ccc" : "#1a1a1a", color: "#fff", border: "none", borderRadius: 8, fontSize: 16, fontWeight: 600, cursor: isLoading || !email || !password ? "not-allowed" : "pointer" }}>
            {isLoading ? "로그인 중..." : "로그인"}
          </button>

          <div style={{ display: "flex", alignItems: "center", gap: 10, margin: "4px 0" }}>
            <span style={{ flex: 1, height: 1, background: "#e5e7eb" }} />
            <span style={{ fontSize: 17, color: "#888" }}>또는</span>
            <span style={{ flex: 1, height: 1, background: "#e5e7eb" }} />
          </div>

          {googleClientId ? (
            <div
              ref={googleButtonRef}
              aria-busy={isGoogleLoading}
              style={{ minHeight: 44, display: "flex", justifyContent: "center" }}
            />
          ) : (
            <button
              type="button"
              disabled
              style={{
                width: "100%",
                height: 38,
                border: "1px solid #d1d5db",
                borderRadius: 8,
                background: "#f8fafc",
                color: "#888",
                fontSize: 15,
                cursor: "not-allowed",
              }}
            >
              Google 로그인 설정 필요
            </button>
          )}
        </div>

        <div style={{ display: "flex", justifyContent: "space-between", marginTop: 16 }}>
          <button onClick={() => onNavigate?.("/password-reset")} style={{ background: "none", border: "none", fontSize: 17, color: "#888", cursor: "pointer" }}>비밀번호를 잊으셨나요?</button>
          <button onClick={() => onNavigate?.("/signup")} style={{ background: "none", border: "none", fontSize: 17, color: "#888", cursor: "pointer" }}>회원가입</button>
        </div>
      </div>
    </div>
  );
}
