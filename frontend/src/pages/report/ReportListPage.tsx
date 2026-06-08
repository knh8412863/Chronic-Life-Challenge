import { useEffect, useState } from "react";

import type { AppRoute } from "../../App";
import { getStoredAccessToken } from "../../api/auth";
import {
  generateWeeklyReport,
  getCurrentWeeklyReport,
  getWeeklyReports,
  type CurrentWeeklyReport,
  type ReportItemStatus,
  type WeeklyReportListItem,
} from "../../api/reports";
import { ErrorState } from "../../components/common/ErrorState";
import { LoadingState } from "../../components/common/LoadingState";

interface Props {
  onNavigate: (route: AppRoute) => void;
}

function formatDate(date: string) {
  const [, month, day] = date.split("-");
  return `${month}.${day}`;
}

function formatPeriod(start: string, end: string) {
  return `${formatDate(start)} - ${formatDate(end)}`;
}

function getWeekTitle(start: string) {
  const d = new Date(`${start}T00:00:00`);
  const weekOfMonth = Math.ceil(d.getDate() / 7);
  return `${d.getFullYear()}년 ${d.getMonth() + 1}월 ${weekOfMonth}주차`;
}

function getStatusText(status: ReportItemStatus) {
  if (status === "HIGH") return "주의";
  if (status === "CAUTION") return "관찰";
  if (status === "NORMAL") return "양호";
  return "부족";
}

function getStatusStyle(status: ReportItemStatus) {
  if (status === "HIGH") return { background: "#FFF1F2", border: "1px solid #FDA4AF", color: "#E11D48" };
  if (status === "CAUTION") return { background: "#FFF8E1", border: "1px solid #FFC107", color: "#F59E0B" };
  if (status === "NORMAL") return { background: "#F0F7F2", border: "1px solid #86EFAC", color: "#3D7A4F" };
  return { background: "#F3F4F6", border: "1px solid #D1D5DB", color: "#6B7280" };
}

function selectedReportStorageKey() {
  return "selectedWeeklyReportId";
}

