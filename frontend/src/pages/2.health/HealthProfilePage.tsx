import { useEffect, useState } from "react";

import type { AppRoute } from "../../App";
import { getStoredAccessToken } from "../../api/auth";
import {
  getHealthProfile,
  updateHealthProfile,
  type HealthProfile,
} from "../../api/healthProfile";
import { ErrorState } from "../../components/common/ErrorState";
import { LoadingState } from "../../components/common/LoadingState";

const fallbackProfile: HealthProfile = {
  name: "",
  email: "",
  birth_date: "",
  gender: "",
  managed_diseases: [],
  height_cm: null,
  weight_kg: null,
  bmi: null,
  family_history: [],
  diagnosed_diseases: [],
  medications: [],
  last_checkup_period: null,
  smoking: "미입력",
  alcohol: "미입력",
  alcohol_amount: null,
  sedentary_hours: null,
  exercise_frequency: null,
  walking_days: null,
  sleep_hours: null,
  stress_level: null,
  diet_score: null,
};

const DISEASE_COLORS: Record<string, string> = {
  당뇨: "pill-yellow",
  DIABETES: "pill-yellow",
  고혈압: "pill-pink",
  HYPERTENSION: "pill-pink",
  이상지질혈증: "pill-blue",
  고지혈증: "pill-blue",
  DYSLIPIDEMIA: "pill-blue",
  비만: "pill-green",
  OBESITY: "pill-green",
  만성신장질환: "pill-violet",
  CKD: "pill-violet",
  OTHER: "pill-green",
};

const DISEASE_LABELS: Record<string, string> = {
  DIABETES: "당뇨",
  HYPERTENSION: "고혈압",
  DYSLIPIDEMIA: "고지혈증",
  OBESITY: "비만",
  CKD: "만성신장질환",
  OTHER: "기타",
};

const DISEASE_OPTIONS = [
  { code: "DIABETES", label: "당뇨" },
  { code: "HYPERTENSION", label: "고혈압" },
  { code: "DYSLIPIDEMIA", label: "고지혈증" },
  { code: "OBESITY", label: "비만" },
  { code: "CKD", label: "만성신장질환" },
];

const MEDICATION_OPTIONS = [
  { code: "HYPERTENSION", label: "고혈압 약" },
  { code: "DIABETES", label: "당뇨 약" },
];

const CHECKUP_OPTIONS = [
  { value: "UNDER_6_MONTHS", label: "6개월 미만" },
  { value: "UNDER_1_YEAR", label: "6개월~1년 미만" },
  { value: "OVER_1_YEAR", label: "1년 이상" },
  { value: "NEVER", label: "한 적 없음" },
];

const SMOKING_OPTIONS = [
  { value: "현재 흡연", label: "예" },
  { value: "비흡연", label: "아니오" },
  { value: "과거 흡연", label: "과거 흡연" },
];

const ALCOHOL_OPTIONS = ["안 마심", "월 1~2회", "주 1~2회", "주 3회 이상"];
const ALCOHOL_AMOUNT_OPTIONS = [
  { value: "1", label: "1~2잔" },
  { value: "2", label: "3~4잔" },
  { value: "3", label: "5~6잔" },
  { value: "4", label: "7~9잔" },
  { value: "5", label: "10잔 이상" },
];
const SEDENTARY_OPTIONS = [
  { value: "1", label: "2시간 미만" },
  { value: "3.5", label: "2~5시간" },
  { value: "6.5", label: "5~8시간" },
  { value: "9", label: "8~10시간" },
  { value: "10", label: "10시간 이상" },
];
const EXERCISE_OPTIONS = [
  { value: "0", label: "거의 안 함" },
  { value: "2", label: "주 1~2회" },
  { value: "4", label: "주 3~4회" },
  { value: "7", label: "거의 매일" },
];
const WALKING_OPTIONS = [
  { value: "0", label: "주 0일" },
  { value: "2", label: "주 1~2일" },
  { value: "4", label: "주 3~4일" },
  { value: "6", label: "주 5~6일" },
  { value: "7", label: "매일" },
];
const SLEEP_OPTIONS = [
  { value: "5", label: "5시간 이하" },
  { value: "6.5", label: "6~7시간" },
  { value: "8", label: "8시간 이상" },
];

const FAMILY_CONDITION_LABELS: Record<string, string> = {
  DIABETES: "당뇨",
  HYPERTENSION: "고혈압",
  CKD: "만성신장질환",
};

