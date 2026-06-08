import { useState } from "react";

type ReportStatus = "양호" | "주의" | "우수";
type LoadingState = "LOADING" | "EMPTY" | "LOADED";

interface Report {
  week: string;
  period: string;
  score: number;
  status: ReportStatus;
  reportId: string;
  exerciseDays: number;
  recordCount: number;
}

interface Props {
  onNavigate: (route: any) => void;
}

const DUMMY_REPORTS: Report[] = [
  { week: "2026년 5월 2주차", period: "05.11 - 05.17", score: 78, status: "양호", reportId: "report_2026_w20", exerciseDays: 4, recordCount: 12 },
  { week: "2026년 5월 1주차", period: "05.04 - 05.10", score: 72, status: "주의", reportId: "report_2026_w19", exerciseDays: 4, recordCount: 12 },
  { week: "2026년 4월 5주차", period: "04.27 - 05.03", score: 75, status: "양호", reportId: "report_2026_w18", exerciseDays: 4, recordCount: 12 },
  { week: "2026년 4월 4주차", period: "04.20 - 04.26", score: 68, status: "주의", reportId: "report_2026_w17", exerciseDays: 4, recordCount: 12 },
  { week: "2026년 4월 3주차", period: "04.13 - 04.19", score: 80, status: "우수", reportId: "report_2026_w16", exerciseDays: 4, recordCount: 12 },
  { week: "2026년 4월 2주차", period: "04.06 - 04.12", score: 74, status: "양호", reportId: "report_2026_w15", exerciseDays: 4, recordCount: 12 },
];

function getStatusStyle(status: ReportStatus) {
  if (status === "주의") return { background: "#FFF8E1", border: "1px solid #FFC107", color: "#F59E0B" };
  if (status === "우수") return { background: "#E8F5E9", border: "1px solid #4CAF50", color: "#16A34A" };
  return { background: "#F0F7F2", border: "1px solid #86EFAC", color: "#3D7A4F" };
}

export default function ReportListPage({ onNavigate }: Props) {
  // TODO: API 연결 시 실제 데이터로 교체
  const [loadingState] = useState<LoadingState>("LOADED");
  const reports = DUMMY_REPORTS;

  return (
    <div style={{ padding: "24px" }}>
      <h1 style={{ fontSize: 22, fontWeight: 700, marginBottom: 6, color: "#1a1a1a" }}>주간 리포트</h1>
      <p style={{ fontSize: 13, color: "#888", marginBottom: 20 }}>리포트는 매주 월요일 자동으로 생성됩니다.</p>

      <div style={{ marginBottom: 20 }}>
        <button
          onClick={() => onNavigate("/reports/export")}
          style={{ padding: "8px 16px", border: "1.5px solid #ccc", borderRadius: 6, background: "#fff", fontSize: 13, cursor: "pointer", color: "#333" }}
        >
          내보내기
        </button>
      </div>

      {loadingState === "LOADING" && (
        <div>
          <p style={{ textAlign: "center", color: "#888", marginBottom: 14 }}>주간 리포트를 불러오는 중입니다...</p>
          <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
            {[1, 2, 3].map((n) => (
              <div key={n} style={{ height: 80, background: "#e8f0ec", borderRadius: 8 }} />
            ))}
          </div>
        </div>
      )}

      {loadingState === "EMPTY" && (
        <div style={{ textAlign: "center", padding: "60px 20px", background: "#FAFCFA", borderRadius: 12 }}>
          <div style={{ fontSize: 48, marginBottom: 16 }}>📄</div>
          <p style={{ fontSize: 16, fontWeight: 700, color: "#666", marginBottom: 8 }}>아직 리포트가 없습니다</p>
          <p style={{ fontSize: 13, color: "#999", lineHeight: 1.6, marginBottom: 20 }}>
            첫 번째 주간 리포트는 건강 데이터를<br />7일 이상 입력한 후 생성됩니다.
          </p>
          <button
            onClick={() => onNavigate("/health")}
            style={{ padding: "10px 24px", background: "#3D7A4F", color: "#fff", border: "none", borderRadius: 6, fontSize: 13, cursor: "pointer" }}
          >
            건강 관리로 이동
          </button>
        </div>
      )}

      {loadingState === "LOADED" && (
        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 14 }}>
          {reports.map((report) => (
            <div key={report.reportId} style={{ background: "#fff", border: "1px solid #e5e7eb", borderRadius: 10, padding: 16, boxShadow: "0 1px 4px rgba(0,0,0,0.05)" }}>
              <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 6 }}>
                <span style={{ fontSize: 14, fontWeight: 700, color: "#1a1a1a" }}>{report.week}</span>
                <span style={{ padding: "3px 8px", borderRadius: 12, fontSize: 10, ...getStatusStyle(report.status) }}>{report.status}</span>
              </div>
              <p style={{ fontSize: 11, color: "#888", marginBottom: 12 }}>{report.period}</p>
              <hr style={{ border: "none", borderTop: "1px solid #f0f0f0", marginBottom: 12 }} />
              <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr 1fr", gap: 8, marginBottom: 14 }}>
                {[
                  { label: "건강 점수", value: report.score },
                  { label: "운동 일수", value: report.exerciseDays },
                  { label: "기록 건수", value: report.recordCount },
                ].map((stat) => (
                  <div key={stat.label} style={{ textAlign: "center" }}>
                    <p style={{ fontSize: 10, color: "#888", marginBottom: 4 }}>{stat.label}</p>
                    <p style={{ fontSize: 22, fontWeight: 700, color: "#1a1a1a" }}>{stat.value}</p>
                  </div>
                ))}
              </div>
              <div style={{ display: "flex", gap: 8 }}>
                <button
                  onClick={() => onNavigate("/reports/detail" as any)}
                  style={{ padding: "7px 14px", background: "#3D7A4F", color: "#fff", border: "none", borderRadius: 6, fontSize: 12, cursor: "pointer" }}
                >
                  상세보기
                </button>
                <button style={{ padding: "7px 14px", background: "#fff", color: "#333", border: "1.5px solid #ddd", borderRadius: 6, fontSize: 12, cursor: "pointer" }}>
                  PDF 다운로드
                </button>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
