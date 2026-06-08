import { useState } from "react";
import type { AppRoute } from "../App";

interface PetEncyclopediaPageProps {
  onNavigate: (route: AppRoute) => void;
}

type PetCategory = "DOG" | "CAT";

// 더미 데이터 — API 연결 시 교체
// GET /api/v1/virtual-pets/catalog?pet_type=DOG → 강아지 탭
// GET /api/v1/virtual-pets/catalog?pet_type=CAT → 고양이 탭
// 응답: { summary: { total_count, unlocked_count, completion_rate }, items: [{ catalog_id, pet_type, display_name, is_unlocked, unlock_condition, affinity_score }] }
const DUMMY_ENCYCLOPEDIA = {
  DOG: [
    { id: 1, name: "골든 리트리버", affection: 2, max_affection: 5, unlocked: true },
    { id: 2, name: "비숑 프리제", affection: 1, max_affection: 5, unlocked: true },
    { id: 3, name: "믹스견", affection: 5, max_affection: 5, unlocked: true },
    { id: 4, name: "시바 이누", affection: 3, max_affection: 5, unlocked: true },
    { id: 5, name: "???", affection: 0, max_affection: 5, unlocked: false },
    { id: 6, name: "???", affection: 0, max_affection: 5, unlocked: false },
    { id: 7, name: "???", affection: 0, max_affection: 5, unlocked: false },
    { id: 8, name: "???", affection: 0, max_affection: 5, unlocked: false },
  ],
  CAT: [
    { id: 9, name: "페르시안", affection: 0, max_affection: 5, unlocked: false },
    { id: 10, name: "러시안 블루", affection: 0, max_affection: 5, unlocked: false },
    { id: 11, name: "???", affection: 0, max_affection: 5, unlocked: false },
    { id: 12, name: "???", affection: 0, max_affection: 5, unlocked: false },
  ],
};

const PET_EMOJI: Record<string, string> = {
  "골든 리트리버": "🦮", "비숑 프리제": "🐩", "믹스견": "🐕", "시바 이누": "🐕‍🦺",
  "페르시안": "🐱", "러시안 블루": "🐈",
};

const UNLOCK_CONDITIONS = [
  { days: 3, label: "3일 연속 챌린지 달성 → 1단계 해제" },
  { days: 7, label: "7일 연속 챌린지 달성 → 2단계 해제" },
  { days: 30, label: "30일 연속 챌린지 달성 → 3단계 해제" },
];

