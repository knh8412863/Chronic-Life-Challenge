import { useEffect, useState } from "react";

import type { AppRoute } from "../../App";
import { deleteActivityLog, getActivityLogs, type DailyActivity } from "../../api/activity";
import { getStoredAccessToken } from "../../api/auth";
import { EXERCISE_TYPE_LABELS, deleteExerciseLog, getExerciseLogs, type ExerciseLog, type ExerciseTypeCode } from "../../api/exercise";
import { deleteKidneyRecord, getKidneyRecords, type KidneyRecord } from "../../api/kidney";
import { deleteLipidRecord, getLipidRecords, type LipidRecord } from "../../api/lipid";
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
import { localDateString } from "../../utils/date";

type Period = "7D" | "30D" | "90D";
type TypeFilter = "ALL" | "BP" | "BG" | "LIPID" | "KIDNEY" | "EXERCISE" | "ACTIVITY";
type HealthRecordRow = {
  id: string;
  recordId: number;
  date: string;
  type: TypeFilter;
  typeLabel: string;
  value: string;
  memo: string;
  vital?: VitalRecord;
  record?: VitalRecord | LipidRecord | KidneyRecord | ExerciseLog | DailyActivity;
  canOpenDetail: boolean;
  canDelete: boolean;
};

function formatDateShort(iso: string) {
  const parts = iso.slice(0, 10).split("-");
  return `${parts[1]}-${parts[2]}`;
}

function isTodayRecord(date: string) {
  return date === localDateString();
}

