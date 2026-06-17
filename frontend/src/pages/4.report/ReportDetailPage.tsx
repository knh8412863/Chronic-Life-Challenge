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

type Tone = {
  bg: string;
  border: string;
  color: string;
  label: string;
};

const statusTones: Record<ReportItemStatus, Tone> = {
  HIGH: { bg: "#FBEDEB", border: "#F4B8B1", color: "#E0584C", label: "위험" },
  CAUTION: { bg: "#FBF2E6", border: "#E9C891", color: "#DD8A2E", label: "주의" },
  NORMAL: { bg: "#E7F3EF", border: "#A7D3C4", color: "#0E7A5F", label: "정상" },
  UNAVAILABLE: { bg: "#F1F4F3", border: "#DDE3E0", color: "#737D85", label: "데이터 부족" },
};

function selectedReportStorageKey() {
  return "selectedWeeklyReportId";
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

function getTone(status: ReportItemStatus) {
  return statusTones[status] ?? statusTones.UNAVAILABLE;
}

function getOverallStatus(report: WeeklyReport): ReportItemStatus {
  if (report.summary_cards.some((card) => card.status === "HIGH")) return "HIGH";
  if (report.summary_cards.some((card) => card.status === "CAUTION")) return "CAUTION";
  if (report.summary_cards.some((card) => card.status === "NORMAL")) return "NORMAL";
  return "UNAVAILABLE";
}

function totalHealthRecords(report: WeeklyReport) {
  const source = report.source_summary;
  return (
    source.health_survey_count +
    source.lipid_obesity_record_count +
    source.renal_record_count +
    source.vital_record_count +
    source.activity_log_count +
    source.exercise_log_count +
    source.meal_log_count
  );
}

function buildScore(report: WeeklyReport) {
  const source = report.source_summary;
  return Math.min(
    100,
    45 +
      Math.min(totalHealthRecords(report), 5) * 6 +
      Math.min(source.exercise_log_count, 5) * 3 +
      Math.min(source.meal_log_count, 5) * 2 +
      Math.min(source.activity_log_count, 5) * 2 +
      Math.min(source.challenge_checkin_count, 7) * 2,
  );
}

function scoreGrade(score: number) {
  if (score >= 75) return "양호";
  if (score >= 55) return "주의";
  return "관리 필요";
}

function metricPercent(metric: WeeklyReportMetricSummary) {
  const numeric = Number(String(metric.value ?? "").replace(/[^0-9.]/g, ""));
  if (!Number.isFinite(numeric) || numeric <= 0) return 8;
  return Math.min(100, numeric * 20);
}

const pageStyle = {
  padding: "28px 24px 40px",
  background: "linear-gradient(180deg, #F6FAF8 0%, #FFFFFF 240px)",
  color: "#14181B",
} as const;

const sectionStyle = {
  background: "#fff",
  border: "1px solid #ECEEF0",
  borderRadius: 18,
  padding: 22,
  boxShadow: "0 10px 28px rgba(20, 24, 27, 0.05)",
  marginBottom: 16,
} as const;

const sectionTitleStyle = {
  fontSize: 16,
  fontWeight: 700,
  color: "#14181B",
  margin: 0,
  marginBottom: 16,
} as const;

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
          style={{ marginTop: 16, padding: "9px 16px", background: "#0E7A5F", color: "#fff", border: "none", borderRadius: 8, fontSize: 13, cursor: "pointer" }}
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
          style={{ padding: "9px 16px", background: "#0E7A5F", color: "#fff", border: "none", borderRadius: 8, fontSize: 13, cursor: "pointer" }}
        >
          목록으로 돌아가기
        </button>
      </div>
    );
  }

  const overallStatus = getOverallStatus(report);
  const overallTone = getTone(overallStatus);
  const score = buildScore(report);
  const source = report.source_summary;
  const challengeRate = report.challenge_summary.completion_rate;

  return (
    <div style={pageStyle}>
      <button
        onClick={() => onNavigate("/reports")}
        style={{ background: "none", border: "none", cursor: "pointer", display: "flex", alignItems: "center", gap: 6, color: "#737D85", fontSize: 13, marginBottom: 20, padding: 0 }}
      >
        ← 리포트 목록으로
      </button>

      <header
        style={{
          background: "linear-gradient(135deg, #0E7A5F 0%, #0A5A46 100%)",
          borderRadius: 24,
          padding: "28px 30px",
          color: "#fff",
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          marginBottom: 18,
          boxShadow: "0 18px 40px rgba(14, 122, 95, 0.22)",
        }}
      >
        <div>
          <p style={{ margin: 0, fontSize: 13, opacity: 0.82, letterSpacing: "0.08em", textTransform: "uppercase" }}>All4Health</p>
          <h1 style={{ margin: "8px 0 10px", fontSize: 28, fontWeight: 800 }}>주간 건강 리포트</h1>
          <p style={{ margin: 0, fontSize: 14, opacity: 0.9 }}>
            {getWeekTitle(report.week_start_date)} · {formatPeriod(report.week_start_date, report.week_end_date)}
          </p>
        </div>
        <div
          style={{
            width: 118,
            height: 118,
            borderRadius: "50%",
            background: "rgba(255,255,255,0.16)",
            border: "8px solid rgba(255,255,255,0.34)",
            display: "flex",
            flexDirection: "column",
            alignItems: "center",
            justifyContent: "center",
          }}
        >
          <strong style={{ fontSize: 38, lineHeight: 1 }}>{score}</strong>
          <span style={{ fontSize: 12, opacity: 0.84 }}>/ 100점</span>
          <span style={{ marginTop: 6, padding: "3px 10px", borderRadius: 999, background: "rgba(255,255,255,0.18)", fontSize: 11 }}>{scoreGrade(score)}</span>
        </div>
      </header>

      <section style={sectionStyle}>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", gap: 16, marginBottom: 16 }}>
          <h2 style={{ ...sectionTitleStyle, marginBottom: 0 }}>이번 주 요약</h2>
          <span style={{ padding: "6px 12px", borderRadius: 999, fontSize: 12, fontWeight: 700, background: overallTone.bg, border: `1px solid ${overallTone.border}`, color: overallTone.color }}>
            {overallTone.label}
          </span>
        </div>
        <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(150px, 1fr))", gap: 12 }}>
          {report.summary_cards.map((card) => {
            const tone = card.label === "걸음 수" ? { bg: "#EAF2FB", border: "#A7C7EA", color: "#185FA5" } : getTone(card.status);
            return (
              <article key={card.label} style={{ padding: 16, borderRadius: 16, background: tone.bg, border: `1px solid ${tone.border}` }}>
                <p style={{ margin: 0, marginBottom: 8, color: tone.color, fontSize: 12, fontWeight: 700 }}>{card.label}</p>
                <p style={{ margin: 0, color: "#14181B", fontSize: 24, fontWeight: 800 }}>{cardValue(card)}</p>
                <p style={{ margin: "8px 0 0", color: "#737D85", fontSize: 12, lineHeight: 1.45 }}>{card.description}</p>
              </article>
            );
          })}
        </div>
      </section>

      <section style={{ ...sectionStyle, background: "#F7FBF9" }}>
        <h2 style={sectionTitleStyle}>건강 분석 요약</h2>
        <p style={{ margin: 0, fontSize: 14, color: "#3F474D", lineHeight: 1.9, whiteSpace: "pre-line" }}>{report.report_text}</p>
      </section>

      <section style={sectionStyle}>
        <h2 style={sectionTitleStyle}>관리 영역별 성과</h2>
        <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(230px, 1fr))", gap: 14 }}>
          {report.metric_summaries.map((metric) => {
            const tone = getTone(metric.status);
            const percent = metric.status === "UNAVAILABLE" ? 8 : metricPercent(metric);
            return (
              <article key={metric.metric} style={{ padding: 16, borderRadius: 16, background: "#F7F9F8", border: "1px solid #ECEEF0" }}>
                <div style={{ display: "flex", justifyContent: "space-between", gap: 12, marginBottom: 10 }}>
                  <span style={{ fontSize: 13, fontWeight: 700, color: "#14181B" }}>{metric.label}</span>
                  <strong style={{ fontSize: 13, color: tone.color }}>{metricValue(metric)}</strong>
                </div>
                <div style={{ height: 8, borderRadius: 999, background: "#E6ECE9", overflow: "hidden", marginBottom: 8 }}>
                  <div style={{ width: `${percent}%`, height: "100%", borderRadius: 999, background: tone.color }} />
                </div>
                <p style={{ margin: 0, fontSize: 12, lineHeight: 1.5, color: "#737D85" }}>{metric.description}</p>
              </article>
            );
          })}
        </div>
      </section>

      <section style={{ display: "grid", gridTemplateColumns: "minmax(0, 1fr) minmax(0, 1fr)", gap: 16, marginBottom: 16 }}>
        <div style={sectionStyle}>
          <h2 style={sectionTitleStyle}>전주 대비 추이</h2>
          <p style={{ margin: 0, fontSize: 14, color: "#3F474D", lineHeight: 1.75 }}>{report.trend_summary.message}</p>
        </div>
        <div style={sectionStyle}>
          <h2 style={sectionTitleStyle}>목표 달성률</h2>
          <div style={{ display: "flex", alignItems: "center", gap: 18 }}>
            <div style={{ width: 96, height: 96, borderRadius: "50%", background: `conic-gradient(#0E7A5F ${Math.min(100, challengeRate)}%, #E6ECE9 0)`, display: "grid", placeItems: "center" }}>
              <div style={{ width: 72, height: 72, borderRadius: "50%", background: "#fff", display: "grid", placeItems: "center" }}>
                <strong style={{ color: "#0E7A5F", fontSize: 21 }}>{challengeRate}%</strong>
              </div>
            </div>
            <div>
              <p style={{ margin: 0, fontSize: 14, color: "#3F474D", lineHeight: 1.7 }}>{report.challenge_summary.message}</p>
              <p style={{ margin: "8px 0 0", fontSize: 12, color: "#737D85" }}>챌린지 체크인 {report.challenge_summary.checkin_count}회</p>
            </div>
          </div>
        </div>
      </section>

      <section style={sectionStyle}>
        <h2 style={sectionTitleStyle}>상세 분석</h2>
        <div style={{ overflowX: "auto", border: "1px solid #ECEEF0", borderRadius: 14 }}>
          <table style={{ width: "100%", borderCollapse: "collapse", fontSize: 13 }}>
            <thead>
              <tr style={{ background: "#F1F4F3", color: "#737D85" }}>
                <th style={{ padding: "12px 14px", textAlign: "left" }}>영역</th>
                <th style={{ padding: "12px 14px", textAlign: "left" }}>기록</th>
                <th style={{ padding: "12px 14px", textAlign: "left" }}>상태</th>
                <th style={{ padding: "12px 14px", textAlign: "left" }}>설명</th>
              </tr>
            </thead>
            <tbody>
              {report.metric_summaries.map((metric) => {
                const tone = getTone(metric.status);
                return (
                  <tr key={metric.metric} style={{ borderTop: "1px solid #ECEEF0" }}>
                    <td style={{ padding: "13px 14px", color: "#14181B", fontWeight: 700 }}>{metric.label}</td>
                    <td style={{ padding: "13px 14px", color: "#3F474D" }}>{metricValue(metric)}</td>
                    <td style={{ padding: "13px 14px" }}>
                      <span style={{ padding: "4px 10px", borderRadius: 999, background: tone.bg, color: tone.color, fontSize: 12, fontWeight: 700 }}>{tone.label}</span>
                    </td>
                    <td style={{ padding: "13px 14px", color: "#737D85" }}>{metric.description}</td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </section>

      <section style={{ ...sectionStyle, background: "#F7F9F8" }}>
        <h2 style={sectionTitleStyle}>데이터 출처 요약</h2>
        <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(120px, 1fr))", gap: 10 }}>
          {[
            ["건강 설문", source.health_survey_count],
            ["혈압·혈당", source.vital_record_count],
            ["지질·비만", source.lipid_obesity_record_count],
            ["신장", source.renal_record_count],
            ["식단", source.meal_log_count],
            ["운동", source.exercise_log_count],
            ["생활습관", source.activity_log_count],
            ["챌린지", source.challenge_checkin_count],
          ].map(([label, value]) => (
            <div key={label} style={{ textAlign: "center", padding: 14, background: "#fff", border: "1px solid #ECEEF0", borderRadius: 14 }}>
              <p style={{ fontSize: 12, color: "#737D85", margin: 0, marginBottom: 6 }}>{label}</p>
              <p style={{ fontSize: 22, fontWeight: 800, color: "#14181B", margin: 0 }}>{value}</p>
            </div>
          ))}
        </div>
      </section>
    </div>
  );
}
