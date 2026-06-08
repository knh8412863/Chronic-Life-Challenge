import type { AppRoute } from "../../App";

interface Props {
  onNavigate: (route: AppRoute) => void;
}

const plannedFormats = ["PDF", "CSV", "Excel (XLSX)", "JSON"];
const plannedData = ["혈압/혈당 기록", "운동 기록", "식단 기록", "예측 결과", "챌린지 기록"];

export default function ReportExportPage({ onNavigate }: Props) {
  return (
    <div style={{ padding: "24px" }}>
      <div style={{ display: "flex", alignItems: "center", gap: 10, marginBottom: 24 }}>
        <button onClick={() => onNavigate("/reports")} style={{ background: "none", border: "none", fontSize: 18, cursor: "pointer", color: "#555" }}>←</button>
        <h1 style={{ fontSize: 20, fontWeight: 700, color: "#1a1a1a", margin: 0 }}>건강 데이터 내보내기</h1>
      </div>

      <div style={{ background: "#FFF8E1", border: "1px solid #FFC107", borderRadius: 10, padding: 18, marginBottom: 18 }}>
        <p style={{ fontSize: 14, fontWeight: 700, color: "#92400E", marginBottom: 6 }}>내보내기 기능은 준비 중입니다.</p>
        <p style={{ fontSize: 13, color: "#8A6B20", lineHeight: 1.6 }}>
          기획문서 기준 PDF 다운로드, 이메일 발송, 첨부파일 저장, 발송 이력 관리는 MVP 후순위 기능입니다.
          현재 버전에서는 앱 내 주간 리포트 조회와 상세 확인을 먼저 제공합니다.
        </p>
      </div>

      <div style={{ background: "#fff", border: "1px solid #e5e7eb", borderRadius: 10, padding: 24, marginBottom: 18 }}>
        <h2 style={{ fontSize: 14, fontWeight: 700, marginBottom: 16 }}>추후 제공 예정 범위</h2>

        <div style={{ marginBottom: 20 }}>
          <p style={{ fontSize: 13, fontWeight: 700, marginBottom: 10 }}>파일 형식</p>
          <div style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
            {plannedFormats.map((format) => (
              <span key={format} style={{ padding: "8px 14px", borderRadius: 6, fontSize: 12, border: "1.5px solid #d1d5db", background: "#F9FAFB", color: "#6B7280" }}>
                {format}
              </span>
            ))}
          </div>
        </div>

        <hr style={{ border: "none", borderTop: "1px solid #f0f0f0", marginBottom: 20 }} />

        <div style={{ marginBottom: 20 }}>
          <p style={{ fontSize: 13, fontWeight: 700, marginBottom: 10 }}>포함 예정 데이터</p>
          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 10 }}>
            {plannedData.map((item) => (
              <div key={item} style={{ display: "flex", alignItems: "center", gap: 8, fontSize: 13, color: "#555" }}>
                <span style={{ width: 8, height: 8, borderRadius: "50%", background: "#3D7A4F" }} />
                {item}
              </div>
            ))}
          </div>
        </div>

        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 10 }}>
          <button
            type="button"
            disabled
            style={{ padding: "11px", background: "#CBD5E1", color: "#fff", border: "none", borderRadius: 6, fontSize: 13, cursor: "not-allowed", fontWeight: 600 }}
          >
            다운로드 준비 중
          </button>
          <button
            type="button"
            disabled
            style={{ padding: "11px", background: "#F3F4F6", color: "#9CA3AF", border: "1.5px solid #E5E7EB", borderRadius: 6, fontSize: 13, cursor: "not-allowed" }}
          >
            이메일 전송 준비 중
          </button>
        </div>
      </div>

      <div style={{ background: "#fff", border: "1px solid #e5e7eb", borderRadius: 10, padding: 20 }}>
        <h2 style={{ fontSize: 14, fontWeight: 700, marginBottom: 14 }}>안내</h2>
        <p style={{ fontSize: 13, color: "#666", lineHeight: 1.7 }}>
          내보내기 기능은 백엔드에서 파일 생성, 저장 위치, 이메일 발송, 재다운로드 정책이 확정된 뒤 연결하는 것이 안전합니다.
        </p>
      </div>
    </div>
  );
}
