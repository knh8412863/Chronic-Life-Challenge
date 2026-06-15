import { forwardRef, useEffect, useImperativeHandle, useRef, useState } from "react";

import type { AppRoute } from "../../App";
import { getActivityLogs, saveActivity, updateActivityLog, type DailyActivity, type SaveActivityBody } from "../../api/activity";
import { getStoredAccessToken } from "../../api/auth";
import {
  EXERCISE_TYPE_ICONS,
  EXERCISE_TYPE_LABELS,
  EXERCISE_TYPES,
  createExerciseLog,
  estimateCaloriesBurned,
  getExerciseLogs,
  updateExerciseLog,
  type CreateExerciseBody,
  type ExerciseLog,
  type ExerciseTypeCode,
} from "../../api/exercise";
import { analyzeHealthCheckupFile, type HealthCheckupOcrData } from "../../api/healthOcr";
import { getCurrentUser } from "../../api/users";
import { createKidneyRecord, getKidneyRecords, updateKidneyRecord, type CreateKidneyBody, type KidneyRecord } from "../../api/kidney";
import { createLipidRecord, getLipidRecords, updateLipidRecord, type CreateLipidBody, type LipidRecord } from "../../api/lipid";
import { createVital, getVitals, updateVital, type CreateVitalBody, type MeasureType, type VitalRecord } from "../../api/vitals";
import { localDateString } from "../../utils/date";

type Tab = "bp" | "lipid" | "kidney" | "exercise" | "activity";
type BpCategory = "BP" | "BG";
type BpTime = "MORNING" | "LUNCH" | "EVENING";

function todayStr() {
  return localDateString();
}
function nowTimeStr() {
  const d = new Date();
  return `${String(d.getHours()).padStart(2, "0")}:${String(d.getMinutes()).padStart(2, "0")}`;
}
function isToday(iso: string) {
  return iso.slice(0, 10) === todayStr();
}
function nonNegativeValue(value: string): string {
  if (value === "") return "";
  const n = Number(value);
  if (Number.isNaN(n)) return "";
  return String(Math.max(0, n));
}

function readEditingRecord<T>(type: TypeFilter): T | null {
  const raw = sessionStorage.getItem("editingHealthRecordData");
  if (!raw) return null;
  try {
    const data = JSON.parse(raw) as { type?: TypeFilter; record?: T };
    return data.type === type ? data.record ?? null : null;
  } catch {
    sessionStorage.removeItem("editingHealthRecordData");
    return null;
  }
}

type TypeFilter = "ALL" | "BP" | "BG" | "LIPID" | "KIDNEY" | "EXERCISE" | "ACTIVITY";

type VitalsInputPageProps = {
  onNavigate?: (route: AppRoute) => void;
};

type HealthRecordFormHandle = {
  hasInput: () => boolean;
  saveDraft: () => Promise<boolean>;
};

const HEALTH_CHECKUP_OCR_EVENT = "all4health:health-checkup-ocr";

function valueString(value?: number | null) {
  return value == null ? "" : String(value);
}

function dispatchHealthCheckupOcr(data: HealthCheckupOcrData) {
  window.dispatchEvent(new CustomEvent<HealthCheckupOcrData>(HEALTH_CHECKUP_OCR_EVENT, { detail: data }));
}

function addHealthCheckupOcrListener(handler: (data: HealthCheckupOcrData) => void) {
  const listener = (event: Event) => handler((event as CustomEvent<HealthCheckupOcrData>).detail);
  window.addEventListener(HEALTH_CHECKUP_OCR_EVENT, listener);
  return () => window.removeEventListener(HEALTH_CHECKUP_OCR_EVENT, listener);
}

