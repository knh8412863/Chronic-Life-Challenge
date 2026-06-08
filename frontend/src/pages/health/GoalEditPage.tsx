import { useEffect, useState } from "react";

import type { AppRoute } from "../../App";
import { getStoredAccessToken } from "../../api/auth";
import {
  getHealthGoals,
  updateHealthGoals,
  type ChronicDiseaseGoal,
  type HealthGoals,
  type LifestyleGoal,
} from "../../api/goal";
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
  { key: "target_weight_kg", label: "체중 또는 BMI", unit: "kg", step: "0.1" },
  { key: "target_egfr", label: "eGFR", unit: "mL/min", step: "0.1" },
];

const LG_ITEMS: { key: LgKey; label: string; unit: string; step: string }[] = [
  { key: "target_steps", label: "걸음수", unit: "보/일", step: "100" },
  { key: "target_exercise_minutes", label: "운동 시간", unit: "분/일", step: "5" },
  { key: "target_water_ml", label: "수분 섭취", unit: "ml/일", step: "100" },
  { key: "target_sleep_hours", label: "수면 시간", unit: "시간", step: "0.5" },
];

const CURRENT_LABELS: Partial<Record<CdgKey | LgKey, string>> = {
  target_systolic_bp: "125/82",
  target_fasting_glucose: "98",
  target_postprandial_glucose: "—",
  target_ldl_cholesterol: "112",
  target_hdl_cholesterol: "52",
  target_triglycerides: "—",
  target_weight_kg: "72.5 / 23.7",
  target_egfr: "—",
  target_steps: "8,423",
  target_exercise_minutes: "30",
  target_water_ml: "1,800",
  target_sleep_hours: "6.5",
};

const fallbackGoals: HealthGoals = {
  chronic_disease_goal: {
    target_systolic_bp: 120,
    target_diastolic_bp: 80,
    target_fasting_glucose: 100,
    target_postprandial_glucose: 140,
    target_hba1c: null,
    target_ldl_cholesterol: 100,
    target_hdl_cholesterol: 60,
    target_triglycerides: 150,
    target_bmi: 22,
    target_weight_kg: 68,
    target_egfr: 60,
    updated_at: "2026-06-05T08:00:00",
  },
  lifestyle_goal: {
    target_steps: 10000,
    target_water_ml: 2000,
    target_exercise_minutes: 45,
    target_sleep_hours: 7.5,
    target_diet_score: null,
    updated_at: "2026-06-05T08:00:00",
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

type GoalEditPageProps = {
  onNavigate?: (route: AppRoute) => void;
};

export function GoalEditPage({ onNavigate }: GoalEditPageProps) {
  const [goals, setGoals] = useState<HealthGoals>(fallbackGoals);
  const [isLoading, setIsLoading] = useState(false);
  const [isSaving, setIsSaving] = useState(false);
  const [cdgDraft, setCdgDraft] = useState<Partial<Record<CdgKey, string>>>({});
  const [lgDraft, setLgDraft] = useState<Partial<Record<LgKey, string>>>({});

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
  }, []);

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
        <p className="goal-section-note">* 현재값은 최근 7일 평균 기준 (미기구 전까지)</p>

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
              <span className="goal-edit-current">{CURRENT_LABELS[key] ?? "—"}</span>
              <div className="goal-edit-input-wrap">
                {key === "target_systolic_bp" ? (
                  <div className="goal-edit-bp-wrap">
                    <input
                      type="number"
                      step={step}
                      className="goal-edit-input"
                      value={cdgDraft.target_systolic_bp ?? ""}
                      placeholder="수축기"
                      onChange={(e) =>
                        setCdgDraft((p) => ({ ...p, target_systolic_bp: e.target.value }))
                      }
                    />
                    <span className="goal-bp-sep">/</span>
                    <input
                      type="number"
                      step={step}
                      className="goal-edit-input"
                      value={cdgDraft.target_diastolic_bp ?? ""}
                      placeholder="이완기"
                      onChange={(e) =>
                        setCdgDraft((p) => ({ ...p, target_diastolic_bp: e.target.value }))
                      }
                    />
                  </div>
                ) : (
                  <input
                    type="number"
                    step={step}
                    className="goal-edit-input"
                    value={cdgDraft[key] ?? ""}
                    placeholder="미설정"
                    onChange={(e) =>
                      setCdgDraft((p) => ({ ...p, [key]: e.target.value }))
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
              <span className="goal-edit-current">{CURRENT_LABELS[key] ?? "—"}</span>
              <div className="goal-edit-input-wrap">
                <input
                  type="number"
                  step={step}
                  className="goal-edit-input"
                  value={lgDraft[key] ?? ""}
                  placeholder="미설정"
                  onChange={(e) => setLgDraft((p) => ({ ...p, [key]: e.target.value }))}
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
