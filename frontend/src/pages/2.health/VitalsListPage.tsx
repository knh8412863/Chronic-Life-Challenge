import { useEffect, useState } from "react";

import type { AppRoute } from "../../App";
import { getStoredAccessToken } from "../../api/auth";
import { getActivityLogs } from "../../api/activity";
import { EXERCISE_TYPE_LABELS, getExerciseLogs, type ExerciseTypeCode } from "../../api/exercise";
import { getKidneyRecords } from "../../api/kidney";
import { getLipidRecords } from "../../api/lipid";
import {
  MEASURE_TYPE_LABELS,
  deleteVital,
  getVitals,
  isBpType,
  type VitalRecord,
  type VitalsListData,
  type VitalsQuery,
} from "../../api/vitals";
import { ErrorState } from "../../components/common/ErrorState";
import { LoadingState } from "../../components/common/LoadingState";

const FALLBACK_ALL_ITEMS: VitalRecord[] = [
  {
    id: 1,
    measure_type: "BP_MORNING",
    measured_at: "2026-05-13T09:30:00",
    systolic: 145,
    diastolic: 92,
    is_critical: true,
    memo: "아침 식후",
    created_at: "2026-05-13T09:30:00",
  },
  {
    id: 2,
    measure_type: "GLUCOSE_FASTING",
    measured_at: "2026-05-12T07:00:00",
    glucose_value: 98,
    is_critical: false,
    memo: null,
    created_at: "2026-05-12T07:00:00",
  },
  {
    id: 3,
    measure_type: "BP_EVENING",
    measured_at: "2026-05-11T21:00:00",
    systolic: 130,
    diastolic: 85,
    is_critical: false,
    memo: "스트레스",
    created_at: "2026-05-11T21:00:00",
  },
  {
    id: 4,
    measure_type: "GLUCOSE_POSTPRANDIAL",
    measured_at: "2026-05-09T13:00:00",
    glucose_value: 105,
    is_critical: false,
    memo: "식후 2시간",
    created_at: "2026-05-09T13:00:00",
  },
];

type Period = "7D" | "30D" | "90D";
type TypeFilter = "ALL" | "BP" | "BG" | "LIPID" | "KIDNEY" | "EXERCISE" | "ACTIVITY";
type HealthRecordRow = {
  id: string;
  date: string;
  type: TypeFilter;
  typeLabel: string;
  value: string;
  status: "정상" | "위험" | "기록";
  memo: string;
  vital?: VitalRecord;
};

function formatDateShort(iso: string) {
  const parts = iso.slice(0, 10).split("-");
  return `${parts[1]}-${parts[2]}`;
}

function measureVal(rec: VitalRecord): string {
  if (isBpType(rec.measure_type)) {
    return `${rec.systolic ?? "—"}/${rec.diastolic ?? "—"}`;
  }
  return rec.glucose_value != null ? `${rec.glucose_value}mg/dL` : "—";
}

function filterByType(items: VitalRecord[], t: TypeFilter): VitalRecord[] {
  if (t === "ALL") return items;
  if (t === "BP") return items.filter((r) => isBpType(r.measure_type));
  if (t === "BG") return items.filter((r) => !isBpType(r.measure_type));
  return [];
}

function calcSummary(items: VitalRecord[]) {
  const bpItems = items.filter((r) => isBpType(r.measure_type) && r.systolic != null);
  const bgItems = items.filter((r) => !isBpType(r.measure_type) && r.glucose_value != null);
  const avg = (arr: number[]) => arr.length ? Math.round(arr.reduce((a, b) => a + b, 0) / arr.length) : null;
  return {
    avg_systolic: avg(bpItems.map((r) => r.systolic!)),
    avg_diastolic: avg(bpItems.map((r) => r.diastolic!)),
    avg_glucose: avg(bgItems.map((r) => r.glucose_value!)),
    critical_count: items.filter((r) => r.is_critical).length,
  };
}

type VitalsListPageProps = {
  onNavigate?: (route: AppRoute) => void;
};

