import { useEffect, useState } from "react";
import type { AppRoute } from "../App";
import { getStoredAccessToken } from "../api/auth";
import {
  getNotificationPreferences,
  updateNotificationPreferences,
  type NotificationPreference,
} from "../api/notifications";
import {
  getPolicyDocument,
  getUserConsents,
  updateUserConsent,
  withdrawCurrentUser,
  type ConsentType,
  type PolicyDocument,
  type UserConsent,
  type WithdrawalReason,
} from "../api/users";

// ──────────────────────────────────────────────
// 비밀번호 변경 페이지
// ──────────────────────────────────────────────
interface ChangePasswordPageProps {
  onNavigate: (route: AppRoute) => void;
}

function PasswordField({ label, value, onChange }: { label: string; value: string; onChange: (v: string) => void }) {
  const [show, setShow] = useState(false);
  return (
    <div>
      <label style={{ fontSize: 10, color: "#555", display: "block", marginBottom: 4 }}>{label}</label>
      <div style={{ position: "relative" }}>
        <input type={show ? "text" : "password"} value={value} onChange={e => onChange(e.target.value)}
          style={{ width: "100%", height: 36, border: "1.5px solid #ddd", borderRadius: 5, padding: "0 36px 0 10px", fontSize: 12, outline: "none", boxSizing: "border-box" }} />
        <button onClick={() => setShow(!show)}
          style={{ position: "absolute", right: 10, top: "50%", transform: "translateY(-50%)", background: "none", border: "none", cursor: "pointer", fontSize: 14, color: "#888" }}>
          {show ? "🙈" : "👁"}
        </button>
      </div>
    </div>
  );
}

