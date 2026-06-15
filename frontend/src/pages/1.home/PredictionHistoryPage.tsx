import { useEffect, useMemo, useState } from "react";

import type { AppRoute } from "../../App";
import { getStoredAccessToken } from "../../api/auth";
import { getPredictionResults, type PredictionResultListItem } from "../../api/predictions";

type PredictionHistoryPageProps = {
  onNavigate: (route: AppRoute) => void;
};

const diseaseLabels: Record<string, string> = {
  diabetes: "당뇨병",
  hypertension: "고혈압",
  kidney: "만성신장질환",
};

const riskLevelLabels: Record<string, string> = {
  HIGH: "고위험",
  MEDIUM: "중위험",
  LOW: "저위험",
};

function formatDate(value: string) {
  return new Intl.DateTimeFormat("ko-KR", {
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
  }).format(new Date(value));
}

function formatProbability(value: number | null) {
  if (value === null) return "결과 없음";
  return `${Math.round(value * 1000) / 10}%`;
}

function buildResultSummary(item: PredictionResultListItem) {
  if (!item.highest_risk_disease) {
    return "예측 결과 없음";
  }
  const disease = diseaseLabels[item.highest_risk_disease] ?? item.highest_risk_disease;
  const highestRiskLevel = item.disease_risks[item.highest_risk_disease]?.risk_level ?? item.overall_risk_level;
  const risk = riskLevelLabels[highestRiskLevel] ?? highestRiskLevel;
  return `${disease} ${risk}`;
}

export function PredictionHistoryPage({ onNavigate }: PredictionHistoryPageProps) {
  const [items, setItems] = useState<PredictionResultListItem[]>([]);
  const [total, setTotal] = useState(0);
  const [isLoading, setIsLoading] = useState(false);
  const [errorMessage, setErrorMessage] = useState("");
  const [recentOnly, setRecentOnly] = useState(false);

  useEffect(() => {
    const token = getStoredAccessToken();
    if (!token) {
      setErrorMessage("로그인 후 예측 이력을 확인할 수 있습니다.");
      return;
    }

    setIsLoading(true);
    setErrorMessage("");
    getPredictionResults(20, token)
      .then((response) => {
        setItems(response.data.items);
        setTotal(response.data.total);
      })
      .catch(() => setErrorMessage("예측 이력을 불러오지 못했습니다."))
      .finally(() => setIsLoading(false));
  }, []);

  const visibleItems = useMemo(() => {
    if (!recentOnly) return items;
    const sevenDaysAgo = new Date();
    sevenDaysAgo.setDate(sevenDaysAgo.getDate() - 7);
    return items.filter((item) => new Date(item.created_at) >= sevenDaysAgo);
  }, [items, recentOnly]);

  return (
    <div className="page-stack">
      <section className="section-header-row">
        <div>
          <h1>예측 이력</h1>
          <p>총 {total}건의 예측 결과</p>
        </div>
        <div className="button-row">
          <button className="green-button" type="button" onClick={() => onNavigate("/prediction/request")}>
            새 예측 요청
          </button>
          <button className={recentOnly ? "small-button is-active" : "small-button"} type="button" onClick={() => setRecentOnly((prev) => !prev)}>
            {recentOnly ? "전체 보기" : "최근 7일"}
          </button>
        </div>
      </section>
      <section className="table-card">
        <table>
          <thead>
            <tr>
              <th>예측일</th>
              <th>결과 요약</th>
              <th>최고 위험도</th>
              <th>피드백</th>
              <th>상세보기</th>
            </tr>
          </thead>
          <tbody>
            {isLoading ? (
              <tr>
                <td colSpan={5}>예측 이력을 불러오는 중입니다.</td>
              </tr>
            ) : errorMessage ? (
              <tr>
                <td colSpan={5}>{errorMessage}</td>
              </tr>
            ) : visibleItems.length > 0 ? (
              visibleItems.map((item) => (
                <tr key={item.result_id}>
                  <td>{formatDate(item.created_at)}</td>
                  <td>{buildResultSummary(item)}</td>
                  <td>{formatProbability(item.highest_risk_score ?? item.highest_risk_probability)}</td>
                  <td>{item.feedback_submitted ? "제출 완료" : "미제출"}</td>
                  <td>
                    <button
                      className="small-button"
                      type="button"
                      onClick={() => {
                        sessionStorage.setItem("predictionResultId", String(item.result_id));
                        window.history.pushState({}, "", `/prediction/result?result_id=${item.result_id}`);
                        onNavigate("/prediction/result");
                      }}
                    >
                      상세
                    </button>
                  </td>
                </tr>
              ))
            ) : (
              <tr>
                <td colSpan={5}>표시할 예측 이력이 없습니다.</td>
              </tr>
            )}
          </tbody>
        </table>
      </section>
      <section className="dashboard-card chart-placeholder">예측 결과가 누적되면 시계열 위험도 변화 차트를 표시합니다.</section>
    </div>
  );
}