export function VitalsInputPage({ onNavigate }: VitalsInputPageProps) {
  const [tab, setTab] = useState<Tab>("bp");
  const [todayRecordCount, setTodayRecordCount] = useState(0);
  const [isSavingAll, setIsSavingAll] = useState(false);
  const [isOcrLoading, setIsOcrLoading] = useState(false);
  const [ocrMessage, setOcrMessage] = useState("");
  const [showOcrNotice, setShowOcrNotice] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const bpRef = useRef<HealthRecordFormHandle>(null);
  const lipidRef = useRef<HealthRecordFormHandle>(null);
  const kidneyRef = useRef<HealthRecordFormHandle>(null);
  const exerciseRef = useRef<HealthRecordFormHandle>(null);
  const activityRef = useRef<HealthRecordFormHandle>(null);

  const refreshTodayRecordCount = () => {
    const token = getStoredAccessToken();
    if (!token) {
      setTodayRecordCount(0);
      return;
    }
    const today = todayStr();
    Promise.allSettled([
      getVitals({ from: today, to: today, limit: 100 }, token),
      getLipidRecords({ limit: 100 }, token),
      getKidneyRecords({ limit: 100 }, token),
      getExerciseLogs({ from: today, to: today, limit: 100 }, token),
      getActivityLogs({ from: today, to: today, limit: 100 }, token),
    ])
      .then(([vitals, lipid, kidney, exercise, activity]) => {
        const count =
          (vitals.status === "fulfilled" ? vitals.value.data.items.filter((item) => isToday(item.measured_at)).length : 0)
          + (lipid.status === "fulfilled" ? lipid.value.data.filter((item) => item.record_date === today).length : 0)
          + (kidney.status === "fulfilled" ? kidney.value.data.filter((item) => item.measured_date === today || item.record_date === today).length : 0)
          + (exercise.status === "fulfilled" ? exercise.value.data.items.length : 0)
          + (activity.status === "fulfilled" ? activity.value.data.length : 0);
        setTodayRecordCount(Math.min(count, 3));
      })
      .catch(() => setTodayRecordCount(0));
  };

  useEffect(() => {
    refreshTodayRecordCount();
    const requestedTab = new URLSearchParams(window.location.search).get("tab");
    if (requestedTab === "exercise") {
      setTab("exercise");
      window.history.replaceState({}, "", "/health/vitals/input");
    }

    const raw = sessionStorage.getItem("editingHealthRecordData");
    if (!raw) return;
    try {
      const data = JSON.parse(raw) as { type?: TypeFilter };
      if (data.type === "LIPID") setTab("lipid");
      else if (data.type === "KIDNEY") setTab("kidney");
      else if (data.type === "EXERCISE") setTab("exercise");
      else if (data.type === "ACTIVITY") setTab("activity");
      else if (data.type === "BP" || data.type === "BG") setTab("bp");
    } catch {
      sessionStorage.removeItem("editingHealthRecordData");
    }
  }, []);

  const handleSaveAll = async () => {
    const forms = [bpRef.current, lipidRef.current, kidneyRef.current, exerciseRef.current, activityRef.current].filter(
      (form): form is HealthRecordFormHandle => Boolean(form),
    );
    const targets = forms.filter((form) => form.hasInput());
    if (targets.length === 0) {
      alert("저장할 건강 기록을 입력해 주세요.");
      return;
    }

    setIsSavingAll(true);
    try {
      for (const form of targets) {
        await form.saveDraft();
      }
      sessionStorage.removeItem("editingHealthRecordData");
      sessionStorage.removeItem("editingVitalData");
      refreshTodayRecordCount();
      onNavigate?.("/health/vitals");
    } catch (error) {
      if (error instanceof Error && error.message === "WEIGHT_REQUIRED") return;
      alert("저장에 실패했습니다. 입력값을 확인한 뒤 다시 시도해 주세요.");
    } finally {
      setIsSavingAll(false);
    }
  };

  const handleHealthCheckupFile = async (file?: File | null) => {
    if (!file) return;
    const token = getStoredAccessToken();
    if (!token) {
      setOcrMessage("로그인 후 건강검진 파일을 불러올 수 있습니다.");
      return;
    }
    setIsOcrLoading(true);
    setOcrMessage("");
    try {
      const response = await analyzeHealthCheckupFile(file, token);
      dispatchHealthCheckupOcr(response.data);
      if (response.data.matched_fields.some((field) => ["sbp", "dbp", "glucose_fasting", "glucose_postprandial"].includes(field))) {
        setTab("bp");
      } else if (response.data.matched_fields.some((field) => ["total_cholesterol", "ldl_cholesterol", "hdl_cholesterol", "triglycerides", "waist_circumference"].includes(field))) {
        setTab("lipid");
      } else if (response.data.matched_fields.some((field) => ["creatinine", "egfr", "bun", "urine_protein_pos"].includes(field))) {
        setTab("kidney");
      } else if (response.data.matched_fields.length > 0) {
        setTab("activity");
      }
      setOcrMessage(
        response.data.matched_fields.length > 0
          ? `건강검진 파일에서 ${response.data.matched_fields.length}개 항목을 불러왔습니다. 수치를 확인한 뒤 저장해 주세요.`
          : "OCR은 완료됐지만 자동으로 매칭된 건강 수치가 없습니다. 인식 결과를 확인하고 직접 입력해 주세요.",
      );
      setShowOcrNotice(true);
    } catch {
      setOcrMessage("건강검진 파일을 분석하지 못했습니다. 파일 형식과 OCR 설정을 확인해 주세요.");
    } finally {
      setIsOcrLoading(false);
      if (fileInputRef.current) fileInputRef.current.value = "";
    }
  };

  return (
    <div className="vitals-input-page page-stack">
      <section className="section-header-row page-heading-row">
        <div className="page-heading">
          <p className="eyebrow">건강 관리</p>
          <h1>건강 기록 입력</h1>
          <p className="goal-section-note">오늘 건강 기록 3회 중 {todayRecordCount}회 입력 완료</p>
        </div>
        <div style={{ display: "flex", flexDirection: "column", alignItems: "flex-end", gap: 8 }}>
          <input
            ref={fileInputRef}
            type="file"
            accept="image/png,image/jpeg,application/pdf"
            style={{ display: "none" }}
            onChange={(event) => handleHealthCheckupFile(event.target.files?.[0])}
          />
          <button
            type="button"
            className="green-button"
            onClick={() => fileInputRef.current?.click()}
            disabled={isOcrLoading}
          >
            {isOcrLoading ? "분석 중..." : "건강검진 파일 불러오기"}
          </button>
        </div>
      </section>

      {showOcrNotice && (
        <div className="app-modal-backdrop" role="dialog" aria-modal="true">
          <div className="app-modal-card">
            <p>글씨가 너무 작거나 흐릿하여 인식하지 못할 수 있습니다.</p>
            <p>수치를 확인한 뒤 저장해 주세요.</p>
            <button type="button" className="green-button" onClick={() => setShowOcrNotice(false)}>
              확인
            </button>
          </div>
        </div>
      )}

      {/* 탭 */}
      <div className="vi-tabs">
        <button
          type="button"
          className={`vi-tab ${tab === "bp" ? "vi-tab--active" : ""}`}
          onClick={() => setTab("bp")}
        >
          혈압/혈당
        </button>
        <button
          type="button"
          className={`vi-tab ${tab === "lipid" ? "vi-tab--active" : ""}`}
          onClick={() => setTab("lipid")}
        >
          지질 지표
        </button>
        <button
          type="button"
          className={`vi-tab ${tab === "kidney" ? "vi-tab--active" : ""}`}
          onClick={() => setTab("kidney")}
        >
          신장
        </button>
        <button
          type="button"
          className={`vi-tab ${tab === "exercise" ? "vi-tab--active" : ""}`}
          onClick={() => setTab("exercise")}
        >
          운동 기록
        </button>
        <button
          type="button"
          className={`vi-tab ${tab === "activity" ? "vi-tab--active" : ""}`}
          onClick={() => setTab("activity")}
        >
          일일 활동 기록
        </button>
      </div>

      <div style={{ display: tab === "bp" ? "block" : "none" }}>
        <BpForm ref={bpRef} onSaveAll={handleSaveAll} isSavingAll={isSavingAll} todayBpCount={todayRecordCount} />
      </div>
      <div style={{ display: tab === "lipid" ? "block" : "none" }}>
        <LipidForm ref={lipidRef} onNavigate={onNavigate} onSaveAll={handleSaveAll} isSavingAll={isSavingAll} />
      </div>
      <div style={{ display: tab === "kidney" ? "block" : "none" }}>
        <KidneyForm ref={kidneyRef} onNavigate={onNavigate} onSaveAll={handleSaveAll} isSavingAll={isSavingAll} />
      </div>
      <div style={{ display: tab === "exercise" ? "block" : "none" }}>
        <ExerciseInputPanel ref={exerciseRef} onNavigate={onNavigate} onSaveAll={handleSaveAll} isSavingAll={isSavingAll} />
      </div>
      <div style={{ display: tab === "activity" ? "block" : "none" }}>
        <ActivityInputPanel ref={activityRef} onNavigate={onNavigate} onSaveAll={handleSaveAll} isSavingAll={isSavingAll} />
      </div>
    </div>
  );
}

