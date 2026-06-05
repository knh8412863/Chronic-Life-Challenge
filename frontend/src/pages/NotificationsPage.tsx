import { EmptyState } from "../components/common/EmptyState";

export function NotificationsPage() {
  return (
    <div className="page-stack">
      <section className="page-heading">
        <p className="eyebrow">알림</p>
        <h1>알림 목록</h1>
        <p>상단바 알림 버튼을 누르면 이동하는 화면입니다.</p>
      </section>
      <EmptyState title="새 알림이 없습니다." description="챌린지, 리포트, 건강 기록 알림이 이곳에 표시됩니다." />
    </div>
  );
}
