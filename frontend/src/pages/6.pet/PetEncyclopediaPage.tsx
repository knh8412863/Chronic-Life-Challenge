import { useEffect, useState } from "react";

import type { AppRoute } from "../../App";
import { getStoredAccessToken } from "../../api/auth";
import { getMyVirtualPet, getPetCatalog, type PetCatalog, type PetCatalogItem, type PetType } from "../../api/pets";
import { ErrorState } from "../../components/common/ErrorState";
import { LoadingState } from "../../components/common/LoadingState";
import { getPetImage, PET_META, PET_TYPES } from "../../utils/petAssets";

interface PetEncyclopediaPageProps {
  onNavigate: (route: AppRoute) => void;
}

const emptyCatalog: PetCatalog = {
  summary: { total_count: 0, unlocked_count: 0, completion_rate: 0 },
  items: [],
};

function PetCard({ pet }: { pet: PetCatalogItem }) {
  const meta = PET_META[pet.pet_type];
  const image = getPetImage(pet.pet_type, "STAGE_1");

  return (
    <div style={{ background: "#fff", border: "1px solid #e0e0e0", borderRadius: 10, padding: 14,
      textAlign: "center", opacity: pet.is_unlocked ? 1 : 0.6 }}>
      {pet.is_unlocked ? (
        <div style={{ width: "100%", height: 70, background: "#f5f5f5", borderRadius: 8,
          display: "flex", alignItems: "center", justifyContent: "center",
          marginBottom: 10, fontSize: 36 }}>
          {image ? (
            <img src={image} alt={`${meta.label} 1단계`} style={{ maxWidth: "90%", maxHeight: "90%", objectFit: "contain" }} />
          ) : meta.emoji}
        </div>
      ) : (
        <div style={{ width: "100%", height: 70, background: "#f0f0f0", border: "1.5px dashed #ddd",
          borderRadius: 8, display: "flex", alignItems: "center", justifyContent: "center",
          marginBottom: 10, fontSize: 24 }}>🔒</div>
      )}
      <p style={{ fontSize: 12, fontWeight: 600, margin: "0 0 6px" }}>{pet.display_name}</p>
      {pet.is_unlocked ? (
        <>
          <p style={{ fontSize: 10, color: "#888", margin: "0 0 4px" }}>
            호감도 {pet.affinity_score ?? 0}/5
          </p>
          <div style={{ height: 6, background: "#f0f0f0", borderRadius: 3, overflow: "hidden" }}>
            <div style={{ width: `${((pet.affinity_score ?? 0) / 5) * 100}%`, height: "100%", background: "#1a1a1a", borderRadius: 3 }} />
          </div>
        </>
      ) : (
        <p style={{ fontSize: 10, color: "#aaa", margin: 0 }}>{pet.unlock_condition}</p>
      )}
    </div>
  );
}

export function PetEncyclopediaPage({ onNavigate }: PetEncyclopediaPageProps) {
  const [activeTab, setActiveTab] = useState<PetType | null>(null);
  const [catalog, setCatalog] = useState<PetCatalog>(emptyCatalog);
  const [isLoading, setIsLoading] = useState(true);
  const [hasApiError, setHasApiError] = useState(false);

  useEffect(() => {
    const token = getStoredAccessToken();
    getMyVirtualPet(token)
      .then((response) => setActiveTab(response.data.pet?.pet_type ?? "DOG"))
      .catch(() => setActiveTab("DOG"));
  }, []);

  useEffect(() => {
    if (!activeTab) return;
    const token = getStoredAccessToken();
    setIsLoading(true);
    getPetCatalog(activeTab, token)
      .then((response) => {
        setCatalog(response.data);
        setHasApiError(false);
      })
      .catch(() => setHasApiError(true))
      .finally(() => setIsLoading(false));
  }, [activeTab]);

  if (isLoading) return <LoadingState message="펫 도감을 불러오는 중입니다." />;

  if (hasApiError) {
    return (
      <div className="page-container">
        <ErrorState title="펫 도감을 불러오지 못했습니다." description="로그인 상태와 서버 연결을 확인해 주세요." />
      </div>
    );
  }

  return (
    <div className="page-container">
      <div style={{ display: "flex", alignItems: "center", gap: 12, marginBottom: 20 }}>
        <button onClick={() => onNavigate("/pet")}
          style={{ background: "none", border: "none", cursor: "pointer", fontSize: 20, color: "#555" }}>←</button>
        <h1 className="page-title" style={{ margin: 0 }}>펫 도감</h1>
      </div>

      <div style={{ display: "flex", borderBottom: "2px solid #e0e0e0", marginBottom: 16 }}>
        {PET_TYPES.map((tab) => (
          <button key={tab} onClick={() => setActiveTab(tab)}
            style={{ padding: "10px 20px", border: "none", background: "none", cursor: "pointer",
              fontSize: 13, fontWeight: activeTab === tab ? 700 : 400,
              color: activeTab === tab ? "#1a1a1a" : "#aaa",
              borderBottom: activeTab === tab ? "2px solid #1a1a1a" : "2px solid transparent",
              marginBottom: -2 }}>
            {PET_META[tab].emoji} {PET_META[tab].label}
          </button>
        ))}
      </div>

      {catalog.items.length === 0 ? (
        <div style={{ display: "flex", flexDirection: "column", alignItems: "center", gap: 12, padding: "40px 20px" }}>
          <div style={{ width: 100, height: 100, border: "1.5px dashed #ddd", borderRadius: 8, display: "flex", alignItems: "center", justifyContent: "center", fontSize: 36 }}>🔒</div>
          <p style={{ fontSize: 14, color: "#555", margin: 0, textAlign: "center" }}>도감 항목이 없습니다.</p>
        </div>
      ) : (
        <div style={{ display: "grid", gridTemplateColumns: "repeat(4, 1fr)", gap: 12, marginBottom: 20 }}>
          {catalog.items.map((pet) => <PetCard key={pet.catalog_id} pet={pet} />)}
        </div>
      )}

      <div style={{ background: "#fff", border: "1px solid #e0e0e0", borderRadius: 10, padding: 16 }}>
        <h3 style={{ fontSize: 13, fontWeight: 600, margin: "0 0 12px" }}>잠금 해제 조건</h3>
        <p style={{ fontSize: 13, fontWeight: 500, color: "#1a1a1a", margin: "0 0 10px" }}>
          챌린지를 연속으로 달성하면 새로운 펫을 잠금 해제할 수 있어요.
        </p>
        <div style={{ display: "flex", flexDirection: "column", gap: 6 }}>
          <p style={{ fontSize: 12, color: "#888", margin: 0 }}>• 기본 제공</p>
          <p style={{ fontSize: 12, color: "#888", margin: 0 }}>• 챌린지 3일 연속 달성</p>
          <p style={{ fontSize: 12, color: "#888", margin: 0 }}>• 챌린지 7일 연속 달성</p>
          <p style={{ fontSize: 12, color: "#888", margin: 0 }}>• 챌린지 30일 연속 달성</p>
        </div>
      </div>
    </div>
  );
}