/* ── 혈압/혈당 폼 ─────────────────────────────────── */
const BpForm = forwardRef<HealthRecordFormHandle, {
  onSaveAll: () => void;
  isSavingAll: boolean;
  todayBpCount: number;
}>(
function BpForm({ onSaveAll, isSavingAll, todayBpCount }, ref) {
  const [category, setCategory] = useState<BpCategory>("BP");
  const [bpTime, setBpTime] = useState<BpTime>("MORNING");
  const [systolic, setSystolic] = useState("");
  const [diastolic, setDiastolic] = useState("");
  const [fastingGlucose, setFastingGlucose] = useState("");
  const [postprandialGlucose, setPostprandialGlucose] = useState("");
  const [date, setDate] = useState(todayStr());
  const [time, setTime] = useState(nowTimeStr());
  const [memo, setMemo] = useState("");
  const [isSaving, setIsSaving] = useState(false);
  const [editingVital, setEditingVital] = useState<VitalRecord | null>(null);

  const isBpWarning = category === "BP" && Number(systolic) >= 140;

  useEffect(() => {
    const raw = sessionStorage.getItem("editingVitalData");
    if (!raw) return;
    try {
      const record = JSON.parse(raw) as VitalRecord;
      setEditingVital(record);
      const measureType = record.measure_type;
      const measuredAt = new Date(record.measured_at);
      setDate(record.measured_at.slice(0, 10));
      if (!Number.isNaN(measuredAt.getTime())) {
        setTime(`${String(measuredAt.getHours()).padStart(2, "0")}:${String(measuredAt.getMinutes()).padStart(2, "0")}`);
      }
      setMemo(record.memo ?? "");
      if (measureType.startsWith("BP_")) {
        setCategory("BP");
        setBpTime(measureType.replace("BP_", "") as BpTime);
        setSystolic(String(record.sbp ?? record.systolic ?? ""));
        setDiastolic(String(record.dbp ?? record.diastolic ?? ""));
      } else {
        setCategory("BG");
        if (measureType === "GLUCOSE_FASTING") {
          setFastingGlucose(String(record.glucose ?? record.glucose_value ?? ""));
        } else {
          setPostprandialGlucose(String(record.glucose ?? record.glucose_value ?? ""));
        }
      }
    } catch {
      sessionStorage.removeItem("editingVitalData");
    }
  }, []);

  useEffect(() => addHealthCheckupOcrListener((data) => {
    const vitals = data.vitals;
    if (vitals.sbp != null) setSystolic(valueString(vitals.sbp));
    if (vitals.dbp != null) setDiastolic(valueString(vitals.dbp));
    if (vitals.glucose_fasting != null) setFastingGlucose(valueString(vitals.glucose_fasting));
    if (vitals.glucose_postprandial != null) setPostprandialGlucose(valueString(vitals.glucose_postprandial));
    if (vitals.glucose_fasting != null || vitals.glucose_postprandial != null) setCategory("BG");
    else if (vitals.sbp != null || vitals.dbp != null) setCategory("BP");
    if (data.matched_fields.length > 0) setMemo((current) => current || "건강검진 OCR로 불러온 수치입니다.");
  }), []);

  const hasInput = () => Boolean(editingVital || systolic || diastolic || fastingGlucose || postprandialGlucose || memo.trim());

  async function saveDraft() {
    const token = getStoredAccessToken();
    const measuredAt = `${date}T${time}:00`;
    const requests: CreateVitalBody[] = [];

    if (editingVital && category === "BP") {
      if (!systolic && !diastolic) return false;
      if (!systolic || !diastolic) throw new Error("혈압 입력값이 부족합니다.");
      requests.push({
        measure_type: `BP_${bpTime}` as MeasureType,
        measured_at: measuredAt,
        systolic: Number(systolic),
        diastolic: Number(diastolic),
      });
    } else if (editingVital && category === "BG") {
      if (!fastingGlucose && !postprandialGlucose) return false;
      if (fastingGlucose) {
        requests.push({
          measure_type: "GLUCOSE_FASTING",
          measured_at: measuredAt,
          glucose: Number(fastingGlucose),
        });
      }
      if (postprandialGlucose) {
        requests.push({
          measure_type: "GLUCOSE_POSTPRANDIAL",
          measured_at: measuredAt,
          glucose: Number(postprandialGlucose),
        });
      }
    } else {
      if (systolic || diastolic) {
        if (!systolic || !diastolic) throw new Error("혈압 입력값이 부족합니다.");
        requests.push({
          measure_type: `BP_${bpTime}` as MeasureType,
          measured_at: measuredAt,
          systolic: Number(systolic),
          diastolic: Number(diastolic),
        });
      }
      if (fastingGlucose) {
        requests.push({
          measure_type: "GLUCOSE_FASTING",
          measured_at: measuredAt,
          glucose: Number(fastingGlucose),
        });
      }
      if (postprandialGlucose) {
        requests.push({
          measure_type: "GLUCOSE_POSTPRANDIAL",
          measured_at: measuredAt,
          glucose: Number(postprandialGlucose),
        });
      }
    }
    const memoText = memo.trim();
    if (memoText) {
      requests.forEach((body) => { body.memo = memoText; });
    }

    if (editingVital) {
      const body = requests[0];
      await updateVital(editingVital.id, body, token ?? undefined);
      return true;
    }
    await Promise.all(requests.map((body) => createVital(body, token ?? undefined)));
    return requests.length > 0;
  }

  useImperativeHandle(ref, () => ({ hasInput, saveDraft }));

  return (
    <div className="vi-form-body">
      <div className="vi-form-hint-row">
        <span className="goal-section-note">
          {editingVital ? "당일 기록 수정 중" : `오늘 ${todayBpCount}/3회 입력 완료`}
        </span>
      </div>

      {/* 측정 유형 */}
      <section className="dashboard-card vi-section">
        <h2>측정 유형</h2>
        <div className="vi-type-grid">
          <button
            type="button"
            className={`vi-type-btn ${category === "BP" ? "vi-type-btn--active" : ""}`}
            onClick={() => setCategory("BP")}
          >
            <span>혈압</span>
          </button>
          <button
            type="button"
            className={`vi-type-btn ${category === "BG" ? "vi-type-btn--active" : ""}`}
            onClick={() => setCategory("BG")}
          >
            <span>혈당</span>
          </button>
        </div>
      </section>

      {/* 측정 시간 */}
      {category === "BP" && (
        <section className="dashboard-card vi-section">
          <h2>측정 시간</h2>
          <div className="vi-time-grid">
            {(["MORNING", "LUNCH", "EVENING"] as BpTime[]).map((t) => (
              <button
                key={t}
                type="button"
                className={`vi-time-btn ${bpTime === t ? "vi-time-btn--active" : ""}`}
                onClick={() => setBpTime(t)}
              >
                {t === "MORNING" ? "아침" : t === "LUNCH" ? "점심" : "저녁"}
              </button>
            ))}
          </div>
        </section>
      )}

      {/* 수치 입력 */}
      <section className="dashboard-card vi-section">
        <h2>{category === "BP" ? "혈압 입력" : "혈당 입력"}</h2>
        {category === "BP" ? (
          <div className="vi-bp-row">
            <div className="vi-bp-input-wrap">
              <input
                type="number"
                className="vi-bp-input vi-bp-systolic"
                placeholder="수축기"
                value={systolic}
                min={0}
                max={250}
                onChange={(e) => setSystolic(nonNegativeValue(e.target.value))}
              />
            </div>
            <span className="vi-bp-sep">/</span>
            <div className="vi-bp-input-wrap">
              <input
                type="number"
                className="vi-bp-input vi-bp-diastolic"
                placeholder="이완기"
                value={diastolic}
                min={0}
                max={150}
                onChange={(e) => setDiastolic(nonNegativeValue(e.target.value))}
              />
            </div>
            <span className="vi-bp-unit">mmHg</span>
          </div>
        ) : (
          <div className="vi-lipid-grid">
            <div className="vi-lipid-field">
              <label className="field-label">공복 혈당 (mg/dL)</label>
              <input
                type="number"
                className="vi-lipid-input vi-lipid-neutral"
                placeholder="예: 98"
                value={fastingGlucose}
                min={0}
                max={600}
                onChange={(e) => setFastingGlucose(nonNegativeValue(e.target.value))}
              />
            </div>
            <div className="vi-lipid-field">
              <label className="field-label">식후 혈당 (mg/dL)</label>
              <input
                type="number"
                className="vi-lipid-input vi-lipid-neutral"
                placeholder="예: 140"
                value={postprandialGlucose}
                min={0}
                max={600}
                onChange={(e) => setPostprandialGlucose(nonNegativeValue(e.target.value))}
              />
            </div>
          </div>
        )}

        {isBpWarning && (
          <div className="vi-warning-banner">
            <p>⚠️ 주의: 수축기 혈압 140 이상 (정상 범위 초과)</p>
            <p>규칙적인 측정과 생활습관 개선이 권고됩니다.</p>
          </div>
        )}
      </section>

      {/* 측정 시간 상세 */}
      <section className="dashboard-card vi-section">
        <h2>측정 시간</h2>
        <div className="vi-datetime-row">
          <div className="vi-field">
            <span className="field-label">날짜</span>
            <input
              type="date"
              className="vi-date-input"
              value={date}
              max={todayStr()}
              onChange={(e) => setDate(e.target.value)}
            />
          </div>
          {category === "BP" && (
            <div className="vi-field">
              <span className="field-label">시간</span>
              <input
                type="time"
                className="vi-date-input"
                value={time}
                onChange={(e) => setTime(e.target.value)}
              />
            </div>
          )}
        </div>
      </section>

      {/* 메모 */}
      <section className="dashboard-card vi-section">
        <h2>메모 (선택)</h2>
        <textarea
          className="vi-memo-input"
          placeholder="특이사항을 입력하세요..."
          value={memo}
          maxLength={200}
          onChange={(e) => setMemo(e.target.value)}
        />
      </section>

      <div className="goal-edit-actions">
        <button
          type="button"
          className="wide-subtle-button"
          onClick={() => window.history.back()}
        >
          취소
        </button>
        <button type="button" className="green-button" onClick={onSaveAll} disabled={isSaving || isSavingAll}>
          {isSaving || isSavingAll ? "저장 중..." : "전체 저장"}
        </button>
      </div>
    </div>
  );
});

