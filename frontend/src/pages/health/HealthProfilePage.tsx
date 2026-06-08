import { useEffect, useState } from "react";

import type { AppRoute } from "../../App";
import { getStoredAccessToken } from "../../api/auth";
import {
  getHealthProfile,
  updateHealthProfile,
  type HealthProfile,
} from "../../api/healthProfile";
import { LoadingState } from "../../components/common/LoadingState";

const fallbackProfile: HealthProfile = {
  name: "홍길동",
  email: "hong@example.com",
  birth_date: "1985-03-15",
  gender: "남성",
  managed_diseases: ["당뇨", "고혈압"],
  height_cm: 175,
  weight_kg: 72.5,
  bmi: 23.7,
  family_history: [
    { condition: "고혈압", relation: "부" },
    { condition: "당뇨", relation: "모" },
    { condition: "만성신장질환", relation: "" },
  ],
  smoking: "비흡연",
  alcohol: "월 2~3회",
};

const DISEASE_COLORS: Record<string, string> = {
  당뇨: "pill-yellow",
  고혈압: "pill-pink",
  이상지질혈증: "pill-blue",
  비만: "pill-green",
  만성신장질환: "pill-violet",
};

type Draft = {
  name: string;
  height_cm: string;
  weight_kg: string;
  smoking: string;
  alcohol: string;
};

function calcBmi(height: string, weight: string): string {
  const h = Number(height) / 100;
  const w = Number(weight);
  if (!h || !w) return "—";
  return (w / (h * h)).toFixed(1);
}

type HealthProfilePageProps = {
  onNavigate?: (route: AppRoute) => void;
};

