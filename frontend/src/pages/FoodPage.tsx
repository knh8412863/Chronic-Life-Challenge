import { useState } from "react";
import type { AppRoute } from "../App";

interface FoodPageProps {
  onNavigate: (route: AppRoute) => void;
}

type TabType = "list" | "input" | "detail";
type MealType = "BREAKFAST" | "LUNCH" | "DINNER" | "SNACK";
type PeriodType = "오늘" | "7일" | "30일" | "직접 선택";

const MEAL_LABELS: Record<MealType, { icon: string; label: string }> = {
  BREAKFAST: { icon: "🍚", label: "아침" },
  LUNCH:     { icon: "☀️", label: "점심" },
  DINNER:    { icon: "🌙", label: "저녁" },
  SNACK:     { icon: "🍪", label: "간식" },
};

// 더미 데이터 — API 연결 시 교체 (GET /api/v1/health/meals)
const DUMMY_MEALS = [
  { meal_log_id: 1, meal_type: "BREAKFAST" as MealType, food_name: "밥, 된장찌개, 계란말이", amount: "밥 한공기, 된장찌개 1그릇", meal_date: "오늘", time: "08:00", calories: 300, sodium_mg: 800, sugar_g: 15, fiber_g: 3, carbs_g: 45, protein_g: 12, fat_g: 8, memo: "", isToday: true },
  { meal_log_id: 2, meal_type: "LUNCH" as MealType, food_name: "돈까스, 소스, 샐러드", amount: "1인분", meal_date: "오늘", time: "12:00", calories: 650, sodium_mg: 1200, sugar_g: 20, fiber_g: 5, carbs_g: 80, protein_g: 25, fat_g: 22, memo: "", isToday: true },
  { meal_log_id: 3, meal_type: "DINNER" as MealType, food_name: "구이 생선, 나물, 된장국", amount: "1인분", meal_date: "어제", time: "18:45", calories: 550, sodium_mg: 1200, sugar_g: 10, fiber_g: 6, carbs_g: 60, protein_g: 30, fat_g: 15, memo: "", isToday: false },
  { meal_log_id: 4, meal_type: "SNACK" as MealType, food_name: "바나나, 우유", amount: "바나나 1개, 우유 1잔", meal_date: "2일 전", time: "15:30", calories: 200, sodium_mg: 100, sugar_g: 25, fiber_g: 2, carbs_g: 35, protein_g: 8, fat_g: 4, memo: "", isToday: false },
];

