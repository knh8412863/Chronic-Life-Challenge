import { useEffect, useMemo, useState } from "react";

import type { AppRoute } from "../../App";
import { getActivityLogs } from "../../api/activity";
import { getStoredAccessToken } from "../../api/auth";
import { getExerciseLogs } from "../../api/exercise";
import { getKidneyRecords } from "../../api/kidney";
import { getLipidRecords } from "../../api/lipid";
import { createPredictionTask, getLatestHealthSurveyInput, getPredictionResults } from "../../api/predictions";
import { getVitals, type VitalRecord } from "../../api/vitals";
import { localDateString } from "../../utils/date";

type PredictionRequestPageProps = {
  onNavigate: (route: AppRoute) => void;
};

const diseases = ["당뇨병", "고혈압", "만성신장질환"];
const DAILY_PREDICTION_LIMIT = 3;

function latestByDate<T>(items: T[], getDate: (item: T) => string | undefined | null) {
  return [...items].sort((a, b) => String(getDate(b) ?? "").localeCompare(String(getDate(a) ?? "")))[0];
}

function latestVital(items: VitalRecord[], predicate: (item: VitalRecord) => boolean) {
  return latestByDate(items.filter(predicate), (item) => item.measured_at || item.created_at);
}

function formatCompleteWithDate(date?: string | null) {
  return date ? `입력됨 · ${date.slice(0, 10)}` : "입력됨";
}

