import { useEffect, useState } from "react";
import type { AppRoute } from "../../App";
import { getStoredAccessToken } from "../../api/auth";
import { getCurrentUser, type UserInfo } from "../../api/users";

interface MyInfoPageProps {
  onNavigate: (route: AppRoute) => void;
}

const DISEASE_LABEL: Record<string, string> = {
  DIABETES: "당뇨",
  HYPERTENSION: "고혈압",
  DYSLIPIDEMIA: "고지혈증",
  OBESITY: "비만",
  CKD: "만성신장질환",
};

function formatDate(value: string) {
  return value.split("T")[0];
}

export function MyInfoPage({ onNavigate }: MyInfoPageProps) {
  const [user, setUser] = useState<UserInfo | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [errorMessage, setErrorMessage] = useState("");

  useEffect(() => {
    let ignore = false;

    async function loadUser() {
      try {
        const result = await getCurrentUser(getStoredAccessToken());
        if (!ignore) setUser(result);
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

  if (isLoading) {
    return <div className="page-container">내 정보를 불러오는 중입니다.</div>;
  }

  if (errorMessage || !user) {
    return (
      <div className="page-container">
        <h1 className="page-title">내 정보</h1>
        <p style={{ color: "#c62828", fontSize: 13 }}>{errorMessage || "내 정보가 없습니다."}</p>
      </div>
    );
  }

  return (
    <div className="page-container">
      <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: 20 }}>
        <h1 className="page-title" style={{ margin: 0 }}>내 정보</h1>
        <button onClick={() => onNavigate("/mypage/edit")}
          style={{ padding: "8px 16px", border: "none", borderRadius: 8, background: "#1a1a1a", color: "#fff", fontSize: 13, fontWeight: 600, cursor: "pointer" }}>
          정보 수정
        </button>
      </div>

      {/* 계정 통계 요약 */}
      <div style={{ display: "grid", gridTemplateColumns: "repeat(4, 1fr)", gap: 12, marginBottom: 20 }}>
        {[
          { label: "레벨", val: user.level, unit: "Lv", bg: "#e8f5e9", color: "#2e7d32", border: "#a5d6a7" },
          { label: "포인트", val: user.points.toLocaleString(), unit: "P", bg: "#fff8e1", color: "#f57f17", border: "#ffe082" },
          { label: "BMI", val: user.bmi ?? "-", unit: "", bg: "#e3f2fd", color: "#1565c0", border: "#90caf9" },
          { label: "가입일수", val: user.joined_days, unit: "일", bg: "#fce4ec", color: "#c2185b", border: "#f48fb1" },
        ].map(item => (
          <div key={item.label} style={{ padding: "12px 14px", background: item.bg, border: `1.5px solid ${item.border}`, borderRadius: 8, textAlign: "center" }}>
            <div style={{ fontSize: 10, color: item.color, marginBottom: 4 }}>{item.label}</div>
            <div style={{ fontSize: 18, fontWeight: 700, color: item.color }}>
              {item.val}<span style={{ fontSize: 10, fontWeight: 400, color: "#aaa" }}>{item.unit}</span>
            </div>
          </div>
        ))}
      </div>

      <div style={{ display: "grid", gridTemplateColumns: "1fr 300px", gap: 14 }}>
        {/* 좌측 */}
        <div>
          {/* 기본 정보 */}
          <div style={{ background: "#fff", border: "1px solid #e0e0e0", borderRadius: 10, padding: 20, marginBottom: 14 }}>
            <h3 style={{ fontSize: 13, fontWeight: 600, margin: "0 0 14px" }}>기본 정보</h3>
            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 14 }}>
              {[
                { label: "이름", val: user.name },
                { label: "이메일", val: user.email },
                { label: "생년월일", val: user.birthday },
                { label: "성별", val: user.gender === "MALE" ? "남성" : "여성" },
                { label: "연락처", val: user.phone_number },
                { label: "가입일", val: formatDate(user.created_at) },
              ].map(item => (
                <div key={item.label}>
                  <p style={{ fontSize: 11, color: "#888", margin: "0 0 4px" }}>{item.label}</p>
                  <p style={{ fontSize: 13, fontWeight: 600, margin: 0 }}>{item.val}</p>
                </div>
              ))}
            </div>
          </div>

          {/* 건강 프로필 */}
          <div style={{ background: "#fff", border: "1px solid #e0e0e0", borderRadius: 10, padding: 20 }}>
            <h3 style={{ fontSize: 13, fontWeight: 600, margin: "0 0 14px" }}>건강 프로필</h3>
            <div style={{ display: "grid", gridTemplateColumns: "repeat(3, 1fr)", gap: 14, marginBottom: 16 }}>
              {[
                { label: "신장", val: user.height ? `${user.height} cm` : "미입력" },
                { label: "체중", val: user.weight ? `${user.weight} kg` : "미입력" },
                { label: "BMI", val: user.bmi ?? "미입력" },
              ].map(item => (
                <div key={item.label}>
                  <p style={{ fontSize: 11, color: "#888", margin: "0 0 4px" }}>{item.label}</p>
                  <p style={{ fontSize: 13, fontWeight: 600, margin: 0 }}>{item.val}</p>
                </div>
              ))}
            </div>
            <hr style={{ border: "none", borderTop: "1px solid #e0e0e0", margin: "0 0 14px" }} />
            <h4 style={{ fontSize: 12, fontWeight: 600, margin: "0 0 10px" }}>관리 대상 만성질환</h4>
            <div style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
              {user.managed_diseases.map(d => (
                <span key={d} style={{ padding: "4px 10px", background: "#f0f0f0", border: "1px solid #ddd", borderRadius: 20, fontSize: 11 }}>
                  {DISEASE_LABEL[d] || d}
                </span>
              ))}
            </div>
          </div>
        </div>

        {/* 우측 */}
        <div>
          {/* 프로필 사진 */}
          <div style={{ background: "#fff", border: "1px solid #e0e0e0", borderRadius: 10, padding: 16, marginBottom: 14 }}>
            <h3 style={{ fontSize: 12, fontWeight: 600, margin: "0 0 12px" }}>프로필 사진</h3>
            <div style={{ width: "100%", height: 140, background: "#f5f5f5", borderRadius: 8, display: "flex", alignItems: "center", justifyContent: "center", fontSize: 40, marginBottom: 10 }}>
              {user.profile_image_url ? <img src={user.profile_image_url} alt="프로필" style={{ width: "100%", height: "100%", objectFit: "cover", borderRadius: 8 }} /> : "👤"}
            </div>
            <button onClick={() => onNavigate("/mypage/edit")}
              style={{ width: "100%", height: 34, border: "1.5px solid #ddd", borderRadius: 6, background: "#fff", fontSize: 12, cursor: "pointer" }}>
              사진 변경
            </button>
          </div>

          {/* 계정 상태 */}
          <div style={{ background: "#fff", border: "1px solid #e0e0e0", borderRadius: 10, padding: 16 }}>
            <h3 style={{ fontSize: 12, fontWeight: 600, margin: "0 0 12px" }}>계정 상태</h3>
            <div style={{ display: "flex", flexDirection: "column", gap: 10 }}>
              {[
                { label: "회원 등급", val: user.membership_grade },
                { label: "포인트", val: `${user.points.toLocaleString()} P` },
                { label: "레벨", val: `Lv. ${user.level}` },
              ].map((item, i) => (
                <div key={item.label}>
                  {i > 0 && <hr style={{ border: "none", borderTop: "1px solid #f0f0f0", margin: "0 0 10px" }} />}
                  <p style={{ fontSize: 11, color: "#888", margin: "0 0 2px" }}>{item.label}</p>
                  <p style={{ fontSize: 13, fontWeight: 600, margin: 0 }}>{item.val}</p>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
