import { useEffect, useState } from "react";

import type { AppRoute } from "../App";
import { getStoredAccessToken } from "../api/auth";
import {
  claimVirtualPetRewards,
  getMyVirtualPet,
  updateVirtualPetName,
  type PetRecentActivity,
  type PetRewardTask,
  type VirtualPet,
} from "../api/pets";
import { ErrorState } from "../components/common/ErrorState";
import { LoadingState } from "../components/common/LoadingState";

interface PetPageProps {
  onNavigate: (route: AppRoute) => void;
}

function ProgressBar({ value, color = "#888" }: { value: number; color?: string }) {
  return (
    <div style={{ flex: 1, height: 8, background: "#f0f0f0", borderRadius: 4, overflow: "hidden" }}>
      <div style={{ width: `${Math.min(value, 100)}%`, height: "100%", background: color, borderRadius: 4 }} />
    </div>
  );
}

function growthStageLabel(stage: string) {
  if (stage === "STAGE_1") return "아기";
  if (stage === "STAGE_2") return "성장기";
  return "성체";
}

function formatActivityTime(value: string) {
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;
  return date.toLocaleString("ko-KR", { month: "2-digit", day: "2-digit", hour: "2-digit", minute: "2-digit" });
}

export function PetPage({ onNavigate }: PetPageProps) {
  const [pet, setPet] = useState<VirtualPet | null>(null);
  const [tasks, setTasks] = useState<PetRewardTask[]>([]);
  const [activities, setActivities] = useState<PetRecentActivity[]>([]);
  const [hasPet, setHasPet] = useState(false);
  const [isLoading, setIsLoading] = useState(true);
  const [hasApiError, setHasApiError] = useState(false);
  const [isEditingName, setIsEditingName] = useState(false);
  const [editName, setEditName] = useState("");
  const [nameError, setNameError] = useState("");
  const [isSavingName, setIsSavingName] = useState(false);
  const [isClaiming, setIsClaiming] = useState(false);

  function loadPet() {
    const token = getStoredAccessToken();
    setIsLoading(true);
    getMyVirtualPet(token)
      .then((response) => {
        setHasPet(response.data.has_pet);
        setPet(response.data.pet);
        setTasks(response.data.today_tasks);
        setActivities(response.data.recent_activities);
        setEditName(response.data.pet?.pet_name ?? "");
        setHasApiError(false);
      })
      .catch(() => setHasApiError(true))
      .finally(() => setIsLoading(false));
  }

  useEffect(() => {
    loadPet();
  }, []);

  async function handleSaveName() {
    const nextName = editName.trim();
    if (!nextName) {
      setNameError("이름을 입력해주세요.");
      return;
    }
    if (nextName.length > 50) {
      setNameError("50자 이내로 입력해주세요.");
      return;
    }

    const token = getStoredAccessToken();
    setIsSavingName(true);
    try {
      const response = await updateVirtualPetName(nextName, token);
      setPet((prev) => (prev ? { ...prev, pet_name: response.data.pet_name } : prev));
      setEditName(response.data.pet_name);
      setIsEditingName(false);
      setNameError("");
    } catch {
      setNameError("이름 변경에 실패했습니다.");
    } finally {
      setIsSavingName(false);
    }
  }

  async function handleClaimRewards() {
    const token = getStoredAccessToken();
    setIsClaiming(true);
    try {
      const response = await claimVirtualPetRewards(token);
      if (response.data.claimed_task_count === 0) {
        alert("수령할 보상이 없습니다.");
      } else {
        alert(`${response.data.awarded_experience} XP를 받았습니다.`);
      }
      loadPet();
    } catch {
      alert("보상 수령에 실패했습니다.");
    } finally {
      setIsClaiming(false);
    }
  }

  if (isLoading) return <LoadingState message="내 펫 정보를 불러오는 중입니다." />;

  if (hasApiError) {
    return (
      <div className="page-container">
        <ErrorState title="펫 정보를 불러오지 못했습니다." description="로그인 상태와 서버 연결을 확인해 주세요." />
      </div>
    );
  }

  if (!hasPet || !pet) {
    return (
      <div className="page-container">
        <h1 className="page-title">내 펫 현황</h1>
        <div style={{ display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center", padding: "80px 20px", gap: 20 }}>
          <div style={{ width: 200, height: 200, border: "2px dashed #ddd", borderRadius: 12, display: "flex", alignItems: "center", justifyContent: "center", fontSize: 64 }}>🐾</div>
          <h2 style={{ fontSize: 18, fontWeight: 600, color: "#1a1a1a", margin: 0 }}>아직 펫을 선택하지 않았어요.</h2>
          <p style={{ fontSize: 14, color: "#888", margin: 0, textAlign: "center" }}>펫을 선택하고 건강 여정을 함께 시작해보세요.</p>
          <button onClick={() => onNavigate("/pet/select")}
            style={{ padding: "12px 32px", border: "none", borderRadius: 8, background: "#1a1a1a", color: "#fff", fontSize: 14, fontWeight: 600, cursor: "pointer" }}>
            펫 선택하기
          </button>
        </div>
      </div>
    );
  }

  const hasClaimableTask = tasks.some((task) => task.is_completed);

  return (
    <div className="page-container">
      <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: 20 }}>
        <h1 className="page-title" style={{ margin: 0 }}>내 펫 현황</h1>
        <button onClick={() => onNavigate("/pet/encyclopedia")}
          style={{ padding: "8px 14px", border: "1.5px solid #ddd", borderRadius: 6, background: "#fff", fontSize: 12, cursor: "pointer" }}>
          📖 펫 도감
        </button>
      </div>

      <div style={{ display: "grid", gridTemplateColumns: "repeat(4, 1fr)", gap: 12, marginBottom: 20 }}>
        {[
          { label: "레벨", val: pet.level, unit: "Lv", bg: "#e8f5e9", color: "#2e7d32", border: "#a5d6a7" },
          { label: "경험치", val: pet.experience, unit: "XP", bg: "#fff8e1", color: "#f57f17", border: "#ffe082" },
          { label: "건강도", val: pet.health_percent, unit: "%", bg: "#e3f2fd", color: "#1565c0", border: "#90caf9" },
          { label: "행복도", val: pet.happiness_percent, unit: "%", bg: "#fce4ec", color: "#c2185b", border: "#f48fb1" },
        ].map((item) => (
          <div key={item.label} style={{ padding: "12px 14px", background: item.bg, border: `1.5px solid ${item.border}`, borderRadius: 8, textAlign: "center" }}>
            <div style={{ fontSize: 10, color: item.color, marginBottom: 4 }}>{item.label}</div>
            <div style={{ fontSize: 20, fontWeight: 700, color: item.color }}>
              {item.val}<span style={{ fontSize: 10, fontWeight: 400, color: "#aaa" }}>{item.unit}</span>
            </div>
          </div>
        ))}
      </div>

      <div style={{ display: "grid", gridTemplateColumns: "1fr 2fr", gap: 14 }}>
        <div style={{ background: "#fff", border: "1px solid #e0e0e0", borderRadius: 10, padding: 20, textAlign: "center" }}>
          <div style={{ width: "100%", height: 120, background: "#f5f5f5", borderRadius: 8, display: "flex", alignItems: "center", justifyContent: "center", marginBottom: 14, fontSize: 64 }}>
            {pet.pet_type === "DOG" ? "🐶" : "🐱"}
          </div>

          {isEditingName ? (
            <div style={{ marginBottom: 6 }}>
              <input value={editName} onChange={(e) => { setEditName(e.target.value); setNameError(""); }}
                maxLength={50}
                style={{ width: "100%", height: 34, border: "1.5px solid #1a1a1a", borderRadius: 6, padding: "0 10px", fontSize: 14, fontWeight: 600, textAlign: "center", outline: "none", boxSizing: "border-box" }} />
              <div style={{ display: "flex", justifyContent: "flex-end", marginTop: 2 }}>
                <span style={{ fontSize: 10, color: "#aaa" }}>{editName.length} / 50</span>
              </div>
              {nameError && <p style={{ fontSize: 11, color: "#E24B4A", margin: "4px 0" }}>{nameError}</p>}
              <div style={{ display: "flex", gap: 8, marginTop: 8 }}>
                <button onClick={handleSaveName} disabled={isSavingName}
                  style={{ flex: 1, height: 32, border: "none", borderRadius: 6, background: "#1a1a1a", color: "#fff", fontSize: 12, cursor: "pointer" }}>
                  {isSavingName ? "저장 중..." : "저장"}
                </button>
                <button onClick={() => { setIsEditingName(false); setEditName(pet.pet_name); setNameError(""); }}
                  style={{ flex: 1, height: 32, border: "1.5px solid #ddd", borderRadius: 6, background: "#fff", fontSize: 12, cursor: "pointer" }}>취소</button>
              </div>
            </div>
          ) : (
            <div style={{ display: "flex", alignItems: "center", justifyContent: "center", gap: 8, marginBottom: 6 }}>
              <span style={{ fontSize: 16, fontWeight: 700 }}>{pet.pet_name}</span>
              <span style={{ padding: "2px 8px", background: "#f0f0f0", borderRadius: 12, fontSize: 11 }}>Lv.{pet.level}</span>
            </div>
          )}

          <p style={{ fontSize: 12, color: "#888", margin: "0 0 14px" }}>
            {pet.pet_type === "DOG" ? "강아지형" : "고양이형"} · {growthStageLabel(pet.growth_stage)}
          </p>

          <hr style={{ border: "none", borderTop: "1px solid #e0e0e0", margin: "0 0 14px" }} />

          <div style={{ display: "flex", flexDirection: "column", gap: 10 }}>
            {[
              { label: "건강", val: pet.health_percent, color: "#2e7d32" },
              { label: "행복", val: pet.happiness_percent, color: "#1565c0" },
            ].map((item) => (
              <div key={item.label} style={{ display: "flex", alignItems: "center", gap: 8 }}>
                <span style={{ fontSize: 11, color: "#888", width: 36, textAlign: "left" }}>{item.label}</span>
                <ProgressBar value={item.val} color={item.color} />
                <span style={{ fontSize: 11, color: "#888", width: 30, textAlign: "right" }}>{item.val}%</span>
              </div>
            ))}
            <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
              <span style={{ fontSize: 11, color: "#888", width: 36, textAlign: "left" }}>경험치</span>
              <ProgressBar value={(pet.experience / pet.next_level_experience) * 100} color="#888" />
              <span style={{ fontSize: 10, color: "#aaa", whiteSpace: "nowrap" }}>
                {pet.experience}/{pet.next_level_experience}
              </span>
            </div>
          </div>

          {!isEditingName && (
            <button onClick={() => setIsEditingName(true)}
              style={{ width: "100%", marginTop: 14, height: 34, border: "1.5px solid #ddd", borderRadius: 6, background: "#fff", fontSize: 12, cursor: "pointer" }}>
              이름 변경
            </button>
          )}
        </div>

        <div style={{ display: "flex", flexDirection: "column", gap: 14 }}>
          <div style={{ background: "#fff", border: "1px solid #e0e0e0", borderRadius: 10, padding: 16 }}>
            <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: 12 }}>
              <h3 style={{ fontSize: 13, fontWeight: 600, margin: 0 }}>오늘의 보상 과제</h3>
              <button
                type="button"
                onClick={handleClaimRewards}
                disabled={!hasClaimableTask || isClaiming}
                style={{ padding: "6px 12px", border: "none", borderRadius: 6, background: hasClaimableTask ? "#1a1a1a" : "#ddd", color: "#fff", fontSize: 11, cursor: hasClaimableTask ? "pointer" : "not-allowed" }}
              >
                {isClaiming ? "수령 중..." : "보상 받기"}
              </button>
            </div>
            <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
              {tasks.map((task) => (
                <div key={task.task_type} style={{ display: "flex", alignItems: "center", gap: 10, padding: "8px 10px",
                  background: task.is_completed ? "#f0f4f0" : "#fafafa",
                  border: "1.5px solid #e0e0e0", borderRadius: 8 }}>
                  <div style={{ width: 20, height: 20, borderRadius: "50%",
                    background: task.is_completed ? "#2e7d32" : "#f0f0f0",
                    border: "1.5px solid #ddd",
                    display: "flex", alignItems: "center", justifyContent: "center",
                    fontSize: 10, color: "#fff", flexShrink: 0 }}>
                    {task.is_completed ? "✓" : ""}
                  </div>
                  <span style={{ fontSize: 12, color: task.is_completed ? "#555" : "#1a1a1a", textDecoration: task.is_completed ? "line-through" : "none", flex: 1 }}>
                    {task.title}
                  </span>
                  <span style={{ padding: "2px 8px", background: "#f0f0f0", border: "1px solid #ddd", borderRadius: 12, fontSize: 11 }}>
                    {task.reward_experience} XP
                  </span>
                </div>
              ))}
            </div>
          </div>

          <div style={{ background: "#fff", border: "1px solid #e0e0e0", borderRadius: 10, padding: 16 }}>
            <h3 style={{ fontSize: 13, fontWeight: 600, margin: "0 0 12px" }}>최근 활동 기록</h3>
            <div style={{ display: "flex", flexDirection: "column" }}>
              {activities.length === 0 ? (
                <p style={{ fontSize: 12, color: "#888", margin: 0 }}>아직 활동 기록이 없습니다.</p>
              ) : activities.map((activity, index) => (
                <div key={`${activity.activity_type}-${activity.created_at}-${index}`} style={{ display: "flex", alignItems: "center", gap: 10, padding: "8px 0",
                  borderBottom: index < activities.length - 1 ? "1px solid #f0f0f0" : "none" }}>
                  <div style={{ width: 32, height: 32, borderRadius: "50%", background: "#f5f5f5",
                    display: "flex", alignItems: "center", justifyContent: "center", fontSize: 16, flexShrink: 0 }}>⭐</div>
                  <span style={{ fontSize: 12, flex: 1 }}>{activity.description}</span>
                  <div style={{ textAlign: "right" }}>
                    <div style={{ fontSize: 12, fontWeight: 700, color: "#2e7d32" }}>+{activity.experience_delta} XP</div>
                    <div style={{ fontSize: 10, color: "#aaa" }}>{formatActivityTime(activity.created_at)}</div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