export function PredictionRequestPage({ onNavigate }: PredictionRequestPageProps) {
  const [selectedDiseases, setSelectedDiseases] = useState(() => new Set(diseases));
  const [analysisMode, setAnalysisMode] = useState<"BASIC" | "DEEP">("BASIC");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [isDataLoading, setIsDataLoading] = useState(false);
  const [errorMessage, setErrorMessage] = useState("");
  const [remainingPredictionCount, setRemainingPredictionCount] = useState(DAILY_PREDICTION_LIMIT);
  const [dataRows, setDataRows] = useState([
    ["건강 프로필", "미입력"],
    ["건강 수치 기록", "미입력"],
    ["생활/운동 기록", "미입력"],
    ["운동 기록", "미입력"],
    ["생활 습관", "미입력"],
    ["가족력", "미입력"],
  ]);

  const isAllSelected = selectedDiseases.size === diseases.length;
  const selectedCount = selectedDiseases.size;
  const selectedDataRows = useMemo(() => {
    if (analysisMode === "BASIC") {
      return dataRows.slice(0, 3);
    }
    return dataRows;
  }, [analysisMode, dataRows]);

  useEffect(() => {
    const token = getStoredAccessToken();
    if (!token) return;

    setIsDataLoading(true);
    Promise.allSettled([
      getLatestHealthSurveyInput(token),
      getVitals({ limit: 100 }, token),
      getLipidRecords({ limit: 100 }, token),
      getKidneyRecords({ limit: 100 }, token),
      getExerciseLogs({ limit: 100 }, token),
      getActivityLogs({ limit: 100 }, token),
      getPredictionResults(100, token),
    ])
      .then(([surveyRes, vitalsRes, lipidRes, kidneyRes, exerciseRes, activityRes, predictionRes]) => {
        const survey = surveyRes.status === "fulfilled" ? surveyRes.value.data : null;
        const vitals = vitalsRes.status === "fulfilled" ? vitalsRes.value.data.items : [];
        const lipids = lipidRes.status === "fulfilled" ? lipidRes.value.data : [];
        const kidneys = kidneyRes.status === "fulfilled" ? kidneyRes.value.data : [];
        const exercises = exerciseRes.status === "fulfilled" ? exerciseRes.value.data : null;
        const activities = activityRes.status === "fulfilled" ? activityRes.value.data : [];
        const predictions = predictionRes.status === "fulfilled" ? predictionRes.value.data.items : [];
        const today = localDateString();
        const todayPredictionCount = predictions.filter((item) => item.created_at.slice(0, 10) === today).length;
        setRemainingPredictionCount(Math.max(DAILY_PREDICTION_LIMIT - todayPredictionCount, 0));
        const latestBp = latestVital(vitals, (item) => item.measure_type.startsWith("BP_"));
        const latestGlucose = latestVital(vitals, (item) => item.measure_type === "GLUCOSE_FASTING");
        const latestLipid = latestByDate(lipids, (item) => item.record_date || item.created_at);
        const latestKidney = latestByDate(kidneys, (item) => item.record_date || item.measured_date || item.created_at);
        const latestExercise = latestByDate(exercises?.items ?? [], (item) => item.exercise_date || item.created_at);
        const latestActivity = latestByDate(activities, (item) => item.activity_date || item.record_date);
        const hasFamilyHistory = Boolean(
          survey?.fh_diabetes_father ||
            survey?.fh_diabetes_mother ||
            survey?.fh_diabetes_sibling ||
            survey?.fh_hypertension_father ||
            survey?.fh_hypertension_mother ||
            survey?.fh_hypertension_sibling ||
            survey?.family_history_ckd,
        );
        const hasLifestyle = Boolean(
          survey?.smoking_status != null ||
            survey?.alcohol_frequency != null ||
            survey?.walking_days != null ||
            survey?.exercise_frequency != null ||
            survey?.sleep_hours != null ||
            survey?.stress_level != null ||
            survey?.diet_score != null ||
            latestActivity?.steps != null ||
            latestActivity?.exercise_minutes != null ||
            latestActivity?.sleep_hours != null ||
            latestActivity?.water_ml != null ||
            latestActivity?.stress_level != null,
        );
        const profileSummary = survey
          ? `${Math.round(survey.height)}cm / ${Math.round(survey.weight)}kg`
          : latestLipid?.height || latestLipid?.weight
            ? `${latestLipid.height ?? "—"}cm / ${latestLipid.weight ?? "—"}kg`
            : "미입력";
        const bpSummary = latestBp
          ? `혈압 ${latestBp.sbp ?? latestBp.systolic}/${latestBp.dbp ?? latestBp.diastolic}`
          : survey?.sbp != null && survey?.dbp != null
            ? `설문 혈압 ${survey.sbp}/${survey.dbp}`
            : "";
        const glucoseSummary = latestGlucose
          ? `공복혈당 ${latestGlucose.glucose ?? latestGlucose.glucose_value}mg/dL`
          : survey?.glucose_fasting != null
            ? `설문 공복혈당 ${survey.glucose_fasting}mg/dL`
            : "";
        const exerciseSummary = latestExercise
          ? `최근 ${latestExercise.duration_minutes}분`
          : latestActivity?.exercise_minutes != null
            ? `최근 ${latestActivity.exercise_minutes}분`
            : "미입력";
        const lipidSummary = latestLipid
          ? [
              latestLipid.total_cholesterol != null ? `총 ${latestLipid.total_cholesterol}` : "",
              latestLipid.ldl != null ? `LDL ${latestLipid.ldl}` : "",
              latestLipid.hdl != null ? `HDL ${latestLipid.hdl}` : "",
              latestLipid.triglycerides != null ? `TG ${latestLipid.triglycerides}` : "",
            ].filter(Boolean).join(" / ") || formatCompleteWithDate(latestLipid.record_date)
          : "미입력";
        const kidneySummary = latestKidney
          ? [
              latestKidney.creatinine != null ? `Cr ${latestKidney.creatinine}` : "",
              latestKidney.egfr != null ? `eGFR ${latestKidney.egfr}` : "",
            ].filter(Boolean).join(" / ") || formatCompleteWithDate(latestKidney.record_date || latestKidney.measured_date)
          : "미입력";
        const healthMetricSummary = [
          bpSummary,
          glucoseSummary,
          latestLipid ? "지질 입력됨" : "",
          latestKidney ? "신장 입력됨" : "",
        ].filter(Boolean).join(" / ") || "미입력";
        const lifestyleSummary = [
          exerciseSummary !== "미입력" ? exerciseSummary : "",
          latestActivity?.steps != null ? `${latestActivity.steps}보` : "",
          hasLifestyle ? "생활습관 입력됨" : "",
        ].filter(Boolean).join(" / ") || "미입력";

        setDataRows([
          ["건강 프로필", profileSummary],
          ["건강 수치 기록", healthMetricSummary],
          ["생활/운동 기록", lifestyleSummary],
          [
            "혈압 기록",
            bpSummary || "미입력",
          ],
          [
            "혈당 기록",
            glucoseSummary || "미입력",
          ],
          ["운동 기록", exerciseSummary],
          ["생활 습관", hasLifestyle ? "완료" : "미입력"],
          ["가족력", hasFamilyHistory ? "입력됨" : "미입력"],
          ["지질 지표", lipidSummary],
          ["신장 지표", kidneySummary],
        ]);
      })
      .finally(() => setIsDataLoading(false));
  }, []);

  const toggleDisease = (disease: string) => {
    setSelectedDiseases((prev) => {
      const next = new Set(prev);
      if (next.has(disease)) {
        next.delete(disease);
      } else {
        next.add(disease);
      }
      return next;
    });
  };

  const toggleAllDiseases = () => {
    setSelectedDiseases(isAllSelected ? new Set() : new Set(diseases));
  };

  const handleStartPrediction = async () => {
    if (selectedDiseases.size === 0) {
      setErrorMessage("예측할 질환을 1개 이상 선택해 주세요.");
      return;
    }

    const token = getStoredAccessToken();
    if (!token) {
      setErrorMessage("로그인 후 예측을 요청할 수 있습니다.");
      onNavigate("/login");
      return;
    }

    setIsSubmitting(true);
    setErrorMessage("");

    try {
      let healthInputId: number | undefined;
      try {
        const latestInput = await getLatestHealthSurveyInput(token);
        healthInputId = latestInput.data.health_input_id;
      } catch {
        healthInputId = undefined;
      }

      const task = await createPredictionTask(
        {
          ...(healthInputId ? { health_input_id: healthInputId } : {}),
          prediction_mode: "SCREENING",
        },
        token,
      );

      sessionStorage.setItem("predictionTaskUuid", task.data.task_uuid);
      sessionStorage.removeItem("predictionResultId");
      sessionStorage.setItem("predictionSelectedDiseases", JSON.stringify([...selectedDiseases]));
      sessionStorage.setItem("predictionAnalysisMode", analysisMode);
      window.history.pushState({}, "", `/prediction/progress?task_uuid=${task.data.task_uuid}`);
      onNavigate("/prediction/progress");
    } catch {
      setErrorMessage("예측에 사용할 건강 수치 또는 건강설문 입력을 찾을 수 없습니다.");
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="page-stack">
      <section className="prediction-title-row">
        <h1>질환 예측 요청</h1>
        <span className="usage-badge">오늘 예측 가능 횟수: {remainingPredictionCount}/3회 남음</span>
      </section>
      <div className="prediction-stepper">
        {["질환 선택", "데이터 확인", "예측 실행"].map((label, index) => (
          <div className={index === 0 ? "is-current" : ""} key={label}>
            <span>{index === 0 ? "✓" : index + 1}</span>
            <small>{label}</small>
          </div>
        ))}
      </div>
      <section className="prediction-request-grid">
        <article className="dashboard-card">
          <h2>예측할 질환을 선택하세요 (3대 만성질환)</h2>
          <div className="checkbox-list">
            {diseases.map((disease) => (
              <label key={disease}>
                <input checked={selectedDiseases.has(disease)} type="checkbox" onChange={() => toggleDisease(disease)} />
                {disease}
              </label>
            ))}
          </div>
          <div className="request-footer">
            <span>선택된 질환: {selectedCount}개</span>
            <button className="small-button" type="button" onClick={toggleAllDiseases}>
              {isAllSelected ? "전체 해제" : "전체 선택"}
            </button>
          </div>
        </article>
        <aside className="dashboard-card">
          <h2>분석 모드</h2>
          <div className="segment-control">
            <button className={analysisMode === "BASIC" ? "is-active" : ""} type="button" onClick={() => setAnalysisMode("BASIC")}>
              기본
            </button>
            <button className={analysisMode === "DEEP" ? "is-active" : ""} type="button" onClick={() => setAnalysisMode("DEEP")}>
              심화
            </button>
          </div>
          <h2>분석 데이터</h2>
          <div className="data-check-list">
            {selectedDataRows.map(([label, value]) => (
              <div key={label}>
                <span>{value === "미입력" ? "·" : "✓"} {label}</span>
                <strong>{value}</strong>
              </div>
            ))}
          </div>
          <button className="green-button" disabled={isSubmitting || isDataLoading || selectedCount === 0} type="button" onClick={handleStartPrediction}>
            {isSubmitting ? "예측 요청 중..." : isDataLoading ? "분석 데이터 확인 중..." : "예측 시작"}
          </button>
          {errorMessage && (
            <div className="warning-banner compact">
              <strong>!</strong>
              <span>{errorMessage}</span>
              <button type="button" onClick={() => onNavigate("/health/vitals/input")}>
                건강 수치 입력
              </button>
            </div>
          )}
        </aside>
      </section>
      <section className="warning-banner compact">
        <strong>⚠</strong>
        <span>본 결과는 의료 진단이 아닌 생활습관 개선을 위한 참고 지표입니다.</span>
      </section>
    </div>
  );
}
