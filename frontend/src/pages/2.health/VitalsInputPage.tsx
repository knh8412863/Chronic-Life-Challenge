import { useEffect, useState } from "react";

import type { AppRoute } from "../../App";
import { getActivityLogs, saveActivity } from "../../api/activity";
import { getStoredAccessToken } from "../../api/auth";
import {
  EXERCISE_TYPE_ICONS,
  EXERCISE_TYPE_LABELS,
  EXERCISE_TYPES,
  createExerciseLog,
  getExerciseLogs,
  type CreateExerciseBody,
  type ExerciseTypeCode,
} from "../../api/exercise";
import { createKidneyRecord, getKidneyRecords, type CreateKidneyBody } from "../../api/kidney";
import { createLipidRecord, getLipidRecords, type CreateLipidBody } from "../../api/lipid";
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

type VitalsInputPageProps = {
  onNavigate?: (route: AppRoute) => void;
};

export function VitalsInputPage({ onNavigate }: VitalsInputPageProps) {
  const [tab, setTab] = useState<Tab>("bp");
  const [todayRecordCount, setTodayRecordCount] = useState(0);

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
  }, []);

  return (
    <div className="vitals-input-page page-stack">
      <section className="section-header-row page-heading-row">
        <div className="page-heading">
          <p className="eyebrow">건강 관리</p>
          <h1>건강 기록 입력</h1>
          <p className="goal-section-note">오늘 건강 기록 3회 중 {todayRecordCount}회 입력 완료</p>
        </div>
      </section>

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
        <BpForm onNavigate={onNavigate} onSaved={refreshTodayRecordCount} todayBpCount={todayRecordCount} />
      </div>
      <div style={{ display: tab === "lipid" ? "block" : "none" }}>
        <LipidForm onNavigate={onNavigate} onSaved={refreshTodayRecordCount} />
      </div>
      <div style={{ display: tab === "kidney" ? "block" : "none" }}>
        <KidneyForm onNavigate={onNavigate} onSaved={refreshTodayRecordCount} />
      </div>
      <div style={{ display: tab === "exercise" ? "block" : "none" }}>
        <ExerciseInputPanel onNavigate={onNavigate} onSaved={refreshTodayRecordCount} />
      </div>
      <div style={{ display: tab === "activity" ? "block" : "none" }}>
        <ActivityInputPanel onNavigate={onNavigate} onSaved={refreshTodayRecordCount} />
      </div>
    </div>
  );
}

/* ── 혈압/혈당 폼 ─────────────────────────────────── */
function BpForm({
  onNavigate,
  onSaved,
  todayBpCount,
}: {
  onNavigate?: (r: AppRoute) => void;
  onSaved: () => void;
  todayBpCount: number;
}) {
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

  async function handleSave() {
    const token = getStoredAccessToken();
    const measuredAt = `${date}T${time}:00`;
    const requests: CreateVitalBody[] = [];

    if (category === "BP") {
      if (!systolic || !diastolic) { alert("수축기 및 이완기 혈압을 입력해 주세요."); return; }
      requests.push({
        measure_type: `BP_${bpTime}` as MeasureType,
        measured_at: measuredAt,
        systolic: Number(systolic),
        diastolic: Number(diastolic),
      });
    } else {
      if (!fastingGlucose && !postprandialGlucose) { alert("공복 또는 식후 혈당 값을 입력해 주세요."); return; }
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

    setIsSaving(true);
    try {
      if (editingVital) {
        const body = requests[0];
        await updateVital(editingVital.id, body, token ?? undefined);
        sessionStorage.removeItem("editingVitalData");
      } else {
        await Promise.all(requests.map((body) => createVital(body, token ?? undefined)));
      }
      onSaved();
      onNavigate?.("/health/vitals");
    } catch {
      alert("저장에 실패했습니다. 다시 시도해 주세요.");
    } finally {
      setIsSaving(false);
    }
  }

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
          onClick={() => onNavigate?.("/health/vitals")}
        >
          취소
        </button>
        <button type="button" className="green-button" onClick={handleSave} disabled={isSaving}>
          {isSaving ? "저장 중..." : "저장"}
        </button>
      </div>
    </div>
  );
}

