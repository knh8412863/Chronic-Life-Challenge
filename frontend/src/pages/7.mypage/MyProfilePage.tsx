export function MyProfilePage() {
  return (
    <div className="page-stack">
      <section className="page-heading">
        <p className="eyebrow">마이페이지</p>
        <h1>내 정보</h1>
        <p>상단바 프로필 버튼과 사이드바 마이페이지 메뉴에서 이동하는 기본 화면입니다.</p>
      </section>
      <section className="content-panel profile-grid">
        <div>
          <span className="field-label">이름</span>
          <strong>사용자</strong>
        </div>
        <div>
          <span className="field-label">이메일</span>
          <strong>user@example.com</strong>
        </div>
        <div>
          <span className="field-label">건강 프로필</span>
          <strong>등록 전</strong>
        </div>
      </section>
    </div>
  );
}