export function ChangePasswordPage({ onNavigate }: ChangePasswordPageProps) {
  const [currentPw, setCurrentPw] = useState("");
  const [newPw, setNewPw] = useState("");
  const [confirmPw, setConfirmPw] = useState("");
  const [errors, setErrors] = useState<Record<string, string>>({});
  const [isSaving, setIsSaving] = useState(false);

  const validate = () => {
    const e: Record<string, string> = {};
    if (!currentPw) e.current = "현재 비밀번호를 입력해주세요.";
    if (newPw.length < 8) e.new = "비밀번호는 8자 이상이어야 합니다.";
    if (!/^(?=.*[a-zA-Z])(?=.*\d)(?=.*[!@#$%^&*])/.test(newPw)) e.new = "영문, 숫자, 특수문자 조합이 필요합니다.";
    if (newPw !== confirmPw) e.confirm = "비밀번호가 일치하지 않습니다.";
    return e;
  };

  const handleSave = () => {
    const e = validate();
    if (Object.keys(e).length > 0) { setErrors(e); return; }
    setIsSaving(true);
    setErrors({ api: "비밀번호 변경 API가 아직 백엔드에 구현되지 않았습니다." });
    setIsSaving(false);
  };

  return (
    <div className="page-container">
      <h1 className="page-title">비밀번호 변경</h1>

      <div style={{ background: "#fff", border: "1px solid #e0e0e0", borderRadius: 10, padding: 24, maxWidth: 500 }}>
        <h3 style={{ fontSize: 13, fontWeight: 600, margin: "0 0 16px" }}>비밀번호 변경</h3>
        <div style={{ display: "flex", flexDirection: "column", gap: 14 }}>
          <div>
            <PasswordField label="현재 비밀번호" value={currentPw} onChange={setCurrentPw} />
            {errors.current && <p style={{ fontSize: 11, color: "#E24B4A", margin: "4px 0 0" }}>{errors.current}</p>}
          </div>
          <div>
            <PasswordField label="새 비밀번호" value={newPw} onChange={setNewPw} />
            {errors.new && <p style={{ fontSize: 11, color: "#E24B4A", margin: "4px 0 0" }}>{errors.new}</p>}
          </div>
          <div>
            <PasswordField label="새 비밀번호 확인" value={confirmPw} onChange={setConfirmPw} />
            {errors.confirm && <p style={{ fontSize: 11, color: "#E24B4A", margin: "4px 0 0" }}>{errors.confirm}</p>}
          </div>
          {errors.api && <p style={{ fontSize: 11, color: "#E24B4A", margin: 0 }}>{errors.api}</p>}
        </div>

        <hr style={{ border: "none", borderTop: "1px solid #e0e0e0", margin: "16px 0" }} />

        <div style={{ background: "#fafafa", border: "1px solid #e0e0e0", borderRadius: 6, padding: "12px 14px" }}>
          <p style={{ fontSize: 11, fontWeight: 600, margin: "0 0 6px" }}>비밀번호 규칙</p>
          {["8자 이상 입력", "영문, 숫자, 특수문자 조합", "연속된 문자/숫자 사용 금지"].map(r => (
            <p key={r} style={{ fontSize: 10, color: "#888", margin: "2px 0" }}>• {r}</p>
          ))}
        </div>

        <div style={{ display: "flex", gap: 10, marginTop: 20 }}>
          <button onClick={handleSave} disabled={isSaving}
            style={{ padding: "10px 24px", border: "none", borderRadius: 8, background: isSaving ? "#aaa" : "#1a1a1a", color: "#fff", fontSize: 13, fontWeight: 600, cursor: isSaving ? "not-allowed" : "pointer" }}>
            {isSaving ? "변경 중..." : "변경"}
          </button>
          <button onClick={() => onNavigate("/mypage/edit")}
            style={{ padding: "10px 24px", border: "1.5px solid #ddd", borderRadius: 8, background: "#fff", fontSize: 13, cursor: "pointer" }}>
            취소
          </button>
        </div>
      </div>
    </div>
  );
}

// ──────────────────────────────────────────────
// 알림 설정 페이지
// ──────────────────────────────────────────────
interface NotificationSettingsPageProps {
  onNavigate: (route: AppRoute) => void;
}

export function NotificationSettingsPage({ onNavigate }: NotificationSettingsPageProps) {
  const [push, setPush] = useState({
    push_enabled: true,
    health_data_reminder_enabled: true,
    challenge_mission_enabled: true,
    prediction_result_enabled: true,
    advice_update_enabled: false,
    virtual_pet_enabled: true,
  });
  const [email, setEmail] = useState({
    email_enabled: true,
    weekly_report_enabled: true,
    important_notice_enabled: true,
    promotion_enabled: false,
    // 월간 리포트는 MVP 제외
  });
  const [quietStart, setQuietStart] = useState("09:00");
  const [quietEnd, setQuietEnd] = useState("21:00");
  const [errorMessage, setErrorMessage] = useState("");
  const [isLoading, setIsLoading] = useState(true);
  const [isSaving, setIsSaving] = useState(false);

  useEffect(() => {
    let ignore = false;

    async function loadPreferences() {
      try {
        const { data } = await getNotificationPreferences(getStoredAccessToken());
        if (ignore) return;
        setPush({
          push_enabled: data.push_enabled,
          health_data_reminder_enabled: data.health_data_reminder_enabled,
          challenge_mission_enabled: data.challenge_mission_enabled,
          prediction_result_enabled: data.prediction_result_enabled,
          advice_update_enabled: data.advice_update_enabled,
          virtual_pet_enabled: data.virtual_pet_enabled,
        });
        setEmail({
          email_enabled: data.email_enabled,
          weekly_report_enabled: data.weekly_report_enabled,
          important_notice_enabled: data.important_notice_enabled,
          promotion_enabled: data.promotion_enabled,
        });
        setQuietStart(data.quiet_start_time.slice(0, 5));
        setQuietEnd(data.quiet_end_time.slice(0, 5));
      } catch {
        if (!ignore) setErrorMessage("알림 설정을 불러오지 못했습니다.");
      } finally {
        if (!ignore) setIsLoading(false);
      }
    }

    void loadPreferences();
    return () => {
      ignore = true;
    };
  }, []);

  const handleSave = async () => {
    setIsSaving(true);
    setErrorMessage("");
    try {
      const payload: Partial<NotificationPreference> = {
        ...push,
        ...email,
        quiet_start_time: quietStart,
        quiet_end_time: quietEnd,
      };
      await updateNotificationPreferences(payload, getStoredAccessToken());
      setIsSaving(false);
      onNavigate("/mypage");
    } catch {
      setIsSaving(false);
      setErrorMessage("알림 설정 저장에 실패했습니다.");
    }
  };

  const togglePush = (key: keyof typeof push) => {
    setPush(prev => ({ ...prev, [key]: !prev[key] }));
  };

  const toggleEmail = (key: keyof typeof email) => {
    setEmail(prev => ({ ...prev, [key]: !prev[key] }));
  };

  const Toggle = ({ checked, onChange }: { checked: boolean; onChange: () => void }) => (
    <div onClick={onChange} style={{ width: 40, height: 22, borderRadius: 11, background: checked ? "#1a1a1a" : "#ddd", position: "relative", cursor: "pointer", flexShrink: 0, transition: "background 0.2s" }}>
      <div style={{ width: 18, height: 18, borderRadius: "50%", background: "#fff", position: "absolute", top: 2, left: checked ? 20 : 2, transition: "left 0.2s" }} />
    </div>
  );

  return (
    <div className="page-container">
      <h1 className="page-title">알림 설정</h1>

      {isLoading && <p style={{ fontSize: 13, color: "#888" }}>알림 설정을 불러오는 중입니다.</p>}
      {errorMessage && <p style={{ fontSize: 12, color: "#c62828" }}>{errorMessage}</p>}

      {/* 푸시 알림 */}
      <div style={{ background: "#fff", border: "1px solid #e0e0e0", borderRadius: 10, padding: 20, marginBottom: 14 }}>
        <h3 style={{ fontSize: 13, fontWeight: 600, margin: "0 0 14px" }}>푸시 알림</h3>
        <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
            <span style={{ fontSize: 13, fontWeight: 600 }}>전체 알림 수신</span>
            <Toggle checked={push.push_enabled} onChange={() => togglePush("push_enabled")} />
          </div>
          <hr style={{ border: "none", borderTop: "1px solid #f0f0f0" }} />
          {[
            { key: "health_data_reminder_enabled" as const, label: "건강 데이터 입력 알림" },
            { key: "challenge_mission_enabled" as const, label: "챌린지 미션 알림" },
            { key: "prediction_result_enabled" as const, label: "예측 결과 알림" },
            { key: "advice_update_enabled" as const, label: "조언 업데이트 알림" },
            { key: "virtual_pet_enabled" as const, label: "가상 펫 상태 알림" },
          ].map(item => (
            <div key={item.key} style={{ display: "flex", justifyContent: "space-between", alignItems: "center", opacity: push.push_enabled ? 1 : 0.4 }}>
              <span style={{ fontSize: 12, color: "#555" }}>{item.label}</span>
              <Toggle checked={push[item.key] && push.push_enabled} onChange={() => push.push_enabled && togglePush(item.key)} />
            </div>
          ))}
        </div>
        {!push.push_enabled && (
          <p style={{ fontSize: 11, color: "#aaa", margin: "10px 0 0" }}>전체 알림 수신이 꺼져 있으면 개별 알림도 비활성화됩니다.</p>
        )}
      </div>

      {/* 이메일 알림 — 월간 리포트 제외 */}
      <div style={{ background: "#fff", border: "1px solid #e0e0e0", borderRadius: 10, padding: 20, marginBottom: 14 }}>
        <h3 style={{ fontSize: 13, fontWeight: 600, margin: "0 0 14px" }}>이메일 알림</h3>
        <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
            <span style={{ fontSize: 13, fontWeight: 600 }}>이메일 알림 수신</span>
            <Toggle checked={email.email_enabled} onChange={() => toggleEmail("email_enabled")} />
          </div>
          <hr style={{ border: "none", borderTop: "1px solid #f0f0f0" }} />
          {[
            { key: "weekly_report_enabled" as const, label: "주간 리포트" },
            { key: "important_notice_enabled" as const, label: "중요 공지사항" },
            { key: "promotion_enabled" as const, label: "이벤트/프로모션" },
            // 월간 리포트는 MVP 범위 제외 (REQ-NTFY-006)
          ].map(item => (
            <div key={item.key} style={{ display: "flex", justifyContent: "space-between", alignItems: "center", opacity: email.email_enabled ? 1 : 0.4 }}>
              <span style={{ fontSize: 12, color: "#555" }}>{item.label}</span>
              <Toggle checked={email[item.key] && email.email_enabled} onChange={() => email.email_enabled && toggleEmail(item.key)} />
            </div>
          ))}
        </div>
      </div>

      {/* 알림 시간 설정 */}
      <div style={{ background: "#fff", border: "1px solid #e0e0e0", borderRadius: 10, padding: 20, marginBottom: 20 }}>
        <h3 style={{ fontSize: 13, fontWeight: 600, margin: "0 0 14px" }}>알림 시간 설정</h3>
        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 14 }}>
          <div>
            <label style={{ fontSize: 10, color: "#555", display: "block", marginBottom: 4 }}>시작 시간</label>
            <input type="time" value={quietStart} onChange={e => setQuietStart(e.target.value)}
              style={{ width: "100%", height: 36, border: "1.5px solid #ddd", borderRadius: 5, padding: "0 10px", fontSize: 12, outline: "none", boxSizing: "border-box" }} />
          </div>
          <div>
            <label style={{ fontSize: 10, color: "#555", display: "block", marginBottom: 4 }}>종료 시간</label>
            <input type="time" value={quietEnd} onChange={e => setQuietEnd(e.target.value)}
              style={{ width: "100%", height: 36, border: "1.5px solid #ddd", borderRadius: 5, padding: "0 10px", fontSize: 12, outline: "none", boxSizing: "border-box" }} />
          </div>
        </div>
        <p style={{ fontSize: 11, color: "#888", margin: "10px 0 0" }}>설정한 시간 외에는 알림을 받지 않습니다.</p>
      </div>

      <div style={{ display: "flex", gap: 10 }}>
        <button onClick={handleSave} disabled={isSaving}
          style={{ padding: "10px 24px", border: "none", borderRadius: 8, background: isSaving ? "#aaa" : "#1a1a1a", color: "#fff", fontSize: 13, fontWeight: 600, cursor: isSaving ? "not-allowed" : "pointer" }}>
          {isSaving ? "저장 중..." : "저장"}
        </button>
        <button onClick={() => onNavigate("/mypage")}
          style={{ padding: "10px 24px", border: "1.5px solid #ddd", borderRadius: 8, background: "#fff", fontSize: 13, cursor: "pointer" }}>
          취소
        </button>
      </div>
    </div>
  );
}

// ──────────────────────────────────────────────
// 약관/동의 관리 페이지
// ──────────────────────────────────────────────
interface TermsManagementPageProps {
  onNavigate: (route: AppRoute) => void;
}

export function TermsManagementPage({ onNavigate }: TermsManagementPageProps) {
  const [consents, setConsents] = useState<UserConsent[]>([]);
  const [recentChanges, setRecentChanges] = useState<{ policy_type: ConsentType; title: string; policy_version: string; changed_at: string | null }[]>([]);
  const [policyModal, setPolicyModal] = useState<PolicyDocument | null>(null);
  const [errorMessage, setErrorMessage] = useState("");

  useEffect(() => {
    let ignore = false;

    async function loadConsents() {
      try {
        const result = await getUserConsents(getStoredAccessToken());
        if (ignore) return;
        setConsents(result.items);
        setRecentChanges(result.recent_policy_changes);
      } catch {
        if (!ignore) setErrorMessage("약관 동의 정보를 불러오지 못했습니다.");
      }
    }

    void loadConsents();
    return () => {
      ignore = true;
    };
  }, []);

  const openPolicy = async (policyType: ConsentType, version?: string) => {
    try {
      setPolicyModal(await getPolicyDocument(policyType, version, getStoredAccessToken()));
    } catch {
      setErrorMessage("약관 전문을 불러오지 못했습니다.");
    }
  };

  const handleToggleConsent = async (consent: UserConsent) => {
    try {
      const updated = await updateUserConsent(
        consent.consent_type,
        !consent.is_agreed,
        consent.policy_version,
        getStoredAccessToken(),
      );
      setConsents(prev => prev.map(item => (item.consent_type === updated.consent_type ? updated : item)));
    } catch {
      setErrorMessage("선택 약관 상태 변경에 실패했습니다.");
    }
  };

  const requiredConsents = consents.filter(consent => consent.is_required);
  const optionalConsents = consents.filter(consent => !consent.is_required);

  return (
    <div className="page-container">
      <h1 className="page-title">약관 및 동의 관리</h1>
      {errorMessage && <p style={{ fontSize: 12, color: "#c62828" }}>{errorMessage}</p>}

      {/* 필수 약관 */}
      <div style={{ background: "#fff", border: "1px solid #e0e0e0", borderRadius: 10, padding: 20, marginBottom: 14 }}>
        <h3 style={{ fontSize: 13, fontWeight: 600, margin: "0 0 14px" }}>필수 약관</h3>
        <div style={{ display: "flex", flexDirection: "column", gap: 0 }}>
          {requiredConsents.map((term, i) => (
            <div key={term.consent_type} style={{ display: "flex", alignItems: "center", justifyContent: "space-between", padding: "12px 0", borderBottom: i < requiredConsents.length - 1 ? "1px solid #f0f0f0" : "none" }}>
              <div>
                <p style={{ fontSize: 12, fontWeight: 600, margin: "0 0 2px" }}>{term.title}</p>
                <p style={{ fontSize: 10, color: "#aaa", margin: 0 }}>{term.agreed_at ? `${term.agreed_at.split("T")[0]} 동의` : "동의 이력 없음"}</p>
              </div>
              <button onClick={() => openPolicy(term.consent_type, term.policy_version)}
                style={{ padding: "6px 12px", border: "1.5px solid #ddd", borderRadius: 6, background: "#fff", fontSize: 11, cursor: "pointer" }}>
                보기
              </button>
            </div>
          ))}
        </div>
      </div>

      {/* 선택 약관 */}
      <div style={{ background: "#fff", border: "1px solid #e0e0e0", borderRadius: 10, padding: 20, marginBottom: 14 }}>
        <h3 style={{ fontSize: 13, fontWeight: 600, margin: "0 0 14px" }}>선택 약관</h3>
        <div style={{ display: "flex", flexDirection: "column", gap: 0 }}>
          {optionalConsents.map((consent, i) => (
            <div key={consent.consent_type} style={{ display: "flex", alignItems: "center", justifyContent: "space-between", padding: "12px 0", borderBottom: i < optionalConsents.length - 1 ? "1px solid #f0f0f0" : "none" }}>
              <div>
                <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 2 }}>
                  <p style={{ fontSize: 12, fontWeight: 600, margin: 0 }}>{consent.title}</p>
                  <span style={{ padding: "2px 8px", background: consent.is_agreed ? "#e8f5e9" : "#fafafa", border: `1px solid ${consent.is_agreed ? "#a5d6a7" : "#e0e0e0"}`, borderRadius: 20, fontSize: 10, color: consent.is_agreed ? "#2e7d32" : "#aaa" }}>
                    {consent.is_agreed ? "동의" : "미동의"}
                  </span>
                </div>
                <p style={{ fontSize: 10, color: "#aaa", margin: 0 }}>
                  {consent.agreed_at ? `${consent.agreed_at} 동의` : "미동의"}
                </p>
              </div>
              {/* 동의 상태에 따라 단독 버튼만 표시 (REQ-AUTH-014) */}
              <button onClick={() => handleToggleConsent(consent)}
                style={{ padding: "6px 12px", border: `1.5px solid ${consent.is_agreed ? "#ddd" : "#1a1a1a"}`, borderRadius: 6, background: consent.is_agreed ? "#fff" : "#1a1a1a", color: consent.is_agreed ? "#555" : "#fff", fontSize: 11, cursor: "pointer" }}>
                {consent.is_agreed ? "철회" : "동의"}
              </button>
            </div>
          ))}
        </div>
      </div>

      {/* 최근 약관 변경 내역 */}
      <div style={{ background: "#fff", border: "1px solid #e0e0e0", borderRadius: 10, padding: 20 }}>
        <h3 style={{ fontSize: 13, fontWeight: 600, margin: "0 0 14px" }}>최근 약관 변경 내역</h3>
        <div style={{ display: "flex", flexDirection: "column", gap: 0 }}>
          {recentChanges.map((change, i) => (
            <div key={`${change.policy_type}-${change.policy_version}`} style={{ display: "flex", alignItems: "center", padding: "10px 0", borderBottom: i < recentChanges.length - 1 ? "1px solid #f0f0f0" : "none" }}>
              <div style={{ flex: 1 }}>
                <p style={{ fontSize: 12, margin: "0 0 2px" }}>{change.title}</p>
                <p style={{ fontSize: 10, color: "#aaa", margin: 0 }}>{change.changed_at ?? "변경일 미등록"} · {change.policy_version}</p>
              </div>
              <button onClick={() => openPolicy(change.policy_type, change.policy_version)}
                style={{ padding: "6px 12px", border: "1.5px solid #ddd", borderRadius: 6, background: "#fff", fontSize: 11, cursor: "pointer" }}>
                변경 내용 보기
              </button>
            </div>
          ))}
        </div>
      </div>

      {policyModal && (
        <div style={{ position: "fixed", inset: 0, background: "rgba(0,0,0,0.45)", display: "flex", alignItems: "center", justifyContent: "center", zIndex: 1000 }}>
          <div style={{ width: 560, maxHeight: "80vh", overflow: "auto", background: "#fff", borderRadius: 12, padding: 24 }}>
            <h3 style={{ fontSize: 16, fontWeight: 700, margin: "0 0 6px" }}>{policyModal.title}</h3>
            <p style={{ fontSize: 11, color: "#888", margin: "0 0 16px" }}>
              {policyModal.policy_version} · {policyModal.changed_at ?? "변경일 미등록"}
            </p>
            <div style={{ whiteSpace: "pre-wrap", fontSize: 12, lineHeight: 1.7, color: "#333", border: "1px solid #eee", borderRadius: 8, padding: 14 }}>
              {policyModal.content}
            </div>
            <button onClick={() => setPolicyModal(null)}
              style={{ marginTop: 16, width: "100%", height: 38, border: "none", borderRadius: 8, background: "#1a1a1a", color: "#fff", fontSize: 13, fontWeight: 600 }}>
              닫기
            </button>
          </div>
        </div>
      )}
    </div>
  );
}