export default function ReportListPage({ onNavigate }: Props) {
  const [current, setCurrent] = useState<CurrentWeeklyReport | null>(null);
  const [reports, setReports] = useState<WeeklyReportListItem[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isGenerating, setIsGenerating] = useState(false);
  const [hasApiError, setHasApiError] = useState(false);

  function loadReports() {
    const token = getStoredAccessToken();
    setIsLoading(true);
    Promise.all([getCurrentWeeklyReport(token), getWeeklyReports(20, token)])
      .then(([currentRes, listRes]) => {
        setCurrent(currentRes.data);
        setReports(listRes.data);
        setHasApiError(false);
      })
      .catch(() => setHasApiError(true))
      .finally(() => setIsLoading(false));
  }

  useEffect(() => {
    loadReports();
  }, []);

  async function handleGenerate() {
    const token = getStoredAccessToken();
    setIsGenerating(true);
    try {
      const response = await generateWeeklyReport(false, token);
      sessionStorage.setItem(selectedReportStorageKey(), String(response.data.report_id));
      onNavigate("/reports/detail");
    } catch {
      alert("리포트 생성에 실패했습니다. 잠시 후 다시 시도해 주세요.");
    } finally {
      setIsGenerating(false);
    }
  }

  function handleDetail(reportId: number) {
    sessionStorage.setItem(selectedReportStorageKey(), String(reportId));
    onNavigate("/reports/detail");
  }

  if (isLoading) return <LoadingState message="주간 리포트를 불러오는 중입니다." />;

  return (
    <div style={{ padding: "24px" }}>
      <h1 style={{ fontSize: 22, fontWeight: 700, marginBottom: 6, color: "#1a1a1a" }}>주간 리포트</h1>
      <p style={{ fontSize: 13, color: "#888", marginBottom: 20 }}>
        최근 7일간의 건강 기록, 예측 결과, 챌린지 실천 내역을 요약합니다.
      </p>

      {hasApiError && (
        <div style={{ marginBottom: 16 }}>
          <ErrorState title="리포트 데이터를 불러오지 못했습니다." description="로그인 상태와 서버 연결을 확인해 주세요." />
        </div>
      )}

      {current?.status === "GENERATABLE" && (
        <div style={{ background: "#F0F7F2", border: "1px solid #B7DEC2", borderRadius: 10, padding: 18, marginBottom: 20 }}>
          <p style={{ fontSize: 14, fontWeight: 700, color: "#2E5F3E", marginBottom: 6 }}>이번 주 리포트를 생성할 수 있습니다.</p>
          <p style={{ fontSize: 13, color: "#4B6B55", marginBottom: 14 }}>
            {current.empty_message ?? "이번 주 건강 데이터로 리포트를 생성할 수 있습니다."}
          </p>
          <button
            type="button"
            onClick={handleGenerate}
            disabled={isGenerating}
            style={{ padding: "9px 18px", background: "#3D7A4F", color: "#fff", border: "none", borderRadius: 6, fontSize: 13, cursor: "pointer" }}
          >
            {isGenerating ? "생성 중..." : "리포트 생성"}
          </button>
        </div>
      )}

      {current?.status === "EMPTY" && reports.length === 0 && (
        <div style={{ textAlign: "center", padding: "60px 20px", background: "#FAFCFA", borderRadius: 12 }}>
          <div style={{ fontSize: 48, marginBottom: 16 }}>📄</div>
          <p style={{ fontSize: 16, fontWeight: 700, color: "#666", marginBottom: 8 }}>아직 리포트가 없습니다.</p>
          <p style={{ fontSize: 13, color: "#999", lineHeight: 1.6, marginBottom: 20 }}>
            {current.empty_message ?? "건강 기록을 입력하면 주간 리포트를 생성할 수 있습니다."}
          </p>
          <button
            type="button"
            onClick={() => onNavigate("/health")}
            style={{ padding: "10px 24px", background: "#3D7A4F", color: "#fff", border: "none", borderRadius: 6, fontSize: 13, cursor: "pointer" }}
          >
            건강 관리로 이동
          </button>
        </div>
      )}

      {reports.length > 0 && (
        <>
          <div style={{ marginBottom: 20 }}>
            <button
              type="button"
              onClick={() => onNavigate("/reports/export")}
              style={{ padding: "8px 16px", border: "1.5px solid #ccc", borderRadius: 6, background: "#fff", fontSize: 13, cursor: "pointer", color: "#333" }}
            >
              내보내기
            </button>
          </div>

          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 14 }}>
            {reports.map((report) => (
              <div key={report.report_id} style={{ background: "#fff", border: "1px solid #e5e7eb", borderRadius: 10, padding: 16, boxShadow: "0 1px 4px rgba(0,0,0,0.05)" }}>
                <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 6 }}>
                  <span style={{ fontSize: 14, fontWeight: 700, color: "#1a1a1a" }}>{getWeekTitle(report.week_start_date)}</span>
                  <span style={{ padding: "3px 8px", borderRadius: 12, fontSize: 10, ...getStatusStyle(report.overall_status) }}>
                    {getStatusText(report.overall_status)}
                  </span>
                </div>
                <p style={{ fontSize: 11, color: "#888", marginBottom: 12 }}>{formatPeriod(report.week_start_date, report.week_end_date)}</p>
                <hr style={{ border: "none", borderTop: "1px solid #f0f0f0", marginBottom: 12 }} />
                <p style={{ minHeight: 40, fontSize: 12, color: "#555", lineHeight: 1.6, marginBottom: 14 }}>{report.summary_text}</p>
                <div style={{ display: "flex", gap: 8 }}>
                  <button
                    type="button"
                    onClick={() => handleDetail(report.report_id)}
                    style={{ padding: "7px 14px", background: "#3D7A4F", color: "#fff", border: "none", borderRadius: 6, fontSize: 12, cursor: "pointer" }}
                  >
                    상세보기
                  </button>
                  <button
                    type="button"
                    onClick={() => onNavigate("/reports/export")}
                    style={{ padding: "7px 14px", background: "#fff", color: "#777", border: "1.5px solid #ddd", borderRadius: 6, fontSize: 12, cursor: "pointer" }}
                  >
                    내보내기
                  </button>
                </div>
              </div>
            ))}
          </div>
        </>
      )}
    </div>
  );
}