const FAMILY_RELATION_LABELS: Record<string, string> = {
  FATHER: "아버지",
  MOTHER: "어머니",
  SIBLING: "형제/자매",
};

type Draft = {
  height_cm: string;
  weight_kg: string;
  managed_diseases: string[];
  diagnosed_diseases: string[];
  medications: string[];
  last_checkup_period: string;
  fh_diabetes_father: boolean;
  fh_diabetes_mother: boolean;
  fh_diabetes_sibling: boolean;
  fh_hypertension_father: boolean;
  fh_hypertension_mother: boolean;
  fh_hypertension_sibling: boolean;
  family_history_ckd: boolean;
  smoking: string;
  alcohol: string;
  alcohol_amount: string;
  sedentary_hours: string;
  exercise_frequency: string;
  walking_days: string;
  sleep_hours: string;
  stress_level: string;
  meal_patterns: string[];
  food_preferences: string[];
};

type HealthProfilePageProps = {
  onNavigate?: (route: AppRoute) => void;
};

function calcBmi(height: string, weight: string): string {
  const h = Number(height) / 100;
  const w = Number(weight);
  if (!h || !w) return "—";
  return (w / (h * h)).toFixed(1);
}

function toNumber(value: string): number | null {
  if (!value.trim()) return null;
  const parsed = Number(value);
  return Number.isFinite(parsed) ? parsed : null;
}

function toggle(items: string[], item: string) {
  return items.includes(item) ? items.filter((value) => value !== item) : [...items, item];
}

function checkupLabel(value?: string | null) {
  return CHECKUP_OPTIONS.find((item) => item.value === value)?.label ?? "미입력";
}

function diseaseLabels(values: string[]) {
  return values.map((value) => DISEASE_LABELS[value] ?? value);
}

function medicationLabels(values: string[]) {
  return values.map((value) => MEDICATION_OPTIONS.find((item) => item.code === value)?.label ?? value);
}

function dietScoreValue(mealPatterns: string[], foodPreferences: string[]): number | null {
  if (mealPatterns.length === 0 && foodPreferences.length === 0) return null;
  let score = 6;
  if (mealPatterns.includes("규칙적인 식사")) score += 2;
  if (mealPatterns.some((item) => ["야식 자주 섭취", "끼니를 거르는 편"].includes(item))) score -= 2;
  if (foodPreferences.includes("채소 섭취가 많은 편")) score += 2;
  if (foodPreferences.some((item) => ["단 음식 선호", "짠 음식 선호", "기름진 음식 선호"].includes(item))) score -= 2;
  return Math.max(0, Math.min(10, score));
}

function familyFlags(profile: HealthProfile) {
  return {
    fh_diabetes_father: profile.family_history.some((item) => item.condition === "DIABETES" && item.relation === "FATHER"),
    fh_diabetes_mother: profile.family_history.some((item) => item.condition === "DIABETES" && item.relation === "MOTHER"),
    fh_diabetes_sibling: profile.family_history.some((item) => item.condition === "DIABETES" && item.relation === "SIBLING"),
    fh_hypertension_father: profile.family_history.some((item) => item.condition === "HYPERTENSION" && item.relation === "FATHER"),
    fh_hypertension_mother: profile.family_history.some((item) => item.condition === "HYPERTENSION" && item.relation === "MOTHER"),
    fh_hypertension_sibling: profile.family_history.some((item) => item.condition === "HYPERTENSION" && item.relation === "SIBLING"),
    family_history_ckd: profile.family_history.some((item) => item.condition === "CKD"),
  };
}

function emptyToDefaultAlcoholAmount(alcohol: string, amount: string) {
  if (!alcohol || alcohol === "음주 안함" || alcohol === "안 마심") return null;
  return toNumber(amount) ?? 1;
}

function optionLabel(options: Array<{ value: string; label: string }>, value?: number | null) {
  if (value == null) return "미입력";
  return options.find((item) => Number(item.value) === Number(value))?.label ?? String(value);
}

function isDrinking(value: string) {
  return Boolean(value) && value !== "음주 안함" && value !== "안 마심";
}