/* ── 지질 지표 폼 ─────────────────────────────────── */
const LipidForm = forwardRef<HealthRecordFormHandle, {
  onNavigate?: (r: AppRoute) => void;
  onSaveAll: () => void;
  isSavingAll: boolean;
}>(
function LipidForm({ onNavigate, onSaveAll, isSavingAll }, ref) {
  const [totalCholesterol, setTotalCholesterol] = useState("");
  const [ldl, setLdl] = useState("");
  const [hdl, setHdl] = useState("");
  const [triglycerides, setTriglycerides] = useState("");
  const [waist, setWaist] = useState("");
  const [date, setDate] = useState(todayStr());
  const [source, setSource] = useState("");
  const [memo, setMemo] = useState("");
  const [isSaving, setIsSaving] = useState(false);
  const [editingLipid, setEditingLipid] = useState<LipidRecord | null>(null);

  useEffect(() => {
    const record = readEditingRecord<LipidRecord>("LIPID");
    if (!record) return;
    setEditingLipid(record);
    setTotalCholesterol(String(record.total_cholesterol ?? ""));
    setLdl(String(record.ldl ?? record.ldl_cholesterol ?? ""));
    setHdl(String(record.hdl ?? record.hdl_cholesterol ?? ""));
    setTriglycerides(String(record.triglycerides ?? ""));
    setWaist(String(record.waist_cm ?? record.waist_circumference ?? ""));
    setDate(record.record_date ?? todayStr());
    setMemo(record.memo ?? "");
  }, []);

  useEffect(() => addHealthCheckupOcrListener((data) => {
    const lipid = data.lipid;
    if (lipid.total_cholesterol != null) setTotalCholesterol(valueString(lipid.total_cholesterol));
    if (lipid.ldl_cholesterol != null) setLdl(valueString(lipid.ldl_cholesterol));
    if (lipid.hdl_cholesterol != null) setHdl(valueString(lipid.hdl_cholesterol));
    if (lipid.triglycerides != null) setTriglycerides(valueString(lipid.triglycerides));
    if (lipid.waist_circumference != null) setWaist(valueString(lipid.waist_circumference));
    if (Object.values(lipid).some((value) => value != null)) {
      setSource("건강검진 OCR");
    }
  }), []);

  const hasInput = () => Boolean(
    editingLipid || totalCholesterol || ldl || hdl || triglycerides || waist,
  );

  async function saveDraft() {
    const token = getStoredAccessToken();
    const body: CreateLipidBody = { record_date: date };
    if (totalCholesterol) body.total_cholesterol = Number(totalCholesterol);
    if (ldl) body.ldl = Number(ldl);
    if (hdl) body.hdl = Number(hdl);
    if (triglycerides) body.triglycerides = Number(triglycerides);
    if (waist) body.waist_cm = Number(waist);
    const memoText = [source.trim() ? `측정 출처: ${source.trim()}` : "", memo.trim()].filter(Boolean).join("\n");
    if (memoText) body.memo = memoText;

    if (!hasInput()) return false;
    if (editingLipid) {
      await updateLipidRecord(editingLipid.id, body, token ?? undefined);
      return true;
    }
    await createLipidRecord(body, token ?? undefined);
    return true;
  }

  useImperativeHandle(ref, () => ({ hasInput, saveDraft }));

  return (
    <div className="vi-form-body">
      <section className="dashboard-card vi-section">
        <h2>지질 지표</h2>
        <div className="vi-lipid-grid">
          <div className="vi-lipid-field">
            <label className="field-label">총 콜레스테롤 (mg/dL)</label>
            <input type="number" min={0} className="vi-lipid-input vi-lipid-neutral" placeholder="예: 200" value={totalCholesterol} onChange={(e) => setTotalCholesterol(nonNegativeValue(e.target.value))} />
          </div>
          <div className="vi-lipid-field">
            <label className="field-label">LDL 콜레스테롤 (저밀도 콜레스테롤, mg/dL)</label>
            <input type="number" min={0} className="vi-lipid-input vi-lipid-neutral" placeholder="예: 100" value={ldl} onChange={(e) => setLdl(nonNegativeValue(e.target.value))} />
          </div>
          <div className="vi-lipid-field">
            <label className="field-label">HDL 콜레스테롤 (고밀도 콜레스테롤, mg/dL)</label>
            <input type="number" min={0} className="vi-lipid-input vi-lipid-neutral" placeholder="예: 50" value={hdl} onChange={(e) => setHdl(nonNegativeValue(e.target.value))} />
          </div>
          <div className="vi-lipid-field">
            <label className="field-label">중성지방 (mg/dL)</label>
            <input type="number" min={0} className="vi-lipid-input vi-lipid-neutral" placeholder="예: 150" value={triglycerides} onChange={(e) => setTriglycerides(nonNegativeValue(e.target.value))} />
          </div>
          <div className="vi-lipid-field">
            <label className="field-label">허리둘레 (cm)</label>
            <input type="number" min={0} className="vi-lipid-input vi-lipid-neutral" placeholder="예: 80" value={waist} onChange={(e) => setWaist(nonNegativeValue(e.target.value))} />
          </div>
        </div>
      </section>

      <section className="dashboard-card vi-section">
        <h2>측정 정보</h2>
        <div className="vi-field" style={{ marginBottom: "16px" }}>
          <span className="field-label">측정 날짜</span>
          <input type="date" className="vi-date-input" value={date} max={todayStr()} onChange={(e) => setDate(e.target.value)} />
        </div>
        <div className="vi-field" style={{ marginBottom: "16px" }}>
          <span className="field-label">측정 출처 (선택)</span>
          <input type="text" className="vi-date-input" placeholder="예: 병원명" value={source} onChange={(e) => setSource(e.target.value)} />
        </div>
        <div className="vi-field">
          <span className="field-label">메모 (선택)</span>
          <textarea className="vi-memo-input" placeholder="메모 (선택사항)" value={memo} onChange={(e) => setMemo(e.target.value)} />
        </div>
      </section>

      <div className="goal-edit-actions">
        <button type="button" className="green-button" onClick={onSaveAll} disabled={isSaving || isSavingAll}>
          {isSaving || isSavingAll ? "저장 중..." : "전체 저장"}
        </button>
        <button type="button" className="wide-subtle-button" onClick={() => onNavigate?.("/health/vitals")}>
          취소
        </button>
      </div>
    </div>
  );
});

