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
  if (status === "HIGH") return { background: "#FFF1F2", border: "0.5px solid #FDA4AF", color: "#E11D48" };
  if (status === "CAUTION") return { background: "#FFF8E1", border: "0.5px solid #FFC107", color: "#F59E0B" };
  if (status === "NORMAL") return { background: "#F0F7F2", border: "0.5px solid #86EFAC", color: "#3D7A4F" };
  return { background: "#F3F4F6", border: "0.5px solid #D1D5DB", color: "#6B7280" };
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

// 걸음 수 카드 전용 블루 스타일 (label 기준으로 JSX에서만 분기)
const STEPS_CARD_STYLE = { background: "#E6F1FB", border: "0.5px solid #85B7EB", color: "#185FA5" };

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
          style={{ marginTop: 16, padding: "9px 16px", background: "#3D7A4F", color: "#fff", border: "none", borderRadius: 8, fontSize: 13, cursor: "pointer" }}
        >
          목록으로 돌아가기
        </button>
      </div>
    );
  }

  if (!report) {
    return (
      <div style={{ padding: 24, textAlign: "center" }}>
        <p style={{ fontSize: 15, fontWeight: 500, color: "#555", marginBottom: 8 }}>조회할 리포트가 없습니다.</p>
        <p style={{ fontSize: 13, color: "#888", marginBottom: 16 }}>리포트를 먼저 생성해 주세요.</p>
        <button
          type="button"
          onClick={() => onNavigate("/reports")}
          style={{ padding: "9px 16px", background: "#3D7A4F", color: "#fff", border: "none", borderRadius: 8, fontSize: 13, cursor: "pointer" }}
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
    <div style={{ padding: "28px 24px" }}>
      {/* 뒤로가기 */}
      <button
        onClick={() => onNavigate("/reports")}
        style={{ background: "none", border: "none", cursor: "pointer", display: "flex", alignItems: "center", gap: 6, color: "#888", fontSize: 13, marginBottom: 20, padding: 0 }}
      >
        ← 리포트 목록으로
      </button>

      {/* 페이지 제목 */}
      <h1 style={{ fontSize: 20, fontWeight: 500, color: "#1a1a1a", margin: 0, marginBottom: 16 }}>주간 리포트 상세</h1>

      {/* 주차 + 상태 뱃지 */}
      <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 24, flexWrap: "wrap" }}>
        <span style={{ fontSize: 15, fontWeight: 500, color: "#1a1a1a" }}>
          {getWeekTitle(report.week_start_date)} ({formatPeriod(report.week_start_date, report.week_end_date)})
        </span>
        <span style={{ padding: "3px 10px", borderRadius: 12, fontSize: 11, fontWeight: 500, ...getStatusStyle(overallStatus) }}>
          {getStatusText(overallStatus)}
        </span>
        <span style={{ padding: "3px 10px", background: "#F3F4F6", borderRadius: 12, fontSize: 11, fontWeight: 500, color: "#6B7280", border: "0.5px solid #D1D5DB" }}>
          {report.source_type === "LLM" ? "AI 생성" : "규칙 기반"}
        </span>
      </div>

      {/* 1. 리포트 조언 */}
      <div style={{ background: "#F2F8F4", border: "0.5px solid #c6e0cc", borderRadius: 12, padding: 20, marginBottom: 14 }}>
        <p style={{ fontSize: 11, fontWeight: 500, color: "#aaa", letterSpacing: "0.07em", textTransform: "uppercase", marginBottom: 12 }}>리포트 조언</p>
        <div style={{ fontSize: 14, color: "#333", lineHeight: 1.9, whiteSpace: "pre-line" }}>
          {report.report_text}
        </div>
      </div>

      {/* 2. 요약 카드 */}
      <div style={{ background: "#fff", border: "0.5px solid #e5e7eb", borderRadius: 12, padding: 20, marginBottom: 14 }}>
        <p style={{ fontSize: 11, fontWeight: 500, color: "#aaa", letterSpacing: "0.07em", textTransform: "uppercase", marginBottom: 14 }}>요약 카드</p>
        <div style={{ display: "grid", gridTemplateColumns: "repeat(5, 1fr)", gap: 10 }}>
          {report.summary_cards.map((card) => (
            <div
              key={card.label}
              style={{
                padding: "12px 8px",
                borderRadius: 10,
                textAlign: "center",
                ...(card.label === "걸음 수" ? STEPS_CARD_STYLE : getStatusStyle(card.status)),
              }}
            >
              <p style={{ fontSize: 10, marginBottom: 6, opacity: 0.75 }}>{card.label}</p>
              <p style={{ fontSize: 18, fontWeight: 500 }}>{cardValue(card)}</p>
              <p style={{ marginTop: 4, fontSize: 10, lineHeight: 1.4, opacity: 0.75 }}>{card.description}</p>
            </div>
          ))}
        </div>
      </div>

      {/* 3. 지표별 요약 */}
      <div style={{ background: "#f9fafb", border: "0.5px solid #e5e7eb", borderRadius: 12, padding: 20, marginBottom: 14 }}>
        <p style={{ fontSize: 11, fontWeight: 500, color: "#aaa", letterSpacing: "0.07em", textTransform: "uppercase", marginBottom: 14 }}>지표별 요약</p>
        <div style={{ display: "flex", flexDirection: "column", gap: 14 }}>
          {report.metric_summaries.map((metric) => (
            <div key={metric.metric}>
              <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 6 }}>
                <span style={{ fontSize: 13, color: "#333" }}>{metric.label}</span>
                <span style={{ fontSize: 13, fontWeight: 500, color: "#333" }}>{metricValue(metric)}</span>
              </div>
              <div style={{ height: 6, background: "#e5e7eb", borderRadius: 4 }}>
                <div
                  style={{
                    width: metric.status === "UNAVAILABLE" ? "8%" : "100%",
                    height: "100%",
                    background: metric.status === "UNAVAILABLE" ? "#CBD5E1" : "#3D7A4F",
                    borderRadius: 4,
                  }}
                />
              </div>
              <p style={{ marginTop: 4, fontSize: 11, color: "#aaa" }}>{metric.description}</p>
            </div>
          ))}
        </div>
      </div>

      {/* 4. 전주 대비 + 챌린지 달성 */}
      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 14, marginBottom: 14 }}>
        <div style={{ background: "#fff", border: "0.5px solid #e5e7eb", borderRadius: 12, padding: 16 }}>
          <p style={{ fontSize: 11, fontWeight: 500, color: "#aaa", letterSpacing: "0.07em", textTransform: "uppercase", marginBottom: 10 }}>전주 대비 추이</p>
          <p style={{ fontSize: 13, color: "#555", lineHeight: 1.7 }}>{report.trend_summary.message}</p>
        </div>
        <div style={{ background: "#fff", border: "0.5px solid #e5e7eb", borderRadius: 12, padding: 16 }}>
          <p style={{ fontSize: 11, fontWeight: 500, color: "#aaa", letterSpacing: "0.07em", textTransform: "uppercase", marginBottom: 10 }}>챌린지 달성</p>
          <p style={{ fontSize: 13, color: "#555", lineHeight: 1.7 }}>{report.challenge_summary.message}</p>
          <p style={{ fontSize: 28, fontWeight: 500, color: "#3D7A4F", marginTop: 10 }}>
            {report.challenge_summary.completion_rate}%
          </p>
        </div>
      </div>

      {/* 5. 데이터 출처 요약 */}
      <div style={{ background: "#fff", border: "0.5px solid #e5e7eb", borderRadius: 12, padding: 20 }}>
        <p style={{ fontSize: 11, fontWeight: 500, color: "#aaa", letterSpacing: "0.07em", textTransform: "uppercase", marginBottom: 14 }}>데이터 출처 요약</p>
        <div style={{ display: "grid", gridTemplateColumns: "repeat(5, 1fr)", gap: 10 }}>
          {[
            ["건강 설문", report.source_summary.health_survey_count],
            ["혈압·혈당", report.source_summary.vital_record_count],
            ["식단", report.source_summary.meal_log_count],
            ["운동", report.source_summary.exercise_log_count],
            ["챌린지", report.source_summary.challenge_checkin_count],
          ].map(([label, value]) => (
            <div key={label} style={{ textAlign: "center", padding: 12, background: "#f9fafb", border: "0.5px solid #e5e7eb", borderRadius: 8 }}>
              <p style={{ fontSize: 11, color: "#888", marginBottom: 6 }}>{label}</p>
              <p style={{ fontSize: 20, fontWeight: 500, color: "#1a1a1a" }}>{value}</p>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}