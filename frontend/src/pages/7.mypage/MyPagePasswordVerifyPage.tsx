import { useState } from "react";

import type { AppRoute } from "../../App";
import { getStoredAccessToken } from "../../api/auth";
import { ApiError } from "../../api/client";
import { verifyCurrentUserPassword } from "../../api/users";

interface MyPagePasswordVerifyPageProps {
  onNavigate: (route: AppRoute) => void;
  onVerified: () => void;
  targetRoute: AppRoute;
}

export function MyPagePasswordVerifyPage({ onNavigate, onVerified, targetRoute }: MyPagePasswordVerifyPageProps) {
  const [password, setPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [message, setMessage] = useState("");

  const handleSubmit = async () => {
    if (!password || isSubmitting) return;

    setIsSubmitting(true);
    setMessage("");
    try {
      await verifyCurrentUserPassword(password, getStoredAccessToken());
      onVerified();
      onNavigate(targetRoute === "/mypage/verify" ? "/mypage/profile" : targetRoute);
    } catch (error) {
      if (error instanceof ApiError && error.status === 401) {
        setMessage("비밀번호가 올바르지 않습니다.");
      } else if (error instanceof ApiError && error.status === 422) {
        setMessage("비밀번호를 8자 이상 입력해주세요.");
      } else {
        setMessage("비밀번호 확인에 실패했습니다. 잠시 후 다시 시도해주세요.");
      }
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="page-container">
      <div style={{ maxWidth: 520, margin: "40px auto" }}>
        <div style={{ background: "#fff", border: "1px solid #e0e0e0", borderRadius: 14, padding: 28 }}>
          <div style={{ width: 54, height: 54, borderRadius: "50%", background: "#f0f0f0", display: "flex", alignItems: "center", justifyContent: "center", fontSize: 26, marginBottom: 18 }}>
            🔒
          </div>
          <h1 style={{ fontSize: 24, fontWeight: 700, color: "#1a1a1a", margin: "0 0 8px" }}>비밀번호 확인</h1>
          <p style={{ fontSize: 15, color: "#666", lineHeight: 1.6, margin: "0 0 24px" }}>
            마이페이지에는 개인정보가 포함되어 있어 비밀번호를 한 번 더 확인합니다.
          </p>

          <label style={{ display: "block", fontSize: 15, fontWeight: 600, color: "#333", marginBottom: 8 }}>
            현재 비밀번호
          </label>
          <div style={{ position: "relative", marginBottom: 12 }}>
            <input
              type={showPassword ? "text" : "password"}
              value={password}
              onChange={(event) => setPassword(event.target.value)}
              onKeyDown={(event) => {
                if (event.key === "Enter") void handleSubmit();
              }}
              placeholder="비밀번호 입력"
              autoFocus
              style={{ width: "100%", height: 44, border: "1.5px solid #ddd", borderRadius: 8, padding: "0 44px 0 12px", fontSize: 16, boxSizing: "border-box", outline: "none" }}
            />
            <button
              type="button"
              onClick={() => setShowPassword((prev) => !prev)}
              style={{ position: "absolute", right: 10, top: "50%", transform: "translateY(-50%)", border: "none", background: "none", cursor: "pointer", fontSize: 15, color: "#777" }}
            >
              {showPassword ? "숨김" : "보기"}
            </button>
          </div>

          {message && <p style={{ fontSize: 14, color: "#c62828", margin: "0 0 14px" }}>{message}</p>}

          <div style={{ display: "flex", gap: 10 }}>
            <button
              type="button"
              onClick={() => onNavigate("/home")}
              style={{ flex: 1, height: 42, border: "1.5px solid #ddd", borderRadius: 8, background: "#fff", color: "#555", fontSize: 15, cursor: "pointer" }}
            >
              취소
            </button>
            <button
              type="button"
              onClick={() => void handleSubmit()}
              disabled={!password || isSubmitting}
              style={{ flex: 1, height: 42, border: "none", borderRadius: 8, background: !password || isSubmitting ? "#ccc" : "#1a1a1a", color: "#fff", fontSize: 15, fontWeight: 700, cursor: !password || isSubmitting ? "not-allowed" : "pointer" }}
            >
              {isSubmitting ? "확인 중..." : "확인"}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
