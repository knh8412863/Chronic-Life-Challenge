import { useState } from "react";

import type { AppRoute } from "../../App";
import { getStoredAccessToken } from "../../api/auth";
import { createKidneyRecord, type CreateKidneyBody } from "../../api/kidney";
import { createLipidRecord, type CreateLipidBody } from "../../api/lipid";
import { createVital, isBpType, type CreateVitalBody, type MeasureType } from "../../api/vitals";

type Tab = "bp" | "lipid" | "kidney";
type BpCategory = "BP" | "BG";
type BpTime = "MORNING" | "LUNCH" | "EVENING";

function todayStr() {
  return new Date().toISOString().slice(0, 10);
}
function nowTimeStr() {
  const d = new Date();
  return `${String(d.getHours()).padStart(2, "0")}:${String(d.getMinutes()).padStart(2, "0")}`;
}

type VitalsInputPageProps = {
  onNavigate?: (route: AppRoute) => void;
};

export function VitalsInputPage({ onNavigate }: VitalsInputPageProps) {
  const [tab, setTab] = useState<Tab>("bp");

  return (
    <div className="vitals-input-page page-stack">
      <section className="section-header-row page-heading-row">
        <div className="page-heading">
          <p className="eyebrow">건강 관리</p>
          <h1>{tab === "bp" ? "혈압/혈당 입력" : tab === "lipid" ? "지질 지표 입력" : "신장 지표 입력"}</h1>
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
      </div>

      {tab === "bp" && <BpForm onNavigate={onNavigate} />}
      {tab === "lipid" && <LipidForm onNavigate={onNavigate} />}
      {tab === "kidney" && <KidneyForm onNavigate={onNavigate} />}
    </div>
  );
}

