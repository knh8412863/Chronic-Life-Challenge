import { useState } from "react";

import type { AppRoute } from "../../App";
import { getStoredAccessToken } from "../../api/auth";
import { exportWeeklyReport, type WeeklyReportExportFormat } from "../../api/reports";
import { ErrorState } from "../../components/common/ErrorState";

interface Props {
  onNavigate: (route: AppRoute) => void;
}

const exportFormats: Array<{
  label: string;
  value: WeeklyReportExportFormat;
  description: string;
  iconBg: string;
  iconColor: string;
  icon: string;
}> = [
  {
    label: "PDF",
    value: "PDF",
    description: "제출·공유용 문서 형식",
    iconBg: "#FEE9E9",
    iconColor: "#C0392B",
    icon: "📄",
  },
  {
    label: "JSON",
    value: "JSON",
    description: "개발·연동 확인용 원본 데이터",
    iconBg: "#EAF1FD",
    iconColor: "#2563EB",
    icon: "{ }",
  },
  {
    label: "CSV",
    value: "CSV",
    description: "스프레드시트용 표 형식",
    iconBg: "#E9F7EE",
    iconColor: "#16A34A",
    icon: "⊞",
  },
];

const includedData: Array<{ name: string; description: string; emoji: string }> = [
  {
    name: "주간 리포트 본문",
    description: "AI가 생성한 한 주간 건강 분석 전체 텍스트",
    emoji: "📝",
  },
  {
    name: "요약 카드",
    description: "걸음 수·칼로리·수면 등 주요 지표를 한눈에 볼 수 있는 카드형 요약",
    emoji: "🃏",
  },
  {
    name: "지표별 요약",
    description: "각 건강 지표(혈당·혈압·체중 등)의 주간 평균 및 추이",
    emoji: "📊",
  },
  {
    name: "챌린지 요약",
    description: "이번 주 참여한 챌린지 달성률 및 완료 현황",
    emoji: "🏆",
  },
  {
    name: "생성 정보",
    description: "리포트 생성 일시, 대상 기간, 버전 정보",
    emoji: "🕐",
  },
];

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
  const [selectedFormat, setSelectedFormat] = useState<WeeklyReportExportFormat>("PDF");
  const [sendEmail, setSendEmail] = useState(false);
  const [isExporting, setIsExporting] = useState(false);
  const [message, setMessage] = useState("");
  const [isSuccess, setIsSuccess] = useState(false);

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
      setIsSuccess(true);
      setMessage(
        response.data.emailed
          ? "리포트 파일을 생성하고 이메일 발송을 요청했습니다."
          : "리포트 파일을 생성했습니다.",
      );
    } catch {
      setIsSuccess(false);
      setMessage("리포트 내보내기에 실패했습니다. 로그인 상태와 리포트 존재 여부를 확인해 주세요.");
    } finally {
      setIsExporting(false);
    }
  }

  return (
    <div style={{ padding: "28px 40px", maxWidth: 860 }}>
      {/* 뒤로가기 */}
      <button
        onClick={() => onNavigate("/reports")}
        style={{
          background: "none",
          border: "none",
          cursor: "pointer",
          display: "flex",
          alignItems: "center",
          gap: 6,
          color: "#888",
          fontSize: 13,
          marginBottom: 20,
          padding: 0,
        }}
      >
        ← 리포트 목록으로
      </button>

      {/* 페이지 제목 */}
      <h1 style={{ fontSize: 20, fontWeight: 500, color: "#1a1a1a", margin: 0, marginBottom: 4 }}>
        건강 데이터 내보내기
      </h1>
      <p style={{ fontSize: 13, color: "#888", marginBottom: 24 }}>
        선택한 주간 리포트를 원하는 형식으로 저장하세요
      </p>

      {message && (
        isSuccess ? (
          <div
            style={{
              background: "#E8F3EC",
              border: "0.5px solid #3D7A4F",
              borderRadius: 10,
              padding: "14px 18px",
              display: "flex",
              alignItems: "center",
              gap: 12,
              marginBottom: 16,
            }}
          >
            <span style={{ fontSize: 20, color: "#3D7A4F", lineHeight: 1 }}>✓</span>
            <span style={{ fontSize: 13, color: "#3D7A4F", fontWeight: 500 }}>{message}</span>
          </div>
        ) : (
          <ErrorState title={message} />
        )
      )}

      {/* 파일 형식 + 이메일 카드 */}
      <div
        style={{
          background: "#fff",
          border: "0.5px solid #e5e7eb",
          borderRadius: 12,
          padding: 24,
          marginBottom: 14,
        }}
      >
        <p style={{ fontSize: 11, fontWeight: 500, color: "#aaa", letterSpacing: "0.07em", textTransform: "uppercase", marginBottom: 12 }}>
          파일 형식
        </p>

        {/* 형식 선택 버튼 */}
        <div style={{ display: "grid", gridTemplateColumns: "repeat(3, 1fr)", gap: 10, marginBottom: 22 }}>
          {exportFormats.map((format) => {
            const isActive = selectedFormat === format.value;
            return (
              <button
                key={format.value}
                type="button"
                onClick={() => setSelectedFormat(format.value)}
                style={{
                  border: isActive ? "2px solid #3D7A4F" : "0.5px solid #e5e7eb",
                  borderRadius: 8,
                  padding: "14px 12px",
                  background: isActive ? "#F2F8F4" : "#fff",
                  cursor: "pointer",
                  textAlign: "left",
                }}
              >
                {/* 아이콘 뱃지 */}
                <div
                  style={{
                    width: 30,
                    height: 30,
                    borderRadius: 8,
                    background: format.iconBg,
                    display: "flex",
                    alignItems: "center",
                    justifyContent: "center",
                    marginBottom: 10,
                    fontSize: format.value === "JSON" ? 10 : 14,
                    fontWeight: 700,
                    color: format.iconColor,
                  }}
                >
                  {format.icon}
                </div>
                <p style={{ fontSize: 13, fontWeight: 500, color: "#1a1a1a", margin: 0, marginBottom: 3 }}>
                  {format.label}
                </p>
                <p style={{ fontSize: 11, color: "#888", margin: 0, lineHeight: 1.5 }}>
                  {format.description}
                </p>
              </button>
            );
          })}
        </div>

        <hr style={{ border: "none", borderTop: "0.5px solid #f0f0f0", marginBottom: 20 }} />

        {/* 이메일 토글 */}
        <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
          <label style={{ position: "relative", width: 36, height: 20, flexShrink: 0 }}>
            <input
              type="checkbox"
              checked={sendEmail}
              onChange={(e) => setSendEmail(e.target.checked)}
              style={{ opacity: 0, width: 0, height: 0 }}
            />
            <span
              style={{
                position: "absolute",
                inset: 0,
                borderRadius: 10,
                background: sendEmail ? "#3D7A4F" : "#d1d5db",
                cursor: "pointer",
                transition: "background 0.2s",
              }}
            />
            <span
              style={{
                position: "absolute",
                width: 14,
                height: 14,
                left: sendEmail ? 19 : 3,
                top: 3,
                borderRadius: "50%",
                background: "#fff",
                transition: "left 0.2s",
              }}
            />
          </label>
          <div>
            <p style={{ fontSize: 14, color: "#1a1a1a", margin: 0 }}>이메일로도 받기</p>
            <p style={{ fontSize: 12, color: "#aaa", margin: 0, marginTop: 2 }}>
              가입한 이메일 주소로 함께 발송됩니다
            </p>
          </div>
        </div>
      </div>

      {/* 포함 데이터 카드 */}
      <div
        style={{
          background: "#fff",
          border: "0.5px solid #e5e7eb",
          borderRadius: 12,
          padding: 24,
          marginBottom: 14,
        }}
      >
        <p style={{ fontSize: 11, fontWeight: 500, color: "#aaa", letterSpacing: "0.07em", textTransform: "uppercase", marginBottom: 12 }}>
          포함 데이터
        </p>

        <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
          {includedData.map((item) => (
            <div
              key={item.name}
              style={{
                display: "flex",
                alignItems: "flex-start",
                gap: 12,
                padding: "12px 14px",
                background: "#f9fafb",
                borderRadius: 8,
              }}
            >
              {/* 아이콘 */}
              <div
                style={{
                  width: 28,
                  height: 28,
                  borderRadius: 7,
                  background: "#E8F3EC",
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "center",
                  flexShrink: 0,
                  fontSize: 14,
                  marginTop: 1,
                }}
              >
                {item.emoji}
              </div>

              {/* 텍스트 */}
              <div>
                <p style={{ fontSize: 13, fontWeight: 500, color: "#1a1a1a", margin: 0, marginBottom: 3 }}>
                  {item.name}
                </p>
                <p style={{ fontSize: 12, color: "#aaa", margin: 0, lineHeight: 1.5 }}>
                  {item.description}
                </p>
              </div>
            </div>
          ))}
        </div>

        {/* 다운로드 버튼 */}
        <button
          type="button"
          onClick={handleExport}
          disabled={isExporting}
          style={{
            width: "100%",
            padding: "13px",
            background: isExporting ? "#A8B9AE" : "#3D7A4F",
            color: "#fff",
            border: "none",
            borderRadius: 8,
            fontSize: 14,
            fontWeight: 500,
            cursor: isExporting ? "not-allowed" : "pointer",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            gap: 8,
            marginTop: 22,
          }}
        >
          {isExporting ? "파일 생성 중..." : "⬇ 파일 다운로드"}
        </button>
      </div>

      {/* 안내 */}
      <div
        style={{
          background: "#f9fafb",
          border: "0.5px solid #e5e7eb",
          borderRadius: 12,
          padding: "14px 18px",
          display: "flex",
          gap: 10,
          alignItems: "flex-start",
        }}
      >
        <span style={{ fontSize: 16, color: "#aaa", marginTop: 1, flexShrink: 0 }}>ℹ</span>
        <p style={{ fontSize: 12, color: "#aaa", margin: 0, lineHeight: 1.7 }}>
          이메일 발송은 서버 SMTP 설정이 완료되었을 때 실제 메일로 전송됩니다.
        </p>
      </div>
    </div>
  );
}