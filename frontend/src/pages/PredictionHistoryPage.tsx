import type { AppRoute } from "../App";

type PredictionHistoryPageProps = {
  onNavigate: (route: AppRoute) => void;
};

export function PredictionHistoryPage({ onNavigate }: PredictionHistoryPageProps) {
  const latestResultId = sessionStorage.getItem("predictionResultId");

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
            {latestResultId ? (
              <tr>
                <td>최근 예측</td>
                <td>현재 세션에서 생성한 예측 결과</td>
                <td>결과 상세에서 확인</td>
                <td>
                  <button
                    className="small-button"
                    type="button"
                    onClick={() => {
                      window.history.pushState({}, "", `/prediction/result?result_id=${latestResultId}`);
                      onNavigate("/prediction/result");
                    }}
                  >
                    상세
                  </button>
                </td>
              </tr>
            ) : (
              <tr>
                <td colSpan={4}>예측 이력 목록 API가 아직 없어 최근 세션 결과만 표시됩니다.</td>
              </tr>
            )}
          </tbody>
        </table>
      </section>
      <section className="dashboard-card chart-placeholder">예측 결과 목록 API 연동 후 시계열 위험도 변화 차트를 표시합니다.</section>
    </div>
  );
}