function ChoiceGroup({
  options,
  value,
  onSelect,
}: {
  options: Array<string | { value: string; label: string }>;
  value: string;
  onSelect: (value: string) => void;
}) {
  return (
    <div className="hp-choice-grid">
      {options.map((item) => {
        const optionValue = typeof item === "string" ? item : item.value;
        const label = typeof item === "string" ? item : item.label;
        return (
          <button
            key={optionValue}
            type="button"
            className={`hp-choice ${value === optionValue ? "is-active" : ""}`}
            onClick={() => onSelect(optionValue)}
          >
            {label}
          </button>
        );
      })}
    </div>
  );
}

export function HealthProfilePage({ onNavigate }: HealthProfilePageProps) {
  const [profile, setProfile] = useState<HealthProfile>(fallbackProfile);
  const [isLoading, setIsLoading] = useState(false);
  const [isEditing, setIsEditing] = useState(false);
  const [isSaving, setIsSaving] = useState(false);
  const [errorMessage, setErrorMessage] = useState("");
  const [draft, setDraft] = useState<Draft>({
    height_cm: "",
    weight_kg: "",
    managed_diseases: [],
    diagnosed_diseases: [],
    medications: [],
    last_checkup_period: "",
    fh_diabetes_father: false,
    fh_diabetes_mother: false,
    fh_diabetes_sibling: false,
    fh_hypertension_father: false,
    fh_hypertension_mother: false,
    fh_hypertension_sibling: false,
    family_history_ckd: false,
    smoking: "",
    alcohol: "",
    alcohol_amount: "",
    sedentary_hours: "",
    exercise_frequency: "",
    walking_days: "",
    sleep_hours: "",
    stress_level: "",
    meal_patterns: [],
    food_preferences: [],
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
    const flags = familyFlags(profile);
    setDraft({
      height_cm: String(profile.height_cm ?? ""),
      weight_kg: String(profile.weight_kg ?? ""),
      managed_diseases: profile.managed_diseases,
      diagnosed_diseases: profile.diagnosed_diseases,
      medications: profile.medications,
      last_checkup_period: profile.last_checkup_period ?? "",
      ...flags,
      smoking: profile.smoking === "미입력" ? "비흡연" : profile.smoking,
      alcohol: profile.alcohol === "미입력" ? "안 마심" : profile.alcohol.split(",")[0].replace("음주 안함", "안 마심"),
      alcohol_amount: String(profile.alcohol_amount ?? ""),
      sedentary_hours: String(profile.sedentary_hours ?? ""),
      exercise_frequency: String(profile.exercise_frequency ?? ""),
      walking_days: String(profile.walking_days ?? ""),
      sleep_hours: String(profile.sleep_hours ?? ""),
      stress_level: String(profile.stress_level ?? ""),
      meal_patterns: [],
      food_preferences: [],
    });
    setIsEditing(true);
  }

  function handleCancel() {
    setIsEditing(false);
  }

  async function handleSave() {
    const token = getStoredAccessToken();
    const height = toNumber(draft.height_cm);
    const weight = toNumber(draft.weight_kg);
    if (!height || !weight) {
      setErrorMessage("건강 프로필 저장을 위해 신장과 체중을 입력해 주세요.");
      return;
    }

    setIsSaving(true);
    setErrorMessage("");
    try {
      const response = await updateHealthProfile(
        {
          height_cm: height,
          weight_kg: weight,
          managed_diseases: draft.managed_diseases,
          diagnosed_diseases: draft.diagnosed_diseases,
          medications: draft.medications,
          last_checkup_period: draft.last_checkup_period || null,
          fh_diabetes_father: draft.fh_diabetes_father,
          fh_diabetes_mother: draft.fh_diabetes_mother,
          fh_diabetes_sibling: draft.fh_diabetes_sibling,
          fh_hypertension_father: draft.fh_hypertension_father,
          fh_hypertension_mother: draft.fh_hypertension_mother,
          fh_hypertension_sibling: draft.fh_hypertension_sibling,
          family_history_ckd: draft.family_history_ckd,
          smoking: draft.smoking || "비흡연",
          alcohol: draft.alcohol || "음주 안함",
          alcohol_amount: emptyToDefaultAlcoholAmount(draft.alcohol, draft.alcohol_amount),
          sedentary_hours: toNumber(draft.sedentary_hours),
          exercise_frequency: toNumber(draft.exercise_frequency),
          walking_days: toNumber(draft.walking_days),
          sleep_hours: toNumber(draft.sleep_hours),
          stress_level: toNumber(draft.stress_level),
          diet_score: dietScoreValue(draft.meal_patterns, draft.food_preferences) ?? profile.diet_score,
        },
        token ?? undefined,
      );
      setProfile(response.data);
      setIsEditing(false);
    } catch {
      setErrorMessage("건강 프로필 저장에 실패했습니다. 입력값과 로그인 상태를 확인해 주세요.");
    } finally {
      setIsSaving(false);
    }
  }

  function set(key: keyof Draft, value: string | string[] | boolean) {
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
            <button type="button" className="wide-subtle-button" onClick={() => onNavigate?.("/health/goal")}>
              건강 목표 설정
            </button>
          </div>
        )}
      </section>

      {errorMessage && <ErrorState title={errorMessage} />}

      <section className="dashboard-card hp-section">
        <h2>기본 정보</h2>
        <div className="hp-info-grid">
          <div className="hp-info-item"><span className="field-label">이름</span><span className="hp-info-val hp-readonly">{profile.name}</span></div>
          <div className="hp-info-item"><span className="field-label">이메일</span><span className="hp-info-val hp-readonly">{profile.email}</span></div>
          <div className="hp-info-item"><span className="field-label">생년월일</span><span className="hp-info-val hp-readonly">{profile.birth_date}</span></div>
          <div className="hp-info-item"><span className="field-label">성별</span><span className="hp-info-val hp-readonly">{profile.gender === "MALE" ? "남성" : profile.gender === "FEMALE" ? "여성" : profile.gender}</span></div>
        </div>
      </section>

      <section className="dashboard-card hp-section">
        <h2>신체 정보</h2>
        <div className="hp-body-grid">
          <div className="hp-body-item">
            <span className="field-label">신장</span>
            {isEditing ? <div className="hp-body-input-wrap"><input type="number" step="0.1" className="hp-edit-input" value={draft.height_cm} onChange={(e) => set("height_cm", e.target.value)} /><span className="hp-body-unit">cm</span></div> : <strong className="hp-body-val">{profile.height_cm ?? "—"}cm</strong>}
          </div>
          <div className="hp-body-item">
            <span className="field-label">체중</span>
            {isEditing ? <div className="hp-body-input-wrap"><input type="number" step="0.1" className="hp-edit-input" value={draft.weight_kg} onChange={(e) => set("weight_kg", e.target.value)} /><span className="hp-body-unit">kg</span></div> : <strong className="hp-body-val">{profile.weight_kg ?? "—"}kg</strong>}
          </div>
          <div className="hp-body-item"><span className="field-label">BMI</span><strong className="hp-body-val">{displayBmi}</strong>{isEditing && <span className="goal-section-note">자동 계산</span>}</div>
        </div>
      </section>

      <section className="dashboard-card hp-section">
        <h2>질병력</h2>
        {isEditing ? (
          <div className="hp-chip-grid">
            {DISEASE_OPTIONS.map((item) => <button key={item.code} type="button" className={`hp-chip ${draft.diagnosed_diseases.includes(item.code) ? "is-active" : ""}`} onClick={() => set("diagnosed_diseases", toggle(draft.diagnosed_diseases, item.code))}>{item.label}</button>)}
          </div>
        ) : (
          <div className="hp-disease-row">{profile.diagnosed_diseases.length ? diseaseLabels(profile.diagnosed_diseases).map((d) => <span key={d} className={`pill ${DISEASE_COLORS[d] ?? "pill-green"}`}>{d}</span>) : <span className="field-label">진단받은 질병 없음</span>}</div>
        )}
      </section>

      <section className="dashboard-card hp-section">
        <h2>관리 중인 만성질환</h2>
        {isEditing ? (
          <div className="hp-chip-grid">
            {DISEASE_OPTIONS.map((item) => <button key={item.code} type="button" className={`hp-chip ${draft.managed_diseases.includes(item.code) ? "is-active" : ""}`} onClick={() => set("managed_diseases", toggle(draft.managed_diseases, item.code))}>{item.label}</button>)}
          </div>
        ) : (
          <div className="hp-disease-row">{profile.managed_diseases.length ? profile.managed_diseases.map((d) => <span key={d} className={`pill ${DISEASE_COLORS[d] ?? "pill-green"}`}>{DISEASE_LABELS[d] ?? d}</span>) : <span className="field-label">등록된 만성질환 없음</span>}</div>
        )}
      </section>

      <section className="dashboard-card hp-section">
        <h2>가족력</h2>
        {isEditing ? (
          <div className="hp-family-edit-grid">
            {[
              ["당뇨", [["아버지", "fh_diabetes_father"], ["어머니", "fh_diabetes_mother"], ["형제/자매", "fh_diabetes_sibling"]]],
              ["고혈압", [["아버지", "fh_hypertension_father"], ["어머니", "fh_hypertension_mother"], ["형제/자매", "fh_hypertension_sibling"]]],
            ].map(([title, items]) => (
              <div key={title as string} className="hp-family-edit-card">
                <strong>{title as string}</strong>
                {(items as string[][]).map(([label, key]) => <label key={key}><input type="checkbox" checked={Boolean(draft[key as keyof Draft])} onChange={(e) => set(key as keyof Draft, e.target.checked)} />{label}</label>)}
              </div>
            ))}
            <div className="hp-family-edit-card"><strong>만성신장질환</strong><label><input type="checkbox" checked={draft.family_history_ckd} onChange={(e) => set("family_history_ckd", e.target.checked)} />가족력 있음</label></div>
          </div>
        ) : profile.family_history.length === 0 ? (
          <p className="field-label">등록된 가족력 없음</p>
        ) : (
          <div className="hp-family-grid">{profile.family_history.map((fh, i) => <div key={i} className="hp-family-item">{FAMILY_CONDITION_LABELS[fh.condition] ?? fh.condition}{fh.relation ? ` (${FAMILY_RELATION_LABELS[fh.relation] ?? fh.relation})` : ""}</div>)}</div>
        )}
      </section>

      <section className="dashboard-card hp-section">
        <h2>현재 복용 중인 약</h2>
        {isEditing ? <div className="hp-chip-grid">{MEDICATION_OPTIONS.map((item) => <button key={item.code} type="button" className={`hp-chip ${draft.medications.includes(item.code) ? "is-active" : ""}`} onClick={() => set("medications", toggle(draft.medications, item.code))}>{item.label}</button>)}</div> : <div className="hp-disease-row">{profile.medications.length ? medicationLabels(profile.medications).map((item) => <span key={item} className="pill pill-blue">{item}</span>) : <span className="field-label">복용 중인 약 없음</span>}</div>}
      </section>

      <section className="dashboard-card hp-section">
        <h2>최근 건강검진</h2>
        {isEditing ? <select className="hp-edit-input" value={draft.last_checkup_period} onChange={(e) => set("last_checkup_period", e.target.value)}><option value="">미입력</option>{CHECKUP_OPTIONS.map((item) => <option key={item.value} value={item.value}>{item.label}</option>)}</select> : <span className="hp-info-val">{checkupLabel(profile.last_checkup_period)}</span>}
      </section>

      <section className="dashboard-card hp-section">
        <h2>생활 습관</h2>
        {isEditing ? (
          <div className="hp-lifestyle-card-grid">
            <div className="hp-lifestyle-card">
              <div className="hp-lifestyle-card-head">
                <span className="hp-lifestyle-icon">흡</span>
                <div>
                  <strong>흡연 습관</strong>
                  <p>현재 흡연 여부를 선택해 주세요.</p>
                </div>
              </div>
              <ChoiceGroup options={SMOKING_OPTIONS} value={draft.smoking} onSelect={(value) => set("smoking", value)} />
            </div>

            <div className="hp-lifestyle-card">
              <div className="hp-lifestyle-card-head">
                <span className="hp-lifestyle-icon">음</span>
                <div>
                  <strong>음주 습관</strong>
                  <p>음주 빈도와 1회 평균 음주량을 선택해 주세요.</p>
                </div>
              </div>
              <ChoiceGroup
                options={ALCOHOL_OPTIONS}
                value={draft.alcohol}
                onSelect={(value) => {
                  set("alcohol", value);
                  if (!isDrinking(value)) set("alcohol_amount", "");
                }}
              />
              {isDrinking(draft.alcohol) && (
                <div className="hp-lifestyle-subgroup">
                  <span className="field-label">1회 평균 음주량</span>
                  <ChoiceGroup options={ALCOHOL_AMOUNT_OPTIONS} value={draft.alcohol_amount} onSelect={(value) => set("alcohol_amount", value)} />
                </div>
              )}
            </div>

            <div className="hp-lifestyle-card">
              <div className="hp-lifestyle-card-head">
                <span className="hp-lifestyle-icon">운</span>
                <div>
                  <strong>신체 활동</strong>
                  <p>평소 운동 빈도와 걷기 일수를 선택해 주세요.</p>
                </div>
              </div>
              <div className="hp-lifestyle-subgroup">
                <span className="field-label">운동 빈도</span>
                <ChoiceGroup options={EXERCISE_OPTIONS} value={draft.exercise_frequency} onSelect={(value) => set("exercise_frequency", value)} />
              </div>
              <div className="hp-lifestyle-subgroup">
                <span className="field-label">걷기 일수</span>
                <ChoiceGroup options={WALKING_OPTIONS} value={draft.walking_days} onSelect={(value) => set("walking_days", value)} />
              </div>
            </div>

            <div className="hp-lifestyle-card">
              <div className="hp-lifestyle-card-head">
                <span className="hp-lifestyle-icon">쉼</span>
                <div>
                  <strong>수면과 좌식 시간</strong>
                  <p>평균 수면 시간과 앉아있는 시간을 선택해 주세요.</p>
                </div>
              </div>
              <div className="hp-lifestyle-subgroup">
                <span className="field-label">평균 수면 시간</span>
                <ChoiceGroup options={SLEEP_OPTIONS} value={draft.sleep_hours} onSelect={(value) => set("sleep_hours", value)} />
              </div>
              <div className="hp-lifestyle-subgroup">
                <span className="field-label">하루 평균 앉아있는 시간</span>
                <ChoiceGroup options={SEDENTARY_OPTIONS} value={draft.sedentary_hours} onSelect={(value) => set("sedentary_hours", value)} />
              </div>
            </div>
          </div>
        ) : (
          <div className="hp-info-grid">
            <div className="hp-info-item"><span className="field-label">흡연</span><span className="hp-info-val">{profile.smoking}</span></div>
            <div className="hp-info-item"><span className="field-label">음주</span><span className="hp-info-val">{profile.alcohol}</span></div>
            <div className="hp-info-item"><span className="field-label">운동 빈도</span><span className="hp-info-val">{optionLabel(EXERCISE_OPTIONS, profile.exercise_frequency)}</span></div>
            <div className="hp-info-item"><span className="field-label">걷기 일수</span><span className="hp-info-val">{optionLabel(WALKING_OPTIONS, profile.walking_days)}</span></div>
            <div className="hp-info-item"><span className="field-label">수면 시간</span><span className="hp-info-val">{optionLabel(SLEEP_OPTIONS, profile.sleep_hours)}</span></div>
            <div className="hp-info-item"><span className="field-label">하루 평균 앉아있는 시간</span><span className="hp-info-val">{optionLabel(SEDENTARY_OPTIONS, profile.sedentary_hours)}</span></div>
          </div>
        )}
      </section>

      <section className="dashboard-card hp-section">
        <h2>식습관</h2>
        {isEditing ? (
          <div className="hp-edit-stack">
            <div><span className="field-label">식사 패턴</span><div className="hp-chip-grid">{["규칙적인 식사", "아침 식사 자주 생략", "야식 자주 섭취", "끼니를 거르는 편"].map((item) => <button key={item} type="button" className={`hp-chip ${draft.meal_patterns.includes(item) ? "is-active" : ""}`} onClick={() => set("meal_patterns", toggle(draft.meal_patterns, item))}>{item}</button>)}</div></div>
            <div><span className="field-label">음식 성향</span><div className="hp-chip-grid">{["채소 섭취가 많은 편", "단 음식 선호", "짠 음식 선호", "기름진 음식 선호"].map((item) => <button key={item} type="button" className={`hp-chip ${draft.food_preferences.includes(item) ? "is-active" : ""}`} onClick={() => set("food_preferences", toggle(draft.food_preferences, item))}>{item}</button>)}</div></div>
            <p className="goal-section-note">식사 패턴과 음식 성향은 식습관 점수로 저장됩니다.</p>
          </div>
        ) : <span className="hp-info-val">식습관 점수 {profile.diet_score ?? "미입력"}{profile.diet_score != null ? "/10" : ""}</span>}
      </section>

      {isEditing && (
        <div className="goal-edit-actions">
          <button type="button" className="wide-subtle-button" onClick={handleCancel} disabled={isSaving}>취소</button>
          <button type="button" className="green-button" onClick={handleSave} disabled={isSaving}>{isSaving ? "저장 중..." : "저장"}</button>
        </div>
      )}
    </div>
  );
}