export function HealthProfilePage({ onNavigate }: HealthProfilePageProps) {
  const [profile, setProfile] = useState<HealthProfile>(fallbackProfile);
  const [isLoading, setIsLoading] = useState(false);
  const [isEditing, setIsEditing] = useState(false);
  const [isSaving, setIsSaving] = useState(false);
  const [draft, setDraft] = useState<Draft>({
    name: "",
    height_cm: "",
    weight_kg: "",
    smoking: "",
    alcohol: "",
  });

  useEffect(() => {
    const token = getStoredAccessToken();
    if (!token) return;
    setIsLoading(true);
    getHealthProfile(token)
      .then((res) => setProfile(res.data))
      .catch(() => {})
      .finally(() => setIsLoading(false));
  }, []);

  function handleEditStart() {
    setDraft({
      name: profile.name,
      height_cm: String(profile.height_cm ?? ""),
      weight_kg: String(profile.weight_kg ?? ""),
      smoking: profile.smoking,
      alcohol: profile.alcohol,
    });
    setIsEditing(true);
  }

  function handleCancel() {
    setIsEditing(false);
  }

  async function handleSave() {
    const token = getStoredAccessToken();
    setIsSaving(true);
    try {
      await updateHealthProfile(
        {
          name: draft.name || undefined,
          height_cm: draft.height_cm ? Number(draft.height_cm) : undefined,
          weight_kg: draft.weight_kg ? Number(draft.weight_kg) : undefined,
          smoking: draft.smoking || undefined,
          alcohol: draft.alcohol || undefined,
        },
        token ?? undefined,
      );
      // 백엔드 없는 환경: 로컬 상태만 업데이트
      setProfile((prev) => ({
        ...prev,
        name: draft.name || prev.name,
        height_cm: draft.height_cm ? Number(draft.height_cm) : prev.height_cm,
        weight_kg: draft.weight_kg ? Number(draft.weight_kg) : prev.weight_kg,
        bmi: draft.height_cm && draft.weight_kg
          ? Number(calcBmi(draft.height_cm, draft.weight_kg))
          : prev.bmi,
        smoking: draft.smoking || prev.smoking,
        alcohol: draft.alcohol || prev.alcohol,
      }));
      setIsEditing(false);
    } catch {
      // API 실패 시에도 로컬 상태 반영
      setProfile((prev) => ({
        ...prev,
        name: draft.name || prev.name,
        height_cm: draft.height_cm ? Number(draft.height_cm) : prev.height_cm,
        weight_kg: draft.weight_kg ? Number(draft.weight_kg) : prev.weight_kg,
        bmi: draft.height_cm && draft.weight_kg
          ? Number(calcBmi(draft.height_cm, draft.weight_kg))
          : prev.bmi,
        smoking: draft.smoking || prev.smoking,
        alcohol: draft.alcohol || prev.alcohol,
      }));
      setIsEditing(false);
    } finally {
      setIsSaving(false);
    }
  }

  function set(key: keyof Draft, value: string) {
    setDraft((prev) => ({ ...prev, [key]: value }));
  }

  if (isLoading) return <LoadingState message="건강 프로필을 불러오는 중입니다." />;

  const displayBmi = isEditing && draft.height_cm && draft.weight_kg
    ? calcBmi(draft.height_cm, draft.weight_kg)
    : String(profile.bmi ?? "—");

  return (
    <div className="health-profile-page page-stack">
      <section className="section-header-row page-heading-row">
        <div className="page-heading">
          <p className="eyebrow">건강 관리</p>
          <h1>건강 프로필</h1>
        </div>
        {!isEditing && (
          <div className="button-row">
            <button type="button" className="green-button" onClick={handleEditStart}>
              프로필 수정
            </button>
          </div>
        )}
      </section>

      {/* 기본 정보 */}
      <section className="dashboard-card hp-section">
        <h2>기본 정보</h2>
        <div className="hp-info-grid">
          <div className="hp-info-item">
            <span className="field-label">이름</span>
            {isEditing ? (
              <input
                type="text"
                className="hp-edit-input"
                value={draft.name}
                onChange={(e) => set("name", e.target.value)}
              />
            ) : (
              <span className="hp-info-val">{profile.name}</span>
            )}
          </div>
          <div className="hp-info-item">
            <span className="field-label">이메일</span>
            <span className="hp-info-val hp-readonly">{profile.email}</span>
          </div>
          <div className="hp-info-item">
            <span className="field-label">생년월일</span>
            <span className="hp-info-val hp-readonly">{profile.birth_date}</span>
          </div>
          <div className="hp-info-item">
            <span className="field-label">성별</span>
            <span className="hp-info-val hp-readonly">{profile.gender}</span>
          </div>
        </div>
      </section>

      {/* 관리 중인 만성질환 */}
      <section className="dashboard-card hp-section">
        <h2>관리 중인 만성질환</h2>
        <p className="goal-section-note">* managed_diseases 배열 기반 표시</p>
        <div className="hp-disease-row">
          {profile.managed_diseases.map((d) => (
            <span key={d} className={`pill ${DISEASE_COLORS[d] ?? "pill-green"}`}>{d}</span>
          ))}
          {profile.managed_diseases.length === 0 && (
            <span className="field-label">등록된 만성질환 없음</span>
          )}
        </div>
      </section>

      {/* 신체 정보 */}
      <section className="dashboard-card hp-section">
        <h2>신체 정보</h2>
        <p className="goal-section-note">* user_profiles 테이블 기준</p>
        <div className="hp-body-grid">
          <div className="hp-body-item">
            <span className="field-label">신장</span>
            {isEditing ? (
              <div className="hp-body-input-wrap">
                <input
                  type="number"
                  step="0.1"
                  className="hp-edit-input"
                  value={draft.height_cm}
                  onChange={(e) => set("height_cm", e.target.value)}
                />
                <span className="hp-body-unit">cm</span>
              </div>
            ) : (
              <strong className="hp-body-val">{profile.height_cm ?? "—"}cm</strong>
            )}
          </div>
          <div className="hp-body-item">
            <span className="field-label">체중</span>
            {isEditing ? (
              <div className="hp-body-input-wrap">
                <input
                  type="number"
                  step="0.1"
                  className="hp-edit-input"
                  value={draft.weight_kg}
                  onChange={(e) => set("weight_kg", e.target.value)}
                />
                <span className="hp-body-unit">kg</span>
              </div>
            ) : (
              <strong className="hp-body-val">{profile.weight_kg ?? "—"}kg</strong>
            )}
          </div>
          <div className="hp-body-item">
            <span className="field-label">BMI</span>
            <strong className="hp-body-val">{displayBmi}</strong>
            {isEditing && <span className="goal-section-note">자동 계산</span>}
          </div>
        </div>
        <div className="hp-vitals-link">
          <button
            type="button"
            className="hp-link-btn"
            onClick={() => onNavigate?.("/health/vitals")}
          >
            → 건강 기록 목록에서 혈당 등 수치 확인
          </button>
        </div>
      </section>

      {/* 가족력 */}
      <section className="dashboard-card hp-section">
        <h2>가족력</h2>
        <p className="goal-section-note">
          * chronic_health_inputs 테이블 기준 (diabetes/hypertension/dyslipidemia/ckd)
        </p>
        {profile.family_history.length === 0 ? (
          <p className="field-label">가족력이 없으면 모두 비활성화 상태로 표시</p>
        ) : (
          <div className="hp-family-grid">
            {profile.family_history.map((fh, i) => (
              <div key={i} className="hp-family-item">
                {fh.condition}{fh.relation ? ` (${fh.relation})` : ""}
              </div>
            ))}
          </div>
        )}
      </section>

      {/* 생활 습관 */}
      <section className="dashboard-card hp-section">
        <h2>생활 습관</h2>
        <div className="hp-info-grid">
          <div className="hp-info-item">
            <span className="field-label">흡연</span>
            {isEditing ? (
              <select
                className="hp-edit-input"
                value={draft.smoking}
                onChange={(e) => set("smoking", e.target.value)}
              >
                <option>비흡연</option>
                <option>과거 흡연</option>
                <option>현재 흡연</option>
              </select>
            ) : (
              <span className="hp-info-val">{profile.smoking}</span>
            )}
          </div>
          <div className="hp-info-item">
            <span className="field-label">음주</span>
            {isEditing ? (
              <select
                className="hp-edit-input"
                value={draft.alcohol}
                onChange={(e) => set("alcohol", e.target.value)}
              >
                <option>음주 안함</option>
                <option>월 1회 미만</option>
                <option>월 2~3회</option>
                <option>주 1~2회</option>
                <option>주 3회 이상</option>
              </select>
            ) : (
              <span className="hp-info-val">{profile.alcohol}</span>
            )}
          </div>
        </div>
      </section>

      {isEditing && (
        <div className="goal-edit-actions">
          <button
            type="button"
            className="wide-subtle-button"
            onClick={handleCancel}
            disabled={isSaving}
          >
            취소
          </button>
          <button
            type="button"
            className="green-button"
            onClick={handleSave}
            disabled={isSaving}
          >
            {isSaving ? "저장 중..." : "저장"}
          </button>
        </div>
      )}
    </div>
  );
}
