interface Props {
  onNavigate: (route: any) => void;
}

const CATEGORY_SCORES = [
  { label: "혈압 관리", pct: 85 },
  { label: "혈당 관리", pct: 72 },
  { label: "운동 실천", pct: 75 },
  { label: "식단 관리", pct: 68 },
  { label: "수면 관리", pct: 88 },
];

export default function ReportDetailPage({ onNavigate }: Props) {
  // TODO: API 연결 시 실제 데이터 fetch
  const report = {
    week: "2026년 5월 2주차",
    period: "05.11 - 05.17",
    status: "양호",
    weeklyAvg: 78,
    prevDiff: "+6",
    monthlyAvg: 75,
    goalRate: 82,
    aiSummary: `이번 주는 혈압 관리가 우수했습니다.\n특히 정기적인 혈압 측정과 염분 섭취 관리가 눈에 띕니다.\n\n다만 운동 시간이 목표보다 2시간 부족하였으므로,\n주 4회 이상 30분 유산소 운동을 권장합니다.`,
    cautions: ["혈압이 약간 높은 편입니다", "염분 섭취를 줄여보세요"],
    praises: ["규칙적인 운동 습관", "충분한 수면 시간"],
    exerciseDays: 4,
    dietDays: 6,
    challengeMissions: 18,
  };

  const summaryCards = [
    { label: "주간 평균", value: `${report.weeklyAvg}점`, bg: "#F0F7F2", border: "#86EFAC", color: "#3D7A4F" },
    { label: "전주 대비", value: `${report.prevDiff}점`, bg: "#FFF8E1", border: "#FFC107", color: "#F59E0B" },
    { label: "월간 평균", value: `${report.monthlyAvg}점`, bg: "#EFF6FF", border: "#93C5FD", color: "#3B82F6" },
    { label: "목표 달성률", value: `${report.goalRate}%`, bg: "#FFF1F2", border: "#FDA4AF", color: "#F43F5E" },
  ];

  return (
    <div style={{ padding: "24px" }}>
      <div style={{ display: "flex", alignItems: "center", gap: 10, marginBottom: 20 }}>
        <button onClick={() => onNavigate("/reports")} style={{ background: "none", border: "none", fontSize: 18, cursor: "pointer", color: "#555" }}>←</button>
        <h1 style={{ fontSize: 20, fontWeight: 700, color: "#1a1a1a", margin: 0 }}>주간 리포트 상세</h1>
      </div>

      <div style={{ display: "flex", alignItems: "center", gap: 10, marginBottom: 20 }}>
        <span style={{ fontSize: 15, fontWeight: 700 }}>{report.week} ({report.period})</span>
        <span style={{ padding: "3px 8px", background: "#F0F7F2", border: "1px solid #86EFAC", borderRadius: 12, fontSize: 10, color: "#3D7A4F" }}>{report.status}</span>
        <div style={{ marginLeft: "auto", display: "flex", gap: 8 }}>
          <button style={{ padding: "6px 14px", border: "1.5px solid #ddd", borderRadius: 6, background: "#fff", fontSize: 12, cursor: "pointer" }}>PDF 다운로드</button>
          <button style={{ padding: "6px 14px", border: "1.5px solid #ddd", borderRadius: 6, background: "#fff", fontSize: 12, cursor: "pointer" }}>공유</button>
        </div>
      </div>

      {/* 종합 건강 점수 */}
      <div style={{ background: "#fff", border: "1px solid #e5e7eb", borderRadius: 10, padding: 20, marginBottom: 18 }}>
        <h2 style={{ fontSize: 14, fontWeight: 700, marginBottom: 14 }}>종합 건강 점수</h2>
        <div style={{ display: "grid", gridTemplateColumns: "repeat(4, 1fr)", gap: 12 }}>
          {summaryCards.map((card) => (
            <div key={card.label} style={{ padding: "12px 10px", background: card.bg, border: `1.5px solid ${card.border}`, borderRadius: 8, textAlign: "center" }}>
              <p style={{ fontSize: 10, color: card.color, marginBottom: 6 }}>{card.label}</p>
              <p style={{ fontSize: 20, fontWeight: 700, color: card.color }}>{card.value}</p>
            </div>
          ))}
        </div>
      </div>

      {/* 카테고리별 점수 */}
      <div style={{ background: "#F5F7FA", border: "1px solid #e5e7eb", borderRadius: 10, padding: 20, marginBottom: 18 }}>
        <h2 style={{ fontSize: 14, fontWeight: 700, marginBottom: 14 }}>카테고리별 점수</h2>
        <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
          {CATEGORY_SCORES.map((item) => (
            <div key={item.label}>
              <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 6 }}>
                <span style={{ fontSize: 12, color: "#333" }}>{item.label}</span>
                <span style={{ fontSize: 12, fontWeight: 700, color: "#333" }}>{item.pct}%</span>
              </div>
              <div style={{ height: 8, background: "#dde8e2", borderRadius: 4 }}>
                <div style={{ width: `${item.pct}%`, height: "100%", background: "#3D7A4F", borderRadius: 4 }} />
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* 차트 영역 */}
      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 14, marginBottom: 18 }}>
        {[
          { title: "혈압 추이", unit: "단위: mmHg (수축기/이완기)\n목표: 120/80 이하" },
          { title: "혈당 추이", unit: "단위: mg/dL\n목표: 공복혈당 100 이하" },
        ].map((chart) => (
          <div key={chart.title} style={{ background: "#fff", border: "1px solid #e5e7eb", borderRadius: 10, padding: 16 }}>
            <h2 style={{ fontSize: 13, fontWeight: 700, marginBottom: 10 }}>{chart.title}</h2>
            {/* TODO: recharts 등 차트 라이브러리 연결 */}
            <div style={{ height: 180, background: "#f9fafb", border: "1.5px dashed #d1d5db", borderRadius: 6, display: "flex", alignItems: "center", justifyContent: "center", color: "#aaa", fontSize: 12 }}>
              차트 영역
            </div>
            <p style={{ fontSize: 11, color: "#888", marginTop: 10, whiteSpace: "pre-line" }}>{chart.unit}</p>
          </div>
        ))}
      </div>

      {/* 세부 항목 */}
      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 14, marginBottom: 18 }}>
        {[
          { title: "혈압/혈당 관리", items: [{ label: "혈압 관리", pct: 85 }, { label: "혈당 관리", pct: 72 }] },
          { title: "운동 실천", note: `주간 운동 일수: ${report.exerciseDays}일` },
          { title: "식단 관리", note: `식단 기록 일수: ${report.dietDays}일` },
          { title: "챌린지 참여", note: `완료한 미션: ${report.challengeMissions}개` },
        ].map((section) => (
          <div key={section.title} style={{ background: "#fff", border: "1px solid #e5e7eb", borderRadius: 10, padding: 16 }}>
            <h2 style={{ fontSize: 13, fontWeight: 700, marginBottom: 10 }}>{section.title}</h2>
            {section.items?.map((item) => (
              <div key={item.label} style={{ marginBottom: 10 }}>
                <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 4 }}>
                  <span style={{ fontSize: 11, color: "#555" }}>{item.label}</span>
                  <span style={{ fontSize: 11, fontWeight: 700 }}>{item.pct}%</span>
                </div>
                <div style={{ height: 6, background: "#e8f0ec", borderRadius: 4 }}>
                  <div style={{ width: `${item.pct}%`, height: "100%", background: "#3D7A4F", borderRadius: 4 }} />
                </div>
              </div>
            ))}
            {section.note && <p style={{ fontSize: 11, color: "#888", marginBottom: 8 }}>{section.note}</p>}
            {!section.items && (
              <div style={{ height: 100, background: "#f9fafb", border: "1.5px dashed #d1d5db", borderRadius: 6, display: "flex", alignItems: "center", justifyContent: "center", color: "#aaa", fontSize: 12 }}>
                차트 영역
              </div>
            )}
          </div>
        ))}
      </div>

      {/* AI 분석 요약 */}
      <div style={{ background: "#fff", border: "1px solid #e5e7eb", borderRadius: 10, padding: 20, marginBottom: 18 }}>
        <h2 style={{ fontSize: 14, fontWeight: 700, marginBottom: 12 }}>AI 분석 요약</h2>
        <div style={{ background: "#F9F9F9", border: "1px solid #e8f0ec", borderRadius: 6, padding: 16, fontSize: 13, color: "#333", lineHeight: 1.7, whiteSpace: "pre-line" }}>
          {report.aiSummary}
        </div>
      </div>

      {/* 건강 조언 */}
      <div style={{ background: "#fff", border: "1px solid #e5e7eb", borderRadius: 10, padding: 20 }}>
        <h2 style={{ fontSize: 14, fontWeight: 700, marginBottom: 14 }}>건강 조언</h2>
        <div style={{ marginBottom: 14 }}>
          <p style={{ fontSize: 13, fontWeight: 700, color: "#E74C3C", marginBottom: 8 }}>⚠ 주의할 점</p>
          {report.cautions.map((c) => (
            <p key={c} style={{ fontSize: 13, color: "#666", lineHeight: 1.6 }}>• {c}</p>
          ))}
        </div>
        <div style={{ marginBottom: 18 }}>
          <p style={{ fontSize: 13, fontWeight: 700, color: "#27AE60", marginBottom: 8 }}>✓ 칭찬할 만한 점</p>
          {report.praises.map((p) => (
            <p key={p} style={{ fontSize: 13, color: "#666", lineHeight: 1.6 }}>• {p}</p>
          ))}
        </div>
        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 10 }}>
          <button style={{ padding: "10px", background: "#f0f7f2", border: "1px solid #dde8e2", borderRadius: 6, fontSize: 13, cursor: "pointer" }}>👍 도움이 됨</button>
          <button style={{ padding: "10px", background: "#f0f7f2", border: "1px solid #dde8e2", borderRadius: 6, fontSize: 13, cursor: "pointer" }}>👎 도움이 안 됨</button>
        </div>
      </div>
    </div>
  );
}
