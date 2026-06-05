type PlaceholderPageProps = {
  title: string;
  description: string;
};

export function PlaceholderPage({ title, description }: PlaceholderPageProps) {
  return (
    <div className="page-stack">
      <section className="page-heading">
        <p className="eyebrow">작업 예정</p>
        <h1>{title}</h1>
        <p>{description}</p>
      </section>
      <section className="content-panel">
        <h2>프론트 작업 안내</h2>
        <p>이 영역에 카테고리별 와이어프레임 화면을 연결하면 됩니다.</p>
      </section>
    </div>
  );
}