function measureVal(rec: VitalRecord): string {
  if (isBpType(rec.measure_type)) {
    return `${rec.systolic ?? "—"}/${rec.diastolic ?? "—"}`;
  }
  return rec.glucose_value != null ? `${rec.glucose_value}mg/dL` : "—";
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
  const [deleteTarget, setDeleteTarget] = useState<HealthRecordRow | null>(null);
  const [deleteError, setDeleteError] = useState("");
  const [isDeleting, setIsDeleting] = useState(false);

  function fetchData(_q?: VitalsQuery) {
    const token = getStoredAccessToken();
    if (!token) return;
    setIsLoading(true);
    Promise.allSettled([
      getVitals({ limit: 100 }, token),
      getLipidRecords({ limit: 100 }, token),
      getKidneyRecords({ limit: 100 }, token),
      getExerciseLogs({ limit: 100 }, token),
      getActivityLogs({ limit: 100 }, token),
    ])
      .then(([vitalsRes, lipidRes, kidneyRes, exerciseRes, activityRes]) => {
        const vitalsData = vitalsRes.status === "fulfilled" ? vitalsRes.value.data : null;
        const lipidData = lipidRes.status === "fulfilled" ? lipidRes.value.data : [];
        const kidneyData = kidneyRes.status === "fulfilled" ? kidneyRes.value.data : [];
        const exerciseData = exerciseRes.status === "fulfilled" ? exerciseRes.value.data.items : [];
        const activityData = activityRes.status === "fulfilled" ? activityRes.value.data : [];
        setApiData(vitalsData);
        const rows: HealthRecordRow[] = [
          ...(vitalsData?.items ?? []).map((rec): HealthRecordRow => ({
            id: `vital-${rec.id}`,
            recordId: rec.id,
            date: rec.measured_at.slice(0, 10),
            type: isBpType(rec.measure_type) ? "BP" : "BG",
            typeLabel: MEASURE_TYPE_LABELS[rec.measure_type],
            value: measureVal(rec),
            memo: rec.memo ?? "—",
            vital: rec,
            record: rec,
            canOpenDetail: true,
            canDelete: true,
          })),
          ...lipidData.map((rec): HealthRecordRow => ({
            id: `lipid-${rec.id}`,
            recordId: rec.id,
            date: rec.record_date,
            type: "LIPID",
            typeLabel: "지질 지표",
            value: [
              rec.total_cholesterol != null ? `총 ${rec.total_cholesterol}` : "",
              rec.ldl != null ? `LDL ${rec.ldl}` : "",
              rec.hdl != null ? `HDL ${rec.hdl}` : "",
              rec.triglycerides != null ? `TG ${rec.triglycerides}` : "",
            ].filter(Boolean).join(" / ") || "—",
            memo: rec.memo ?? "—",
            record: rec,
            canOpenDetail: true,
            canDelete: true,
          })),
          ...kidneyData.map((rec): HealthRecordRow => ({
            id: `kidney-${rec.id}`,
            recordId: rec.id,
            date: rec.record_date ?? rec.measured_date,
            type: "KIDNEY",
            typeLabel: "신장 지표",
            value: [
              rec.creatinine != null ? `Cr ${rec.creatinine}` : "",
              rec.bun != null ? `BUN ${rec.bun}` : "",
              rec.egfr != null ? `eGFR ${rec.egfr}` : "",
            ].filter(Boolean).join(" / ") || "—",
            memo: rec.memo ?? "—",
            record: rec,
            canOpenDetail: true,
            canDelete: true,
          })),
          ...exerciseData.map((log): HealthRecordRow => ({
            id: `exercise-${log.id}`,
            recordId: log.id,
            date: log.exercise_date,
            type: "EXERCISE",
            typeLabel: "운동 기록",
            value: `${EXERCISE_TYPE_LABELS[log.exercise_type as ExerciseTypeCode] ?? log.exercise_type} · ${log.duration_minutes}분`,
            memo: log.memo ?? "—",
            record: log,
            canOpenDetail: true,
            canDelete: true,
          })),
          ...activityData.map((log): HealthRecordRow => ({
            id: `activity-${log.id ?? log.activity_log_id ?? log.activity_date}`,
            recordId: log.id ?? log.activity_log_id ?? 0,
            date: log.activity_date,
            type: "ACTIVITY",
            typeLabel: "일일 활동",
            value: [
              log.steps != null ? `${log.steps}보` : "",
              log.sleep_hours != null ? `수면 ${log.sleep_hours}시간` : "",
              log.water_ml != null ? `수분 ${log.water_ml}ml` : "",
            ].filter(Boolean).join(" / ") || "—",
            memo: log.memo ?? "—",
            record: log,
            canOpenDetail: true,
            canDelete: Boolean(log.id ?? log.activity_log_id),
          })),
        ];
        setRecordRows(rows.sort((a, b) => b.date.localeCompare(a.date) || a.typeLabel.localeCompare(b.typeLabel)));
        setHasApiError([vitalsRes, lipidRes, kidneyRes, exerciseRes, activityRes].some((res) => res.status === "rejected"));
      })
      .catch(() => setHasApiError(true))
      .finally(() => setIsLoading(false));
  }

  useEffect(() => {
    fetchData({ period });
  }, [period, typeFilter]);

  async function handleDelete(row: HealthRecordRow) {
    const token = getStoredAccessToken();
    setIsDeleting(true);
    setDeleteError("");
    try {
      if (row.type === "BP" || row.type === "BG") {
        await deleteVital(row.recordId, token ?? undefined);
      } else if (row.type === "LIPID") {
        await deleteLipidRecord(row.recordId, token ?? undefined);
      } else if (row.type === "KIDNEY") {
        await deleteKidneyRecord(row.recordId, token ?? undefined);
      } else if (row.type === "EXERCISE") {
        await deleteExerciseLog(row.recordId, token ?? undefined);
      } else if (row.type === "ACTIVITY") {
        await deleteActivityLog(row.recordId, token ?? undefined);
      }
      setDeleteTarget(null);
      fetchData({ period });
    } catch {
      setDeleteError("삭제에 실패했습니다. 잠시 후 다시 시도해주세요.");
    } finally {
      setIsDeleting(false);
    }
  }

  function handleDetail(rec: VitalRecord) {
    sessionStorage.setItem("selectedVitalId", String(rec.id));
    sessionStorage.setItem("selectedVitalData", JSON.stringify(rec));
    onNavigate?.("/health/vitals/detail");
  }

  function handleEdit(row: HealthRecordRow) {
    sessionStorage.setItem("editingHealthRecordData", JSON.stringify({ type: row.type, record: row.record }));
    if (row.vital) {
      sessionStorage.setItem("editingVitalData", JSON.stringify(row.vital));
    }
    onNavigate?.("/health/vitals/input");
  }

  if (isLoading) return <LoadingState message="건강 기록을 불러오는 중입니다." />;

  // 토큰 없는 환경: 클라이언트 필터 적용
  const displayItems = apiData ? apiData.items : [];
  const displayRows = recordRows.length
    ? recordRows.filter((row) => typeFilter === "ALL" || row.type === typeFilter)
    : [];

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
          title="일부 건강 기록을 불러오지 못했습니다."
          description="연결된 항목만 먼저 표시합니다. 새로고침 후 다시 확인해 주세요."
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
                <th>메모</th>
                <th>수정/삭제</th>
              </tr>
            </thead>
            <tbody>
              {displayRows.length === 0 ? (
                <tr>
                  <td colSpan={5} className="empty-hint" style={{ textAlign: "center", padding: "32px" }}>
                    해당 조건에 기록이 없습니다.
                  </td>
                </tr>
              ) : (
                displayRows.map((row) => {
                  const isToday = isTodayRecord(row.date);
                  const canOpenDetail = row.canOpenDetail && Boolean(row.vital);
                  const canEdit = row.canOpenDetail && isToday;
                  const canDelete = row.canDelete && row.recordId > 0 && isToday;
                  return (
                    <tr
                      key={row.id}
                      className={canOpenDetail ? "vl-row-clickable" : undefined}
                      onClick={() => canOpenDetail && row.vital && handleDetail(row.vital)}
                    >
                      <td>{formatDateShort(row.date)}</td>
                      <td>{row.typeLabel}</td>
                      <td>{row.value}</td>
                      <td className="vl-memo-cell">{row.memo}</td>
                      <td onClick={(e) => e.stopPropagation()}>
                        <div className="vl-action-row">
                          <span
                            className="health-record-action-tooltip"
                            data-tooltip={!isToday ? "당일 기록만 수정할 수 있습니다." : undefined}
                          >
                            <button
                              type="button"
                              className="vl-action-btn"
                              onClick={(e) => { e.stopPropagation(); canEdit && handleEdit(row); }}
                              disabled={!canEdit}
                            >
                              수정
                            </button>
                          </span>
                          <span
                            className="health-record-action-tooltip"
                            data-tooltip={!isToday ? "당일 기록만 삭제할 수 있습니다." : !row.canDelete ? "삭제 가능한 기록 ID가 없습니다." : undefined}
                          >
                            <button
                              type="button"
                              className="vl-action-btn vl-delete-btn"
                              onClick={(e) => { e.stopPropagation(); canDelete && setDeleteTarget(row); }}
                              disabled={!canDelete}
                            >
                              삭제
                            </button>
                          </span>
                        </div>
                      </td>
                    </tr>
                  );
                })
              )}
            </tbody>
          </table>
        </div>
      </section>
      {deleteTarget && (
        <div className="app-modal-backdrop" role="dialog" aria-modal="true">
          <div className="app-modal-card">
            <h2>건강 기록 삭제</h2>
            <p>선택한 {deleteTarget.typeLabel} 기록을 삭제하시겠습니까?</p>
            <p style={{ color: "#888", fontSize: 13 }}>
              삭제한 기록은 복구할 수 없습니다.
            </p>
            {deleteError && <p style={{ color: "#c62828", fontSize: 13 }}>{deleteError}</p>}
            <div style={{ display: "flex", gap: 10, marginTop: 14 }}>
              <button
                type="button"
                className="wide-subtle-button"
                onClick={() => { setDeleteTarget(null); setDeleteError(""); }}
                disabled={isDeleting}
                style={{ flex: 1 }}
              >
                취소
              </button>
              <button
                type="button"
                className="vl-action-btn vl-delete-btn"
                onClick={() => void handleDelete(deleteTarget)}
                disabled={isDeleting}
                style={{ flex: 1, height: 40 }}
              >
                {isDeleting ? "삭제 중..." : "삭제"}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