export function FoodPage({ onNavigate }: FoodPageProps) {
  const [tab, setTab] = useState<TabType>("list");
  const [selectedMeal, setSelectedMeal] = useState<typeof DUMMY_MEALS[0] | null>(null);
  const [period, setPeriod] = useState<PeriodType>("오늘");
  const [mealTypeFilter, setMealTypeFilter] = useState("전체");
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false);
  const [deleteTargetId, setDeleteTargetId] = useState<number | null>(null);
  const [meals, setMeals] = useState(DUMMY_MEALS);

  // 식단 직접 입력 상태
  const [inputMealType, setInputMealType] = useState<MealType>("BREAKFAST");
  const [foodItems, setFoodItems] = useState([{ food: "", amount: "" }]);
  const [inputDate, setInputDate] = useState(new Date().toISOString().split("T")[0]);
  const [inputTime, setInputTime] = useState("08:00");
  const [calories, setCalories] = useState("");
  const [carbs, setCarbs] = useState("");
  const [protein, setProtein] = useState("");
  const [fat, setFat] = useState("");
  const [sodium, setSodium] = useState("");
  const [sugar, setSugar] = useState("");
  const [fiberG, setFiberG] = useState("");
  const [memo, setMemo] = useState("");
  const [showValidation, setShowValidation] = useState(false);
  const [showSaveSuccess, setShowSaveSuccess] = useState(false);

  // 상세/수정 상태
  const [isEditMode, setIsEditMode] = useState(false);
  const [editFoodName, setEditFoodName] = useState("");
  const [editAmount, setEditAmount] = useState("");

  const totalCalories = meals.reduce((s, m) => s + m.calories, 0);
  const totalSodium = meals.reduce((s, m) => s + m.sodium_mg, 0);
  const totalSugar = meals.reduce((s, m) => s + m.sugar_g, 0);

  const filteredMeals = meals.filter(m => {
    if (mealTypeFilter === "전체") return true;
    return MEAL_LABELS[m.meal_type].label === mealTypeFilter;
  });

  const handleSaveInput = () => {
    const hasFood = foodItems.some(f => f.food.trim());
    if (!hasFood) { setShowValidation(true); return; }
    // TODO: API 연결 — POST /api/v1/health/meals
    // body: {
    //   food_name: foodItems.map(f => f.food).join(", "),
    //   amount: foodItems.map(f => f.amount).join(", "),
    //   meal_type: inputMealType,           // BREAKFAST/LUNCH/DINNER/SNACK (필수)
    //   meal_date: inputDate,               // date (optional)
    //   calories: Number(calories) || 0,
    //   carbs_g: Number(carbs) || 0,
    //   protein_g: Number(protein) || 0,
    //   fat_g: Number(fat) || 0,
    //   sodium_mg: Number(sodium) || 0,
    //   sugar_g: Number(sugar) || 0,
    //   fiber_g: Number(fiberG) || 0,
    //   memo,
    // }
    setShowSaveSuccess(true);
    setTimeout(() => { setShowSaveSuccess(false); setTab("list"); }, 1500);
  };

  const handleDelete = (id: number) => {
    // TODO: API 연결 — DELETE /api/v1/health/meals/{meal_log_id}
    // 204 No Content 응답 시 목록에서 제거
    setMeals(prev => prev.filter(m => m.meal_log_id !== id));
    setShowDeleteConfirm(false);
  };

  const openDetail = (meal: typeof DUMMY_MEALS[0]) => {
    setSelectedMeal(meal);
    setEditFoodName(meal.food_name);
    setEditAmount(meal.amount);
    setIsEditMode(false);
    setTab("detail");
  };

  const handleSaveEdit = () => {
    // TODO: API 연결 — PATCH /api/v1/health/meals/{meal_log_id}
    // body: { food_name: editFoodName, amount: editAmount }
    // 당일 기록만 수정 가능 (과거 기록: 410 PAST_RECORD_LOCKED)
    if (selectedMeal) {
      setMeals(prev => prev.map(m => m.meal_log_id === selectedMeal.meal_log_id
        ? { ...m, food_name: editFoodName, amount: editAmount } : m));
    }
    setIsEditMode(false);
  };

  const tabs = ["식단 직접 입력", "식단 기록 목록", "식단 기록 상세/수정"];
  const tabKeys: TabType[] = ["input", "list", "detail"];

  return (
    <div className="page-container">
      <h1 className="page-title">식단 기록</h1>

      {/* 탭 */}
      <div style={{ display: "flex", borderBottom: "2px solid #e0e0e0", marginBottom: 20 }}>
        {tabs.map((t, i) => (
          <button key={t} onClick={() => setTab(tabKeys[i])}
            style={{ padding: "10px 16px", border: "none", background: "none", cursor: "pointer",
              fontSize: 13, fontWeight: tab === tabKeys[i] ? 700 : 400,
              color: tab === tabKeys[i] ? "#1a1a1a" : "#888",
              borderBottom: tab === tabKeys[i] ? "2px solid #1a1a1a" : "2px solid transparent",
              marginBottom: -2 }}>
            {t}
          </button>
        ))}
      </div>

      {/* ── 식단 직접 입력 ── */}
      {tab === "input" && (
        <div>
          {showSaveSuccess && (
            <div style={{ padding: "12px 16px", background: "#e8f5e9", border: "1px solid #a5d6a7", borderRadius: 6, marginBottom: 16, fontSize: 12, color: "#2e7d32" }}>
              식단이 저장되었습니다.
            </div>
          )}

          {/* 식사 유형 선택 */}
          <div style={{ display: "grid", gridTemplateColumns: "repeat(4, 1fr)", gap: 12, marginBottom: 20 }}>
            {(Object.keys(MEAL_LABELS) as MealType[]).map(type => (
              <button key={type} onClick={() => setInputMealType(type)}
                style={{ padding: "16px 8px", border: `2px solid ${inputMealType === type ? "#1a1a1a" : "#e0e0e0"}`,
                  borderRadius: 8, background: inputMealType === type ? "#f5f5f5" : "#fff",
                  cursor: "pointer", textAlign: "center" }}>
                <div style={{ fontSize: 28, marginBottom: 6 }}>{MEAL_LABELS[type].icon}</div>
                <div style={{ fontSize: 12, fontWeight: inputMealType === type ? 700 : 400 }}>{MEAL_LABELS[type].label}</div>
                <div style={{ fontSize: 9, color: "#aaa", marginTop: 2 }}>{type}</div>
              </button>
            ))}
          </div>

          {/* 음식명 & 섭취량 */}
          <div style={{ marginBottom: 20 }}>
            <h3 style={{ fontSize: 13, fontWeight: 600, marginBottom: 10 }}>음식명 & 섭취량</h3>
            {showValidation && <p style={{ fontSize: 11, color: "#E24B4A", marginBottom: 8 }}>음식명을 입력해주세요</p>}
            <div style={{ display: "flex", flexDirection: "column", gap: 10 }}>
              {foodItems.map((item, i) => (
                <div key={i} style={{ display: "flex", gap: 10, alignItems: "center" }}>
                  <input value={item.food} onChange={e => setFoodItems(prev => prev.map((f, j) => j === i ? { ...f, food: e.target.value } : f))}
                    placeholder="음식명"
                    style={{ flex: 2, height: 36, border: `1.5px solid ${showValidation && !item.food ? "#E24B4A" : "#ddd"}`, borderRadius: 5, padding: "0 12px", fontSize: 12, outline: "none", boxSizing: "border-box" }} />
                  <input value={item.amount} onChange={e => setFoodItems(prev => prev.map((f, j) => j === i ? { ...f, amount: e.target.value } : f))}
                    placeholder="섭취량 (예: 1인분)"
                    style={{ flex: 1, height: 36, border: "1.5px solid #ddd", borderRadius: 5, padding: "0 12px", fontSize: 12, outline: "none", boxSizing: "border-box" }} />
                  {foodItems.length > 1 && (
                    <button onClick={() => setFoodItems(prev => prev.filter((_, j) => j !== i))}
                      style={{ width: 32, height: 32, border: "1px solid #ddd", borderRadius: "50%", background: "#fff", cursor: "pointer", fontSize: 14 }}>🗑️</button>
                  )}
                </div>
              ))}
              {foodItems.length < 10 && (
                <button onClick={() => setFoodItems(prev => [...prev, { food: "", amount: "" }])}
                  style={{ padding: 10, border: "1.5px dashed #aaa", borderRadius: 5, background: "#fafafa", cursor: "pointer", fontSize: 12, color: "#888" }}>
                  + 음식 추가
                </button>
              )}
            </div>
          </div>

          {/* 식사 시간 */}
          <div style={{ marginBottom: 20 }}>
            <h3 style={{ fontSize: 13, fontWeight: 600, marginBottom: 10 }}>식사 시간</h3>
            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 10 }}>
              <input type="date" value={inputDate} onChange={e => setInputDate(e.target.value)}
                style={{ height: 36, border: "1.5px solid #ddd", borderRadius: 5, padding: "0 12px", fontSize: 12, outline: "none" }} />
              <input type="time" value={inputTime} onChange={e => setInputTime(e.target.value)}
                style={{ height: 36, border: "1.5px solid #ddd", borderRadius: 5, padding: "0 12px", fontSize: 12, outline: "none" }} />
            </div>
          </div>

          {/* 칼로리 */}
          <div style={{ marginBottom: 20 }}>
            <h3 style={{ fontSize: 13, fontWeight: 600, marginBottom: 10 }}>칼로리 (선택)</h3>
            <input type="number" value={calories} onChange={e => setCalories(e.target.value)} placeholder="0"
              style={{ width: "100%", height: 36, border: "1.5px solid #ddd", borderRadius: 5, padding: "0 12px", fontSize: 12, outline: "none", boxSizing: "border-box" }} />
          </div>

          {/* 영양 성분 */}
          <div style={{ marginBottom: 20 }}>
            <h3 style={{ fontSize: 13, fontWeight: 600, marginBottom: 10 }}>영양 성분 (선택)</h3>
            <div style={{ display: "grid", gridTemplateColumns: "repeat(3, 1fr)", gap: 10 }}>
              {[
                { label: "탄수화물 (g)", val: carbs, set: setCarbs },
                { label: "단백질 (g)", val: protein, set: setProtein },
                { label: "지방 (g)", val: fat, set: setFat },
                { label: "나트륨 (mg)", val: sodium, set: setSodium },
                { label: "당류 (g)", val: sugar, set: setSugar },
                { label: "식이섬유 (g)", val: fiberG, set: setFiberG },
              ].map(({ label, val, set }) => (
                <div key={label}>
                  <label style={{ fontSize: 10, color: "#555", display: "block", marginBottom: 4 }}>{label}</label>
                  <input type="number" value={val} onChange={e => set(e.target.value)} placeholder="0"
                    style={{ width: "100%", height: 34, border: "1.5px solid #ddd", borderRadius: 5, padding: "0 10px", fontSize: 12, outline: "none", boxSizing: "border-box" }} />
                </div>
              ))}
            </div>
            <p style={{ fontSize: 10, color: "#aaa", marginTop: 6 }}>입력하지 않으면 0으로 저장됩니다.</p>
          </div>

          {/* 메모 */}
          <div style={{ marginBottom: 20 }}>
            <h3 style={{ fontSize: 13, fontWeight: 600, marginBottom: 10 }}>메모</h3>
            <textarea value={memo} onChange={e => setMemo(e.target.value)}
              placeholder="음식의 특징, 조리방법, 또는 기타 사항을 기록하세요 (선택사항)"
              style={{ width: "100%", minHeight: 80, border: "1.5px solid #ddd", borderRadius: 5, padding: 12, fontSize: 12, outline: "none", resize: "vertical", boxSizing: "border-box" }} />
          </div>

          <div style={{ display: "flex", gap: 10 }}>
            <button onClick={handleSaveInput}
              style={{ flex: 1, height: 40, border: "1.5px solid #ddd", borderRadius: 8, background: "#fff", fontSize: 13, cursor: "pointer" }}>
              📁 저장
            </button>
            <button onClick={() => { setFoodItems([{ food: "", amount: "" }]); setCalories(""); setMemo(""); setShowValidation(false); }}
              style={{ flex: 1, height: 40, border: "none", borderRadius: 8, background: "#1a1a1a", color: "#fff", fontSize: 13, fontWeight: 600, cursor: "pointer" }}>
              초기화
            </button>
          </div>
        </div>
      )}

      {/* ── 식단 기록 목록 ── */}
      {tab === "list" && (
        <div>
          {/* 필터 카드 */}
          <div style={{ background: "#fff", border: "1px solid #e0e0e0", borderRadius: 10, padding: 16, marginBottom: 16 }}>
            <h3 style={{ fontSize: 12, fontWeight: 600, marginBottom: 10 }}>기간</h3>
            <div style={{ display: "flex", gap: 8, marginBottom: 12 }}>
              {(["오늘", "7일", "30일", "직접 선택"] as PeriodType[]).map(p => (
                <button key={p} onClick={() => setPeriod(p)}
                  style={{ flex: 1, padding: 8, border: `1.5px solid ${period === p ? "#1a1a1a" : "#ddd"}`,
                    borderRadius: 5, background: period === p ? "#f5f5f5" : "#fff",
                    fontSize: 11, fontWeight: period === p ? 700 : 400, cursor: "pointer" }}>
                  {p}
                </button>
              ))}
            </div>
            {period === "직접 선택" && (
              <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 10, marginBottom: 12 }}>
                <input type="date" placeholder="시작일" style={{ height: 36, border: "1.5px solid #ddd", borderRadius: 5, padding: "0 10px", fontSize: 12, outline: "none" }} />
                <input type="date" placeholder="종료일" style={{ height: 36, border: "1.5px solid #ddd", borderRadius: 5, padding: "0 10px", fontSize: 12, outline: "none" }} />
              </div>
            )}

            <h3 style={{ fontSize: 12, fontWeight: 600, marginBottom: 8 }}>식사 유형</h3>
            <select value={mealTypeFilter} onChange={e => setMealTypeFilter(e.target.value)}
              style={{ width: "100%", height: 36, border: "1.5px solid #ddd", borderRadius: 5, padding: "0 12px", fontSize: 12, outline: "none", marginBottom: 12 }}>
              {["전체", "아침", "점심", "저녁", "간식"].map(t => <option key={t}>{t}</option>)}
            </select>

            <button onClick={() => setTab("input")}
              style={{ width: "100%", height: 36, border: "none", borderRadius: 8, background: "#1a1a1a", color: "#fff", fontSize: 13, fontWeight: 600, cursor: "pointer" }}>
              + 새로운 식단 추가
            </button>
          </div>

          {/* API 연결 시: daily_summary 배열로 날짜별 합산 표시 필요
              GET /api/v1/health/meals?from=...&to=...
              응답: { daily_summary: [{ meal_date, meal_count, total_calories, total_sodium_mg, total_sugar_g, total_fiber_g }] } */}
          <div style={{ display: "grid", gridTemplateColumns: "repeat(4, 1fr)", gap: 12, marginBottom: 20 }}>
            {[
              { label: "총 칼로리", val: totalCalories.toLocaleString(), unit: "kcal", bg: "#e3f2fd", color: "#1565c0", border: "#90caf9" },
              { label: "총 나트륨", val: totalSodium.toLocaleString(), unit: "mg", bg: "#fff8e1", color: "#f57f17", border: "#ffe082" },
              { label: "총 당류", val: totalSugar, unit: "g", bg: "#fce4ec", color: "#c2185b", border: "#f48fb1" },
              { label: "식사 횟수", val: filteredMeals.length, unit: "회", bg: "#fafafa", color: "#555", border: "#e0e0e0" },
            ].map(item => (
              <div key={item.label} style={{ padding: "12px 14px", background: item.bg, border: `1.5px solid ${item.border}`, borderRadius: 8, textAlign: "center" }}>
                <div style={{ fontSize: 10, color: item.color, marginBottom: 4 }}>{item.label}</div>
                <div style={{ fontSize: 20, fontWeight: 700, color: item.color }}>
                  {item.val}<span style={{ fontSize: 10, fontWeight: 400, color: "#aaa" }}>{item.unit}</span>
                </div>
              </div>
            ))}
          </div>

          {/* 식단 목록 */}
          {filteredMeals.length === 0 ? (
            <div style={{ textAlign: "center", padding: "60px 20px" }}>
              <div style={{ fontSize: 64, marginBottom: 16 }}>🍽️</div>
              <p style={{ fontSize: 14, color: "#555" }}>이 날의 식단 기록이 없습니다.</p>
              <button onClick={() => setTab("input")}
                style={{ marginTop: 20, padding: "10px 24px", border: "none", borderRadius: 8, background: "#1a1a1a", color: "#fff", fontSize: 13, cursor: "pointer" }}>
                + 새로운 식단 추가
              </button>
            </div>
          ) : (
            <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
              {filteredMeals.map(meal => (
                <div key={meal.meal_log_id} style={{ background: "#fff", border: "1px solid #e0e0e0", borderRadius: 10, padding: 14 }}>
                  <div style={{ display: "flex", gap: 10, marginBottom: 10, alignItems: "flex-start" }}>
                    <div style={{ width: 36, height: 36, background: "#f5f5f5", borderRadius: 8, display: "flex", alignItems: "center", justifyContent: "center", fontSize: 20, flexShrink: 0 }}>
                      {MEAL_LABELS[meal.meal_type].icon}
                    </div>
                    <div style={{ flex: 1 }}>
                      <p style={{ fontSize: 13, fontWeight: 600, margin: 0 }}>{MEAL_LABELS[meal.meal_type].label} - {meal.food_name}</p>
                      <p style={{ fontSize: 11, color: "#888", margin: "2px 0 0" }}>{meal.meal_date} {meal.time}</p>
                    </div>
                  </div>
                  <p style={{ fontSize: 11, color: "#555", margin: "0 0 10px" }}>
                    {meal.calories}kcal &nbsp; 나트륨 {meal.sodium_mg}mg &nbsp; 당류 {meal.sugar_g}g
                  </p>
                  <div style={{ display: "flex", gap: 8 }}>
                    <button onClick={() => openDetail(meal)}
                      style={{ padding: "6px 12px", border: "1.5px solid #ddd", borderRadius: 6, background: "#fff", fontSize: 11, cursor: "pointer" }}>
                      ✏️ 상세/수정
                    </button>
                    <button
                      disabled={!meal.isToday}
                      onClick={() => { setDeleteTargetId(meal.meal_log_id); setShowDeleteConfirm(true); }}
                      title={!meal.isToday ? "당일 기록만 삭제할 수 있습니다." : ""}
                      style={{ padding: "6px 12px", border: "1.5px solid #ddd", borderRadius: 6, background: "#fff", fontSize: 11,
                        cursor: meal.isToday ? "pointer" : "not-allowed", opacity: meal.isToday ? 1 : 0.4 }}>
                      🗑️ 삭제
                    </button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* ── 식단 기록 상세/수정 ── */}
      {tab === "detail" && selectedMeal && (
        <div>
          <div style={{ display: "flex", alignItems: "center", gap: 10, marginBottom: 16 }}>
            <div style={{ fontSize: 24 }}>{MEAL_LABELS[selectedMeal.meal_type].icon}</div>
            <h2 style={{ fontSize: 15, fontWeight: 700, margin: 0 }}>
              {MEAL_LABELS[selectedMeal.meal_type].label} - {selectedMeal.food_name}
            </h2>
            {!isEditMode && selectedMeal.isToday && (
              <button onClick={() => setIsEditMode(true)}
                style={{ marginLeft: "auto", padding: "6px 14px", border: "1.5px solid #ddd", borderRadius: 6, background: "#fff", fontSize: 12, cursor: "pointer" }}>
                수정
              </button>
            )}
          </div>

          {/* 기본 정보 */}
          <div style={{ background: "#fff", border: "1px solid #e0e0e0", borderRadius: 10, padding: 18, marginBottom: 16 }}>
            <h3 style={{ fontSize: 13, fontWeight: 600, marginBottom: 14 }}>📋 기본 정보</h3>
            <div style={{ marginBottom: 12 }}>
              <p style={{ fontSize: 11, fontWeight: 600, margin: "0 0 6px" }}>음식명</p>
              {isEditMode
                ? <input value={editFoodName} onChange={e => setEditFoodName(e.target.value)} style={{ width: "100%", height: 34, border: "1.5px solid #ddd", borderRadius: 5, padding: "0 12px", fontSize: 12, outline: "none", boxSizing: "border-box" }} />
                : <p style={{ fontSize: 12, color: "#333", margin: 0 }}>{selectedMeal.food_name}</p>
              }
            </div>
            <div style={{ marginBottom: 12 }}>
              <p style={{ fontSize: 11, fontWeight: 600, margin: "0 0 6px" }}>섭취량</p>
              {isEditMode
                ? <input value={editAmount} onChange={e => setEditAmount(e.target.value)} style={{ width: "100%", height: 34, border: "1.5px solid #ddd", borderRadius: 5, padding: "0 12px", fontSize: 12, outline: "none", boxSizing: "border-box" }} />
                : <p style={{ fontSize: 12, color: "#333", margin: 0 }}>{selectedMeal.amount}</p>
              }
            </div>
            <div>
              <p style={{ fontSize: 11, fontWeight: 600, margin: "0 0 6px" }}>식사 시간</p>
              <p style={{ fontSize: 12, color: "#333", margin: 0 }}>{selectedMeal.meal_date} {selectedMeal.time}</p>
            </div>
          </div>

          {/* 영양 정보 */}
          <div style={{ background: "#fff", border: "1px solid #e0e0e0", borderRadius: 10, padding: 18, marginBottom: 16 }}>
            <h3 style={{ fontSize: 13, fontWeight: 600, marginBottom: 14 }}>📊 영양 정보</h3>
            <table style={{ width: "100%", borderCollapse: "collapse", fontSize: 12 }}>
              <thead>
                <tr style={{ background: "#f5f5f5" }}>
                  <th style={{ padding: "8px 12px", textAlign: "left", fontWeight: 600, border: "1px solid #e0e0e0" }}>영양소</th>
                  <th style={{ padding: "8px 12px", textAlign: "left", fontWeight: 600, border: "1px solid #e0e0e0" }}>함량</th>
                </tr>
              </thead>
              <tbody>
                {[
                  { label: "칼로리", val: `${selectedMeal.calories} kcal` },
                  { label: "탄수화물", val: `${selectedMeal.carbs_g}g` },
                  { label: "단백질", val: `${selectedMeal.protein_g}g` },
                  { label: "지방", val: `${selectedMeal.fat_g}g` },
                  { label: "나트륨", val: `${selectedMeal.sodium_mg}mg` },
                  { label: "당류", val: `${selectedMeal.sugar_g}g` },
                ].map((row, i) => (
                  <tr key={i} style={{ background: i % 2 === 0 ? "#fafafa" : "#fff" }}>
                    <td style={{ padding: "8px 12px", border: "1px solid #e0e0e0" }}>{row.label}</td>
                    <td style={{ padding: "8px 12px", border: "1px solid #e0e0e0", color: "#FF6B35", fontWeight: 600 }}>{row.val}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {/* 메모 */}
          <div style={{ background: "#fff", border: "1px solid #e0e0e0", borderRadius: 10, padding: 18, marginBottom: 16 }}>
            <h3 style={{ fontSize: 13, fontWeight: 600, marginBottom: 10 }}>📝 메모</h3>
            <p style={{ fontSize: 12, color: "#555", margin: 0 }}>{selectedMeal.memo || "메모 없음"}</p>
          </div>

          {!selectedMeal.isToday && (
            <p style={{ fontSize: 11, color: "#aaa", textAlign: "center", marginBottom: 8 }}>당일 기록만 수정 또는 삭제할 수 있습니다.</p>
          )}

          <div style={{ display: "flex", gap: 10 }}>
            {isEditMode ? (
              <>
                <button onClick={handleSaveEdit}
                  style={{ flex: 1, height: 40, border: "none", borderRadius: 8, background: "#1a1a1a", color: "#fff", fontSize: 13, fontWeight: 600, cursor: "pointer" }}>
                  📁 저장
                </button>
                <button onClick={() => setIsEditMode(false)}
                  style={{ flex: 1, height: 40, border: "1.5px solid #ddd", borderRadius: 8, background: "#fff", fontSize: 13, cursor: "pointer" }}>
                  취소
                </button>
              </>
            ) : selectedMeal.isToday ? (
              <>
                <button onClick={() => setIsEditMode(true)}
                  style={{ flex: 1, height: 40, border: "1.5px solid #ddd", borderRadius: 8, background: "#fff", fontSize: 13, cursor: "pointer" }}>
                  수정
                </button>
                <button onClick={() => { setDeleteTargetId(selectedMeal.meal_log_id); setShowDeleteConfirm(true); }}
                  style={{ flex: 1, height: 40, border: "1.5px solid #ddd", borderRadius: 8, background: "#fff", fontSize: 13, cursor: "pointer" }}>
                  🗑️ 삭제
                </button>
              </>
            ) : (
              <button onClick={() => setTab("list")}
                style={{ flex: 1, height: 40, border: "1.5px solid #ddd", borderRadius: 8, background: "#fff", fontSize: 13, cursor: "pointer" }}>
                닫기
              </button>
            )}
          </div>
        </div>
      )}

      {/* 삭제 확인 모달 */}
      {showDeleteConfirm && (
        <div style={{ position: "fixed", inset: 0, background: "rgba(0,0,0,0.5)", display: "flex", alignItems: "center", justifyContent: "center", zIndex: 1000 }}>
          <div style={{ background: "#fff", borderRadius: 12, padding: 24, maxWidth: 360, width: "90%" }}>
            <h3 style={{ fontSize: 15, fontWeight: 600, marginBottom: 16 }}>이 식단 기록을 삭제할까요?</h3>
            <div style={{ display: "flex", gap: 10 }}>
              <button onClick={() => deleteTargetId && handleDelete(deleteTargetId)}
                style={{ flex: 1, height: 38, border: "none", borderRadius: 8, background: "#c62828", color: "#fff", fontSize: 13, fontWeight: 600, cursor: "pointer" }}>
                삭제
              </button>
              <button onClick={() => setShowDeleteConfirm(false)}
                style={{ flex: 1, height: 38, border: "1.5px solid #ddd", borderRadius: 8, background: "#fff", fontSize: 13, cursor: "pointer" }}>
                취소
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
