import { useEffect, useRef, useState } from "react";
import type { ChangeEvent } from "react";
import type { AppRoute } from "../../App";
import { getStoredAccessToken } from "../../api/auth";
import { ApiError } from "../../api/client";
import {
  confirmCurrentUserEmailChange,
  getCurrentUser,
  requestCurrentUserEmailChange,
  updateCurrentUser,
} from "../../api/users";
import { getStoredProfileImage, resizeProfileImageFile, setStoredProfileImage } from "../../utils/profileImage";

interface EditProfilePageProps {
  onNavigate: (route: AppRoute) => void;
}

const DISEASE_OPTIONS = [
  { code: "HYPERTENSION", label: "고혈압" },
  { code: "DIABETES", label: "당뇨" },
  { code: "DYSLIPIDEMIA", label: "고지혈증" },
  { code: "OBESITY", label: "비만" },
  { code: "CKD", label: "만성신장질환" },
];

export function EditProfilePage({ onNavigate }: EditProfilePageProps) {
  const profileImageInputRef = useRef<HTMLInputElement | null>(null);
  const [email, setEmail] = useState("");
  const [birthday, setBirthday] = useState("");
  const [gender, setGender] = useState<"MALE" | "FEMALE">("MALE");
  const [name, setName] = useState("");
  const [phone, setPhone] = useState("");
  const [profileImageUrl, setProfileImageUrl] = useState<string | null>(null);
  const [profileImagePreviewUrl, setProfileImagePreviewUrl] = useState<string | null>(null);
  const [profileImageDataUrl, setProfileImageDataUrl] = useState<string | null>(null);
  const [selectedProfileImageName, setSelectedProfileImageName] = useState("");
  const [userId, setUserId] = useState<number | null>(null);
  const [height, setHeight] = useState("");
  const [weight, setWeight] = useState("");
  const [diseases, setDiseases] = useState<string[]>([]);
  const [bmi, setBmi] = useState<number | null>(null);
  const [showDiseaseWarning, setShowDiseaseWarning] = useState(false);
  const [isLoading, setIsLoading] = useState(true);
  const [isSaving, setIsSaving] = useState(false);
  const [saveSuccess, setSaveSuccess] = useState(false);
  const [errorMessage, setErrorMessage] = useState("");
  const [showEmailChangeModal, setShowEmailChangeModal] = useState(false);
  const [newEmail, setNewEmail] = useState("");
  const [emailChangeMessage, setEmailChangeMessage] = useState("");
  const [emailChangeError, setEmailChangeError] = useState("");
  const [isRequestingEmailChange, setIsRequestingEmailChange] = useState(false);

  useEffect(() => {
    let ignore = false;

    async function loadUser() {
      try {
        const token = getStoredAccessToken();
        const emailChangeToken = new URLSearchParams(window.location.search).get("email_change_token");
        const changedUser = emailChangeToken
          ? await confirmCurrentUserEmailChange(emailChangeToken, token)
          : null;
        if (emailChangeToken) {
          window.history.replaceState({}, "", "/mypage/edit");
          setEmailChangeMessage("이메일 변경 인증이 완료되었습니다.");
        }
        const user = changedUser ?? await getCurrentUser(token);
        if (ignore) return;
        const storedProfileImage = getStoredProfileImage(user.id);
        const profileImage = storedProfileImage ?? user.profile_image_url;
        setUserId(user.id);
        setName(user.name);
        setEmail(user.email);
        setBirthday(user.birthday);
        setGender(user.gender);
        setPhone(user.phone_number);
        setProfileImageUrl(user.profile_image_url);
        setProfileImagePreviewUrl(profileImage);
        setHeight(user.height ? String(user.height) : "");
        setWeight(user.weight ? String(user.weight) : "");
        setDiseases(user.managed_diseases);
      } catch (error) {
        if (!ignore) {
          if (error instanceof ApiError && new URLSearchParams(window.location.search).get("email_change_token")) {
            setErrorMessage(String(error.detail ?? error.message));
            window.history.replaceState({}, "", "/mypage/edit");
          } else {
            setErrorMessage("내 정보를 불러오지 못했습니다.");
          }
        }
      } finally {
        if (!ignore) setIsLoading(false);
      }
    }

    void loadUser();
    return () => {
      ignore = true;
    };
  }, []);

  useEffect(() => {
    const h = parseFloat(height);
    const w = parseFloat(weight);
    if (h > 0 && w > 0) setBmi(parseFloat((w / Math.pow(h / 100, 2)).toFixed(1)));
    else setBmi(null);
  }, [height, weight]);

  const toggleDisease = (code: string) => {
    const prev = diseases;
    const next = prev.includes(code) ? prev.filter(d => d !== code) : [...prev, code];
    setDiseases(next);
    // 관리 질환 변경 시 경고 안내
    if (next.length !== prev.length) setShowDiseaseWarning(true);
  };

  const handleRequestEmailChange = async () => {
    setIsRequestingEmailChange(true);
    setEmailChangeError("");
    setEmailChangeMessage("");
    try {
      await requestCurrentUserEmailChange({ new_email: newEmail }, getStoredAccessToken());
      setEmailChangeMessage("인증메일을 전송했습니다. 새 이메일의 메일함에서 인증 링크를 눌러주세요.");
    } catch (error) {
      if (error instanceof ApiError) {
        setEmailChangeError(String(error.detail ?? error.message));
      } else {
        setEmailChangeError("인증메일 전송에 실패했습니다.");
      }
    } finally {
      setIsRequestingEmailChange(false);
    }
  };

  const handleProfileImageChange = async (event: ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;
    if (!file.type.startsWith("image/")) {
      setErrorMessage("이미지 파일만 선택할 수 있습니다.");
      return;
    }

    setErrorMessage("");
    try {
      const dataUrl = await resizeProfileImageFile(file);
      setSelectedProfileImageName(file.name);
      setProfileImageDataUrl(dataUrl);
      setProfileImagePreviewUrl(dataUrl);
    } catch {
      setErrorMessage("프로필 사진을 처리하지 못했습니다. 다른 이미지를 선택해주세요.");
    }
  };

  const handleSave = async () => {
    setIsSaving(true);
    setErrorMessage("");
    try {
      await updateCurrentUser(
        {
          phone_number: phone,
          height: height ? Number(height) : undefined,
          weight: weight ? Number(weight) : undefined,
          profile_image_url: profileImageUrl,
          managed_diseases: diseases,
        },
        getStoredAccessToken(),
      );
      if (userId !== null && profileImageDataUrl) {
        setStoredProfileImage(userId, profileImageDataUrl);
      }
      setIsSaving(false);
      setSaveSuccess(true);
      setTimeout(() => { setSaveSuccess(false); onNavigate("/mypage"); }, 1500);
    } catch {
      setIsSaving(false);
      setErrorMessage("정보 저장에 실패했습니다.");
    }
  };

  if (isLoading) {
    return <div className="page-container">내 정보를 불러오는 중입니다.</div>;
  }

  return (
    <div className="page-container">
      <h1 className="page-title">내 정보 수정</h1>

      {saveSuccess && (
        <div style={{ padding: "12px 16px", background: "#e8f5e9", border: "1px solid #a5d6a7", borderRadius: 6, marginBottom: 16, fontSize: 12, color: "#2e7d32" }}>
          정보가 저장되었습니다.
        </div>
      )}
      {errorMessage && (
        <div style={{ padding: "12px 16px", background: "#fff5f5", border: "1px solid #ffcccc", borderRadius: 6, marginBottom: 16, fontSize: 12, color: "#c62828" }}>
          {errorMessage}
        </div>
      )}

      <div style={{ display: "grid", gridTemplateColumns: "1fr 300px", gap: 14 }}>
        {/* 좌측 */}
        <div>
          {/* 기본 정보 */}
          <div style={{ background: "#fff", border: "1px solid #e0e0e0", borderRadius: 10, padding: 20, marginBottom: 14 }}>
            <h3 style={{ fontSize: 13, fontWeight: 600, margin: "0 0 14px" }}>기본 정보</h3>
            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 14 }}>
              {/* 이름 */}
              <div>
                <label style={{ fontSize: 10, color: "#555", display: "block", marginBottom: 4 }}>이름</label>
                <div style={{ height: 34, border: "1.5px solid #e0e0e0", borderRadius: 5, background: "#fafafa", padding: "0 10px", display: "flex", alignItems: "center" }}>
                  <span style={{ fontSize: 11, color: "#aaa" }}>{name}</span>
                </div>
              </div>

              {/* 이메일 */}
              <div>
                <label style={{ fontSize: 10, color: "#555", display: "block", marginBottom: 4 }}>이메일</label>
                <div style={{ height: 34, border: "1.5px solid #e0e0e0", borderRadius: 5, background: "#fafafa", padding: "0 10px", display: "flex", alignItems: "center", justifyContent: "space-between" }}>
                  <span style={{ fontSize: 11, color: "#aaa" }}>{email}</span>
                  <button
                    type="button"
                    onClick={() => {
                      setNewEmail("");
                      setEmailChangeError("");
                      setEmailChangeMessage("");
                      setShowEmailChangeModal(true);
                    }}
                    style={{ padding: "2px 8px", border: "1px solid #e0e0e0", borderRadius: 20, fontSize: 10, color: "#555", background: "#fff", cursor: "pointer", whiteSpace: "nowrap" }}
                  >
                    인증 후 변경
                  </button>
                </div>
                <p style={{ fontSize: 10, color: "#aaa", margin: "4px 0 0" }}>이메일 변경 시 본인 인증이 필요합니다.</p>
              </div>

              {/* 생년월일 */}
              <div>
                <label style={{ fontSize: 10, color: "#555", display: "block", marginBottom: 4 }}>생년월일</label>
                <div style={{ height: 34, border: "1.5px solid #e0e0e0", borderRadius: 5, background: "#fafafa", padding: "0 10px", display: "flex", alignItems: "center" }}>
                  <span style={{ fontSize: 11, color: "#aaa" }}>{birthday}</span>
                </div>
              </div>

              {/* 성별 */}
              <div>
                <label style={{ fontSize: 10, color: "#555", display: "block", marginBottom: 4 }}>성별</label>
                <div style={{ height: 34, border: "1.5px solid #e0e0e0", borderRadius: 5, background: "#fafafa", padding: "0 10px", display: "flex", alignItems: "center" }}>
                  <span style={{ fontSize: 11, color: "#aaa" }}>{gender === "MALE" ? "남성" : "여성"}</span>
                </div>
              </div>

              {/* 연락처 */}
              <div style={{ gridColumn: "span 2" }}>
                <label style={{ fontSize: 10, color: "#555", display: "block", marginBottom: 4 }}>연락처</label>
                <input value={phone} onChange={e => setPhone(e.target.value)} placeholder="010-1234-5678"
                  style={{ width: "100%", height: 34, border: "1.5px solid #ddd", borderRadius: 5, padding: "0 10px", fontSize: 12, outline: "none", boxSizing: "border-box" }} />
              </div>
            </div>
          </div>

          {/* 건강 프로필 */}
          <div style={{ background: "#fff", border: "1px solid #e0e0e0", borderRadius: 10, padding: 20 }}>
            <h3 style={{ fontSize: 13, fontWeight: 600, margin: "0 0 14px" }}>건강 프로필</h3>
            <div style={{ display: "grid", gridTemplateColumns: "repeat(3, 1fr)", gap: 14, marginBottom: 16 }}>
              <div>
                <label style={{ fontSize: 10, color: "#555", display: "block", marginBottom: 4 }}>신장 (cm)</label>
                <input type="number" value={height} onChange={e => setHeight(e.target.value)} placeholder="175"
                  style={{ width: "100%", height: 34, border: "1.5px solid #ddd", borderRadius: 5, padding: "0 10px", fontSize: 12, outline: "none", boxSizing: "border-box" }} />
              </div>
              <div>
                <label style={{ fontSize: 10, color: "#555", display: "block", marginBottom: 4 }}>체중 (kg)</label>
                <input type="number" value={weight} onChange={e => setWeight(e.target.value)} placeholder="72"
                  style={{ width: "100%", height: 34, border: "1.5px solid #ddd", borderRadius: 5, padding: "0 10px", fontSize: 12, outline: "none", boxSizing: "border-box" }} />
              </div>
              <div>
                <label style={{ fontSize: 10, color: "#555", display: "block", marginBottom: 4 }}>BMI (자동 계산)</label>
                <div style={{ height: 34, border: "1.5px solid #e0e0e0", borderRadius: 5, background: "#fafafa", padding: "0 10px", display: "flex", alignItems: "center" }}>
                  <span style={{ fontSize: 12, color: "#555", fontWeight: 600 }}>{bmi ?? "—"}</span>
                </div>
                <p style={{ fontSize: 10, color: "#aaa", margin: "4px 0 0" }}>신장/체중 기준 서버 자동 계산</p>
              </div>
            </div>

            <hr style={{ border: "none", borderTop: "1px solid #e0e0e0", margin: "0 0 14px" }} />

            <h4 style={{ fontSize: 12, fontWeight: 600, margin: "0 0 10px" }}>관리 대상 만성질환</h4>
            {showDiseaseWarning && (
              <div style={{ padding: "8px 12px", background: "#fff8e1", border: "1px solid #ffe082", borderRadius: 6, marginBottom: 10, fontSize: 11, color: "#f57f17" }}>
                ⚠️ 관리 질환 변경 시 건강 목표 및 위험도 예측 기준이 재설정될 수 있습니다.
              </div>
            )}
            <div style={{ display: "grid", gridTemplateColumns: "repeat(3, 1fr)", gap: 8 }}>
              {DISEASE_OPTIONS.map(d => (
                <label key={d.code} style={{ display: "flex", alignItems: "center", gap: 8, cursor: "pointer" }}>
                  <input type="checkbox" checked={diseases.includes(d.code)} onChange={() => toggleDisease(d.code)} style={{ width: 14, height: 14, cursor: "pointer" }} />
                  <span style={{ fontSize: 12, color: "#333" }}>{d.label}</span>
                </label>
              ))}
            </div>
          </div>
        </div>

        {/* 우측 */}
        <div>
          {/* 프로필 사진 */}
          <div style={{ background: "#fff", border: "1px solid #e0e0e0", borderRadius: 10, padding: 16, marginBottom: 14 }}>
            <h3 style={{ fontSize: 12, fontWeight: 600, margin: "0 0 12px" }}>프로필 사진</h3>
            <div style={{ width: "100%", height: 140, background: "#f5f5f5", borderRadius: 8, display: "flex", alignItems: "center", justifyContent: "center", fontSize: 40, marginBottom: 10, overflow: "hidden" }}>
              {profileImagePreviewUrl ? (
                <img src={profileImagePreviewUrl} alt="프로필 미리보기" style={{ width: "100%", height: "100%", objectFit: "cover" }} />
              ) : (
                "👤"
              )}
            </div>
            <input
              ref={profileImageInputRef}
              type="file"
              accept="image/*"
              onChange={handleProfileImageChange}
              style={{ display: "none" }}
            />
            <button
              type="button"
              onClick={() => profileImageInputRef.current?.click()}
              style={{ width: "100%", height: 34, border: "1.5px solid #ddd", borderRadius: 6, background: "#fff", fontSize: 12, cursor: "pointer" }}
            >
              사진 변경
            </button>
            {selectedProfileImageName && (
              <p style={{ fontSize: 10, color: "#777", margin: "8px 0 0", wordBreak: "break-all" }}>
                선택됨: {selectedProfileImageName}
              </p>
            )}
            {!profileImageUrl && !selectedProfileImageName && (
              <p style={{ fontSize: 10, color: "#aaa", margin: "8px 0 0" }}>내 정보 수정 화면에서만 사진을 변경할 수 있습니다.</p>
            )}
          </div>

          {/* 계정 설정 */}
          <div style={{ background: "#fff", border: "1px solid #e0e0e0", borderRadius: 10, padding: 16 }}>
            <h3 style={{ fontSize: 12, fontWeight: 600, margin: "0 0 12px" }}>계정 설정</h3>
            <button onClick={() => onNavigate("/mypage/change-password")}
              style={{ width: "100%", height: 36, border: "1.5px solid #ddd", borderRadius: 6, background: "#fff", fontSize: 12, cursor: "pointer" }}>
              비밀번호 변경
            </button>
          </div>
        </div>
      </div>

      <div style={{ display: "flex", justifyContent: "flex-end", gap: 10, marginTop: 24 }}>
        <button onClick={handleSave} disabled={isSaving}
          style={{ padding: "10px 24px", border: "none", borderRadius: 8, background: isSaving ? "#aaa" : "#1a1a1a", color: "#fff", fontSize: 13, fontWeight: 600, cursor: isSaving ? "not-allowed" : "pointer" }}>
          {isSaving ? "저장 중..." : "저장"}
        </button>
        <button onClick={() => onNavigate("/mypage")}
          style={{ padding: "10px 24px", border: "1.5px solid #ddd", borderRadius: 8, background: "#fff", fontSize: 13, cursor: "pointer" }}>
          취소
        </button>
      </div>
      <div style={{ display: "flex", justifyContent: "flex-end", marginTop: 18 }}>
        <button
          type="button"
          onClick={() => onNavigate("/mypage/withdrawal")}
          style={{ border: "none", background: "transparent", color: "#999", fontSize: 11, cursor: "pointer", textDecoration: "underline" }}
        >
          회원 탈퇴하기
        </button>
      </div>

      {showEmailChangeModal && (
        <div className="app-modal-backdrop" role="dialog" aria-modal="true">
          <div className="app-modal-card" style={{ padding: 24, maxWidth: 420 }}>
            <h2 style={{ margin: "0 0 8px", fontSize: 18 }}>이메일 변경</h2>
            <p style={{ margin: "0 0 16px", color: "#666", fontSize: 13, lineHeight: 1.6 }}>
              새 이메일 주소를 입력하면 인증메일을 전송합니다.
              <br />
              인증 링크를 누르면 이메일이 변경됩니다.
            </p>
            <label style={{ display: "grid", gap: 6, fontSize: 12, color: "#555", fontWeight: 600 }}>
              새 이메일
              <input
                type="email"
                value={newEmail}
                onChange={(event) => setNewEmail(event.target.value)}
                placeholder="example@email.com"
                style={{ width: "100%", height: 38, border: "1.5px solid #ddd", borderRadius: 6, padding: "0 10px", fontSize: 13, boxSizing: "border-box" }}
              />
            </label>
            {emailChangeMessage && (
              <p style={{ margin: "12px 0 0", color: "#2e7d32", fontSize: 12, lineHeight: 1.5 }}>{emailChangeMessage}</p>
            )}
            {emailChangeError && (
              <p style={{ margin: "12px 0 0", color: "#c62828", fontSize: 12, lineHeight: 1.5 }}>{emailChangeError}</p>
            )}
            <div style={{ display: "flex", gap: 10, marginTop: 18 }}>
              <button
                type="button"
                className="wide-subtle-button"
                onClick={() => setShowEmailChangeModal(false)}
                style={{ flex: 1 }}
              >
                닫기
              </button>
              <button
                type="button"
                className="green-button"
                onClick={handleRequestEmailChange}
                disabled={isRequestingEmailChange || !newEmail}
                style={{ flex: 1 }}
              >
                {isRequestingEmailChange ? "전송 중..." : "인증메일 전송"}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
