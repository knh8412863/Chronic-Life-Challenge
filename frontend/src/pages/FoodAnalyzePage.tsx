import { useState } from "react";

import type { AppRoute } from "../App";
import { getStoredAccessToken } from "../api/auth";
import { createFoodAnalysis, createMealLog, type FoodAnalysisResult, type MealType } from "../api/foods";
import { ErrorState } from "../components/common/ErrorState";
import { LoadingState } from "../components/common/LoadingState";

interface FoodAnalyzePageProps {
  onNavigate: (route: AppRoute) => void;
}

const MEAL_LABELS: Record<MealType, string> = {
  BREAKFAST: "아침",
  LUNCH: "점심",
  DINNER: "저녁",
  SNACK: "간식",
};

function numberOrNull(value: string) {
  if (value.trim() === "") return null;
  return Number(value);
}

function riskFlagLabel(flag: string) {
  const labels: Record<string, string> = {
    HIGH_CALORIES: "고열량",
    HIGH_SODIUM: "나트륨 주의",
    HIGH_SUGAR: "당류 주의",
    HIGH_FAT: "지방 주의",
    LOW_PROTEIN: "단백질 부족",
    LOW_FIBER: "식이섬유 부족",
  };
  return labels[flag] ?? flag;
}

export function FoodAnalyzePage({ onNavigate }: FoodAnalyzePageProps) {
  const [mealType, setMealType] = useState<MealType>("BREAKFAST");
  const [mealDate, setMealDate] = useState(new Date().toISOString().slice(0, 10));
  const [foodName, setFoodName] = useState("");
  const [amount, setAmount] = useState("");
  const [calories, setCalories] = useState("");
  const [carbs, setCarbs] = useState("");
  const [protein, setProtein] = useState("");
  const [fat, setFat] = useState("");
  const [sodium, setSodium] = useState("");
  const [sugar, setSugar] = useState("");
  const [fiber, setFiber] = useState("");
  const [result, setResult] = useState<FoodAnalysisResult | null>(null);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [isSaving, setIsSaving] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [saved, setSaved] = useState(false);

  const buildPayload = () => ({
    meal_date: mealDate,
    meal_type: mealType,
    food_name: foodName.trim(),
    amount: amount.trim() || null,
    calories: numberOrNull(calories),
    carbs_g: numberOrNull(carbs),
    protein_g: numberOrNull(protein),
    fat_g: numberOrNull(fat),
    sodium_mg: numberOrNull(sodium),
    sugar_g: numberOrNull(sugar),
    fiber_g: numberOrNull(fiber),
  });

  async function handleAnalyze() {
    if (!foodName.trim()) {
      setErrorMessage("음식명을 입력해 주세요.");
      return;
    }

    const token = getStoredAccessToken();
    if (!token) {
      setErrorMessage("로그인 후 식단 분석을 사용할 수 있습니다.");
      return;
    }

    setIsAnalyzing(true);
    setErrorMessage(null);
    setSaved(false);
    try {
      const response = await createFoodAnalysis(buildPayload(), token);
      setResult(response.data);
    } catch {
      setErrorMessage("식단 분석에 실패했습니다. 입력값을 확인한 뒤 다시 시도해 주세요.");
    } finally {
      setIsAnalyzing(false);
    }
  }

  async function handleSaveResult() {
    if (!result) return;

    const token = getStoredAccessToken();
    if (!token) {
      setErrorMessage("로그인 후 식단 기록을 저장할 수 있습니다.");
      return;
    }

    setIsSaving(true);
    setErrorMessage(null);
    try {
      await createMealLog(
        {
          food_analysis_result_id: result.food_analysis_result_id,
          meal_date: result.meal_date ?? mealDate,
          meal_type: result.meal_type ?? mealType,
        },
        token,
      );
      setSaved(true);
      setTimeout(() => onNavigate("/food"), 800);
    } catch {
      setErrorMessage("분석 결과 저장에 실패했습니다. 잠시 후 다시 시도해 주세요.");
    } finally {
      setIsSaving(false);
    }
  }

  return (
    <div className="page-container">
      <h1 className="page-title">식단 분석</h1>

      <div style={{ display: "grid", gridTemplateColumns: "minmax(0, 1fr) 340px", gap: 16 }}>
        <section style={{ background: "#fff", border: "1px solid #e0e0e0", borderRadius: 10, padding: 20 }}>
          <h2 style={{ fontSize: 15, fontWeight: 700, marginBottom: 6 }}>영양성분 직접 입력</h2>
          <p style={{ fontSize: 12, color: "#777", marginBottom: 18 }}>
            음식명과 확인 가능한 영양성분을 입력하면 식단 관리 참고용 분석 결과를 생성합니다.
          </p>

          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 12, marginBottom: 14 }}>
            <div>
              <label style={{ display: "block", fontSize: 11, fontWeight: 600, marginBottom: 5 }}>식사일</label>
              <input
                type="date"
                value={mealDate}
                onChange={(event) => setMealDate(event.target.value)}
                style={{ width: "100%", height: 36, border: "1px solid #ddd", borderRadius: 6, padding: "0 10px" }}
              />
            </div>
            <div>
              <label style={{ display: "block", fontSize: 11, fontWeight: 600, marginBottom: 5 }}>식사 유형</label>
              <select
                value={mealType}
                onChange={(event) => setMealType(event.target.value as MealType)}
                style={{ width: "100%", height: 36, border: "1px solid #ddd", borderRadius: 6, padding: "0 10px" }}
              >
                {(Object.keys(MEAL_LABELS) as MealType[]).map((type) => (
                  <option key={type} value={type}>{MEAL_LABELS[type]}</option>
                ))}
              </select>
            </div>
          </div>

          <div style={{ display: "grid", gridTemplateColumns: "2fr 1fr", gap: 12, marginBottom: 14 }}>
            <div>
              <label style={{ display: "block", fontSize: 11, fontWeight: 600, marginBottom: 5 }}>음식명</label>
              <input
                value={foodName}
                onChange={(event) => setFoodName(event.target.value)}
                placeholder="예: 현미밥, 닭가슴살 샐러드"
                style={{ width: "100%", height: 36, border: "1px solid #ddd", borderRadius: 6, padding: "0 10px" }}
              />
            </div>
            <div>
              <label style={{ display: "block", fontSize: 11, fontWeight: 600, marginBottom: 5 }}>섭취량</label>
              <input
                value={amount}
                onChange={(event) => setAmount(event.target.value)}
                placeholder="예: 1인분"
                style={{ width: "100%", height: 36, border: "1px solid #ddd", borderRadius: 6, padding: "0 10px" }}
              />
            </div>
          </div>

          <div style={{ display: "grid", gridTemplateColumns: "repeat(4, 1fr)", gap: 10 }}>
            {[
              { label: "칼로리", unit: "kcal", value: calories, setter: setCalories },
              { label: "탄수화물", unit: "g", value: carbs, setter: setCarbs },
              { label: "단백질", unit: "g", value: protein, setter: setProtein },
              { label: "지방", unit: "g", value: fat, setter: setFat },
              { label: "나트륨", unit: "mg", value: sodium, setter: setSodium },
              { label: "당류", unit: "g", value: sugar, setter: setSugar },
              { label: "식이섬유", unit: "g", value: fiber, setter: setFiber },
            ].map(({ label, unit, value, setter }) => (
              <div key={label}>
                <label style={{ display: "block", fontSize: 10, color: "#555", marginBottom: 4 }}>
                  {label} ({unit})
                </label>
                <input
                  type="number"
                  min="0"
                  value={value}
                  onChange={(event) => setter(event.target.value)}
                  placeholder="0"
                  style={{ width: "100%", height: 34, border: "1px solid #ddd", borderRadius: 6, padding: "0 10px" }}
                />
              </div>
            ))}
          </div>

          <div style={{ marginTop: 18, display: "flex", gap: 10 }}>
            <button
              type="button"
              onClick={handleAnalyze}
              disabled={isAnalyzing}
              style={{ flex: 1, height: 40, border: "none", borderRadius: 8, background: "#1a1a1a", color: "#fff", fontWeight: 700 }}
            >
              {isAnalyzing ? "분석 중..." : "식단 분석하기"}
            </button>
            <button
              type="button"
              onClick={() => onNavigate("/food")}
              style={{ width: 120, height: 40, border: "1px solid #ddd", borderRadius: 8, background: "#fff" }}
            >
              목록으로
            </button>
          </div>
        </section>

        <aside style={{ display: "flex", flexDirection: "column", gap: 12 }}>
          {isAnalyzing && <LoadingState message="식단을 분석하는 중입니다." skeletonCount={2} />}
          {errorMessage && <ErrorState title={errorMessage} />}
          {result && (
            <section style={{ background: "#fff", border: "1px solid #e0e0e0", borderRadius: 10, padding: 18 }}>
              <h2 style={{ fontSize: 15, fontWeight: 700, marginBottom: 8 }}>분석 결과</h2>
              <p style={{ fontSize: 13, margin: "0 0 10px" }}>{result.food_name}</p>
              <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 8, marginBottom: 12 }}>
                <div style={{ padding: 10, borderRadius: 8, background: "#e8f5e9" }}>
                  <p style={{ fontSize: 10, margin: 0, color: "#2e7d32" }}>건강 점수</p>
                  <strong style={{ fontSize: 22, color: "#2e7d32" }}>{result.health_score}</strong>
                </div>
                <div style={{ padding: 10, borderRadius: 8, background: "#f5f5f5" }}>
                  <p style={{ fontSize: 10, margin: 0, color: "#777" }}>칼로리</p>
                  <strong style={{ fontSize: 22 }}>{result.nutrition.calories ?? 0}</strong>
                </div>
              </div>
              <div style={{ display: "flex", flexWrap: "wrap", gap: 6, marginBottom: 12 }}>
                {result.risk_flags.length === 0 ? (
                  <span style={{ fontSize: 11, padding: "4px 8px", borderRadius: 999, background: "#e8f5e9", color: "#2e7d32" }}>
                    큰 위험 신호 없음
                  </span>
                ) : (
                  result.risk_flags.map((flag) => (
                    <span key={flag} style={{ fontSize: 11, padding: "4px 8px", borderRadius: 999, background: "#fff8e1", color: "#f57f17" }}>
                      {riskFlagLabel(flag)}
                    </span>
                  ))
                )}
              </div>
              <p style={{ fontSize: 12, color: "#555", lineHeight: 1.6 }}>{result.advice_text}</p>
              <button
                type="button"
                onClick={handleSaveResult}
                disabled={isSaving || saved}
                style={{ width: "100%", height: 40, border: "none", borderRadius: 8, background: saved ? "#2e7d32" : "#1a1a1a", color: "#fff", fontWeight: 700 }}
              >
                {isSaving ? "저장 중..." : saved ? "저장 완료" : "기록으로 저장"}
              </button>
            </section>
          )}
        </aside>
      </div>
    </div>
  );
}
