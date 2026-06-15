import { useEffect, useState } from "react";
import type { AppRoute } from "../../App";
import { getStoredAccessToken } from "../../api/auth";
import {
  createMealLog,
  deleteMealLog,
  getMealLogs,
  updateMealLog,
  type MealLog,
  type MealType,
} from "../../api/foods";
import { EmptyState } from "../../components/common/EmptyState";
import { ErrorState } from "../../components/common/ErrorState";
import { LoadingState } from "../../components/common/LoadingState";
import { localDateString, localDaysAgoString } from "../../utils/date";

interface FoodPageProps {
  onNavigate: (route: AppRoute) => void;
  view?: "list" | "input";
}

type TabType = "list" | "input" | "detail";
type PeriodType = "오늘" | "7일" | "30일" | "직접 선택";

const MEAL_LABELS: Record<MealType, { icon: string; label: string }> = {
  BREAKFAST: { icon: "🍚", label: "아침" },
  LUNCH:     { icon: "☀️", label: "점심" },
  DINNER:    { icon: "🌙", label: "저녁" },
  SNACK:     { icon: "🍪", label: "간식" },
};

type FoodMeal = MealLog & {
  time: string;
  isToday: boolean;
};

type FoodInputItem = {
  food: string;
  amount: string;
  calories: string;
  carbs: string;
  protein: string;
  fat: string;
  sodium: string;
  sugar: string;
  fiberG: string;
};

const emptyFoodInputItem = (): FoodInputItem => ({
  food: "",
  amount: "",
  calories: "",
  carbs: "",
  protein: "",
  fat: "",
  sodium: "",
  sugar: "",
  fiberG: "",
});

function todayString() {
  return localDateString();
}

function daysAgo(days: number) {
  return localDaysAgoString(days);
}

function mealTimeLabel(createdAt: string) {
  return new Date(createdAt).toLocaleTimeString("ko-KR", {
    hour: "2-digit",
    minute: "2-digit",
    hour12: false,
  });
}

function toFoodMeal(meal: MealLog): FoodMeal {
  return {
    ...meal,
    time: mealTimeLabel(meal.created_at),
    isToday: meal.meal_date === todayString(),
  };
}

function periodRange(period: PeriodType) {
  if (period === "오늘") return { from: todayString(), to: todayString() };
  if (period === "7일") return { from: daysAgo(6), to: todayString() };
  if (period === "30일") return { from: daysAgo(29), to: todayString() };
  return {};
}

function numberOrNull(value: string) {
  if (value.trim() === "") return null;
  return Number(value);
}

function sumFoodItemNumber(items: FoodInputItem[], key: keyof Pick<FoodInputItem, "calories" | "carbs" | "protein" | "fat" | "sodium" | "sugar" | "fiberG">) {
  const values = items
    .filter(item => item.food.trim())
    .map(item => numberOrNull(item[key]))
    .filter((value): value is number => value !== null);
  if (values.length === 0) return null;
  return Number(values.reduce((sum, value) => sum + value, 0).toFixed(2));
}

