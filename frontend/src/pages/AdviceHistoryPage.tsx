const adviceRows = [
  ["2026-05-15", "혈압관리", "도움됨", "혈압과 LDL 콜레스테롤 관리가 필요해요."],
  ["2026-05-14", "식단", "도움됨", "나트륨 섭취를 하루 2000mg 이하로 제한하세요."],
  ["2026-05-13", "운동", "도움 안됨", "주 3회 이상 유산소 운동을 30분씩 실천해보세요."],
  ["2026-05-12", "수면", "미피드백", "수면 시간을 7시간 이상 확보하세요."],
];

export function AdviceHistoryPage() {
  return (
    <div className="page-stack">
      <h1>조언 이력</h1>
      <section className="advice-history-list">
        {adviceRows.map(([date, category, feedback, content]) => (
          <article className="dashboard-card advice-history-item" key={date}>
            <div>
              <span>{date}</span>
              <span className="chip">{category}</span>
              <span>{feedback}</span>
            </div>
            <p>{content}</p>
            <button className={feedback === "미피드백" ? "green-button" : "small-button"} type="button">
              {feedback === "미피드백" ? "피드백 남기기" : "상세보기"}
            </button>
          </article>
        ))}
      </section>
    </div>
  );
}