export function PetEncyclopediaPage({ onNavigate }: PetEncyclopediaPageProps) {
  const [activeTab, setActiveTab] = useState<PetCategory>("DOG");

  const currentList = DUMMY_ENCYCLOPEDIA[activeTab];
  const unlockedCount = currentList.filter(p => p.unlocked).length;
  const totalCount = currentList.length;
  const collectionRate = Math.round((unlockedCount / totalCount) * 100);

  return (
    <div className="page-container">
      <div style={{ display: "flex", alignItems: "center", gap: 12, marginBottom: 20 }}>
        <button onClick={() => onNavigate("/pet")}
          style={{ background: "none", border: "none", cursor: "pointer", fontSize: 20, color: "#555" }}>←</button>
        <h1 className="page-title" style={{ margin: 0 }}>펫 도감</h1>
      </div>

      {/* 준비 중 배너 */}
      <div style={{ background: "#fafafa", border: "1.5px solid #e0e0e0", borderRadius: 8, padding: "10px 14px", marginBottom: 16 }}>
        <p style={{ fontSize: 12, color: "#888", margin: 0 }}>이 기능은 현재 준비 중입니다. 일부 기능이 제한될 수 있어요.</p>
      </div>

      {/* 탭 */}
      <div style={{ display: "flex", borderBottom: "2px solid #e0e0e0", marginBottom: 16 }}>
        {(["DOG", "CAT"] as PetCategory[]).map(tab => (
          <button key={tab} onClick={() => setActiveTab(tab)}
            style={{ padding: "10px 20px", border: "none", background: "none", cursor: "pointer",
              fontSize: 13, fontWeight: activeTab === tab ? 700 : 400,
              color: activeTab === tab ? "#1a1a1a" : "#aaa",
              borderBottom: activeTab === tab ? "2px solid #1a1a1a" : "2px solid transparent",
              marginBottom: -2 }}>
            {tab === "DOG" ? "🐶 강아지" : "🐱 고양이"}
          </button>
        ))}
      </div>

      {/* 수집 현황 */}
      <div style={{ background: "#fff", border: "1px solid #e0e0e0", borderRadius: 10, padding: 14, marginBottom: 16 }}>
        <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
          <span style={{ fontSize: 13, fontWeight: 600 }}>수집 현황</span>
          <span style={{ fontSize: 12, color: "#888" }}>{unlockedCount} / {totalCount} 종류</span>
          <div style={{ flex: 1, height: 10, background: "#f0f0f0", borderRadius: 5, overflow: "hidden" }}>
            <div style={{ width: `${collectionRate}%`, height: "100%", background: "#1a1a1a", borderRadius: 5 }} />
          </div>
          <span style={{ fontSize: 14, fontWeight: 700 }}>{collectionRate}%</span>
        </div>
      </div>

      {/* 펫 그리드 */}
      {unlockedCount === 0 ? (
        <div style={{ display: "flex", flexDirection: "column", alignItems: "center", gap: 12, padding: "40px 20px" }}>
          <div style={{ width: 100, height: 100, border: "1.5px dashed #ddd", borderRadius: 8, display: "flex", alignItems: "center", justifyContent: "center", fontSize: 36 }}>🔒</div>
          <p style={{ fontSize: 14, color: "#555", margin: 0, textAlign: "center" }}>아직 수집한 펫이 없어요.</p>
          <p style={{ fontSize: 12, color: "#aaa", margin: 0, textAlign: "center" }}>챌린지를 달성하면 새로운 펫을 만날 수 있어요.</p>
        </div>
      ) : (
        <div style={{ display: "grid", gridTemplateColumns: "repeat(4, 1fr)", gap: 12, marginBottom: 20 }}>
          {currentList.map(pet => (
            <div key={pet.id} style={{ background: "#fff", border: "1px solid #e0e0e0", borderRadius: 10, padding: 14,
              textAlign: "center", opacity: pet.unlocked ? 1 : 0.6 }}>
              {pet.unlocked ? (
                <div style={{ width: "100%", height: 70, background: "#f5f5f5", borderRadius: 8,
                  display: "flex", alignItems: "center", justifyContent: "center",
                  marginBottom: 10, fontSize: 36 }}>
                  {PET_EMOJI[pet.name] || "🐾"}
                </div>
              ) : (
                <div style={{ width: "100%", height: 70, background: "#f0f0f0", border: "1.5px dashed #ddd",
                  borderRadius: 8, display: "flex", alignItems: "center", justifyContent: "center",
                  marginBottom: 10, fontSize: 24 }}>🔒</div>
              )}
              <p style={{ fontSize: 12, fontWeight: 600, margin: "0 0 6px" }}>{pet.name}</p>
              {pet.unlocked ? (
                <>
                  <p style={{ fontSize: 10, color: "#888", margin: "0 0 4px" }}>호감도 {pet.affection}/{pet.max_affection}</p>
                  <div style={{ height: 6, background: "#f0f0f0", borderRadius: 3, overflow: "hidden" }}>
                    <div style={{ width: `${(pet.affection / pet.max_affection) * 100}%`, height: "100%", background: "#1a1a1a", borderRadius: 3 }} />
                  </div>
                </>
              ) : (
                <p style={{ fontSize: 10, color: "#aaa", margin: 0 }}>잠금 해제 조건</p>
              )}
            </div>
          ))}
        </div>
      )}

      {/* 잠금 해제 조건 */}
      <div style={{ background: "#fff", border: "1px solid #e0e0e0", borderRadius: 10, padding: 16 }}>
        <h3 style={{ fontSize: 13, fontWeight: 600, margin: "0 0 12px" }}>잠금 해제 조건</h3>
        <p style={{ fontSize: 13, fontWeight: 500, color: "#1a1a1a", margin: "0 0 10px" }}>
          챌린지를 연속으로 달성하면 새로운 펫을 잠금 해제할 수 있어요.
        </p>
        <div style={{ display: "flex", flexDirection: "column", gap: 6 }}>
          {UNLOCK_CONDITIONS.map(cond => (
            <p key={cond.days} style={{ fontSize: 12, color: "#888", margin: 0 }}>• {cond.label}</p>
          ))}
        </div>
      </div>
    </div>
  );
}
