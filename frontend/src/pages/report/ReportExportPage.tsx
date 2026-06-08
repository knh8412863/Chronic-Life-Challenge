import { useState } from "react";

type Period = "최근 1개월" | "최근 3개월" | "최근 6개월" | "최근 1년" | "전체 기간" | "사용자 지정";
type FileFormat = "CSV" | "Excel (XLSX)" | "PDF" | "JSON";

interface Props {
  onNavigate: (route: any) => void;
}

const EXPORT_HISTORY = [
  { date: "2026-05-10", type: "CSV", size: "2.1 MB", statusIcon: "✓", statusColor: "#3D7A4F" },
  { date: "2026-04-25", type: "PDF", size: "5.8 MB", statusIcon: "⏰", statusColor: "#888" },
  { date: "2026-04-01", type: "Excel", size: "3.2 MB", statusIcon: "⚠", statusColor: "#F59E0B" },
];

export default function ReportExportPage({ onNavigate }: Props) {
  const [selectedPeriod, setSelectedPeriod] = useState<Period>("최근 3개월");
  const [selectedFormat, setSelectedFormat] = useState<FileFormat>("CSV");
  const [showEmailInput, setShowEmailInput] = useState(false);
  const [showTooltip, setShowTooltip] = useState(false);
  const [checkedData, setCheckedData] = useState<Record<string, boolean>>({
    "혈압/혈당 기록": true,
    "운동 기록": true,
    "식단 기록": true,
    "체중 기록": true,
    "예측 결과": false,
    "챌린지 기록": false,
  });

  const periods: Period[] = ["최근 1개월", "최근 3개월", "최근 6개월", "최근 1년", "전체 기간", "사용자 지정"];
  const formats: FileFormat[] = ["CSV", "Excel (XLSX)", "PDF", "JSON"];

  return (
    <div style={{ padding: "24px" }}>
      <div style={{ display: "flex", alignItems: "center", gap: 10, marginBottom: 24 }}>
        <button onClick={() => onNavigate("/reports")} style={{ background: "none", border: "none", fontSize: 18, cursor: "pointer", color: "#555" }}>←</button>
        <h1 style={{ fontSize: 20, fontWeight: 700, color: "#1a1a1a", margin: 0 }}>건강 데이터 내보내기</h1>
      </div>

      <div style={{ background: "#fff", border: "1px solid #e5e7eb", borderRadius: 10, padding: 24, marginBottom: 18 }}>
        <h2 style={{ fontSize: 14, fontWeight: 700, marginBottom: 16 }}>내보내기 옵션</h2>

        {/* 데이터 범위 */}
        <div style={{ marginBottom: 20 }}>
          <p style={{ fontSize: 13, fontWeight: 700, marginBottom: 10 }}>데이터 범위</p>
          <div style={{ display: "grid", gridTemplateColumns: "repeat(3, 1fr)", gap: 8 }}>
            {periods.map((p) => (
              <button key={p} onClick={() => setSelectedPeriod(p)} style={{
                padding: "9px 12px", borderRadius: 6, fontSize: 12, cursor: "pointer",
                border: `1.5px solid ${selectedPeriod === p ? "#3D7A4F" : "#d1d5db"}`,
                background: selectedPeriod === p ? "#F0F7F2" : "#fff",
                color: selectedPeriod === p ? "#3D7A4F" : "#555",
                fontWeight: selectedPeriod === p ? 600 : 400,
              }}>{p}</button>
            ))}
          </div>
        </div>

        <hr style={{ border: "none", borderTop: "1px solid #f0f0f0", marginBottom: 20 }} />

        {/* 포함할 데이터 */}
        <div style={{ marginBottom: 20 }}>
          <p style={{ fontSize: 13, fontWeight: 700, marginBottom: 10 }}>포함할 데이터</p>
          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 10 }}>
            {Object.entries(checkedData).map(([key, checked]) => (
              <label key={key} style={{ display: "flex", alignItems: "center", gap: 8, cursor: "pointer", fontSize: 13 }}>
                <input type="checkbox" checked={checked} onChange={() => setCheckedData((prev) => ({ ...prev, [key]: !prev[key] }))} style={{ accentColor: "#3D7A4F", width: 15, height: 15 }} />
                {key}
              </label>
            ))}
          </div>
        </div>

        <hr style={{ border: "none", borderTop: "1px solid #f0f0f0", marginBottom: 20 }} />

        {/* 파일 형식 */}
        <div style={{ marginBottom: 20 }}>
          <p style={{ fontSize: 13, fontWeight: 700, marginBottom: 10 }}>파일 형식</p>
          <div style={{ display: "flex", gap: 8 }}>
            {formats.map((f) => (
              <button key={f} onClick={() => setSelectedFormat(f)} style={{
                padding: "8px 16px", borderRadius: 6, fontSize: 12, cursor: "pointer",
                border: `1.5px solid ${selectedFormat === f ? "#3D7A4F" : "#d1d5db"}`,
                background: selectedFormat === f ? "#F0F7F2" : "#fff",
                color: selectedFormat === f ? "#3D7A4F" : "#555",
                fontWeight: selectedFormat === f ? 600 : 400,
              }}>{f}</button>
            ))}
          </div>
        </div>

        <hr style={{ border: "none", borderTop: "1px solid #f0f0f0", marginBottom: 20 }} />

        {/* 미리보기 */}
        <div style={{ background: "#FAFCFA", border: "1px solid #e8f0ec", borderRadius: 8, padding: 16, marginBottom: 16 }}>
          <p style={{ fontSize: 13, fontWeight: 700, marginBottom: 10 }}>미리보기</p>
          <p style={{ fontSize: 12, color: "#888", marginBottom: 8 }}>선택한 옵션:</p>
          <p style={{ fontSize: 12, color: "#333", marginBottom: 4 }}>• 기간: {selectedPeriod}</p>
          <p style={{ fontSize: 12, color: "#333", marginBottom: 4 }}>• 데이터: {Object.entries(checkedData).filter(([, v]) => v).map(([k]) => k).join(", ")}</p>
          <p style={{ fontSize: 12, color: "#333", marginBottom: 4 }}>• 형식: {selectedFormat}</p>
          <div style={{ display: "flex", alignItems: "center", gap: 6 }}>
            <p style={{ fontSize: 12, color: "#333" }}>• 예상 파일 크기: 약 2.4 MB</p>
            <div style={{ position: "relative" }}
              onMouseEnter={() => setShowTooltip(true)}
              onMouseLeave={() => setShowTooltip(false)}
            >
              <span style={{ fontSize: 13, fontWeight: 700, color: "#0066CC", cursor: "pointer" }}> (?)</span>
              {showTooltip && (
                <div style={{ position: "absolute", top: 24, left: 0, background: "#333", color: "#fff", padding: 10, borderRadius: 6, fontSize: 11, width: 260, zIndex: 1000, lineHeight: 1.6 }}>
                  파일 크기는 선택한 데이터 기간과 형식에 따라 달라집니다.<br /><br />
                  • CSV: 가장 작음 (~500KB)<br />
                  • JSON: 중간 (~1.5MB)<br />
                  • Excel: 중간 (~2.5MB)<br />
                  • PDF: 가장 큼 (~8MB)
                </div>
              )}
            </div>
          </div>
        </div>

        <div style={{ textAlign: "center", marginBottom: 16, fontSize: 13, color: "#666" }}>✓ 옵션 설정 완료</div>

        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 10 }}>
          <button style={{ padding: "11px", background: "#3D7A4F", color: "#fff", border: "none", borderRadius: 6, fontSize: 13, cursor: "pointer", fontWeight: 600 }}>
            {/* TODO: API 연결 시 실제 다운로드 처리 */}
            다운로드
          </button>
          <button onClick={() => setShowEmailInput(!showEmailInput)} style={{ padding: "11px", background: "#fff", color: "#333", border: "1.5px solid #ddd", borderRadius: 6, fontSize: 13, cursor: "pointer" }}>
            이메일로 전송
          </button>
        </div>

        {showEmailInput && (
          <div style={{ marginTop: 14 }}>
            <input type="email" placeholder="받는 이메일 주소" style={{ width: "100%", height: 38, border: "1px solid #d1d5db", borderRadius: 6, padding: "0 12px", fontSize: 13, marginBottom: 10, boxSizing: "border-box" }} />
            <label style={{ display: "flex", alignItems: "center", gap: 8, fontSize: 12 }}>
              <input type="checkbox" style={{ accentColor: "#3D7A4F" }} />
              비밀번호로 보호 (선택)
            </label>
          </div>
        )}
      </div>

      {/* 최근 내보내기 기록 */}
      <div style={{ background: "#fff", border: "1px solid #e5e7eb", borderRadius: 10, padding: 20 }}>
        <h2 style={{ fontSize: 14, fontWeight: 700, marginBottom: 14 }}>최근 내보내기 기록</h2>
        {EXPORT_HISTORY.map((item, i) => (
          <div key={i} style={{ display: "flex", alignItems: "center", gap: 10, padding: "10px 0", borderBottom: i < EXPORT_HISTORY.length - 1 ? "1px solid #f0f0f0" : "none" }}>
            <span style={{ fontSize: 16, color: item.statusColor }}>{item.statusIcon}</span>
            <span style={{ fontSize: 12, color: "#888" }}>{item.date}</span>
            <span style={{ padding: "2px 8px", background: "#EFF6FF", border: "1px solid #93C5FD", borderRadius: 12, fontSize: 10, color: "#3B82F6" }}>{item.type}</span>
            <span style={{ fontSize: 12, color: "#888" }}>{item.size}</span>
            <div style={{ marginLeft: "auto" }}>
              <button style={{ padding: "5px 12px", border: "1.5px solid #ddd", borderRadius: 6, background: "#fff", fontSize: 11, cursor: "pointer" }}>재다운로드</button>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