/* ── 신장 지표 폼 ─────────────────────────────────── */
const KidneyForm = forwardRef<HealthRecordFormHandle, {
  onNavigate?: (r: AppRoute) => void;
  onSaveAll: () => void;
  isSavingAll: boolean;
}>(
function KidneyForm({ onNavigate, onSaveAll, isSavingAll }, ref) {
  const [creatinine, setCreatinine] = useState("");
  const [bun, setBun] = useState("");
  const [egfr, setEgfr] = useState("");
  const [proteinuria, setProteinuria] = useState<boolean | null>(null);
  const [date, setDate] = useState(todayStr());
  const [source, setSource] = useState("");
  const [memo, setMemo] = useState("");
  const [isSaving, setIsSaving] = useState(false);
  const [editingKidney, setEditingKidney] = useState<KidneyRecord | null>(null);

  useEffect(() => {
    const record = readEditingRecord<KidneyRecord>("KIDNEY");
    if (!record) return;
    setEditingKidney(record);
    setCreatinine(String(record.creatinine ?? ""));
    setBun(String(record.bun ?? ""));
    setEgfr(String(record.egfr ?? ""));
    setProteinuria(record.urine_protein_pos == null ? null : record.urine_protein_pos !== true);
    setDate(record.record_date ?? record.measured_date ?? todayStr());
    setMemo(record.memo ?? "");
  }, []);

  useEffect(() => addHealthCheckupOcrListener((data) => {
    const renal = data.renal;
    if (renal.creatinine != null) setCreatinine(valueString(renal.creatinine));
    if (renal.bun != null) setBun(valueString(renal.bun));
    if (renal.egfr != null) setEgfr(valueString(renal.egfr));
    if (renal.urine_protein_pos != null) setProteinuria(!renal.urine_protein_pos);
    if (Object.values(renal).some((value) => value != null)) {
      setSource("건강검진 OCR");
    }
  }), []);

  const calculatedEgfr =
    creatinine
      ? (Math.round((186 * Math.pow(Number(creatinine), -1.154)) * 10) / 10).toFixed(1)
      : null;

  const hasInput = () => Boolean(
    editingKidney || creatinine || bun || egfr || proteinuria !== null,
  );

  async function saveDraft() {
    const token = getStoredAccessToken();
    if (!hasInput()) return false;
    const body: CreateKidneyBody = {
      measured_date: date,
      record_date: date,
    };
    if (creatinine) body.creatinine = Number(creatinine);
    if (bun) body.bun = Number(bun);
    if (egfr) body.egfr = Number(egfr);
    else if (calculatedEgfr) body.egfr = Number(calculatedEgfr);
    if (proteinuria !== null) body.urine_protein_pos = !proteinuria;
    const memoText = [source.trim() ? `측정 출처: ${source.trim()}` : "", memo.trim()].filter(Boolean).join("\n");
    if (memoText) body.memo = memoText;

    if (editingKidney) {
      await updateKidneyRecord(editingKidney.id, body, token ?? undefined);
      return true;
    }
    await createKidneyRecord(body, token ?? undefined);
    return true;
  }

  useImperativeHandle(ref, () => ({ hasInput, saveDraft }));

  return (
    <div className="vi-form-body">
      <div className="vi-kidney-layout">
        {/* 신장 기능 검사 */}
        <section className="dashboard-card vi-section">
          <h2>신장 기능 검사</h2>
          <div className="vi-field" style={{ marginBottom: "16px" }}>
            <label className="field-label">혈청 크레아티닌 (mg/dL)</label>
            <input
              type="number"
              step="0.1"
              min={0}
              className="vi-kidney-input"
              placeholder="예: 1.0"
              value={creatinine}
              onChange={(e) => setCreatinine(nonNegativeValue(e.target.value))}
            />
          </div>
          <div className="vi-field" style={{ marginBottom: "16px" }}>
            <label className="field-label">BUN (mg/dL)</label>
            <input
              type="number"
              step="0.1"
              min={0}
              className="vi-kidney-input"
              placeholder="예: 15"
              value={bun}
              onChange={(e) => setBun(nonNegativeValue(e.target.value))}
            />
          </div>
          <div className="vi-field">
            <label className="field-label">eGFR (자동계산 또는 직접 입력)</label>
            <div className="vi-egfr-display">
              {egfr || calculatedEgfr
                ? `${egfr || calculatedEgfr} mL/min/1.73m²`
                : "90 mL/min/1.73m²"}
            </div>
            <input
              type="number"
              step="0.1"
              min={0}
              className="vi-kidney-input"
              placeholder="직접 입력"
              value={egfr}
              onChange={(e) => setEgfr(nonNegativeValue(e.target.value))}
              style={{ marginTop: "8px" }}
            />
            {calculatedEgfr && (
              <button
                type="button"
                className="wide-subtle-button"
                style={{ marginTop: "8px" }}
                onClick={() => setEgfr(calculatedEgfr)}
              >
                자동계산 값 사용
              </button>
            )}
            <p className="goal-section-note">* 크레아티닌+나이+성별로 자동계산되지만 직접 입력도 가능합니다</p>
          </div>
        </section>

        {/* 소변 검사 */}
        <section className="dashboard-card vi-section">
          <h2>소변 검사</h2>
          <span className="field-label">단백뇨 (선택)</span>
          <div className="vi-time-grid" style={{ marginTop: "8px" }}>
            <button
              type="button"
              className={`vi-time-btn ${proteinuria === true ? "vi-time-btn--active" : ""}`}
              onClick={() => setProteinuria(true)}
            >
              음성
            </button>
            <button
              type="button"
              className={`vi-time-btn ${proteinuria === false ? "vi-time-btn--active" : ""}`}
              onClick={() => setProteinuria(false)}
            >
              양성
            </button>
          </div>
          <p className="goal-section-note" style={{ marginTop: "8px" }}>
            * 검사 결과지에 표시된 단백뇨 여부를 선택해주세요.
          </p>
        </section>
      </div>

      {/* 측정 정보 */}
      <section className="dashboard-card vi-section">
        <h2>측정 정보</h2>
        <div className="vi-field" style={{ marginBottom: "16px" }}>
          <span className="field-label">측정 날짜</span>
          <input type="date" className="vi-date-input" value={date} max={todayStr()} onChange={(e) => setDate(e.target.value)} />
        </div>
        <div className="vi-field" style={{ marginBottom: "16px" }}>
          <span className="field-label">측정 출처 (선택)</span>
          <input type="text" className="vi-date-input" placeholder="예: 병원명" value={source} onChange={(e) => setSource(e.target.value)} />
        </div>
        <div className="vi-field">
          <span className="field-label">메모 (선택)</span>
          <textarea className="vi-memo-input" placeholder="예: OO병원에서 측정" value={memo} onChange={(e) => setMemo(e.target.value)} />
        </div>
      </section>

      <div className="goal-edit-actions">
        <button type="button" className="green-button" onClick={onSaveAll} disabled={isSaving || isSavingAll}>
          {isSaving || isSavingAll ? "저장 중..." : "전체 저장"}
        </button>
        <button type="button" className="wide-subtle-button" onClick={() => onNavigate?.("/health/vitals")}>
          취소
        </button>
      </div>
    </div>
  );
});

