import type { AppRoute } from "../../App";

type HubItem = {
  title: string;
  description: string;
  route: AppRoute;
  icon: string;
};

const HUB_ITEMS: HubItem[] = [
  {
    title: "건강 목표",
    description: "만성질환 수치·생활습관 목표를 확인하고 관리합니다.",
    route: "/health/goal",
    icon: "🎯",
  },
  {
    title: "건강 프로필",
    description: "기본 정보, 만성질환, 가족력, 생활습관을 확인합니다.",
    route: "/health/profile",
    icon: "👤",
  },
  {
    title: "건강 기록 목록",
    description: "혈압, 공복 혈당, 식후 혈당 기록 목록을 확인합니다.",
    route: "/health/vitals",
    icon: "💉",
  },
  {
    title: "건강 수치 기록",
    description: "혈압·혈당·지질·신장 수치를 새로 기록합니다.",
    route: "/health/vitals/input",
    icon: "📝",
  },
  {
    title: "운동 기록",
    description: "운동 종류, 시간, 소모 칼로리를 기록하고 확인합니다.",
    route: "/health/exercise",
    icon: "🏃",
  },
  {
    title: "일일 활동 기록",
    description: "걸음수, 수면, 수분 섭취, 스트레스 수준을 기록합니다.",
    route: "/health/activity",
    icon: "📊",
  },
];

type HealthHubPageProps = {
  onNavigate: (route: AppRoute) => void;
};

export function HealthHubPage({ onNavigate }: HealthHubPageProps) {
  return (
    <div className="page-stack" style={{ maxWidth: "900px" }}>
      <section className="page-heading-row">
        <div className="page-heading">
          <h1>건강 관리</h1>
        </div>
      </section>

      <div className="health-hub-grid">
        {HUB_ITEMS.map((item) => (
          <button
            key={item.route}
            type="button"
            className="health-hub-card"
            onClick={() => onNavigate(item.route)}
          >
            <span className="health-hub-icon">{item.icon}</span>
            <strong className="health-hub-title">{item.title}</strong>
            <p className="health-hub-desc">{item.description}</p>
          </button>
        ))}
      </div>
    </div>
  );
}