export function FoodPage({ onNavigate, view = "list" }: FoodPageProps) {
  const isFixedInput = view === "input";
  const [tab, setTab] = useState<TabType>(view);
  const [selectedMeal, setSelectedMeal] = useState<FoodMeal | null>(null);
  const [period, setPeriod] = useState<PeriodType>("오늘");
  const [mealTypeFilter, setMealTypeFilter] = useState("전체");
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false);
  const [deleteTargetId, setDeleteTargetId] = useState<number | null>(null);
  const [meals, setMeals] = useState<FoodMeal[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [hasError, setHasError] = useState(false);

  // 식단 직접 입력 상태
  const [inputMealType, setInputMealType] = useState<MealType>("BREAKFAST");
  const [foodItems, setFoodItems] = useState<FoodInputItem[]>([emptyFoodInputItem()]);
  const [inputDate, setInputDate] = useState(todayString());
  const [inputTime, setInputTime] = useState("08:00");
  const [memo, setMemo] = useState("");
  const [showValidation, setShowValidation] = useState(false);
  const [showSaveSuccess, setShowSaveSuccess] = useState(false);

  // 상세/수정 상태
  const [isEditMode, setIsEditMode] = useState(false);
  const [editFoodName, setEditFoodName] = useState("");
  const [editAmount, setEditAmount] = useState("");

  const totalCalories = meals.reduce((s, m) => s + (m.calories ?? 0), 0);
  const totalSodium = meals.reduce((s, m) => s + (m.sodium_mg ?? 0), 0);
  const totalSugar = meals.reduce((s, m) => s + (m.sugar_g ?? 0), 0);

  const filteredMeals = meals.filter(m => {
    if (mealTypeFilter === "전체") return true;
    return MEAL_LABELS[m.meal_type].label === mealTypeFilter;
  });

  function fetchMeals() {
    const token = getStoredAccessToken();
    if (!token) return;

    const range = periodRange(period);
    setIsLoading(true);
    getMealLogs(
      {
        ...range,
        meal_type: mealTypeFilter === "전체" ? undefined : (Object.keys(MEAL_LABELS) as MealType[]).find(
          (type) => MEAL_LABELS[type].label === mealTypeFilter,
        ),
        limit: 100,
      },
      token,
    )
      .then((response) => {
        setMeals(response.data.items.map(toFoodMeal));
        setHasError(false);
      })
      .catch(() => setHasError(true))
      .finally(() => setIsLoading(false));
  }

  useEffect(() => {
    fetchMeals();
  }, [period, mealTypeFilter]);

  useEffect(() => {
    setTab(view);
    setSelectedMeal(null);
    setIsEditMode(false);
  }, [view]);

  const handleSaveInput = async () => {
    const hasFood = foodItems.some(f => f.food.trim());
    if (!hasFood) { setShowValidation(true); return; }
    const token = getStoredAccessToken();
    if (!token) { setHasError(true); return; }

    try {
      await createMealLog(
        {
          food_name: foodItems.map(f => f.food.trim()).filter(Boolean).join(", "),
          amount: foodItems.map(f => f.amount.trim()).filter(Boolean).join(", ") || null,
          meal_type: inputMealType,
          meal_date: inputDate,
          calories: sumFoodItemNumber(foodItems, "calories"),
          carbs_g: sumFoodItemNumber(foodItems, "carbs"),
          protein_g: sumFoodItemNumber(foodItems, "protein"),
          fat_g: sumFoodItemNumber(foodItems, "fat"),
          sodium_mg: sumFoodItemNumber(foodItems, "sodium"),
          sugar_g: sumFoodItemNumber(foodItems, "sugar"),
          fiber_g: sumFoodItemNumber(foodItems, "fiberG"),
          memo: memo.trim() || null,
        },
        token,
      );
      setShowSaveSuccess(true);
      fetchMeals();
      setTimeout(() => {
        setShowSaveSuccess(false);
        if (isFixedInput) onNavigate("/food");
        else setTab("list");
      }, 800);
    } catch {
      setHasError(true);
    }
  };

  const handleDelete = async (id: number) => {
    const token = getStoredAccessToken();
    if (!token) return;
    try {
      await deleteMealLog(id, token);
      setMeals(prev => prev.filter(m => m.meal_log_id !== id));
      setShowDeleteConfirm(false);
      if (selectedMeal?.meal_log_id === id) {
        setSelectedMeal(null);
        setTab("list");
      }
    } catch {
      setHasError(true);
    }
  };

  const openDetail = (meal: FoodMeal) => {
    setSelectedMeal(meal);
    setEditFoodName(meal.food_name);
    setEditAmount(meal.amount ?? "");
    setIsEditMode(false);
    setTab("detail");
  };

  const handleSaveEdit = async () => {
    if (selectedMeal) {
      const token = getStoredAccessToken();
      if (!token) return;
      try {
        const response = await updateMealLog(
          selectedMeal.meal_log_id,
          { food_name: editFoodName, amount: editAmount || null },
          token,
        );
        const updated = toFoodMeal(response.data);
        setMeals(prev => prev.map(m => m.meal_log_id === selectedMeal.meal_log_id ? updated : m));
        setSelectedMeal(updated);
      } catch {
        setHasError(true);
      }
    }
    setIsEditMode(false);
  };

  const pageTitle = tab === "input" ? "식단 직접 입력" : tab === "detail" ? "식단 기록 상세" : "식단 기록 목록";

  return (
    <div className="page-container">
      <h1 className="page-title">{pageTitle}</h1>

      {hasError && (
        <ErrorState title="식단 데이터를 처리하지 못했습니다." description="로그인 상태와 입력값을 확인한 뒤 다시 시도해 주세요." />
      )}

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
              </button>
            ))}
          </div>

          {/* 음식명 & 섭취량 */}
          <div style={{ marginBottom: 20 }}>
            <h3 style={{ fontSize: 13, fontWeight: 600, marginBottom: 10 }}>음식명 & 섭취량</h3>
            {showValidation && <p style={{ fontSize: 11, color: "#E24B4A", marginBottom: 8 }}>음식명을 입력해주세요</p>}
            <div style={{ display: "flex", flexDirection: "column", gap: 10 }}>
              {foodItems.map((item, i) => (
                <div key={i} style={{ border: "1px solid #eee", borderRadius: 8, padding: 12, background: "#fff" }}>
                  <div style={{ display: "flex", gap: 10, alignItems: "center", marginBottom: 10 }}>
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
                  <div style={{ display: "grid", gridTemplateColumns: "repeat(4, 1fr)", gap: 8 }}>
                    {[
                      { key: "calories" as const, label: "칼로리", unit: "kcal" },
                      { key: "carbs" as const, label: "탄수화물", unit: "g" },
                      { key: "protein" as const, label: "단백질", unit: "g" },
                      { key: "fat" as const, label: "지방", unit: "g" },
                      { key: "sodium" as const, label: "나트륨", unit: "mg" },
                      { key: "sugar" as const, label: "당류", unit: "g" },
                      { key: "fiberG" as const, label: "식이섬유", unit: "g" },
                    ].map(({ key, label, unit }) => (
                      <div key={key}>
                        <label style={{ fontSize: 10, color: "#555", display: "block", marginBottom: 4 }}>{label} ({unit})</label>
                        <input
                          type="number"
                          value={item[key]}
                          onChange={e => setFoodItems(prev => prev.map((f, j) => j === i ? { ...f, [key]: e.target.value } : f))}
                          placeholder="0"
                          style={{ width: "100%", height: 34, border: "1.5px solid #ddd", borderRadius: 5, padding: "0 10px", fontSize: 12, outline: "none", boxSizing: "border-box" }}
                        />
                      </div>
                    ))}
                  </div>
                </div>
              ))}
              {foodItems.length < 10 && (
                <button onClick={() => setFoodItems(prev => [...prev, emptyFoodInputItem()])}
                  style={{ padding: 10, border: "1.5px dashed #aaa", borderRadius: 5, background: "#fafafa", cursor: "pointer", fontSize: 12, color: "#888" }}>
                  + 음식 추가
                </button>
              )}
              <p style={{ fontSize: 10, color: "#aaa", margin: 0 }}>음식이 여러 개면 각 항목의 영양정보를 합산해 한 끼 식단으로 저장합니다.</p>
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

          {/* 메모 */}
          <div style={{ marginBottom: 20 }}>
            <h3 style={{ fontSize: 13, fontWeight: 600, marginBottom: 10 }}>메모</h3>
            <textarea value={memo} onChange={e => setMemo(e.target.value)}
              placeholder="음식의 특징, 조리방법, 또는 기타 사항을 기록하세요 (선택사항)"
              style={{ width: "100%", minHeight: 80, border: "1.5px solid #ddd", borderRadius: 5, padding: 12, fontSize: 12, outline: "none", resize: "vertical", boxSizing: "border-box" }} />
          </div>

          <div style={{ display: "flex", gap: 10 }}>
            <button onClick={() => { setFoodItems([emptyFoodInputItem()]); setMemo(""); setShowValidation(false); }}
              style={{ flex: 1, height: 40, border: "1.5px solid #ddd", borderRadius: 8, background: "#fff", fontSize: 13, cursor: "pointer" }}>
              초기화
            </button>
            <button onClick={handleSaveInput}
              style={{ flex: 1, height: 40, border: "none", borderRadius: 8, background: "#1a1a1a", color: "#fff", fontSize: 13, fontWeight: 600, cursor: "pointer" }}>
              저장
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

          </div>

          <div style={{ display: "grid", gridTemplateColumns: "repeat(3, 1fr)", gap: 12, marginBottom: 20 }}>
            {[
              { label: "총 칼로리", val: totalCalories.toLocaleString(), unit: "kcal", bg: "#e3f2fd", color: "#1565c0", border: "#90caf9" },
              { label: "총 나트륨", val: totalSodium.toLocaleString(), unit: "mg", bg: "#fff8e1", color: "#f57f17", border: "#ffe082" },
              { label: "총 당류", val: totalSugar, unit: "g", bg: "#fce4ec", color: "#c2185b", border: "#f48fb1" },
            ].map(item => (
              <div key={item.label} style={{ padding: "12px 14px", background: item.bg, border: `1.5px solid ${item.border}`, borderRadius: 8, textAlign: "center" }}>
                <div style={{ fontSize: 10, color: item.color, marginBottom: 4 }}>{item.label}</div>
                <div style={{ fontSize: 20, fontWeight: 700, color: item.color }}>
                  {item.val}<span style={{ fontSize: 10, fontWeight: 400, color: "#aaa" }}>{item.unit}</span>
                </div>
              </div>
            ))}
          </div>

          {isLoading ? (
            <LoadingState message="식단 기록을 불러오는 중입니다." />
          ) : filteredMeals.length === 0 ? (
            <div style={{ background: "#fff", border: "1px solid #e0e0e0", borderRadius: 10 }}>
              <EmptyState title="식단 기록이 없습니다." description="새로운 식단을 입력하거나 식단 분석 결과를 저장해 보세요." icon="🍽️" />
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
                    {meal.calories ?? 0}kcal &nbsp; 나트륨 {meal.sodium_mg ?? 0}mg &nbsp; 당류 {meal.sugar_g ?? 0}g
                  </p>
                  <div style={{ display: "flex", gap: 8 }}>
                    <button onClick={() => openDetail(meal)}
                      style={{ padding: "6px 12px", border: "1.5px solid #ddd", borderRadius: 6, background: "#fff", fontSize: 11, cursor: "pointer" }}>
                      상세
                    </button>
                    <button
                      disabled={!meal.isToday}
                      onClick={() => { setDeleteTargetId(meal.meal_log_id); setShowDeleteConfirm(true); }}
                      title={!meal.isToday ? "당일 기록만 삭제할 수 있습니다." : ""}
                      style={{ padding: "6px 12px", border: "1.5px solid #ddd", borderRadius: 6, background: "#fff", fontSize: 11,
                        cursor: meal.isToday ? "pointer" : "not-allowed", opacity: meal.isToday ? 1 : 0.4 }}>
                      삭제
                    </button>
                  </div>
                </div>
              ))}
            </div>
          )}
          <div style={{ display: "flex", justifyContent: "center", marginTop: 20 }}>
            <button
              type="button"
              className="green-button"
              onClick={() => onNavigate("/food/analyze")}
            >
              식단 기록하기
            </button>
          </div>
        </div>
      )}

      {/* ── 식단 기록 상세 ── */}
      {tab === "detail" && !selectedMeal && (
        <div>
          <EmptyState
            title="선택된 식단 기록이 없습니다."
            description="식단 기록 목록에서 수정할 기록을 먼저 선택해 주세요."
            icon="🍽️"
          />
          <div style={{ display: "flex", justifyContent: "center", marginTop: -36 }}>
            <button
              type="button"
              className="green-button"
              onClick={() => setTab("list")}
            >
              식단 기록 목록 보기
            </button>
          </div>
        </div>
      )}

      {tab === "detail" && selectedMeal && (
        <div>
          <div style={{ display: "flex", alignItems: "center", gap: 10, marginBottom: 16 }}>
            <div style={{ fontSize: 24 }}>{MEAL_LABELS[selectedMeal.meal_type].icon}</div>
            <h2 style={{ fontSize: 15, fontWeight: 700, margin: 0 }}>
              {MEAL_LABELS[selectedMeal.meal_type].label} - {selectedMeal.food_name}
            </h2>
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
                  { label: "칼로리", val: `${selectedMeal.calories ?? 0} kcal` },
                  { label: "탄수화물", val: `${selectedMeal.carbs_g ?? 0}g` },
                  { label: "단백질", val: `${selectedMeal.protein_g ?? 0}g` },
                  { label: "지방", val: `${selectedMeal.fat_g ?? 0}g` },
                  { label: "나트륨", val: `${selectedMeal.sodium_mg ?? 0}mg` },
                  { label: "당류", val: `${selectedMeal.sugar_g ?? 0}g` },
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
                  저장
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
                  삭제
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
