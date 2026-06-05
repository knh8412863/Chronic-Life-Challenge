const summaryCards = [
  { title: "오늘 건강 점수", value: "82점", description: "최근 기록 기준 양호한 상태입니다.", tone: "green" },
  { title: "최근 예측 결과", value: "당뇨 주의", description: "생활습관 관리가 필요한 상태입니다.", tone: "pink" },
  { title: "참여 중 챌린지", value: "3개", description: "오늘 체크인할 챌린지가 있습니다.", tone: "blue" },
];

export function HomePage() {
  return (
    <div className="page-stack">
      <section className="page-heading">
        <p className="eyebrow">홈/메인</p>
        <h1>오늘의 건강 대시보드</h1>
        <p>건강 기록, 예측 결과, 조언, 챌린지를 한 화면에서 확인합니다.</p>
      </section>

      <section className="summary-grid" aria-label="홈 요약">
        {summaryCards.map((card) => (
          <article className={`summary-card summary-${card.tone}`} key={card.title}>
            <p>{card.title}</p>
            <strong>{card.value}</strong>
            <span>{card.description}</span>
          </article>
        ))}
      </section>

      <section className="home-two-column">
        <article className="content-panel">
          <h2>오늘의 AI 조언</h2>
          <p>혈압과 LDL 콜레스테롤 관리가 필요해요. 오늘은 짠 음식을 줄이고 20분 가볍게 산책해보세요.</p>
          <button className="small-button" type="button">
            상세보기
          </button>
        </article>
        <article className="content-panel">
          <h2>이번 주 챌린지</h2>
          <div className="challenge-lines">
            <div>
              <span>걷기 6,000보</span>
              <strong>92%</strong>
            </div>
            <progress max="100" value="92" />
            <div>
              <span>저염 식단</span>
              <strong>78%</strong>
            </div>
            <progress max="100" value="78" />
          </div>
        </article>
      </section>
    </div>
  );
}