const ExerciseInputPanel = forwardRef<HealthRecordFormHandle, {
  onNavigate?: (r: AppRoute) => void;
  onSaveAll: () => void;
  isSavingAll: boolean;
}>(
function ExerciseInputPanel({ onNavigate, onSaveAll, isSavingAll }, ref) {
  const [selectedType, setSelectedType] = useState<ExerciseTypeCode>("RUNNING");
  const [date, setDate] = useState(todayStr());
  const [minutes, setMinutes] = useState("");
  const [calories, setCalories] = useState("");
  const [memo, setMemo] = useState("");
  const [isSaving, setIsSaving] = useState(false);
  const [editingExercise, setEditingExercise] = useState<ExerciseLog | null>(null);
  const [hasEdited, setHasEdited] = useState(false);
  const [weightKg, setWeightKg] = useState<number | null>(null);
  const [hasWeightProfile, setHasWeightProfile] = useState(true);
  const [isCaloriesManual, setIsCaloriesManual] = useState(false);
  const [showWeightRequiredModal, setShowWeightRequiredModal] = useState(false);

  useEffect(() => {
    const record = readEditingRecord<ExerciseLog>("EXERCISE");
    if (!record) return;
    setEditingExercise(record);
    setSelectedType(record.exercise_type);
    setDate(record.exercise_date ?? todayStr());
    setMinutes(String(record.duration_minutes));
    setCalories(String(record.calories_burned ?? ""));
    setIsCaloriesManual(record.calories_burned != null);
    setMemo(record.memo ?? "");
  }, []);

  useEffect(() => {
    getCurrentUser(getStoredAccessToken())
      .then((user) => {
        setWeightKg(user.weight);
        setHasWeightProfile(user.weight != null);
      })
      .catch(() => {
        setWeightKg(null);
        setHasWeightProfile(false);
      });
  }, []);

  useEffect(() => {
    if (isCaloriesManual) return;
    const duration = Number(minutes || 0);
    const estimated = duration > 0 ? estimateCaloriesBurned(selectedType, duration, weightKg) : null;
    setCalories(estimated === null ? "" : String(estimated));
  }, [isCaloriesManual, minutes, selectedType, weightKg]);

  const hasInput = () => Boolean(editingExercise || minutes || calories || memo.trim());

  async function saveDraft() {
    const token = getStoredAccessToken();
    if (!hasInput()) return false;
    if (!minutes || Number(minutes) <= 0) return false;
    if (!calories && !hasWeightProfile) {
      setShowWeightRequiredModal(true);
      throw new Error("WEIGHT_REQUIRED");
    }
    const body: CreateExerciseBody = {
      exercise_type: selectedType,
      duration_minutes: Number(minutes),
      exercise_date: date,
    };
    if (calories) body.calories_burned = Number(calories);
    if (memo.trim()) body.memo = memo.trim();

    if (editingExercise) {
      await updateExerciseLog(editingExercise.id, body, token ?? undefined);
      return true;
    }
    await createExerciseLog(body, token ?? undefined);
    return true;
  }

  useImperativeHandle(ref, () => ({ hasInput, saveDraft }));

  return (
    <div className="ex-input-body">
      <section className="dashboard-card vi-section">
        <h2>운동 종류</h2>
        <div className="ex-type-grid">
          {EXERCISE_TYPES.map((t) => (
            <button
              key={t}
              type="button"
              className={`ex-type-btn ${selectedType === t ? "ex-type-btn--active" : ""}`}
              onClick={() => { setSelectedType(t); setHasEdited(true); }}
            >
              <span className="ex-type-icon">{EXERCISE_TYPE_ICONS[t]}</span>
              <span>{EXERCISE_TYPE_LABELS[t]}</span>
            </button>
          ))}
        </div>
      </section>
      <section className="dashboard-card vi-section">
        <h2>운동 정보</h2>
        <div className="ex-info-row">
          <div className="vi-field" style={{ flex: 1 }}>
            <span className="field-label">운동 날짜</span>
            <input type="date" className="vi-date-input" value={date} max={todayStr()} onChange={(e) => { setDate(e.target.value); setHasEdited(true); }} />
          </div>
          <div className="vi-field">
            <span className="field-label">운동 시간 (분)</span>
            <div className="ex-stepper">
              <button type="button" className="ex-stepper-btn" onClick={() => { setMinutes((m) => String(Math.max(0, Number(m || 0) - 5))); setHasEdited(true); }}>−</button>
              <span className="ex-stepper-val">{minutes}</span>
              <button type="button" className="ex-stepper-btn" onClick={() => { setMinutes((m) => String(Math.min(720, Number(m || 0) + 5))); setHasEdited(true); }}>+</button>
              <span className="field-label">분</span>
            </div>
          </div>
        </div>
      </section>
      <section className="dashboard-card vi-section">
        <h2>예상 소모 칼로리</h2>
        <input
          type="number"
          min={0}
          className="vi-date-input"
          placeholder="내 체중·운동종류·운동시간 기준 자동 계산"
          value={calories}
          onChange={(e) => {
            setCalories(nonNegativeValue(e.target.value));
            setIsCaloriesManual(true);
            setHasEdited(true);
          }}
        />
        <p className="goal-section-note">
          * MET 기준 예상값입니다. 자동 계산에는 건강 프로필의 체중이 필요합니다.
        </p>
      </section>
      <section className="dashboard-card vi-section">
        <h2>운동 메모 (선택)</h2>
        <textarea className="vi-memo-input" placeholder="운동 중에 느낀 점을 기록하세요..." value={memo} onChange={(e) => { setMemo(e.target.value); setHasEdited(true); }} />
      </section>
      <div className="goal-edit-actions">
        <button type="button" className="wide-subtle-button" onClick={() => onNavigate?.("/health/vitals")}>취소</button>
        <button type="button" className="green-button" onClick={onSaveAll} disabled={isSaving || isSavingAll}>{isSaving || isSavingAll ? "저장 중..." : "전체 저장"}</button>
      </div>
      {showWeightRequiredModal && (
        <div className="app-modal-backdrop" role="dialog" aria-modal="true">
          <div className="app-modal-card">
            <h2>체중 입력이 필요합니다</h2>
            <p>운동 종류와 시간을 기준으로 예상 소모 칼로리를 계산하려면 건강 프로필에 체중이 필요합니다.</p>
            <div className="button-row">
              <button type="button" className="wide-subtle-button" onClick={() => setShowWeightRequiredModal(false)}>
                닫기
              </button>
              <button type="button" className="green-button" onClick={() => onNavigate?.("/health/profile")}>
                건강 프로필로 이동
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
});

const ActivityInputPanel = forwardRef<HealthRecordFormHandle, {
  onNavigate?: (r: AppRoute) => void;
  onSaveAll: () => void;
  isSavingAll: boolean;
}>(
function ActivityInputPanel({ onNavigate, onSaveAll, isSavingAll }, ref) {
  const [steps, setSteps] = useState("");
  const [exerciseMinutes, setExerciseMinutes] = useState("");
  const [sleepHours, setSleepHours] = useState("");
  const [waterMl, setWaterMl] = useState("");
  const [stressLevel, setStressLevel] = useState(3);
  const [isSaving, setIsSaving] = useState(false);
  const [editingActivity, setEditingActivity] = useState<DailyActivity | null>(null);
  const [hasEdited, setHasEdited] = useState(false);
  const [hasStressEdited, setHasStressEdited] = useState(false);

  useEffect(() => {
    const record = readEditingRecord<DailyActivity>("ACTIVITY");
    if (!record) return;
    setEditingActivity(record);
    setSteps(String(record.steps ?? ""));
    setExerciseMinutes(String(record.exercise_minutes ?? ""));
    setSleepHours(String(record.sleep_hours ?? ""));
    setWaterMl(String(record.water_ml ?? ""));
    setStressLevel(record.stress_level ?? 3);
    setHasStressEdited(record.stress_level != null);
  }, []);

  useEffect(() => addHealthCheckupOcrListener((data) => {
    const activity = data.activity;
    let changed = false;
    if (activity.steps != null) {
      setSteps(valueString(activity.steps));
      changed = true;
    }
    if (activity.exercise_minutes != null) {
      setExerciseMinutes(valueString(activity.exercise_minutes));
      changed = true;
    }
    if (activity.sleep_hours != null) {
      setSleepHours(valueString(activity.sleep_hours));
      changed = true;
    }
    if (activity.water_ml != null) {
      setWaterMl(valueString(activity.water_ml));
      changed = true;
    }
    if (changed) setHasEdited(true);
  }), []);

  const hasInput = () => Boolean(editingActivity || hasEdited || steps || exerciseMinutes || sleepHours || waterMl);

  async function saveDraft() {
    const token = getStoredAccessToken();
    if (!hasInput()) return false;
    const body: SaveActivityBody = {
      steps: steps ? Number(steps) : undefined,
      exercise_minutes: exerciseMinutes ? Number(exerciseMinutes) : undefined,
      sleep_hours: sleepHours ? Number(sleepHours) : undefined,
      water_ml: waterMl ? Number(waterMl) : undefined,
    };
    if (hasStressEdited) body.stress_level = stressLevel;
    const activityId = editingActivity?.id ?? editingActivity?.activity_log_id;
    if (activityId) {
      await updateActivityLog(activityId, body, token ?? undefined);
      return true;
    }
    await saveActivity(body, token ?? undefined);
    return true;
  }

  useImperativeHandle(ref, () => ({ hasInput, saveDraft }));

  return (
    <div className="activity-page page-stack">
      <div className="act-two-col">
        <section className="dashboard-card act-section">
          <h2>활동량</h2>
          <div className="vi-field" style={{ marginBottom: "20px" }}>
            <label className="field-label">걸음 수 (보)</label>
            <input type="number" min={0} className="act-input" placeholder="예: 8,000" value={steps} onChange={(e) => { setSteps(nonNegativeValue(e.target.value)); setHasEdited(true); }} />
          </div>
          <div className="vi-field">
            <label className="field-label">운동 시간 (분)</label>
            <input type="number" min={0} className="act-input" placeholder="예: 30" value={exerciseMinutes} onChange={(e) => { setExerciseMinutes(nonNegativeValue(e.target.value)); setHasEdited(true); }} />
          </div>
        </section>
        <section className="dashboard-card act-section">
          <h2>생활 습관</h2>
          <div className="vi-field" style={{ marginBottom: "20px" }}>
            <label className="field-label">수면 시간 (시간)</label>
            <input type="number" step="0.5" min={0} max={24} className="act-input" placeholder="예: 7.5" value={sleepHours} onChange={(e) => { setSleepHours(nonNegativeValue(e.target.value)); setHasEdited(true); }} />
          </div>
          <div className="vi-field">
            <label className="field-label">물 섭취 (ml)</label>
            <input type="number" step="50" min={0} className="act-input" placeholder="예: 1,800" value={waterMl} onChange={(e) => { setWaterMl(nonNegativeValue(e.target.value)); setHasEdited(true); }} />
          </div>
        </section>
      </div>
      <section className="dashboard-card act-section">
        <h2>컨디션</h2>
        <div className="act-slider-row">
          <div className="act-slider-item" style={{ flex: 1 }}>
            <label className="field-label">스트레스 수준 {stressLevel} / 5</label>
            <input type="range" className="act-slider" min={1} max={5} step={1} value={stressLevel} onChange={(e) => { setStressLevel(Number(e.target.value)); setHasEdited(true); setHasStressEdited(true); }} />
          </div>
        </div>
      </section>
      <div className="goal-edit-actions">
        <button type="button" className="wide-subtle-button" onClick={() => onNavigate?.("/health/vitals")}>취소</button>
        <button type="button" className="green-button" onClick={onSaveAll} disabled={isSaving || isSavingAll}>{isSaving || isSavingAll ? "저장 중..." : "전체 저장"}</button>
      </div>
    </div>
  );
});