/* ── 지질 지표 폼 ─────────────────────────────────── */
function LipidForm({ onNavigate, onSaved }: { onNavigate?: (r: AppRoute) => void; onSaved: () => void }) {
  const [totalCholesterol, setTotalCholesterol] = useState("");
  const [ldl, setLdl] = useState("");
  const [hdl, setHdl] = useState("");
  const [triglycerides, setTriglycerides] = useState("");
  const [waist, setWaist] = useState("");
  const [date, setDate] = useState(todayStr());
  const [source, setSource] = useState("");
  const [memo, setMemo] = useState("");
  const [isSaving, setIsSaving] = useState(false);

  async function handleSave() {
    const token = getStoredAccessToken();
    const body: CreateLipidBody = { record_date: date };
    if (totalCholesterol) body.total_cholesterol = Number(totalCholesterol);
    if (ldl) body.ldl = Number(ldl);
    if (hdl) body.hdl = Number(hdl);
    if (triglycerides) body.triglycerides = Number(triglycerides);
    if (waist) body.waist_cm = Number(waist);
    const memoText = [source.trim() ? `측정 출처: ${source.trim()}` : "", memo.trim()].filter(Boolean).join("\n");
    if (memoText) body.memo = memoText;

    setIsSaving(true);
    try {
      await createLipidRecord(body, token ?? undefined);
      onSaved();
      onNavigate?.("/health/vitals");
    } catch {
      alert("저장에 실패했습니다. 다시 시도해 주세요.");
    } finally {
      setIsSaving(false);
    }
  }

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
            <label className="field-label">LDL 콜레스테롤 (mg/dL)</label>
            <input type="number" min={0} className="vi-lipid-input vi-lipid-neutral" placeholder="예: 100" value={ldl} onChange={(e) => setLdl(nonNegativeValue(e.target.value))} />
          </div>
          <div className="vi-lipid-field">
            <label className="field-label">HDL 콜레스테롤 (mg/dL)</label>
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
        <button type="button" className="green-button" onClick={handleSave} disabled={isSaving}>
          {isSaving ? "저장 중..." : "저장"}
        </button>
        <button type="button" className="wide-subtle-button" onClick={() => onNavigate?.("/health/vitals")}>
          취소
        </button>
      </div>
    </div>
  );
}

/* ── 신장 지표 폼 ─────────────────────────────────── */
function KidneyForm({ onNavigate, onSaved }: { onNavigate?: (r: AppRoute) => void; onSaved: () => void }) {
  const [creatinine, setCreatinine] = useState("");
  const [bun, setBun] = useState("");
  const [egfr, setEgfr] = useState("");
  const [proteinuria, setProteinuria] = useState<boolean>(true);
  const [date, setDate] = useState(todayStr());
  const [source, setSource] = useState("");
  const [memo, setMemo] = useState("");
  const [isSaving, setIsSaving] = useState(false);

  const calculatedEgfr =
    creatinine
      ? (Math.round((186 * Math.pow(Number(creatinine), -1.154)) * 10) / 10).toFixed(1)
      : null;

  async function handleSave() {
    const token = getStoredAccessToken();
    const body: CreateKidneyBody = {
      measured_date: date,
      record_date: date,
      urine_protein_pos: !proteinuria,
    };
    if (creatinine) body.creatinine = Number(creatinine);
    if (bun) body.bun = Number(bun);
    if (egfr) body.egfr = Number(egfr);
    else if (calculatedEgfr) body.egfr = Number(calculatedEgfr);
    const memoText = [source.trim() ? `측정 출처: ${source.trim()}` : "", memo.trim()].filter(Boolean).join("\n");
    if (memoText) body.memo = memoText;

    setIsSaving(true);
    try {
      await createKidneyRecord(body, token ?? undefined);
      onSaved();
      onNavigate?.("/health/vitals");
    } catch {
      alert("저장에 실패했습니다. 다시 시도해 주세요.");
    } finally {
      setIsSaving(false);
    }
  }

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
              className={`vi-time-btn ${proteinuria ? "vi-time-btn--active" : ""}`}
              onClick={() => setProteinuria(true)}
            >
              음성
            </button>
            <button
              type="button"
              className={`vi-time-btn ${!proteinuria ? "vi-time-btn--active" : ""}`}
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
        <button type="button" className="green-button" onClick={handleSave} disabled={isSaving}>
          {isSaving ? "저장 중..." : "저장"}
        </button>
        <button type="button" className="wide-subtle-button" onClick={() => onNavigate?.("/health/vitals")}>
          취소
        </button>
      </div>
    </div>
  );
}