// ──────────────────────────────────────────────
// 회원 탈퇴 페이지
// ──────────────────────────────────────────────
interface WithdrawalPageProps {
  onNavigate: (route: AppRoute) => void;
}

const WITHDRAWAL_REASONS = [
  { code: "NOT_USEFUL", label: "서비스 이용 빈도가 낮음" },
  { code: "HARD_TO_USE", label: "사용이 어려움" },
  { code: "PRIVACY_CONCERN", label: "개인정보 보호 우려" },
  { code: "FOUND_ALTERNATIVE", label: "다른 서비스로 이동" },
  { code: "OTHER", label: "기타" },
];

export function WithdrawalPage({ onNavigate }: WithdrawalPageProps) {
  const [reason, setReason] = useState<WithdrawalReason | "">("");
  const [comment, setComment] = useState("");
  const [password, setPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [agreed, setAgreed] = useState(false);
  const [showConfirm, setShowConfirm] = useState(false);
  const [pwError, setPwError] = useState("");
  const [isDeleting, setIsDeleting] = useState(false);

  const isValid = reason && password && agreed;

  const handleWithdraw = async () => {
    if (!reason) return;
    setIsDeleting(true);
    setPwError("");
    try {
      await withdrawCurrentUser(
        {
          password,
          withdrawal_reason: reason,
          withdrawal_comment: comment || null,
          confirm_agreed: true,
        },
        getStoredAccessToken(),
      );
      setIsDeleting(false);
      setShowConfirm(false);
      onNavigate("/");
    } catch {
      setIsDeleting(false);
      setShowConfirm(false);
      setPwError("회원 탈퇴 처리에 실패했습니다. 비밀번호를 확인해주세요.");
    }
  };

  return (
    <div className="page-container">
      <h1 className="page-title">회원 탈퇴</h1>

      <div style={{ background: "#fff", border: "1px solid #e0e0e0", borderRadius: 10, padding: 24, maxWidth: 600 }}>
        {/* 유의사항 */}
        <div style={{ background: "#fff5f5", border: "1.5px solid #ffcccc", borderRadius: 8, padding: 16, marginBottom: 20 }}>
          <p style={{ fontSize: 13, fontWeight: 600, margin: "0 0 10px" }}>⚠ 회원 탈퇴 시 유의사항</p>
          {[
            "모든 건강 데이터가 영구 삭제됩니다",
            "예측 이력 및 리포트가 삭제됩니다",
            "챌린지 진행 상황 및 뱃지가 삭제됩니다",
            "포인트 및 레벨이 초기화됩니다",
            "탈퇴 후 일정 기간 동일 이메일 재가입이 제한될 수 있습니다",
          ].map((item, i) => <p key={i} style={{ fontSize: 12, color: "#c62828", margin: "4px 0" }}>• {item}</p>)}
        </div>

        {/* 탈퇴 사유 */}
        <h3 style={{ fontSize: 13, fontWeight: 600, margin: "0 0 12px" }}>탈퇴 사유</h3>
        <div style={{ display: "flex", flexDirection: "column", gap: 8, marginBottom: 16 }}>
          {WITHDRAWAL_REASONS.map(r => (
            <label key={r.code} style={{ display: "flex", alignItems: "center", gap: 8, cursor: "pointer" }}>
              <input type="radio" name="reason" value={r.code} checked={reason === r.code} onChange={() => setReason(r.code as WithdrawalReason)} style={{ width: 14, height: 14 }} />
              <span style={{ fontSize: 12, color: "#333" }}>{r.label}</span>
            </label>
          ))}
        </div>

        {/* 추가 의견 */}
        <div style={{ marginBottom: 16 }}>
          <label style={{ fontSize: 10, color: "#555", display: "block", marginBottom: 4 }}>추가 의견 (선택사항)</label>
          <textarea value={comment} onChange={e => setComment(e.target.value)}
            placeholder="서비스 개선을 위한 의견을 남겨주세요"
            style={{ width: "100%", minHeight: 80, border: "1.5px solid #ddd", borderRadius: 5, padding: 10, fontSize: 12, outline: "none", resize: "vertical", boxSizing: "border-box" }} />
        </div>

        <hr style={{ border: "none", borderTop: "1px solid #e0e0e0", margin: "0 0 16px" }} />

        {/* 본인 확인 */}
        <h3 style={{ fontSize: 13, fontWeight: 600, margin: "0 0 12px" }}>본인 확인</h3>
        <div style={{ position: "relative", marginBottom: 4 }}>
          <input type={showPassword ? "text" : "password"} value={password} onChange={e => { setPassword(e.target.value); setPwError(""); }}
            placeholder="비밀번호를 입력하세요"
            style={{ width: "100%", height: 36, border: `1.5px solid ${pwError ? "#E24B4A" : "#ddd"}`, borderRadius: 5, padding: "0 36px 0 10px", fontSize: 12, outline: "none", boxSizing: "border-box" }} />
          <button onClick={() => setShowPassword(!showPassword)}
            style={{ position: "absolute", right: 10, top: "50%", transform: "translateY(-50%)", background: "none", border: "none", cursor: "pointer", fontSize: 14 }}>
            {showPassword ? "🙈" : "👁"}
          </button>
        </div>
        {pwError && <p style={{ fontSize: 11, color: "#E24B4A", margin: "0 0 10px" }}>{pwError}</p>}

        {/* 동의 체크 */}
        <label style={{ display: "flex", alignItems: "flex-start", gap: 8, cursor: "pointer", marginTop: 14, marginBottom: 20 }}>
          <input type="checkbox" checked={agreed} onChange={() => setAgreed(!agreed)} style={{ width: 14, height: 14, marginTop: 2, cursor: "pointer" }} />
          <span style={{ fontSize: 12, color: "#333" }}>위 유의사항을 모두 확인했으며, 회원 탈퇴에 동의합니다</span>
        </label>

        <div style={{ display: "flex", gap: 10 }}>
          <button onClick={() => setShowConfirm(true)} disabled={!isValid}
            style={{ padding: "10px 24px", border: "none", borderRadius: 8, background: !isValid ? "#ccc" : "#c62828", color: "#fff", fontSize: 13, fontWeight: 600, cursor: !isValid ? "not-allowed" : "pointer" }}>
            회원 탈퇴
          </button>
          <button onClick={() => onNavigate("/mypage")}
            style={{ padding: "10px 24px", border: "1.5px solid #ddd", borderRadius: 8, background: "#fff", fontSize: 13, cursor: "pointer" }}>
            취소
          </button>
        </div>
      </div>

      {/* 최종 확인 모달 */}
      {showConfirm && (
        <div style={{ position: "fixed", inset: 0, background: "rgba(0,0,0,0.5)", display: "flex", alignItems: "center", justifyContent: "center", zIndex: 1000 }}>
          <div style={{ background: "#fff", borderRadius: 12, padding: 28, maxWidth: 360, width: "90%" }}>
            <h3 style={{ fontSize: 16, fontWeight: 700, textAlign: "center", margin: "0 0 12px" }}>정말 탈퇴하시겠어요?</h3>
            <p style={{ fontSize: 13, color: "#555", textAlign: "center", lineHeight: 1.6, margin: "0 0 24px" }}>
              탈퇴 후 모든 데이터가 삭제되며<br />복구할 수 없습니다.
            </p>
            <div style={{ display: "flex", gap: 10 }}>
              <button onClick={() => setShowConfirm(false)}
                style={{ flex: 1, height: 40, border: "1.5px solid #ddd", borderRadius: 8, background: "#fff", fontSize: 13, cursor: "pointer" }}>
                취소
              </button>
              <button onClick={handleWithdraw} disabled={isDeleting}
                style={{ flex: 1, height: 40, border: "none", borderRadius: 8, background: isDeleting ? "#aaa" : "#c62828", color: "#fff", fontSize: 13, fontWeight: 600, cursor: isDeleting ? "not-allowed" : "pointer" }}>
                {isDeleting ? "처리 중..." : "탈퇴 확인"}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
