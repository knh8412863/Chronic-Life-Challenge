import { useState } from "react";

import type { AppRoute } from "../../App";
import { getStoredAccessToken } from "../../api/auth";
import { exportWeeklyReport, type WeeklyReportExportFormat } from "../../api/reports";
import { ErrorState } from "../../components/common/ErrorState";

interface Props {
  onNavigate: (route: AppRoute) => void;
}

const exportFormats: Array<{ label: string; value: WeeklyReportExportFormat; description: string }> = [
  { label: "PDF", value: "PDF", description: "제출/공유용 문서 형식" },
  { label: "JSON", value: "JSON", description: "개발/연동 확인용 원본 구조 데이터" },
  { label: "CSV", value: "CSV", description: "스프레드시트에서 열 수 있는 표 형식 데이터" },
];

const includedData = ["주간 리포트 본문", "요약 카드", "지표별 요약", "챌린지 요약", "생성 정보"];

function selectedReportStorageKey() {
  return "selectedWeeklyReportId";
}

function base64ToArrayBuffer(content: string) {
  const binary = window.atob(content);
  const bytes = Uint8Array.from(binary, (char) => char.charCodeAt(0));
  return bytes.buffer;
}

function downloadFile(fileName: string, contentType: string, content: string, encoding: "TEXT" | "BASE64") {
  const data = encoding === "BASE64" ? base64ToArrayBuffer(content) : content;
  const blob = new Blob([data], { type: contentType });
  const url = URL.createObjectURL(blob);
  const anchor = document.createElement("a");
  anchor.href = url;
  anchor.download = fileName;
  document.body.appendChild(anchor);
  anchor.click();
  anchor.remove();
  URL.revokeObjectURL(url);
}

export default function ReportExportPage({ onNavigate }: Props) {
  const [selectedFormat, setSelectedFormat] = useState<WeeklyReportExportFormat>("JSON");
  const [sendEmail, setSendEmail] = useState(false);
  const [isExporting, setIsExporting] = useState(false);
  const [message, setMessage] = useState("");

  async function handleExport() {
    const reportId = Number(sessionStorage.getItem(selectedReportStorageKey()));
    if (!reportId) {
      setMessage("내보낼 리포트를 먼저 선택해 주세요.");
      return;
    }

    setIsExporting(true);
    setMessage("");
    try {
      const response = await exportWeeklyReport(reportId, selectedFormat, getStoredAccessToken(), sendEmail);
      downloadFile(
        response.data.file_name,
        response.data.content_type,
        response.data.content,
        response.data.content_encoding,
      );
      setMessage(response.data.emailed ? "리포트 파일을 생성하고 이메일 발송을 요청했습니다." : "리포트 파일을 생성했습니다.");
    } catch {
      setMessage("리포트 내보내기에 실패했습니다. 로그인 상태와 리포트 존재 여부를 확인해 주세요.");
    } finally {
      setIsExporting(false);
    }
  }

  return (
    <div style={{ padding: "24px" }}>
      <div style={{ display: "flex", alignItems: "center", gap: 10, marginBottom: 24 }}>
        <button onClick={() => onNavigate("/reports")} style={{ background: "none", border: "none", fontSize: 18, cursor: "pointer", color: "#555" }}>←</button>
        <h1 style={{ fontSize: 20, fontWeight: 700, color: "#1a1a1a", margin: 0 }}>건강 데이터 내보내기</h1>
      </div>

      {message && <ErrorState title={message} />}

      <div style={{ background: "#fff", border: "1px solid #e5e7eb", borderRadius: 10, padding: 24, marginBottom: 18 }}>
        <h2 style={{ fontSize: 14, fontWeight: 700, marginBottom: 16 }}>파일 형식 선택</h2>
        <div style={{ display: "grid", gridTemplateColumns: "repeat(3, 1fr)", gap: 12, marginBottom: 22 }}>
          {exportFormats.map((format) => (
            <button
              key={format.value}
              type="button"
              onClick={() => setSelectedFormat(format.value)}
              style={{
                padding: 16,
                border: selectedFormat === format.value ? "1.5px solid #3D7A4F" : "1.5px solid #d1d5db",
                borderRadius: 8,
                background: selectedFormat === format.value ? "#F0F7F2" : "#fff",
                color: "#333",
                textAlign: "left",
              }}
            >
              <strong style={{ display: "block", marginBottom: 6 }}>{format.label}</strong>
              <span style={{ fontSize: 12, color: "#666" }}>{format.description}</span>
            </button>
          ))}
        </div>

        <hr style={{ border: "none", borderTop: "1px solid #f0f0f0", marginBottom: 20 }} />

        <label style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 20, fontSize: 13, color: "#444" }}>
          <input type="checkbox" checked={sendEmail} onChange={(event) => setSendEmail(event.target.checked)} />
          이메일로도 받기
        </label>

        <div style={{ marginBottom: 20 }}>
          <p style={{ fontSize: 13, fontWeight: 700, marginBottom: 10 }}>포함 데이터</p>
          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 10 }}>
            {includedData.map((item) => (
              <div key={item} style={{ display: "flex", alignItems: "center", gap: 8, fontSize: 13, color: "#555" }}>
                <span style={{ width: 8, height: 8, borderRadius: "50%", background: "#3D7A4F" }} />
                {item}
              </div>
            ))}
          </div>
        </div>

        <button
          type="button"
          onClick={handleExport}
          disabled={isExporting}
          style={{ width: "100%", padding: "11px", background: isExporting ? "#A8B9AE" : "#3D7A4F", color: "#fff", border: "none", borderRadius: 6, fontSize: 13, cursor: isExporting ? "not-allowed" : "pointer", fontWeight: 600 }}
        >
          {isExporting ? "파일 생성 중..." : "파일 다운로드"}
        </button>
      </div>

      <div style={{ background: "#F8FAFC", border: "1px solid #e5e7eb", borderRadius: 10, padding: 20 }}>
        <h2 style={{ fontSize: 14, fontWeight: 700, marginBottom: 14 }}>안내</h2>
        <p style={{ fontSize: 13, color: "#666", lineHeight: 1.7 }}>
          이메일 발송은 서버 SMTP 설정이 되어 있을 때 실제 메일로 전송됩니다.
        </p>
      </div>
    </div>
  );
}
