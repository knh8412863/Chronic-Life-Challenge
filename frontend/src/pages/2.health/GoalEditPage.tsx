import { useEffect, useState } from "react";

import type { AppRoute } from "../../App";
import { getTodayActivity } from "../../api/activity";
import { getStoredAccessToken } from "../../api/auth";
import { getExerciseLogs } from "../../api/exercise";
import {
  getHealthGoals,
  updateHealthGoals,
  type ChronicDiseaseGoal,
  type HealthGoals,
  type LifestyleGoal,
} from "../../api/goal";
import { getKidneyRecords } from "../../api/kidney";
import { getLipidRecords } from "../../api/lipid";
import { getCurrentUser } from "../../api/users";
import { getVitals } from "../../api/vitals";
import { LoadingState } from "../../components/common/LoadingState";

type CdgKey = keyof Omit<ChronicDiseaseGoal, "updated_at">;
type LgKey = keyof Omit<LifestyleGoal, "updated_at">;

const CDG_ITEMS: { key: CdgKey; label: string; unit: string; step: string; currentKey?: string }[] = [
  { key: "target_systolic_bp", label: "혈압 (수축기/이완기)", unit: "mmHg", step: "1" },
  { key: "target_fasting_glucose", label: "공복혈당", unit: "mg/dL", step: "1" },
  { key: "target_postprandial_glucose", label: "식후혈당", unit: "mg/dL", step: "1" },
  { key: "target_ldl_cholesterol", label: "LDL 콜레스테롤", unit: "mg/dL", step: "1" },
  { key: "target_hdl_cholesterol", label: "HDL 콜레스테롤", unit: "mg/dL", step: "1" },
  { key: "target_triglycerides", label: "중성지방", unit: "mg/dL", step: "1" },
  { key: "target_weight_kg", label: "체중", unit: "kg", step: "0.1" },
  { key: "target_egfr", label: "eGFR", unit: "mL/min", step: "0.1" },
];

const LG_ITEMS: { key: LgKey; label: string; unit: string; step: string }[] = [
  { key: "target_steps", label: "걸음수", unit: "보/일", step: "100" },
  { key: "target_exercise_minutes", label: "운동 시간", unit: "분/일", step: "5" },
  { key: "target_water_ml", label: "수분 섭취", unit: "ml/일", step: "100" },
  { key: "target_sleep_hours", label: "수면 시간", unit: "시간", step: "0.5" },
];

const CURRENT_LABELS: Partial<Record<CdgKey | LgKey, string>> = {
  target_systolic_bp: "—",
  target_fasting_glucose: "—",
  target_postprandial_glucose: "—",
  target_ldl_cholesterol: "—",
  target_hdl_cholesterol: "—",
  target_triglycerides: "—",
  target_weight_kg: "—",
  target_egfr: "—",
  target_steps: "—",
  target_exercise_minutes: "—",
  target_water_ml: "—",
  target_sleep_hours: "—",
};

type GoalSuggestionState = Partial<Record<CdgKey | LgKey, string>>;
type GoalCurrentState = Partial<Record<CdgKey | LgKey, string>>;

const fallbackGoals: HealthGoals = {
  chronic_disease_goal: {
    target_systolic_bp: null,
    target_diastolic_bp: null,
    target_fasting_glucose: null,
    target_postprandial_glucose: null,
    target_hba1c: null,
    target_ldl_cholesterol: null,
    target_hdl_cholesterol: null,
    target_triglycerides: null,
    target_bmi: null,
    target_weight_kg: null,
    target_egfr: null,
    updated_at: "",
  },
  lifestyle_goal: {
    target_steps: null,
    target_water_ml: null,
    target_exercise_minutes: null,
    target_sleep_hours: null,
    target_diet_score: null,
    updated_at: "",
  },
};

function numToStr(v: number | null): string {
  return v === null ? "" : String(v);
}
function strToNum(s: string): number | null {
  if (!s) return null;
  const n = Number(s);
  return Number.isNaN(n) ? null : n;
}
function normalizeNonNegativeInput(value: string): string {
  if (value === "") return "";
  const n = Number(value);
  if (Number.isNaN(n)) return "";
  return String(Math.max(0, n));
}

