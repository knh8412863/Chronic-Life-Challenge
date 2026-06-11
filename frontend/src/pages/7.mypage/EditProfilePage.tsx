import { useState, useEffect } from "react";
import type { AppRoute } from "../../App";
import { getStoredAccessToken } from "../../api/auth";
import { getCurrentUser, updateCurrentUser } from "../../api/users";

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
  const [email, setEmail] = useState("");
  const [birthday, setBirthday] = useState("");
  const [gender, setGender] = useState<"MALE" | "FEMALE">("MALE");
  const [name, setName] = useState("");
  const [phone, setPhone] = useState("");
  const [height, setHeight] = useState("");
  const [weight, setWeight] = useState("");
  const [diseases, setDiseases] = useState<string[]>([]);
  const [bmi, setBmi] = useState<number | null>(null);
  const [showDiseaseWarning, setShowDiseaseWarning] = useState(false);
  const [isLoading, setIsLoading] = useState(true);
  const [isSaving, setIsSaving] = useState(false);
  const [saveSuccess, setSaveSuccess] = useState(false);
  const [errorMessage, setErrorMessage] = useState("");

  useEffect(() => {
    let ignore = false;

    async function loadUser() {
      try {
        const user = await getCurrentUser(getStoredAccessToken());
        if (ignore) return;
        setName(user.name);
        setEmail(user.email);
        setBirthday(user.birthday);
        setGender(user.gender);
        setPhone(user.phone_number);
        setHeight(user.height ? String(user.height) : "");
        setWeight(user.weight ? String(user.weight) : "");
        setDiseases(user.managed_diseases);
      } catch {
        if (!ignore) setErrorMessage("내 정보를 불러오지 못했습니다.");
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

  const handleSave = async () => {
    setIsSaving(true);
    setErrorMessage("");
    try {
      await updateCurrentUser(
        {
          phone_number: phone,
          height: height ? Number(height) : undefined,
          weight: weight ? Number(weight) : undefined,
          managed_diseases: diseases,
        },
        getStoredAccessToken(),
      );
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
                <label style={{ fontSize: 10, color: "#555", display: "block", marginBottom: 4 }}>이름 (읽기 전용)</label>
                <div style={{ height: 34, border: "1.5px solid #e0e0e0", borderRadius: 5, background: "#fafafa", padding: "0 10px", display: "flex", alignItems: "center" }}>
                  <span style={{ fontSize: 11, color: "#aaa" }}>{name}</span>
                </div>
              </div>

              {/* 이메일 — 수정 불가 */}
              <div>
                <label style={{ fontSize: 10, color: "#555", display: "block", marginBottom: 4 }}>이메일</label>
                <div style={{ height: 34, border: "1.5px solid #e0e0e0", borderRadius: 5, background: "#fafafa", padding: "0 10px", display: "flex", alignItems: "center", justifyContent: "space-between" }}>
                  <span style={{ fontSize: 11, color: "#aaa" }}>{email}</span>
                  <button
                    type="button"
                    disabled
                    title="이메일 변경 API가 준비되면 활성화됩니다."
                    style={{ padding: "2px 8px", border: "1px solid #e0e0e0", borderRadius: 20, fontSize: 10, color: "#888", background: "#fff", cursor: "not-allowed", whiteSpace: "nowrap" }}
                  >
                    인증 후 변경
                  </button>
                </div>
                <p style={{ fontSize: 10, color: "#aaa", margin: "4px 0 0" }}>이메일 변경 시 본인 인증이 필요합니다.</p>
              </div>

              {/* 생년월일 — 읽기 전용 */}
              <div>
                <label style={{ fontSize: 10, color: "#555", display: "block", marginBottom: 4 }}>생년월일 (읽기 전용)</label>
                <div style={{ height: 34, border: "1.5px solid #e0e0e0", borderRadius: 5, background: "#fafafa", padding: "0 10px", display: "flex", alignItems: "center" }}>
                  <span style={{ fontSize: 11, color: "#aaa" }}>{birthday}</span>
                </div>
              </div>

              {/* 성별 — 읽기 전용 */}
              <div>
                <label style={{ fontSize: 10, color: "#555", display: "block", marginBottom: 4 }}>성별 (읽기 전용)</label>
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
            <div style={{ width: "100%", height: 140, background: "#f5f5f5", borderRadius: 8, display: "flex", alignItems: "center", justifyContent: "center", fontSize: 40, marginBottom: 10 }}>👤</div>
            <button style={{ width: "100%", height: 34, border: "1.5px solid #ddd", borderRadius: 6, background: "#fff", fontSize: 12, cursor: "pointer" }}>
              {/* TODO: 파일 업로드 후 profile_image_url을 PATCH /api/v1/users/me 에 포함 */}
              사진 변경
            </button>
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
    </div>
  );
}
