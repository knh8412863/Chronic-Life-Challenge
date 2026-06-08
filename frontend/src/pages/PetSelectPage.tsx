import { useState } from "react";
import type { AppRoute } from "../App";
import { getStoredAccessToken } from "../api/auth";
import { createVirtualPet } from "../api/pets";

interface PetSelectPageProps {
  onNavigate: (route: AppRoute) => void;
}

type PetType = "DOG" | "CAT";
type Step = "select" | "name" | "confirm";

const PET_INFO = {
  DOG: {
    emoji: "🐶",
    label: "강아지",
    desc: "충성스럽고 활발한 동반자",
    features: ["운동 활동 보너스 +20%", "일일 활동 점수 강화", "산책 챌린지 특화"],
  },
  CAT: {
    emoji: "🐱",
    label: "고양이",
    desc: "독립적이고 차분한 동반자",
    features: ["건강 일지 보너스 +20%", "일상 기록 습관 강화", "생활습관 챌린지 특화"],
  },
};

export function PetSelectPage({ onNavigate }: PetSelectPageProps) {
  const [step, setStep] = useState<Step>("select");
  const [selectedPet, setSelectedPet] = useState<PetType | null>(null);
  const [petName, setPetName] = useState("");
  const [nameError, setNameError] = useState("");
  const [isSaving, setIsSaving] = useState(false);

  const handleSelectPet = (type: PetType) => {
    setSelectedPet(type);
    setStep("name");
  };

  const handleConfirmName = () => {
    if (!petName.trim()) { setNameError("이름을 입력해주세요."); return; }
    if (petName.length > 50) { setNameError("50자 이내로 입력해주세요."); return; }
    setNameError("");
    setStep("confirm");
  };

  const handleFinalConfirm = async () => {
    if (!selectedPet) return;
    const token = getStoredAccessToken();
    setIsSaving(true);
    try {
      await createVirtualPet({ pet_type: selectedPet, pet_name: petName.trim() }, token);
      onNavigate("/pet");
    } catch {
      alert("펫 선택에 실패했습니다. 이미 선택한 펫이 있거나 입력값을 확인해 주세요.");
    } finally {
      setIsSaving(false);
    }
  };

  return (
    <div className="page-container">
      <h1 className="page-title">펫 선택</h1>

      {/* 안내 카드 */}
      <div style={{ background: "#fff", border: "1px solid #e0e0e0", borderRadius: 10, padding: 20, textAlign: "center", marginBottom: 20 }}>
        <h2 style={{ fontSize: 16, fontWeight: 600, margin: "0 0 8px" }}>어떤 펫과 함께 건강 여정을 시작하시겠어요?</h2>
        <p style={{ fontSize: 12, color: "#888", margin: 0 }}>펫을 선택하면 건강 활동을 통해 함께 성장할 수 있습니다</p>
      </div>

      {/* 펫 선택 카드 */}
      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 20, marginBottom: 20 }}>
        {(["DOG", "CAT"] as PetType[]).map(type => {
          const info = PET_INFO[type];
          const isSelected = selectedPet === type;
          const isOther = selectedPet !== null && selectedPet !== type;

          return (
            <div key={type} style={{ background: "#fff", border: `2px solid ${isSelected ? "#1a1a1a" : "#e0e0e0"}`,
              borderRadius: 10, padding: 24, textAlign: "center", opacity: isOther ? 0.45 : 1,
              transition: "all 0.2s" }}>
              <div style={{ width: "100%", height: 160, background: "#f5f5f5", borderRadius: 12,
                display: "flex", alignItems: "center", justifyContent: "center",
                marginBottom: 16, fontSize: 80 }}>
                {info.emoji}
              </div>
              <h3 style={{ fontSize: 17, fontWeight: 700, margin: "0 0 8px" }}>{info.label}</h3>
              <p style={{ fontSize: 12, color: "#888", margin: "0 0 16px" }}>{info.desc}</p>
              <hr style={{ border: "none", borderTop: "1px solid #e0e0e0", margin: "0 0 16px" }} />

              {/* 이름 입력 (선택된 펫에만 표시) */}
              {isSelected && step === "name" ? (
                <div style={{ textAlign: "left", marginBottom: 16 }}>
                  <label style={{ fontSize: 12, fontWeight: 600, display: "block", marginBottom: 6 }}>펫 이름</label>
                  <input value={petName} onChange={e => { setPetName(e.target.value); setNameError(""); }}
                    maxLength={50} placeholder="최대 50자"
                    style={{ width: "100%", height: 36, border: `1.5px solid ${nameError ? "#E24B4A" : "#1a1a1a"}`, borderRadius: 6, padding: "0 10px", fontSize: 12, outline: "none", boxSizing: "border-box" }} />
                  <div style={{ display: "flex", justifyContent: "space-between", marginTop: 4 }}>
                    <span style={{ fontSize: 11, color: "#E24B4A" }}>{nameError}</span>
                    <span style={{ fontSize: 10, color: "#aaa" }}>{petName.length} / 50</span>
                  </div>
                </div>
              ) : (
                <div style={{ display: "flex", flexDirection: "column", gap: 6, textAlign: "left", marginBottom: 16 }}>
                  {info.features.map(f => (
                    <p key={f} style={{ fontSize: 11, color: "#888", margin: 0 }}>• {f}</p>
                  ))}
                </div>
              )}

              <button
                onClick={() => isSelected && step === "name" ? handleConfirmName() : !isOther && handleSelectPet(type)}
                disabled={isOther}
                style={{ width: "100%", height: 40, border: "none", borderRadius: 8,
                  background: isSelected ? "#1a1a1a" : "#f5f5f5",
                  color: isSelected ? "#fff" : "#555",
                  fontSize: 13, fontWeight: 600, cursor: isOther ? "not-allowed" : "pointer" }}>
                {isSelected && step === "name" ? "확인" : `${info.label} 선택`}
              </button>
            </div>
          );
        })}
      </div>

      <div style={{ background: "#fafafa", border: "1px solid #e0e0e0", borderRadius: 8, padding: "12px 16px", textAlign: "center" }}>
        <p style={{ fontSize: 11, color: "#888", margin: 0 }}>💡 펫은 나중에 변경할 수 없으니 신중히 선택해주세요</p>
      </div>

      {/* 확인 모달 */}
      {step === "confirm" && selectedPet && (
        <div style={{ position: "fixed", inset: 0, background: "rgba(0,0,0,0.5)", display: "flex", alignItems: "center", justifyContent: "center", zIndex: 1000 }}>
          <div style={{ background: "#fff", border: "1.5px solid #e0e0e0", borderRadius: 12, padding: 28, maxWidth: 400, width: "90%", boxShadow: "0 4px 24px rgba(0,0,0,0.15)" }}>
            <h3 style={{ fontSize: 17, fontWeight: 700, textAlign: "center", margin: "0 0 12px" }}>펫 선택 확인</h3>
            <div style={{ textAlign: "center", marginBottom: 24, fontSize: 48 }}>
              {PET_INFO[selectedPet].emoji}
            </div>
            <p style={{ fontSize: 14, color: "#555", textAlign: "center", margin: "0 0 24px", lineHeight: 1.6 }}>
              <strong>{petName}</strong>을(를) 선택하시겠어요?<br />
              한 번 선택하면 변경할 수 없습니다.
            </p>
            <div style={{ display: "flex", gap: 10 }}>
              <button onClick={() => setStep("name")}
                style={{ flex: 1, height: 40, border: "1.5px solid #ddd", borderRadius: 8, background: "#fff", fontSize: 13, cursor: "pointer" }}>
                취소
              </button>
              <button onClick={handleFinalConfirm} disabled={isSaving}
                style={{ flex: 1, height: 40, border: "none", borderRadius: 8, background: "#1a1a1a", color: "#fff", fontSize: 13, fontWeight: 600, cursor: "pointer" }}>
                {isSaving ? "선택 중..." : "선택 완료"}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
