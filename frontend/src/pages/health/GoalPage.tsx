import { useEffect, useState } from "react";

import type { AppRoute } from "../../App";
import { getStoredAccessToken } from "../../api/auth";
import { getHealthGoals, type HealthGoals } from "../../api/goal";
import { getScoreHistory, type ScoreHistory } from "../../api/stats";
import { ErrorState } from "../../components/common/ErrorState";
import { LoadingState } from "../../components/common/LoadingState";

type CurrentValues = {
  systolic_bp: number | null;
  diastolic_bp: number | null;
  fasting_glucose: number | null;
  postprandial_glucose: number | null;
  ldl_cholesterol: number | null;
  hdl_cholesterol: number | null;
  triglycerides: number | null;
  weight_kg: number | null;
  bmi: number | null;
  egfr: number | null;
  steps: number | null;
  exercise_minutes: number | null;
  water_ml: number | null;
  sleep_hours: number | null;
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

const fallbackCurrent: CurrentValues = {
  systolic_bp: 125,
  diastolic_bp: 82,
  fasting_glucose: 98,
  postprandial_glucose: null,
  ldl_cholesterol: 112,
  hdl_cholesterol: 52,
  triglycerides: null,
  weight_kg: 72.5,
  bmi: 23.7,
  egfr: null,
  steps: 8423,
  exercise_minutes: 30,
  water_ml: 1800,
  sleep_hours: 6.5,
};

const fallbackHistory: ScoreHistory = {
  period: "30D",
  points: [],
};

function calcProgress(current: number | null, target: number | null, higherIsBetter: boolean): number {
  if (current === null || target === null || target === 0) return 0;
  if (higherIsBetter) {
    return Math.min(100, Math.round((current / target) * 100));
  }
  if (current <= target) return 100;
  return Math.max(0, Math.round((target / current) * 100));
}

type GoalRowProps = {
  label: string;
  currentText: string;
  targetText: string;
  progress: number;
  isDefault?: boolean;
};

function GoalRow({ label, currentText, targetText, progress, isDefault }: GoalRowProps) {
  return (
    <div className="goal-progress-row">
      <div className="goal-progress-left">
        <span className="goal-progress-label">
          {label}
          {isDefault && <span className="goal-default-badge">기본값 사용 중</span>}
        </span>
        <span className="goal-progress-meta">
          현재: {currentText}&nbsp;&nbsp;목표: {targetText}
        </span>
      </div>
      <div className="goal-progress-bar-wrap">
        <div
          className="goal-progress-bar"
          style={{ width: `${progress}%` }}
        />
      </div>
      <span className="goal-progress-pct">{progress}%</span>
    </div>
  );
}

type GoalPageProps = {
  onNavigate?: (route: AppRoute) => void;
};

export function GoalPage({ onNavigate }: GoalPageProps) {
  const [goals, setGoals] = useState<HealthGoals>(fallbackGoals);
  const [history, setHistory] = useState<ScoreHistory>(fallbackHistory);
  const [isLoading, setIsLoading] = useState(false);
  const [hasApiError, setHasApiError] = useState(false);
  const current = fallbackCurrent;

  useEffect(() => {
    const token = getStoredAccessToken();
    if (!token) return;

    setIsLoading(true);
    Promise.all([getHealthGoals(token), getScoreHistory("30D", token)])
      .then(([goalsRes, historyRes]) => {
        setGoals(goalsRes.data);
        setHistory(historyRes.data);
        setHasApiError(false);
      })
      .catch(() => setHasApiError(true))
      .finally(() => setIsLoading(false));
  }, []);

  if (isLoading) return <LoadingState message="건강 목표를 불러오는 중입니다." />;

  const cdg = goals.chronic_disease_goal;
  const lg = goals.lifestyle_goal;
  const maxScore = Math.max(...history.points.map((p) => p.total_score), 1);

  return (
    <div className="goal-page page-stack">
      <section className="section-header-row page-heading-row">
        <div className="page-heading">
          <p className="eyebrow">건강 관리</p>
          <h1>건강 목표</h1>
        </div>
        <div className="button-row">
          <button
            type="button"
            className="green-button"
            onClick={() => onNavigate?.("/health/goal/edit")}
          >
            목표 수정
          </button>
        </div>
      </section>

      {hasApiError && (
        <ErrorState
          title="건강 목표 데이터를 불러오지 못했습니다."
          description="현재 화면은 예시 데이터로 표시됩니다."
        />
      )}

      {/* 만성질환 수치 목표 */}
      <section className="dashboard-card goal-section">
        <div className="goal-section-header">
          <h2>만성질환 수치 목표</h2>
        </div>
        <p className="goal-section-note">
          * 현재 풍선이 없는 경우 최근 일부 항목만 표시됩니다 (예: eGFR은 만성신장질환 관리 시 적용)
        </p>

        <GoalRow
          label="혈압 (수축기/이완기)"
          currentText={
            current.systolic_bp != null
              ? `${current.systolic_bp}/${current.diastolic_bp}mmHg`
              : "—mmHg"
          }
          targetText={
            cdg.target_systolic_bp != null
              ? `${cdg.target_systolic_bp}/${cdg.target_diastolic_bp}mmHg`
              : "미설정"
          }
          progress={calcProgress(current.systolic_bp, cdg.target_systolic_bp, false)}
        />
        <GoalRow
          label="공복혈당"
          currentText={current.fasting_glucose != null ? `${current.fasting_glucose}mg/dL` : "—mg/dL"}
          targetText={cdg.target_fasting_glucose != null ? `<${cdg.target_fasting_glucose}mg/dL` : "미설정"}
          progress={calcProgress(current.fasting_glucose, cdg.target_fasting_glucose, false)}
        />
        <GoalRow
          label="식후혈당"
          currentText={current.postprandial_glucose != null ? `${current.postprandial_glucose}mg/dL` : "—mg/dL"}
          targetText={cdg.target_postprandial_glucose != null ? `<${cdg.target_postprandial_glucose}mg/dL` : "미설정"}
          progress={calcProgress(current.postprandial_glucose, cdg.target_postprandial_glucose, false)}
          isDefault={current.postprandial_glucose === null}
        />
        <GoalRow
          label="LDL 콜레스테롤"
          currentText={current.ldl_cholesterol != null ? `${current.ldl_cholesterol}mg/dL` : "—mg/dL"}
          targetText={cdg.target_ldl_cholesterol != null ? `<${cdg.target_ldl_cholesterol}mg/dL` : "미설정"}
          progress={calcProgress(current.ldl_cholesterol, cdg.target_ldl_cholesterol, false)}
        />
        <GoalRow
          label="HDL 콜레스테롤"
          currentText={current.hdl_cholesterol != null ? `${current.hdl_cholesterol}mg/dL` : "—mg/dL"}
          targetText={cdg.target_hdl_cholesterol != null ? `≥${cdg.target_hdl_cholesterol}mg/dL` : "미설정"}
          progress={calcProgress(current.hdl_cholesterol, cdg.target_hdl_cholesterol, true)}
        />
        <GoalRow
          label="중성지방"
          currentText={current.triglycerides != null ? `${current.triglycerides}mg/dL` : "—mg/dL"}
          targetText={cdg.target_triglycerides != null ? `<${cdg.target_triglycerides}mg/dL` : "미설정"}
          progress={calcProgress(current.triglycerides, cdg.target_triglycerides, false)}
          isDefault={current.triglycerides === null}
        />
        <GoalRow
          label="체중 또는 BMI"
          currentText={
            current.weight_kg != null
              ? `${current.weight_kg}/${current.bmi}kg`
              : "—kg"
          }
          targetText={
            cdg.target_weight_kg != null
              ? `${cdg.target_weight_kg}/${cdg.target_bmi}kg`
              : cdg.target_bmi != null
                ? `BMI ${cdg.target_bmi}`
                : "미설정"
          }
          progress={calcProgress(current.bmi, cdg.target_bmi, false)}
        />
        <GoalRow
          label="eGFR"
          currentText={current.egfr != null ? `${current.egfr}mL/min` : "—mL/min"}
          targetText={cdg.target_egfr != null ? `≥${cdg.target_egfr}mL/min` : "미설정"}
          progress={calcProgress(current.egfr, cdg.target_egfr, true)}
          isDefault={current.egfr === null}
        />
      </section>

      {/* 생활습관 목표 */}
      <section className="dashboard-card goal-section">
        <div className="goal-section-header">
          <h2>생활습관 목표</h2>
        </div>

        <GoalRow
          label="걸음수"
          currentText={current.steps != null ? `${current.steps.toLocaleString()}보/일` : "—보/일"}
          targetText={lg.target_steps != null ? `${lg.target_steps.toLocaleString()}보/일` : "미설정"}
          progress={calcProgress(current.steps, lg.target_steps, true)}
        />
        <GoalRow
          label="운동 시간"
          currentText={current.exercise_minutes != null ? `${current.exercise_minutes}분/일` : "—분/일"}
          targetText={lg.target_exercise_minutes != null ? `${lg.target_exercise_minutes}분/일` : "미설정"}
          progress={calcProgress(current.exercise_minutes, lg.target_exercise_minutes, true)}
        />
        <GoalRow
          label="수분 섭취"
          currentText={current.water_ml != null ? `${current.water_ml.toLocaleString()}ml/일` : "—ml/일"}
          targetText={lg.target_water_ml != null ? `${lg.target_water_ml.toLocaleString()}ml/일` : "미설정"}
          progress={calcProgress(current.water_ml, lg.target_water_ml, true)}
        />
        <GoalRow
          label="수면 시간"
          currentText={current.sleep_hours != null ? `${current.sleep_hours}시간` : "—시간"}
          targetText={lg.target_sleep_hours != null ? `${lg.target_sleep_hours}시간` : "미설정"}
          progress={calcProgress(current.sleep_hours, lg.target_sleep_hours, true)}
        />
      </section>

      {/* 최근 30일 건강 점수 추이 */}
      <section className="dashboard-card goal-section">
        <div className="goal-section-header">
          <h2>최근 30일 건강 점수 추이</h2>
        </div>
        <p className="goal-section-note">* /health/statistics API 기준 기간 건강 지표 요약</p>
        {history.points.length === 0 ? (
          <div className="goal-chart-placeholder">
            <span>30일 건강 점수 추이 차트 (110점 만점)</span>
          </div>
        ) : (
          <div className="goal-score-chart">
            {history.points.map((p) => {
              const h = Math.round((p.total_score / maxScore) * 100);
              const parts = p.date.split("-");
              return (
                <div key={p.date} className="goal-score-col">
                  <div className="goal-score-bar-wrap">
                    <div className="goal-score-bar" style={{ height: `${h}%` }} />
                  </div>
                  <span className="goal-score-date">{parts[1]}/{parts[2]}</span>
                </div>
              );
            })}
          </div>
        )}
      </section>
    </div>
  );
}