export function VitalsListPage({ onNavigate }: VitalsListPageProps) {
  const [apiData, setApiData] = useState<VitalsListData | null>(null);
  const [recordRows, setRecordRows] = useState<HealthRecordRow[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [hasApiError, setHasApiError] = useState(false);
  const [period, setPeriod] = useState<Period>("30D");
  const [typeFilter, setTypeFilter] = useState<TypeFilter>("ALL");

  function fetchData(_q?: VitalsQuery) {
    const token = getStoredAccessToken();
    if (!token) return;
    setIsLoading(true);
    Promise.all([
      getVitals({ limit: 100 }, token),
      getLipidRecords({ limit: 100 }, token),
      getKidneyRecords({ limit: 100 }, token),
      getExerciseLogs({ limit: 100 }, token),
      getActivityLogs({ limit: 100 }, token),
    ])
      .then(([vitalsRes, lipidRes, kidneyRes, exerciseRes, activityRes]) => {
        setApiData(vitalsRes.data);
        const rows: HealthRecordRow[] = [
          ...vitalsRes.data.items.map((rec): HealthRecordRow => ({
            id: `vital-${rec.id}`,
            date: rec.measured_at.slice(0, 10),
            type: isBpType(rec.measure_type) ? "BP" : "BG",
            typeLabel: MEASURE_TYPE_LABELS[rec.measure_type],
            value: measureVal(rec),
            status: rec.is_critical ? "위험" : "정상",
            memo: rec.memo ?? "—",
            vital: rec,
          })),
          ...lipidRes.data.map((rec): HealthRecordRow => ({
            id: `lipid-${rec.id}`,
            date: rec.record_date,
            type: "LIPID",
            typeLabel: "지질 지표",
            value: [
              rec.total_cholesterol != null ? `총 ${rec.total_cholesterol}` : "",
              rec.ldl != null ? `LDL ${rec.ldl}` : "",
              rec.hdl != null ? `HDL ${rec.hdl}` : "",
              rec.triglycerides != null ? `TG ${rec.triglycerides}` : "",
            ].filter(Boolean).join(" / ") || "—",
            status: "기록",
            memo: rec.memo ?? "—",
          })),
          ...kidneyRes.data.map((rec): HealthRecordRow => ({
            id: `kidney-${rec.id}`,
            date: rec.record_date ?? rec.measured_date,
            type: "KIDNEY",
            typeLabel: "신장 지표",
            value: [
              rec.creatinine != null ? `Cr ${rec.creatinine}` : "",
              rec.bun != null ? `BUN ${rec.bun}` : "",
              rec.egfr != null ? `eGFR ${rec.egfr}` : "",
            ].filter(Boolean).join(" / ") || "—",
            status: "기록",
            memo: rec.memo ?? "—",
          })),
          ...exerciseRes.data.items.map((log): HealthRecordRow => ({
            id: `exercise-${log.id}`,
            date: log.exercise_date,
            type: "EXERCISE",
            typeLabel: "운동 기록",
            value: `${EXERCISE_TYPE_LABELS[log.exercise_type as ExerciseTypeCode] ?? log.exercise_type} · ${log.duration_minutes}분`,
            status: "기록",
            memo: log.memo ?? "—",
          })),
          ...activityRes.data.map((log): HealthRecordRow => ({
            id: `activity-${log.id ?? log.activity_log_id ?? log.activity_date}`,
            date: log.activity_date,
            type: "ACTIVITY",
            typeLabel: "일일 활동",
            value: [
              log.steps != null ? `${log.steps}보` : "",
              log.sleep_hours != null ? `수면 ${log.sleep_hours}시간` : "",
              log.water_ml != null ? `수분 ${log.water_ml}ml` : "",
            ].filter(Boolean).join(" / ") || "—",
            status: "기록",
            memo: log.memo ?? "—",
          })),
        ];
        setRecordRows(rows.sort((a, b) => b.date.localeCompare(a.date)));
        setHasApiError(false);
      })
      .catch(() => setHasApiError(true))
      .finally(() => setIsLoading(false));
  }

  useEffect(() => {
    fetchData({ period });
  }, [period, typeFilter]);

  async function handleDelete(id: number) {
    if (!window.confirm("이 기록을 삭제하시겠습니까?")) return;
    const token = getStoredAccessToken();
    try {
      await deleteVital(id, token ?? undefined);
      fetchData({ period });
    } catch {
      alert("삭제에 실패했습니다.");
    }
  }

  function handleDetail(rec: VitalRecord) {
    sessionStorage.setItem("selectedVitalId", String(rec.id));
    sessionStorage.setItem("selectedVitalData", JSON.stringify(rec));
    onNavigate?.("/health/vitals/detail");
  }

  if (isLoading) return <LoadingState message="건강 기록을 불러오는 중입니다." />;

  // 토큰 없는 환경: 클라이언트 필터 적용
  const displayItems = apiData
    ? apiData.items
    : filterByType(FALLBACK_ALL_ITEMS, typeFilter);
  const displayRows = recordRows.length
    ? recordRows.filter((row) => typeFilter === "ALL" || row.type === typeFilter)
    : filterByType(FALLBACK_ALL_ITEMS, typeFilter).map((rec): HealthRecordRow => ({
      id: `fallback-${rec.id}`,
      date: rec.measured_at.slice(0, 10),
      type: isBpType(rec.measure_type) ? "BP" : "BG",
      typeLabel: MEASURE_TYPE_LABELS[rec.measure_type],
      value: measureVal(rec),
      status: rec.is_critical ? "위험" : "정상",
      memo: rec.memo ?? "—",
      vital: rec,
    }));

  const summary = apiData ? apiData.summary : calcSummary(displayItems);

  return (
    <div className="vitals-list-page page-stack">
      <section className="section-header-row page-heading-row">
        <div className="page-heading">
          <p className="eyebrow">건강 관리</p>
          <h1>건강 기록 목록</h1>
        </div>
        <div className="button-row">
          <button
            type="button"
            className="green-button"
            onClick={() => onNavigate?.("/health/vitals/input")}
          >
            + 기록 추가
          </button>
        </div>
      </section>

      {hasApiError && (
        <ErrorState
          title="데이터를 불러오지 못했습니다."
          description="현재 화면은 예시 데이터로 표시됩니다."
        />
      )}

      {/* 기간 + 유형 필터 */}
      <div className="vl-filter-row">
        <div className="period-tabs">
          {(["7D", "30D", "90D"] as Period[]).map((p) => (
            <button
              key={p}
              type="button"
              className={`period-tab ${period === p ? "period-tab--active" : ""}`}
              onClick={() => setPeriod(p)}
            >
              {p === "7D" ? "7일" : p === "30D" ? "30일" : "90일"}
            </button>
          ))}
        </div>
        <select className="vi-date-input" value={typeFilter} onChange={(e) => setTypeFilter(e.target.value as TypeFilter)}>
          <option value="ALL">전체</option>
          <option value="BP">혈압</option>
          <option value="BG">혈당</option>
          <option value="LIPID">지질 지표</option>
          <option value="KIDNEY">신장 지표</option>
          <option value="EXERCISE">운동 기록</option>
          <option value="ACTIVITY">일일 활동</option>
        </select>
      </div>

      {/* 요약 카드 */}
      <div className="vl-summary-grid">
        <div className="vl-summary-card">
          <span className="field-label">평균 혈압</span>
          <strong className="vl-summary-val">
            {summary.avg_systolic ?? "—"}/{summary.avg_diastolic ?? "—"}
            <small> mmHg</small>
          </strong>
        </div>
        <div className="vl-summary-card">
          <span className="field-label">평균 혈당</span>
          <strong className="vl-summary-val">
            {summary.avg_glucose ?? "—"}
            <small> mg/dL</small>
          </strong>
        </div>
        <div className="vl-summary-card">
          <span className="field-label">위험 횟수</span>
          <strong className="vl-summary-val">
            {summary.critical_count}
            <small> 회</small>
          </strong>
        </div>
      </div>
      {!apiData && (
        <p className="goal-section-note" style={{ margin: "0 0 4px" }}>
          * 예시 데이터 (로그인 후 실제 데이터 표시)
        </p>
      )}

      {/* 기록 목록 테이블 */}
      <section className="dashboard-card">
        <h2 style={{ padding: "20px 20px 0", margin: 0, fontSize: "15px", fontWeight: 700 }}>
          기록 목록 ({displayRows.length}건)
        </h2>
        <div className="table-card" style={{ border: "none", borderRadius: 0 }}>
          <table>
            <thead>
              <tr>
                <th>날짜</th>
                <th>유형</th>
                <th>측정값</th>
                <th>상태</th>
                <th>메모</th>
                <th>수정/삭제</th>
              </tr>
            </thead>
            <tbody>
              {displayRows.length === 0 ? (
                <tr>
                  <td colSpan={6} className="empty-hint" style={{ textAlign: "center", padding: "32px" }}>
                    해당 조건에 기록이 없습니다.
                  </td>
                </tr>
              ) : (
                displayRows.map((row) => (
                  <tr
                    key={row.id}
                    className={row.vital ? "vl-row-clickable" : undefined}
                    onClick={() => row.vital && handleDetail(row.vital)}
                  >
                    <td>{formatDateShort(row.date)}</td>
                    <td>{row.typeLabel}</td>
                    <td>{row.value}</td>
                    <td>
                      <span className={`vl-status-badge ${row.status === "위험" ? "vl-status-danger" : "vl-status-normal"}`}>
                        {row.status}
                      </span>
                    </td>
                    <td className="vl-memo-cell">{row.memo}</td>
                    <td onClick={(e) => e.stopPropagation()}>
                      <div className="vl-action-row">
                        <button
                          type="button"
                          className="vl-action-btn"
                          onClick={(e) => { e.stopPropagation(); row.vital && handleDetail(row.vital); }}
                          disabled={!row.vital}
                        >
                          수정
                        </button>
                        <button
                          type="button"
                          className="vl-action-btn vl-delete-btn"
                          onClick={(e) => { e.stopPropagation(); row.vital && handleDelete(row.vital.id); }}
                          disabled={!row.vital}
                        >
                          삭제
                        </button>
                      </div>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
        <p className="goal-section-note" style={{ padding: "8px 20px 16px" }}>
          과거 기록은 수정·삭제가 불가합니다. (당일 기록만 허용)
        </p>
      </section>
    </div>
  );
}
