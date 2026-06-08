import { useEffect, useState } from "react";

import type { AppRoute } from "../../App";
import { getStoredAccessToken } from "../../api/auth";
import {
  getWeeklyReport,
  getWeeklyReports,
  type ReportItemStatus,
  type WeeklyReport,
  type WeeklyReportMetricSummary,
  type WeeklyReportSummaryCard,
} from "../../api/reports";
import { ErrorState } from "../../components/common/ErrorState";
import { LoadingState } from "../../components/common/LoadingState";

interface Props {
  onNavigate: (route: AppRoute) => void;
}

function selectedReportStorageKey() {
  return "selectedWeeklyReportId";
}

function getStatusStyle(status: ReportItemStatus) {
  if (status === "HIGH") return { background: "#FFF1F2", border: "1px solid #FDA4AF", color: "#E11D48" };
  if (status === "CAUTION") return { background: "#FFF8E1", border: "1px solid #FFC107", color: "#F59E0B" };
  if (status === "NORMAL") return { background: "#F0F7F2", border: "1px solid #86EFAC", color: "#3D7A4F" };
  return { background: "#F3F4F6", border: "1px solid #D1D5DB", color: "#6B7280" };
}

function getStatusText(status: ReportItemStatus) {
  if (status === "HIGH") return "주의";
  if (status === "CAUTION") return "관찰";
  if (status === "NORMAL") return "양호";
  return "부족";
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

function cardValue(card: WeeklyReportSummaryCard) {
  return card.value || "확인 필요";
}

function metricValue(metric: WeeklyReportMetricSummary) {
  return `${metric.value}${metric.unit ?? ""}`;
}

export default function ReportDetailPage({ onNavigate }: Props) {
  const [report, setReport] = useState<WeeklyReport | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [hasApiError, setHasApiError] = useState(false);

  useEffect(() => {
    const token = getStoredAccessToken();
    const savedId = Number(sessionStorage.getItem(selectedReportStorageKey()));

    async function loadReport() {
      setIsLoading(true);
      try {
        if (savedId) {
          const response = await getWeeklyReport(savedId, token);
          setReport(response.data);
        } else {
          const listResponse = await getWeeklyReports(1, token);
          const firstReport = listResponse.data[0];
          if (!firstReport) {
            setReport(null);
          } else {
            const response = await getWeeklyReport(firstReport.report_id, token);
            setReport(response.data);
            sessionStorage.setItem(selectedReportStorageKey(), String(firstReport.report_id));
          }
        }
        setHasApiError(false);
      } catch {
        setHasApiError(true);
      } finally {
        setIsLoading(false);
      }
    }

    loadReport();
  }, []);

  if (isLoading) return <LoadingState message="주간 리포트 상세를 불러오는 중입니다." />;

  if (hasApiError) {
    return (
      <div style={{ padding: 24 }}>
        <ErrorState title="리포트 상세를 불러오지 못했습니다." description="리포트가 삭제되었거나 서버 연결에 실패했습니다." />
        <button
          type="button"
          onClick={() => onNavigate("/reports")}
          style={{ marginTop: 16, padding: "9px 16px", background: "#3D7A4F", color: "#fff", border: "none", borderRadius: 6, fontSize: 13, cursor: "pointer" }}
        >
          목록으로 돌아가기
        </button>
      </div>
    );
  }

  if (!report) {
    return (
      <div style={{ padding: 24, textAlign: "center" }}>
        <p style={{ fontSize: 15, fontWeight: 700, color: "#555", marginBottom: 8 }}>조회할 리포트가 없습니다.</p>
        <p style={{ fontSize: 13, color: "#888", marginBottom: 16 }}>리포트를 먼저 생성해 주세요.</p>
        <button
          type="button"
          onClick={() => onNavigate("/reports")}
          style={{ padding: "9px 16px", background: "#3D7A4F", color: "#fff", border: "none", borderRadius: 6, fontSize: 13, cursor: "pointer" }}
        >
          목록으로 돌아가기
        </button>
      </div>
    );
  }

  const overallStatus = report.summary_cards.some((card) => card.status === "HIGH")
    ? "HIGH"
    : report.summary_cards.some((card) => card.status === "CAUTION")
      ? "CAUTION"
      : report.summary_cards.some((card) => card.status === "NORMAL")
        ? "NORMAL"
        : "UNAVAILABLE";

  return (
    <div style={{ padding: "24px" }}>
      <div style={{ display: "flex", alignItems: "center", gap: 10, marginBottom: 20 }}>
        <button onClick={() => onNavigate("/reports")} style={{ background: "none", border: "none", fontSize: 18, cursor: "pointer", color: "#555" }}>←</button>
        <h1 style={{ fontSize: 20, fontWeight: 700, color: "#1a1a1a", margin: 0 }}>주간 리포트 상세</h1>
      </div>

      <div style={{ display: "flex", alignItems: "center", gap: 10, marginBottom: 20 }}>
        <span style={{ fontSize: 15, fontWeight: 700 }}>
          {getWeekTitle(report.week_start_date)} ({formatPeriod(report.week_start_date, report.week_end_date)})
        </span>
        <span style={{ padding: "3px 8px", borderRadius: 12, fontSize: 10, ...getStatusStyle(overallStatus) }}>
          {getStatusText(overallStatus)}
        </span>
        <span style={{ padding: "3px 8px", background: "#F3F4F6", borderRadius: 12, fontSize: 10, color: "#555" }}>
          {report.source_type === "LLM" ? "AI 생성" : "규칙 기반"}
        </span>
        <div style={{ marginLeft: "auto", display: "flex", gap: 8 }}>
          <button
            type="button"
            onClick={() => onNavigate("/reports/export")}
            style={{ padding: "6px 14px", border: "1.5px solid #ddd", borderRadius: 6, background: "#fff", fontSize: 12, cursor: "pointer" }}
          >
            내보내기
          </button>
        </div>
      </div>

      <div style={{ background: "#fff", border: "1px solid #e5e7eb", borderRadius: 10, padding: 20, marginBottom: 18 }}>
        <h2 style={{ fontSize: 14, fontWeight: 700, marginBottom: 14 }}>요약 카드</h2>
        <div style={{ display: "grid", gridTemplateColumns: "repeat(5, 1fr)", gap: 12 }}>
          {report.summary_cards.map((card) => (
            <div key={card.label} style={{ padding: "12px 10px", borderRadius: 8, textAlign: "center", ...getStatusStyle(card.status) }}>
              <p style={{ fontSize: 10, marginBottom: 6 }}>{card.label}</p>
              <p style={{ fontSize: 20, fontWeight: 700 }}>{cardValue(card)}</p>
              <p style={{ marginTop: 6, fontSize: 10, lineHeight: 1.4 }}>{card.description}</p>
            </div>
          ))}
        </div>
      </div>

      <div style={{ background: "#F5F7FA", border: "1px solid #e5e7eb", borderRadius: 10, padding: 20, marginBottom: 18 }}>
        <h2 style={{ fontSize: 14, fontWeight: 700, marginBottom: 14 }}>지표별 요약</h2>
        <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
          {report.metric_summaries.map((metric) => (
            <div key={metric.metric}>
              <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 6 }}>
                <span style={{ fontSize: 12, color: "#333" }}>{metric.label}</span>
                <span style={{ fontSize: 12, fontWeight: 700, color: "#333" }}>{metricValue(metric)}</span>
              </div>
              <div style={{ height: 8, background: "#dde8e2", borderRadius: 4 }}>
                <div
                  style={{
                    width: metric.status === "UNAVAILABLE" ? "8%" : "100%",
                    height: "100%",
                    background: metric.status === "UNAVAILABLE" ? "#CBD5E1" : "#3D7A4F",
                    borderRadius: 4,
                  }}
                />
              </div>
              <p style={{ marginTop: 4, fontSize: 11, color: "#888" }}>{metric.description}</p>
            </div>
          ))}
        </div>
      </div>

      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 14, marginBottom: 18 }}>
        <div style={{ background: "#fff", border: "1px solid #e5e7eb", borderRadius: 10, padding: 16 }}>
          <h2 style={{ fontSize: 13, fontWeight: 700, marginBottom: 10 }}>전주 대비 추이</h2>
          <p style={{ fontSize: 13, color: "#555", lineHeight: 1.7 }}>{report.trend_summary.message}</p>
        </div>
        <div style={{ background: "#fff", border: "1px solid #e5e7eb", borderRadius: 10, padding: 16 }}>
          <h2 style={{ fontSize: 13, fontWeight: 700, marginBottom: 10 }}>챌린지 달성</h2>
          <p style={{ fontSize: 13, color: "#555", lineHeight: 1.7 }}>{report.challenge_summary.message}</p>
          <p style={{ fontSize: 22, fontWeight: 700, color: "#3D7A4F", marginTop: 8 }}>
            {report.challenge_summary.completion_rate}%
          </p>
        </div>
      </div>

      <div style={{ background: "#fff", border: "1px solid #e5e7eb", borderRadius: 10, padding: 20, marginBottom: 18 }}>
        <h2 style={{ fontSize: 14, fontWeight: 700, marginBottom: 12 }}>리포트 조언</h2>
        <div style={{ background: "#F9F9F9", border: "1px solid #e8f0ec", borderRadius: 6, padding: 16, fontSize: 13, color: "#333", lineHeight: 1.7, whiteSpace: "pre-line" }}>
          {report.report_text}
        </div>
      </div>

      <div style={{ background: "#fff", border: "1px solid #e5e7eb", borderRadius: 10, padding: 20 }}>
        <h2 style={{ fontSize: 14, fontWeight: 700, marginBottom: 14 }}>데이터 출처 요약</h2>
        <div style={{ display: "grid", gridTemplateColumns: "repeat(5, 1fr)", gap: 10 }}>
          {[
            ["건강 설문", report.source_summary.health_survey_count],
            ["혈압·혈당", report.source_summary.vital_record_count],
            ["식단", report.source_summary.meal_log_count],
            ["운동", report.source_summary.exercise_log_count],
            ["챌린지", report.source_summary.challenge_checkin_count],
          ].map(([label, value]) => (
            <div key={label} style={{ textAlign: "center", padding: 12, background: "#FAFCFA", border: "1px solid #e8f0ec", borderRadius: 8 }}>
              <p style={{ fontSize: 11, color: "#888", marginBottom: 6 }}>{label}</p>
              <p style={{ fontSize: 20, fontWeight: 700, color: "#1a1a1a" }}>{value}</p>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
