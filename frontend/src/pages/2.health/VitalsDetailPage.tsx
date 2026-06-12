import { useEffect, useState } from "react";

import type { AppRoute } from "../../App";
import { getStoredAccessToken } from "../../api/auth";
import {
  MEASURE_TYPE_LABELS,
  deleteVital,
  getVitalDetail,
  isBpType,
  type VitalDetail,
} from "../../api/vitals";
import { LoadingState } from "../../components/common/LoadingState";
import { localDateString } from "../../utils/date";

function formatDateTime(iso: string) {
  const d = new Date(iso);
  const pad = (n: number) => String(n).padStart(2, "0");
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())} ${pad(d.getHours())}:${pad(d.getMinutes())}`;
}

const fallbackDetail: VitalDetail = {
  id: 0,
  measure_type: "BP_MORNING",
  measured_at: `${localDateString()}T00:00:00`,
  systolic: null,
  diastolic: null,
  is_critical: false,
  memo: null,
  created_at: `${localDateString()}T00:00:00`,
  avg_systolic_7d: null,
  avg_diastolic_7d: null,
  avg_glucose_7d: null,
  recent_records: [],
};

type VitalsDetailPageProps = {
  onNavigate?: (route: AppRoute) => void;
};

export function VitalsDetailPage({ onNavigate }: VitalsDetailPageProps) {
  const [detail, setDetail] = useState<VitalDetail>(fallbackDetail);
  const [isLoading, setIsLoading] = useState(false);
  const [showDeleteModal, setShowDeleteModal] = useState(false);
  const [deleteError, setDeleteError] = useState("");
  const [isDeleting, setIsDeleting] = useState(false);

  useEffect(() => {
    const storedData = sessionStorage.getItem("selectedVitalData");
    if (storedData) {
      try {
        setDetail(JSON.parse(storedData) as VitalDetail);
      } catch {
        /* ignore */
      }
    }

    const idStr = sessionStorage.getItem("selectedVitalId");
    const token = getStoredAccessToken();
    if (!idStr || !token) return;

    const id = Number(idStr);
    setIsLoading(true);
    getVitalDetail(id, token)
      .then((res) => setDetail(res.data))
      .catch(() => {})
      .finally(() => setIsLoading(false));
  }, []);

  if (isLoading) return <LoadingState message="기록을 불러오는 중입니다." />;

  const isBp = isBpType(detail.measure_type);
  const canModify = detail.id > 0 && detail.measured_at.slice(0, 10) === localDateString();

  function handleEdit() {
    sessionStorage.setItem("editingVitalData", JSON.stringify(detail));
    onNavigate?.("/health/vitals/input");
  }

  async function handleDelete() {
    if (!canModify) return;
    const token = getStoredAccessToken();
    setIsDeleting(true);
    setDeleteError("");
    try {
      await deleteVital(detail.id, token ?? undefined);
      onNavigate?.("/health/vitals");
    } catch {
      setDeleteError("삭제에 실패했습니다. 잠시 후 다시 시도해주세요.");
    } finally {
      setIsDeleting(false);
    }
  }

  return (
    <div className="vitals-detail-page page-stack">
      <section className="section-header-row page-heading-row">
        <div className="page-heading">
          <p className="eyebrow">건강 관리</p>
          <h1>건강 기록 상세</h1>
        </div>
        <div className="button-row">
          <button
            type="button"
            className="wide-subtle-button"
            onClick={handleEdit}
            disabled={!canModify}
          >
            수정
          </button>
          <button type="button" className="vl-action-btn vl-delete-btn" onClick={() => setShowDeleteModal(true)} disabled={!canModify}>
            삭제
          </button>
        </div>
      </section>

      {/* 수치 요약 카드 */}
      {isBp ? (
        <div className="vd-stat-grid">
          <div className="vd-stat-card vd-stat-green">
            <span className="field-label">수축기</span>
            <strong className="vd-stat-val">{detail.systolic ?? "—"}<small>mmHg</small></strong>
          </div>
          <div className="vd-stat-card vd-stat-yellow">
            <span className="field-label">이완기</span>
            <strong className="vd-stat-val">{detail.diastolic ?? "—"}<small>mmHg</small></strong>
          </div>
          <div className="vd-stat-card vd-stat-blue">
            <span className="field-label">평균 수축기</span>
            <strong className="vd-stat-val">{detail.avg_systolic_7d ?? "—"}<small>mmHg</small></strong>
          </div>
          <div className="vd-stat-card vd-stat-pink">
            <span className="field-label">평균 이완기</span>
            <strong className="vd-stat-val">{detail.avg_diastolic_7d ?? "—"}<small>mmHg</small></strong>
          </div>
        </div>
      ) : (
        <div className="vd-stat-grid">
          <div className="vd-stat-card vd-stat-green">
            <span className="field-label">혈당</span>
            <strong className="vd-stat-val">{detail.glucose_value ?? "—"}<small>mg/dL</small></strong>
          </div>
          <div className="vd-stat-card vd-stat-blue">
            <span className="field-label">평균 혈당 (7일)</span>
            <strong className="vd-stat-val">{detail.avg_glucose_7d ?? "—"}<small>mg/dL</small></strong>
          </div>
        </div>
      )}

      <div className="vd-body-row">
        {/* 기록 정보 */}
        <section className="dashboard-card vd-info-card">
          <h2>기록 정보</h2>

          <div className="vd-info-row">
            <span className="field-label">기록 유형</span>
            <p className="vd-info-val">{MEASURE_TYPE_LABELS[detail.measure_type]}</p>
          </div>

          <div className="vd-info-row">
            <span className="field-label">측정일시</span>
            <p className="vd-info-val">{formatDateTime(detail.measured_at)}</p>
          </div>

          <div className="vd-info-row">
            <span className="field-label">측정값</span>
            <div>
              {isBp ? (
                <>
                  <p className="vd-measure-label">수축기 혈압</p>
                  <p className="vd-measure-big">{detail.systolic ?? "—"} mmHg</p>
                  <p className="vd-measure-label" style={{ marginTop: "12px" }}>이완기 혈압</p>
                  <p className="vd-measure-big">{detail.diastolic ?? "—"} mmHg</p>
                </>
              ) : (
                <p className="vd-measure-big">{detail.glucose_value ?? "—"} mg/dL</p>
              )}
            </div>
          </div>

          <div className="vd-info-row">
            <span className="field-label">상태</span>
            <div>
              <span className={`vl-status-badge ${detail.is_critical ? "vl-status-danger" : "vl-status-normal"} vd-status-large`}>
                {detail.is_critical ? "위험" : "정상"}
              </span>
            </div>
          </div>

          {detail.memo && (
            <div className="vd-info-row">
              <span className="field-label">메모</span>
              <p className="vd-memo">{detail.memo}</p>
            </div>
          )}
        </section>

        {/* 추이 분석 */}
        <section className="dashboard-card vd-trend-card">
          <h2>추이 분석 (선택)</h2>
          <div className="vd-chart-placeholder">
            <span>최근 7일 혈압 추이</span>
          </div>
          {isBp && (
            <div className="vd-avg-list">
              <p>평균 수축기: {detail.avg_systolic_7d ?? "—"} mmHg</p>
              <p>평균 이완기: {detail.avg_diastolic_7d ?? "—"} mmHg</p>
            </div>
          )}
        </section>
      </div>

      {showDeleteModal && (
        <div className="app-modal-backdrop" role="dialog" aria-modal="true">
          <div className="app-modal-card">
            <h2>건강 기록 삭제</h2>
            <p>선택한 혈압/혈당 기록을 삭제하시겠습니까?</p>
            <p style={{ color: "#888", fontSize: 13 }}>
              삭제한 기록은 복구할 수 없습니다.
            </p>
            {deleteError && <p style={{ color: "#c62828", fontSize: 13 }}>{deleteError}</p>}
            <div style={{ display: "flex", gap: 10, marginTop: 14 }}>
              <button
                type="button"
                className="wide-subtle-button"
                onClick={() => { setShowDeleteModal(false); setDeleteError(""); }}
                disabled={isDeleting}
                style={{ flex: 1 }}
              >
                취소
              </button>
              <button
                type="button"
                className="vl-action-btn vl-delete-btn"
                onClick={() => void handleDelete()}
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
