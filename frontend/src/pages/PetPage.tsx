import { useState } from "react";
import type { AppRoute } from "../App";

interface PetPageProps {
  onNavigate: (route: AppRoute) => void;
}

// 더미 데이터 — API 연결 시 교체
// GET /api/v1/virtual-pets → has_pet, pet 정보, today_tasks, recent_activities 한 번에 조회
const DUMMY_PET = {
  pet_id: 1,
  pet_name: "쿠키",
  pet_type: "DOG" as "DOG" | "CAT",
  level: 5,
  experience_points: 450,
  next_level_xp: 1000,
  growth_stage: "STAGE_2" as "STAGE_1" | "STAGE_2" | "STAGE_3", // STAGE_1/STAGE_2/STAGE_3
  health_score: 75,
  happiness_score: 60,
};

const DUMMY_TASKS = [
  { task_id: 1, title: "혈압 측정", xp: 30, completed: true },
  { task_id: 2, title: "운동 30분 이상", xp: 50, completed: true },
  { task_id: 3, title: "물 2L 마시기", xp: 20, completed: false },
  { task_id: 4, title: "건강 일지 작성", xp: 40, completed: false },
];

const DUMMY_ACTIVITIES = [
  { title: "혈압 측정 완료", xp: 30, date: "오늘 08:30" },
  { title: "운동 기록 완료", xp: 50, date: "오늘 10:15" },
  { title: "건강 목표 달성", xp: 100, date: "어제" },
  { title: "출석 보너스", xp: 10, date: "어제" },
];

function ProgressBar({ value, color = "#888" }: { value: number; color?: string }) {
  return (
    <div style={{ flex: 1, height: 8, background: "#f0f0f0", borderRadius: 4, overflow: "hidden" }}>
      <div style={{ width: `${value}%`, height: "100%", background: color, borderRadius: 4 }} />
    </div>
  );
}

