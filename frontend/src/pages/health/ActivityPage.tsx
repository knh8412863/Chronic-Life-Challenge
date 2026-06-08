import { useEffect, useState } from "react";

import type { AppRoute } from "../../App";
import { getStoredAccessToken } from "../../api/auth";
import { getTodayActivity, saveActivity, type DailyActivity } from "../../api/activity";
import { LoadingState } from "../../components/common/LoadingState";

function todayStr() {
  return new Date().toISOString().slice(0, 10);
}

const fallbackActivity: DailyActivity = {
  activity_date: todayStr(),
  steps: 8423,
  exercise_minutes: 30,
  sleep_hours: 7.5,
  water_ml: 1800,
  stress_level: 3,
  diet_score: 7.0,
  exists: true,
};

type ActivityPageProps = {
  onNavigate?: (route: AppRoute) => void;
};

export function ActivityPage({ onNavigate: _onNavigate }: ActivityPageProps) {
  const [activity, setActivity] = useState<DailyActivity>(fallbackActivity);
  const [isLoading, setIsLoading] = useState(false);
  const [isSaving, setIsSaving] = useState(false);

  const [steps, setSteps] = useState(String(fallbackActivity.steps ?? ""));
  const [exerciseMinutes, setExerciseMinutes] = useState(String(fallbackActivity.exercise_minutes ?? ""));
  const [sleepHours, setSleepHours] = useState(String(fallbackActivity.sleep_hours ?? ""));
  const [waterMl, setWaterMl] = useState(String(fallbackActivity.water_ml ?? ""));
  const [stressLevel, setStressLevel] = useState(fallbackActivity.stress_level ?? 3);
  const [dietScore, setDietScore] = useState(fallbackActivity.diet_score ?? 7.0);

  useEffect(() => {
    const token = getStoredAccessToken();
    if (!token) return;
    setIsLoading(true);
    getTodayActivity(token)
      .then((res) => {
        setActivity(res.data);
        setSteps(String(res.data.steps ?? ""));
        setExerciseMinutes(String(res.data.exercise_minutes ?? ""));
        setSleepHours(String(res.data.sleep_hours ?? ""));
        setWaterMl(String(res.data.water_ml ?? ""));
        setStressLevel(res.data.stress_level ?? 3);
        setDietScore(res.data.diet_score ?? 7.0);
      })
      .catch(() => {})
      .finally(() => setIsLoading(false));
  }, []);

  async function handleSave() {
    const token = getStoredAccessToken();
    setIsSaving(true);
    try {
      await saveActivity(
        {
          steps: steps ? Number(steps) : undefined,
          exercise_minutes: exerciseMinutes ? Number(exerciseMinutes) : undefined,
          sleep_hours: sleepHours ? Number(sleepHours) : undefined,
          water_ml: waterMl ? Number(waterMl) : undefined,
          stress_level: stressLevel,
          diet_score: dietScore,
        },
        token ?? undefined,
      );
      alert("저장되었습니다.");
    } catch {
      alert("저장에 실패했습니다. 다시 시도해 주세요.");
    } finally {
      setIsSaving(false);
    }
  }

  if (isLoading) return <LoadingState message="오늘의 활동을 불러오는 중입니다." />;

  return (
    <div className="activity-page page-stack">
      <section className="section-header-row page-heading-row">
        <div className="page-heading">
          <p className="eyebrow">건강 관리</p>
          <h1>일일 활동 기록</h1>
        </div>
      </section>

      {activity.exists && (
        <div className="act-notice">
          ℹ️ 오늘 기록이 이미 있습니다. 저장하면 기존 기록이 업데이트됩니다.
        </div>
      )}

      <div className="act-two-col">
        {/* 활동량 */}
        <section className="dashboard-card act-section">
          <h2>활동량</h2>
          <div className="vi-field" style={{ marginBottom: "20px" }}>
            <label className="field-label">걸음 수 (보)</label>
            <input
              type="number"
              className="act-input"
              placeholder="예: 8,000"
              value={steps}
              min={0}
              onChange={(e) => setSteps(e.target.value)}
            />
          </div>
          <div className="vi-field">
            <label className="field-label">운동 시간 (분)</label>
            <input
              type="number"
              className="act-input"
              placeholder="예: 30"
              value={exerciseMinutes}
              min={0}
              onChange={(e) => setExerciseMinutes(e.target.value)}
            />
          </div>
        </section>

        {/* 생활 습관 */}
        <section className="dashboard-card act-section">
          <h2>생활 습관</h2>
          <div className="vi-field" style={{ marginBottom: "20px" }}>
            <label className="field-label">수면 시간 (시간)</label>
            <input
              type="number"
              step="0.5"
              className="act-input"
              placeholder="예: 7.5"
              value={sleepHours}
              min={0}
              max={24}
              onChange={(e) => setSleepHours(e.target.value)}
            />
          </div>
          <div className="vi-field">
            <label className="field-label">물 섭취 (ml)</label>
            <input
              type="number"
              step="50"
              className="act-input"
              placeholder="예: 1,800"
              value={waterMl}
              min={0}
              onChange={(e) => setWaterMl(e.target.value)}
            />
          </div>
        </section>
      </div>

      {/* 컨디션 */}
      <section className="dashboard-card act-section">
        <h2>컨디션</h2>

        <div className="act-slider-row">
          <div className="act-slider-item">
            <label className="field-label">
              스트레스 수준 {stressLevel} / 5
            </label>
            <input
              type="range"
              className="act-slider"
              min={1}
              max={5}
              step={1}
              value={stressLevel}
              onChange={(e) => setStressLevel(Number(e.target.value))}
            />
            <p className="goal-section-note">* stress_level: tinyint (1~5 범위)</p>
          </div>

          <div className="act-slider-item">
            <label className="field-label">
              식단 점수 {dietScore.toFixed(1)} / 10
            </label>
            <input
              type="range"
              className="act-slider"
              min={0}
              max={10}
              step={0.1}
              value={dietScore}
              onChange={(e) => setDietScore(Number(e.target.value))}
            />
            <p className="goal-section-note">* diet_score: decimal(3,1) (0~10 범위)</p>
          </div>
        </div>
      </section>

      <div className="goal-edit-actions">
        <button type="button" className="wide-subtle-button">
          취소
        </button>
        <button type="button" className="green-button" onClick={handleSave} disabled={isSaving}>
          {isSaving ? "저장 중..." : "저장"}
        </button>
      </div>
    </div>
  );
}