function ExerciseInputPanel({ onNavigate, onSaved }: { onNavigate?: (r: AppRoute) => void; onSaved: () => void }) {
  const [selectedType, setSelectedType] = useState<ExerciseTypeCode>("RUNNING");
  const [date, setDate] = useState(todayStr());
  const [minutes, setMinutes] = useState(30);
  const [calories, setCalories] = useState("");
  const [memo, setMemo] = useState("");
  const [isSaving, setIsSaving] = useState(false);

  async function handleSave() {
    const token = getStoredAccessToken();
    const body: CreateExerciseBody = {
      exercise_type: selectedType,
      duration_minutes: minutes,
      exercise_date: date,
    };
    if (calories) body.calories_burned = Number(calories);
    if (memo.trim()) body.memo = memo.trim();

    setIsSaving(true);
    try {
      await createExerciseLog(body, token ?? undefined);
      onSaved();
      onNavigate?.("/health/vitals");
    } catch {
      alert("저장에 실패했습니다. 다시 시도해 주세요.");
    } finally {
      setIsSaving(false);
    }
  }

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
              onClick={() => setSelectedType(t)}
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
            <input type="date" className="vi-date-input" value={date} max={todayStr()} onChange={(e) => setDate(e.target.value)} />
          </div>
          <div className="vi-field">
            <span className="field-label">운동 시간 (분)</span>
            <div className="ex-stepper">
              <button type="button" className="ex-stepper-btn" onClick={() => setMinutes((m) => Math.max(1, m - 5))}>−</button>
              <span className="ex-stepper-val">{minutes}</span>
              <button type="button" className="ex-stepper-btn" onClick={() => setMinutes((m) => Math.min(720, m + 5))}>+</button>
              <span className="field-label">분</span>
            </div>
          </div>
        </div>
      </section>
      <section className="dashboard-card vi-section">
        <h2>소모 칼로리 (선택)</h2>
        <input type="number" min={0} className="vi-date-input" placeholder="예: 180" value={calories} onChange={(e) => setCalories(nonNegativeValue(e.target.value))} />
      </section>
      <section className="dashboard-card vi-section">
        <h2>운동 메모 (선택)</h2>
        <textarea className="vi-memo-input" placeholder="운동 중에 느낀 점을 기록하세요..." value={memo} onChange={(e) => setMemo(e.target.value)} />
      </section>
      <div className="goal-edit-actions">
        <button type="button" className="wide-subtle-button" onClick={() => onNavigate?.("/health/vitals")}>취소</button>
        <button type="button" className="green-button" onClick={handleSave} disabled={isSaving}>{isSaving ? "저장 중..." : "저장"}</button>
      </div>
    </div>
  );
}

function ActivityInputPanel({ onNavigate, onSaved }: { onNavigate?: (r: AppRoute) => void; onSaved: () => void }) {
  const [steps, setSteps] = useState("");
  const [exerciseMinutes, setExerciseMinutes] = useState("");
  const [sleepHours, setSleepHours] = useState("");
  const [waterMl, setWaterMl] = useState("");
  const [stressLevel, setStressLevel] = useState(3);
  const [isSaving, setIsSaving] = useState(false);

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
        },
        token ?? undefined,
      );
      onSaved();
      onNavigate?.("/health/vitals");
    } catch {
      alert("저장에 실패했습니다. 다시 시도해 주세요.");
    } finally {
      setIsSaving(false);
    }
  }

  return (
    <div className="activity-page page-stack">
      <div className="act-two-col">
        <section className="dashboard-card act-section">
          <h2>활동량</h2>
          <div className="vi-field" style={{ marginBottom: "20px" }}>
            <label className="field-label">걸음 수 (보)</label>
            <input type="number" min={0} className="act-input" placeholder="예: 8,000" value={steps} onChange={(e) => setSteps(nonNegativeValue(e.target.value))} />
          </div>
          <div className="vi-field">
            <label className="field-label">운동 시간 (분)</label>
            <input type="number" min={0} className="act-input" placeholder="예: 30" value={exerciseMinutes} onChange={(e) => setExerciseMinutes(nonNegativeValue(e.target.value))} />
          </div>
        </section>
        <section className="dashboard-card act-section">
          <h2>생활 습관</h2>
          <div className="vi-field" style={{ marginBottom: "20px" }}>
            <label className="field-label">수면 시간 (시간)</label>
            <input type="number" step="0.5" min={0} max={24} className="act-input" placeholder="예: 7.5" value={sleepHours} onChange={(e) => setSleepHours(nonNegativeValue(e.target.value))} />
          </div>
          <div className="vi-field">
            <label className="field-label">물 섭취 (ml)</label>
            <input type="number" step="50" min={0} className="act-input" placeholder="예: 1,800" value={waterMl} onChange={(e) => setWaterMl(nonNegativeValue(e.target.value))} />
          </div>
        </section>
      </div>
      <section className="dashboard-card act-section">
        <h2>컨디션</h2>
        <div className="act-slider-row">
          <div className="act-slider-item" style={{ flex: 1 }}>
            <label className="field-label">스트레스 수준 {stressLevel} / 5</label>
            <input type="range" className="act-slider" min={1} max={5} step={1} value={stressLevel} onChange={(e) => setStressLevel(Number(e.target.value))} />
          </div>
        </div>
      </section>
      <div className="goal-edit-actions">
        <button type="button" className="wide-subtle-button" onClick={() => onNavigate?.("/health/vitals")}>취소</button>
        <button type="button" className="green-button" onClick={handleSave} disabled={isSaving}>{isSaving ? "저장 중..." : "저장"}</button>
      </div>
    </div>
  );
}