export function PetPage({ onNavigate }: PetPageProps) {
  const [hasPet] = useState(true); // TODO: API 연결 시 GET /api/v1/virtual-pets 응답의 has_pet으로 교체
  const [isEditingName, setIsEditingName] = useState(false);
  const [petName, setPetName] = useState(DUMMY_PET.pet_name);
  const [editName, setEditName] = useState(DUMMY_PET.pet_name);
  const [nameError, setNameError] = useState("");

  const handleSaveName = () => {
    if (!editName.trim()) { setNameError("이름을 입력해주세요."); return; }
    if (editName.length > 50) { setNameError("50자 이내로 입력해주세요."); return; }
    // TODO: API 연결 — PATCH /api/v1/virtual-pets/me/name
    // body: { pet_name: editName }
    // 응답: 200 { data: { pet_id, pet_name } }
    // 실패: 404 RESOURCE_NOT_FOUND / 422 VALIDATION_ERROR (1~50자)
    setPetName(editName);
    setIsEditingName(false);
    setNameError("");
  };

  // ── 빈 상태 (펫 미보유) ──
  if (!hasPet) {
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

  // ── 내 펫 현황 ──
  return (
    <div className="page-container">
      <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: 20 }}>
        <h1 className="page-title" style={{ margin: 0 }}>내 펫 현황</h1>
        <button onClick={() => onNavigate("/pet/encyclopedia")}
          style={{ padding: "8px 14px", border: "1.5px solid #ddd", borderRadius: 6, background: "#fff", fontSize: 12, cursor: "pointer" }}>
          📖 펫 도감
        </button>
      </div>

      {/* 통계 요약 */}
      <div style={{ display: "grid", gridTemplateColumns: "repeat(4, 1fr)", gap: 12, marginBottom: 20 }}>
        {[
          { label: "레벨", val: DUMMY_PET.level, unit: "Lv", bg: "#e8f5e9", color: "#2e7d32", border: "#a5d6a7" },
          { label: "경험치", val: DUMMY_PET.experience_points, unit: "XP", bg: "#fff8e1", color: "#f57f17", border: "#ffe082" },
          { label: "건강도", val: DUMMY_PET.health_score, unit: "%", bg: "#e3f2fd", color: "#1565c0", border: "#90caf9" },
          { label: "행복도", val: DUMMY_PET.happiness_score, unit: "%", bg: "#fce4ec", color: "#c2185b", border: "#f48fb1" },
        ].map(item => (
          <div key={item.label} style={{ padding: "12px 14px", background: item.bg, border: `1.5px solid ${item.border}`, borderRadius: 8, textAlign: "center" }}>
            <div style={{ fontSize: 10, color: item.color, marginBottom: 4 }}>{item.label}</div>
            <div style={{ fontSize: 20, fontWeight: 700, color: item.color }}>
              {item.val}<span style={{ fontSize: 10, fontWeight: 400, color: "#aaa" }}>{item.unit}</span>
            </div>
          </div>
        ))}
      </div>

      <div style={{ display: "grid", gridTemplateColumns: "1fr 2fr", gap: 14 }}>
        {/* 펫 카드 */}
        <div style={{ background: "#fff", border: "1px solid #e0e0e0", borderRadius: 10, padding: 20, textAlign: "center" }}>
          <div style={{ width: "100%", height: 120, background: "#f5f5f5", borderRadius: 8, display: "flex", alignItems: "center", justifyContent: "center", marginBottom: 14, fontSize: 64 }}>
            {DUMMY_PET.pet_type === "DOG" ? "🐶" : "🐱"}
          </div>

          {/* 이름 편집 */}
          {isEditingName ? (
            <div style={{ marginBottom: 6 }}>
              <input value={editName} onChange={e => { setEditName(e.target.value); setNameError(""); }}
                maxLength={50}
                style={{ width: "100%", height: 34, border: "1.5px solid #1a1a1a", borderRadius: 6, padding: "0 10px", fontSize: 14, fontWeight: 600, textAlign: "center", outline: "none", boxSizing: "border-box" }} />
              <div style={{ display: "flex", justifyContent: "flex-end", marginTop: 2 }}>
                <span style={{ fontSize: 10, color: "#aaa" }}>{editName.length} / 50</span>
              </div>
              {nameError && <p style={{ fontSize: 11, color: "#E24B4A", margin: "4px 0" }}>{nameError}</p>}
              <div style={{ display: "flex", gap: 8, marginTop: 8 }}>
                <button onClick={handleSaveName}
                  style={{ flex: 1, height: 32, border: "none", borderRadius: 6, background: "#1a1a1a", color: "#fff", fontSize: 12, cursor: "pointer" }}>저장</button>
                <button onClick={() => { setIsEditingName(false); setEditName(petName); setNameError(""); }}
                  style={{ flex: 1, height: 32, border: "1.5px solid #ddd", borderRadius: 6, background: "#fff", fontSize: 12, cursor: "pointer" }}>취소</button>
              </div>
            </div>
          ) : (
            <div style={{ display: "flex", alignItems: "center", justifyContent: "center", gap: 8, marginBottom: 6 }}>
              <span style={{ fontSize: 16, fontWeight: 700 }}>{petName}</span>
              <span style={{ padding: "2px 8px", background: "#f0f0f0", borderRadius: 12, fontSize: 11 }}>Lv.{DUMMY_PET.level}</span>
            </div>
          )}

          <p style={{ fontSize: 12, color: "#888", margin: "0 0 14px" }}>
            {DUMMY_PET.pet_type === "DOG" ? "강아지형" : "고양이형"} · {
              DUMMY_PET.growth_stage === "STAGE_1" ? "아기" :
              DUMMY_PET.growth_stage === "STAGE_2" ? "성장기" : "성체"
            }
          </p>

          <hr style={{ border: "none", borderTop: "1px solid #e0e0e0", margin: "0 0 14px" }} />

          <div style={{ display: "flex", flexDirection: "column", gap: 10 }}>
            {[
              { label: "건강", val: DUMMY_PET.health_score, color: "#2e7d32" },
              { label: "행복", val: DUMMY_PET.happiness_score, color: "#1565c0" },
            ].map(item => (
              <div key={item.label} style={{ display: "flex", alignItems: "center", gap: 8 }}>
                <span style={{ fontSize: 11, color: "#888", width: 36, textAlign: "left" }}>{item.label}</span>
                <ProgressBar value={item.val} color={item.color} />
                <span style={{ fontSize: 11, color: "#888", width: 30, textAlign: "right" }}>{item.val}%</span>
              </div>
            ))}
            <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
              <span style={{ fontSize: 11, color: "#888", width: 36, textAlign: "left" }}>경험치</span>
              <ProgressBar value={(DUMMY_PET.experience_points / DUMMY_PET.next_level_xp) * 100} color="#888" />
              <span style={{ fontSize: 10, color: "#aaa", whiteSpace: "nowrap" }}>
                {DUMMY_PET.experience_points}/{DUMMY_PET.next_level_xp}
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

        {/* 오른쪽 패널 */}
        <div style={{ display: "flex", flexDirection: "column", gap: 14 }}>
          {/* 오늘의 보상 과제 */}
          <div style={{ background: "#fff", border: "1px solid #e0e0e0", borderRadius: 10, padding: 16 }}>
            <h3 style={{ fontSize: 13, fontWeight: 600, margin: "0 0 12px" }}>오늘의 보상 과제</h3>
            <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
              {DUMMY_TASKS.map(task => (
                <div key={task.task_id} style={{ display: "flex", alignItems: "center", gap: 10, padding: "8px 10px",
                  background: task.completed ? "#f0f4f0" : "#fafafa",
                  border: "1.5px solid #e0e0e0", borderRadius: 8 }}>
                  <div style={{ width: 20, height: 20, borderRadius: "50%",
                    background: task.completed ? "#2e7d32" : "#f0f0f0",
                    border: "1.5px solid #ddd",
                    display: "flex", alignItems: "center", justifyContent: "center",
                    fontSize: 10, color: "#fff", flexShrink: 0 }}>
                    {task.completed ? "✓" : ""}
                  </div>
                  <span style={{ fontSize: 12, color: task.completed ? "#555" : "#1a1a1a", textDecoration: task.completed ? "line-through" : "none", flex: 1 }}>
                    {task.title}
                  </span>
                  <span style={{ padding: "2px 8px", background: "#f0f0f0", border: "1px solid #ddd", borderRadius: 12, fontSize: 11 }}>
                    {task.xp} XP
                  </span>
                </div>
              ))}
            </div>
          </div>

          {/* 최근 활동 기록 */}
          <div style={{ background: "#fff", border: "1px solid #e0e0e0", borderRadius: 10, padding: 16 }}>
            <h3 style={{ fontSize: 13, fontWeight: 600, margin: "0 0 12px" }}>최근 활동 기록</h3>
            <div style={{ display: "flex", flexDirection: "column" }}>
              {DUMMY_ACTIVITIES.map((activity, i) => (
                <div key={i} style={{ display: "flex", alignItems: "center", gap: 10, padding: "8px 0",
                  borderBottom: i < DUMMY_ACTIVITIES.length - 1 ? "1px solid #f0f0f0" : "none" }}>
                  <div style={{ width: 32, height: 32, borderRadius: "50%", background: "#f5f5f5",
                    display: "flex", alignItems: "center", justifyContent: "center", fontSize: 16, flexShrink: 0 }}>⭐</div>
                  <span style={{ fontSize: 12, flex: 1 }}>{activity.title}</span>
                  <div style={{ textAlign: "right" }}>
                    <div style={{ fontSize: 12, fontWeight: 700, color: "#2e7d32" }}>+{activity.xp} XP</div>
                    <div style={{ fontSize: 10, color: "#aaa" }}>{activity.date}</div>
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