/* ── 혈압/혈당 폼 ─────────────────────────────────── */
function BpForm({ onNavigate }: { onNavigate?: (r: AppRoute) => void }) {
  const [category, setCategory] = useState<BpCategory>("BP");
  const [bpTime, setBpTime] = useState<BpTime>("MORNING");
  const [systolic, setSystolic] = useState("");
  const [diastolic, setDiastolic] = useState("");
  const [glucose, setGlucose] = useState("");
  const [glucoseTime, setGlucoseTime] = useState<"FASTING" | "POSTPRANDIAL">("FASTING");
  const [date, setDate] = useState(todayStr());
  const [time, setTime] = useState(nowTimeStr());
  const [memo, setMemo] = useState("");
  const [isSaving, setIsSaving] = useState(false);

  const isBpWarning = category === "BP" && Number(systolic) >= 140;

  function getMeasureType(): MeasureType {
    if (category === "BP") {
      return `BP_${bpTime}` as MeasureType;
    }
    return glucoseTime === "FASTING" ? "GLUCOSE_FASTING" : "GLUCOSE_POSTPRANDIAL";
  }

  async function handleSave() {
    const token = getStoredAccessToken();
    const measuredAt = `${date}T${time}:00`;
    const mt = getMeasureType();
    const body: CreateVitalBody = { measure_type: mt, measured_at: measuredAt };

    if (isBpType(mt)) {
      if (!systolic || !diastolic) { alert("수축기 및 이완기 혈압을 입력해 주세요."); return; }
      body.systolic = Number(systolic);
      body.diastolic = Number(diastolic);
    } else {
      if (!glucose) { alert("혈당 값을 입력해 주세요."); return; }
      body.glucose = Number(glucose);
    }
    if (memo.trim()) body.memo = memo.trim();

    setIsSaving(true);
    try {
      await createVital(body, token ?? undefined);
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
        <span className="goal-section-note">오늘 2/3회 입력 완료</span>
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
            <span className="vi-type-code">BP</span>
            <span>혈압</span>
          </button>
          <button
            type="button"
            className={`vi-type-btn ${category === "BG" ? "vi-type-btn--active" : ""}`}
            onClick={() => setCategory("BG")}
          >
            <span className="vi-type-code">BG</span>
            <span>혈당</span>
          </button>
        </div>
      </section>

      {/* 측정 시간 (혈압: 아침/점심/저녁, 혈당: 공복/식후) */}
      <section className="dashboard-card vi-section">
        <h2>측정 시간</h2>
        {category === "BP" ? (
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
            <p className="goal-section-note" style={{ gridColumn: "1/-1", marginTop: "4px" }}>
              * measure_type: BP_MORNING / BP_LUNCH / BP_EVENING
            </p>
          </div>
        ) : (
          <div className="vi-time-grid">
            <button
              type="button"
              className={`vi-time-btn ${glucoseTime === "FASTING" ? "vi-time-btn--active" : ""}`}
              onClick={() => setGlucoseTime("FASTING")}
            >
              공복
            </button>
            <button
              type="button"
              className={`vi-time-btn ${glucoseTime === "POSTPRANDIAL" ? "vi-time-btn--active" : ""}`}
              onClick={() => setGlucoseTime("POSTPRANDIAL")}
            >
              식후
            </button>
          </div>
        )}
      </section>

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
                min={60}
                max={250}
                onChange={(e) => setSystolic(e.target.value)}
              />
            </div>
            <span className="vi-bp-sep">/</span>
            <div className="vi-bp-input-wrap">
              <input
                type="number"
                className="vi-bp-input vi-bp-diastolic"
                placeholder="이완기"
                value={diastolic}
                min={40}
                max={150}
                onChange={(e) => setDiastolic(e.target.value)}
              />
            </div>
            <span className="vi-bp-unit">mmHg</span>
          </div>
        ) : (
          <div className="vi-glucose-row">
            <input
              type="number"
              className="vi-bp-input"
              placeholder="예: 98"
              value={glucose}
              min={40}
              max={600}
              onChange={(e) => setGlucose(e.target.value)}
            />
            <span className="vi-bp-unit">mg/dL</span>
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
          <div className="vi-field">
            <span className="field-label">시간</span>
            <input
              type="time"
              className="vi-date-input"
              value={time}
              onChange={(e) => setTime(e.target.value)}
            />
          </div>
        </div>
        <p className="goal-section-note">* API: measured_at (datetime 단일 필드)</p>
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
function LipidForm({ onNavigate }: { onNavigate?: (r: AppRoute) => void }) {
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
            <input type="number" className="vi-lipid-input vi-lipid-neutral" placeholder="예: 200" value={totalCholesterol} onChange={(e) => setTotalCholesterol(e.target.value)} />
          </div>
          <div className="vi-lipid-field">
            <label className="field-label">LDL 콜레스테롤 (mg/dL)</label>
            <input type="number" className="vi-lipid-input vi-lipid-pink" placeholder="예: 100" value={ldl} onChange={(e) => setLdl(e.target.value)} />
          </div>
          <div className="vi-lipid-field">
            <label className="field-label">HDL 콜레스테롤 (mg/dL)</label>
            <input type="number" className="vi-lipid-input vi-lipid-green" placeholder="예: 50" value={hdl} onChange={(e) => setHdl(e.target.value)} />
          </div>
          <div className="vi-lipid-field">
            <label className="field-label">중성지방 (mg/dL)</label>
            <input type="number" className="vi-lipid-input vi-lipid-yellow" placeholder="예: 150" value={triglycerides} onChange={(e) => setTriglycerides(e.target.value)} />
          </div>
          <div className="vi-lipid-field">
            <label className="field-label">허리둘레 (cm)</label>
            <input type="number" className="vi-lipid-input vi-lipid-neutral" placeholder="예: 80" value={waist} onChange={(e) => setWaist(e.target.value)} />
          </div>
        </div>
      </section>

      <section className="dashboard-card vi-section">
        <h2>측정 정보</h2>
        <div className="vi-field" style={{ marginBottom: "16px" }}>
          <span className="field-label">측정 날짜</span>
          <input type="date" className="vi-date-input" value={date} max={todayStr()} onChange={(e) => setDate(e.target.value)} />
          <p className="goal-section-note">* API body: record_date (date 타입), 시간 필드 없음</p>
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
function KidneyForm({ onNavigate }: { onNavigate?: (r: AppRoute) => void }) {
  const [creatinine, setCreatinine] = useState("");
  const [bun, setBun] = useState("");
  const [egfr, setEgfr] = useState("");
  const [proteinuria, setProteinuria] = useState<boolean>(true);
  const [date, setDate] = useState(todayStr());
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
    if (memo.trim()) body.memo = memo.trim();

    setIsSaving(true);
    try {
      await createKidneyRecord(body, token ?? undefined);
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
              className="vi-kidney-input"
              placeholder="예: 1.0"
              value={creatinine}
              onChange={(e) => setCreatinine(e.target.value)}
            />
          </div>
          <div className="vi-field" style={{ marginBottom: "16px" }}>
            <label className="field-label">BUN (mg/dL)</label>
            <input
              type="number"
              step="0.1"
              className="vi-kidney-input"
              placeholder="예: 15"
              value={bun}
              onChange={(e) => setBun(e.target.value)}
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
              className="vi-kidney-input"
              placeholder="직접 입력"
              value={egfr}
              onChange={(e) => setEgfr(e.target.value)}
              style={{ marginTop: "8px" }}
            />
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
            * ERD: urine_protein_pos (boolean) — 참/모두 달력 입력
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
        <div className="vi-field">
          <span className="field-label">메모 / 측정 기관 (선택)</span>
          <textarea className="vi-memo-input" placeholder="예: OO병원에서 측정" value={memo} onChange={(e) => setMemo(e.target.value)} />
          <p className="goal-section-note">* API body: memo 필드로 측정 기관 정보 포함 가능</p>
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