function latestByDate<T>(items: T[], getDate: (item: T) => string | undefined | null) {
  return [...items].sort((a, b) => String(getDate(b) ?? "").localeCompare(String(getDate(a) ?? "")))[0];
}

function roundTo(value: number, digits = 0) {
  const factor = 10 ** digits;
  return Math.round(value * factor) / factor;
}

function achievableLower(current: number | null | undefined, ideal: number, stepDown: number, digits = 0) {
  if (current == null || current <= 0) return "";
  if (current <= ideal) return String(ideal);
  return String(roundTo(Math.max(ideal, current - stepDown), digits));
}

function achievableHigher(current: number | null | undefined, ideal: number, stepUp: number, digits = 0) {
  if (current == null || current <= 0) return "";
  if (current >= ideal) return String(ideal);
  return String(roundTo(Math.min(ideal, current + stepUp), digits));
}

type GoalEditPageProps = {
  onNavigate?: (route: AppRoute) => void;
};

export function GoalEditPage({ onNavigate }: GoalEditPageProps) {
  const [goals, setGoals] = useState<HealthGoals>(fallbackGoals);
  const [isLoading, setIsLoading] = useState(false);
  const [isSaving, setIsSaving] = useState(false);
  const [cdgDraft, setCdgDraft] = useState<Partial<Record<CdgKey, string>>>({});
  const [lgDraft, setLgDraft] = useState<Partial<Record<LgKey, string>>>({});
  const [currentLabels, setCurrentLabels] = useState<GoalCurrentState>(CURRENT_LABELS);
  const [suggestions, setSuggestions] = useState<GoalSuggestionState>({});

  useEffect(() => {
    const token = getStoredAccessToken();
    if (!token) {
      initDraft(fallbackGoals);
      return;
    }
    setIsLoading(true);
    getHealthGoals(token)
      .then((res) => {
        setGoals(res.data);
        initDraft(res.data);
      })
      .catch(() => initDraft(fallbackGoals))
      .finally(() => setIsLoading(false));
    loadCurrentGoalContext(token);
  }, []);

  async function loadCurrentGoalContext(token: string) {
    const [userRes, vitalsRes, lipidRes, kidneyRes, activityRes, exerciseRes] = await Promise.allSettled([
      getCurrentUser(token),
      getVitals({ limit: 100 }, token),
      getLipidRecords({ limit: 100 }, token),
      getKidneyRecords({ limit: 100 }, token),
      getTodayActivity(token),
      getExerciseLogs({ limit: 30 }, token),
    ]);

    const user = userRes.status === "fulfilled" ? userRes.value : null;
    const vitals = vitalsRes.status === "fulfilled" ? vitalsRes.value.data.items : [];
    const lipids = lipidRes.status === "fulfilled" ? lipidRes.value.data : [];
    const kidneys = kidneyRes.status === "fulfilled" ? kidneyRes.value.data : [];
    const activity = activityRes.status === "fulfilled" ? activityRes.value.data : null;
    const exercises = exerciseRes.status === "fulfilled" ? exerciseRes.value.data.items : [];

    const latestBp = latestByDate(vitals.filter((item) => item.measure_type.startsWith("BP_")), (item) => item.measured_at);
    const latestFasting = latestByDate(vitals.filter((item) => item.measure_type === "GLUCOSE_FASTING"), (item) => item.measured_at);
    const latestPostprandial = latestByDate(
      vitals.filter((item) => item.measure_type === "GLUCOSE_POSTPRANDIAL"),
      (item) => item.measured_at,
    );
    const latestLipid = latestByDate(lipids, (item) => item.record_date || item.created_at);
    const latestKidney = latestByDate(kidneys, (item) => item.record_date || item.measured_date || item.created_at);
    const recentExerciseMinutes = exercises[0]?.duration_minutes ?? activity?.exercise_minutes ?? null;

    const sbp = latestBp?.sbp ?? latestBp?.systolic ?? null;
    const dbp = latestBp?.dbp ?? latestBp?.diastolic ?? null;
    const fasting = latestFasting?.glucose ?? latestFasting?.glucose_value ?? null;
    const postprandial = latestPostprandial?.glucose ?? latestPostprandial?.glucose_value ?? null;
    const weight = user?.weight ?? latestLipid?.weight ?? null;
    const egfr = latestKidney?.egfr ?? null;
    const ldl = latestLipid?.ldl_cholesterol ?? latestLipid?.ldl ?? null;
    const hdl = latestLipid?.hdl_cholesterol ?? latestLipid?.hdl ?? null;
    const triglycerides = latestLipid?.triglycerides ?? null;

    setCurrentLabels({
      target_systolic_bp: sbp && dbp ? `${sbp}/${dbp}` : "—",
      target_fasting_glucose: fasting != null ? String(fasting) : "—",
      target_postprandial_glucose: postprandial != null ? String(postprandial) : "—",
      target_ldl_cholesterol: ldl != null ? String(ldl) : "—",
      target_hdl_cholesterol: hdl != null ? String(hdl) : "—",
      target_triglycerides: triglycerides != null ? String(triglycerides) : "—",
      target_weight_kg: weight != null ? String(weight) : "—",
      target_egfr: egfr != null ? String(egfr) : "—",
      target_steps: activity?.steps != null ? String(activity.steps) : "—",
      target_exercise_minutes: recentExerciseMinutes != null ? String(recentExerciseMinutes) : "—",
      target_water_ml: activity?.water_ml != null ? String(activity.water_ml) : "—",
      target_sleep_hours: activity?.sleep_hours != null ? String(activity.sleep_hours) : "—",
    });

    setSuggestions({
      target_systolic_bp: achievableLower(sbp, 120, 10),
      target_diastolic_bp: achievableLower(dbp, 80, 5),
      target_fasting_glucose: achievableLower(fasting, 95, 10),
      target_postprandial_glucose: achievableLower(postprandial, 140, 20),
      target_ldl_cholesterol: achievableLower(ldl, 100, 20),
      target_hdl_cholesterol: achievableHigher(hdl, user?.gender === "MALE" ? 40 : 50, 5),
      target_triglycerides: achievableLower(triglycerides, 150, 30),
      target_weight_kg: weight != null && weight > 0 ? String(roundTo(Math.max(30, weight - Math.min(3, weight * 0.05)), 1)) : "",
      target_egfr: achievableHigher(egfr, 90, 5, 1),
      target_steps: String(Math.min(10000, Math.max(5000, (activity?.steps ?? 4000) + 1000))),
      target_exercise_minutes: String(Math.min(60, Math.max(20, (recentExerciseMinutes ?? 10) + 10))),
      target_water_ml: String(Math.min(2000, Math.max(1200, (activity?.water_ml ?? 900) + 300))),
      target_sleep_hours: String(roundTo(Math.min(8, Math.max(6.5, Number(activity?.sleep_hours ?? 6) + 0.5)), 1)),
    });
  }

  function initDraft(g: HealthGoals) {
    const cdg: Partial<Record<CdgKey, string>> = {};
    const lg: Partial<Record<LgKey, string>> = {};
    CDG_ITEMS.forEach(({ key }) => {
      cdg[key] = numToStr(g.chronic_disease_goal[key]);
    });
    LG_ITEMS.forEach(({ key }) => {
      lg[key] = numToStr(g.lifestyle_goal[key]);
    });
    setCdgDraft(cdg);
    setLgDraft(lg);
  }

  async function handleSave() {
    const token = getStoredAccessToken();
    const cdgPatch: Partial<Omit<ChronicDiseaseGoal, "updated_at">> = {};
    const lgPatch: Partial<Omit<LifestyleGoal, "updated_at">> = {};
    CDG_ITEMS.forEach(({ key }) => {
      (cdgPatch as Record<string, number | null>)[key] = strToNum(cdgDraft[key] ?? "");
    });
    LG_ITEMS.forEach(({ key }) => {
      (lgPatch as Record<string, number | null>)[key] = strToNum(lgDraft[key] ?? "");
    });

    setIsSaving(true);
    try {
      const res = await updateHealthGoals(
        { chronic_disease_goal: cdgPatch, lifestyle_goal: lgPatch },
        token ?? undefined,
      );
      setGoals(res.data);
      onNavigate?.("/health/goal");
    } catch {
      alert("저장에 실패했습니다. 다시 시도해 주세요.");
    } finally {
      setIsSaving(false);
    }
  }

  if (isLoading) return <LoadingState message="건강 목표를 불러오는 중입니다." />;

  return (
    <div className="goal-edit-page page-stack">
      <section className="section-header-row page-heading-row">
        <div className="page-heading">
          <p className="eyebrow">건강 관리</p>
          <h1>건강 목표 수정</h1>
        </div>
      </section>

      {/* 만성질환 수치 목표 */}
      <section className="dashboard-card goal-section">
        <div className="goal-section-header">
          <h2>만성질환 수치 목표</h2>
        </div>

        <div className="goal-edit-table">
          <div className="goal-edit-thead">
            <span>항목</span>
            <span>단위</span>
            <span>현재값</span>
            <span>목표값</span>
          </div>
          {CDG_ITEMS.map(({ key, label, unit, step }) => (
            <div key={key} className="goal-edit-row">
              <span className="goal-edit-item-label">{label}</span>
              <span className="goal-edit-unit-col">{unit}</span>
              <span className="goal-edit-current">{currentLabels[key] ?? "—"}</span>
              <div className="goal-edit-input-wrap">
                {key === "target_systolic_bp" ? (
                  <div className="goal-edit-bp-wrap">
                    <input
                      type="number"
                      step={step}
                      min={0}
                      className="goal-edit-input"
                      value={cdgDraft.target_systolic_bp ?? ""}
                      placeholder={suggestions.target_systolic_bp || "수축기"}
                      onChange={(e) =>
                        setCdgDraft((p) => ({ ...p, target_systolic_bp: normalizeNonNegativeInput(e.target.value) }))
                      }
                    />
                    <span className="goal-bp-sep">/</span>
                    <input
                      type="number"
                      step={step}
                      min={0}
                      className="goal-edit-input"
                      value={cdgDraft.target_diastolic_bp ?? ""}
                      placeholder={suggestions.target_diastolic_bp || "이완기"}
                      onChange={(e) =>
                        setCdgDraft((p) => ({ ...p, target_diastolic_bp: normalizeNonNegativeInput(e.target.value) }))
                      }
                    />
                  </div>
                ) : (
                  <input
                    type="number"
                    step={step}
                    min={0}
                    className="goal-edit-input"
                    value={cdgDraft[key] ?? ""}
                    placeholder={suggestions[key] || "미설정"}
                    onChange={(e) =>
                      setCdgDraft((p) => ({ ...p, [key]: normalizeNonNegativeInput(e.target.value) }))
                    }
                  />
                )}
              </div>
            </div>
          ))}
        </div>
      </section>

      {/* 생활습관 목표 */}
      <section className="dashboard-card goal-section">
        <div className="goal-section-header">
          <h2>생활습관 목표</h2>
        </div>

        <div className="goal-edit-table">
          <div className="goal-edit-thead">
            <span>항목</span>
            <span>단위</span>
            <span>현재값</span>
            <span>목표값</span>
          </div>
          {LG_ITEMS.map(({ key, label, unit, step }) => (
            <div key={key} className="goal-edit-row">
              <span className="goal-edit-item-label">{label}</span>
              <span className="goal-edit-unit-col">{unit}</span>
              <span className="goal-edit-current">{currentLabels[key] ?? "—"}</span>
              <div className="goal-edit-input-wrap">
                <input
                  type="number"
                  step={step}
                  min={0}
                  className="goal-edit-input"
                  value={lgDraft[key] ?? ""}
                  placeholder={suggestions[key] || "미설정"}
                  onChange={(e) => setLgDraft((p) => ({ ...p, [key]: normalizeNonNegativeInput(e.target.value) }))}
                />
              </div>
            </div>
          ))}
        </div>
      </section>

      <div className="goal-edit-actions">
        <button
          type="button"
          className="wide-subtle-button"
          onClick={() => onNavigate?.("/health/goal")}
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
    </div>
  );
}
