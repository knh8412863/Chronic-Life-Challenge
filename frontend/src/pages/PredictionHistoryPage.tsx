import type { AppRoute } from "../App";

type PredictionHistoryPageProps = {
  onNavigate: (route: AppRoute) => void;
};

const historyRows = [
  ["2026-05-10", "고혈압 위험 높음", "72%"],
  ["2026-04-20", "당뇨 위험 중간", "41%"],
  ["2026-03-15", "모두 저위험", "28%"],
];

export function PredictionHistoryPage({ onNavigate }: PredictionHistoryPageProps) {
  return (
    <div className="page-stack">
      <section className="section-header-row">
        <h1>예측 이력</h1>
        <div className="button-row">
          <button className="green-button" type="button" onClick={() => onNavigate("/prediction/request")}>
            새 예측 요청
          </button>
          <button className="small-button" type="button">
            최근 7일
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
              <th>상세보기</th>
            </tr>
          </thead>
          <tbody>
            {historyRows.map(([date, summary, risk]) => (
              <tr key={date}>
                <td>{date}</td>
                <td>{summary}</td>
                <td>{risk}</td>
                <td>
                  <button className="small-button" type="button" onClick={() => onNavigate("/prediction/result")}>
                    상세
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </section>
      <section className="dashboard-card chart-placeholder">시계열 위험도 변화 차트</section>
    </div>
  );
}
