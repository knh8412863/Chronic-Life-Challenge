import { useState } from "react";
import type { AppRoute } from "../App";

interface FoodAnalyzePageProps {
  onNavigate: (route: AppRoute) => void;
}

type AnalyzeStep = "upload" | "analyzing" | "result" | "failure";
type MealType = "BREAKFAST" | "LUNCH" | "DINNER" | "SNACK";

const MEAL_LABELS: Record<MealType, string> = {
  BREAKFAST: "아침 ☀️",
  LUNCH: "점심 ☀️",
  DINNER: "저녁 🌙",
  SNACK: "간식 🍪",
};

// 더미 분석 결과 — API 연결 시 교체 (GET /api/v1/food/analyze/{task_uuid})
const DUMMY_RESULT = {
  food_analysis_result_id: 12,
  food_name: "백미밥, 된장찌개, 김치, 계란말이, 시금치나물",
  foods: [
    { name: "백미밥", confidence: 97 },
    { name: "된장찌개", confidence: 84 },
    { name: "김치", confidence: 71 },
    { name: "계란말이", confidence: 68 },
    { name: "시금치나물", confidence: 55 },
  ],
  nutrition: { calories: 680, carbs_g: 95, protein_g: 28, fat_g: 18, sodium_mg: 2100, fiber_g: 8, sugar_g: 28 },
  health_score: 75,
  risk_flags: ["나트륨 주의"],
  advice_text: "균형잡힌 식단이지만 나트륨이 1일 권장량을 초과했습니다.",
};

function StepIndicator({ step }: { step: AnalyzeStep }) {
  const steps = ["사진 업로드", "분석 진행", "결과 확인"];
  const current = step === "upload" ? 0 : step === "analyzing" ? 1 : 2;
  const failed = step === "failure";

  return (
    <div style={{ display: "flex", alignItems: "center", marginBottom: 24 }}>
      {steps.map((s, i) => (
        <div key={s} style={{ display: "flex", alignItems: "center", flex: 1 }}>
          <div style={{ display: "flex", flexDirection: "column", alignItems: "center", flex: 1 }}>
            <div style={{
              width: 28, height: 28, borderRadius: "50%",
              background: failed && i === 1 ? "#c62828" : i <= current ? "#1a1a1a" : "#f0f0f0",
              color: i <= current || (failed && i === 1) ? "#fff" : "#aaa",
              display: "flex", alignItems: "center", justifyContent: "center",
              fontSize: 11, fontWeight: 600, marginBottom: 4,
            }}>
              {failed && i === 1 ? "✕" : i < current ? "✓" : i + 1}
            </div>
            <span style={{ fontSize: 9, color: i <= current ? "#1a1a1a" : "#aaa", textAlign: "center", whiteSpace: "nowrap" }}>{s}</span>
          </div>
          {i < steps.length - 1 && (
            <div style={{ height: 1, flex: 1, background: i < current ? "#1a1a1a" : "#e0e0e0", margin: "0 4px", marginBottom: 18 }} />
          )}
        </div>
      ))}
    </div>
  );
}

export function FoodAnalyzePage({ onNavigate }: FoodAnalyzePageProps) {
  const [step, setStep] = useState<AnalyzeStep>("upload");
  const [mealType, setMealType] = useState<MealType>("BREAKFAST");
  const [hasImage, setHasImage] = useState(false);
  const [saveState, setSaveState] = useState<"IDLE" | "LOADING" | "SUCCESS" | "ERROR">("IDLE");

  const handleStartAnalysis = () => {
    if (!hasImage) return;
    setStep("analyzing");
    // TODO: API 연결 — POST /api/v1/food/analyze
    // ※ v2.0 기준: 이미지가 아닌 영양성분 텍스트 기반 동기 분석
    // body: { food_name (required), meal_type, meal_date, amount, calories, carbs_g, protein_g, fat_g, sodium_mg, sugar_g, fiber_g }
    // 응답: 201 { food_analysis_result_id, task_uuid, status: "SUCCESS", nutrition, health_score, risk_flags, advice_text }
    // Rate Limit: 사용자당 일 4회 (REQ-FOOD-001)
    // 개발용: 2초 후 결과로 이동
    setTimeout(() => {
      // 실패 시뮬레이션: setStep("failure")
      setStep("result");
    }, 2000);
  };

  const handleSaveResult = () => {
    setSaveState("LOADING");
    // TODO: API 연결 — POST /api/v1/health/meals
    // body: { food_analysis_result_id: DUMMY_RESULT.food_analysis_result_id, meal_type, meal_date }
    // food_analysis_result_id로 분석 결과와 연결하여 meal_logs에 저장
    // 저장 성공 후 /food 식단 기록 상세/수정 화면으로 이동
    setTimeout(() => {
      setSaveState("SUCCESS");
      setTimeout(() => onNavigate("/food"), 1200);
    }, 1000);
  };

  return (
    <div className="page-container">
      <h1 className="page-title">식단 AI 분석</h1>
      <StepIndicator step={step} />

      {/* ── 1단계: 사진 업로드 ── */}
      {step === "upload" && (
        <div style={{ background: "#fff", border: "1px solid #e0e0e0", borderRadius: 10, padding: 24 }}>
          <h2 style={{ fontSize: 14, fontWeight: 600, marginBottom: 4 }}>식사 사진 업로드</h2>
          <p style={{ fontSize: 12, color: "#888", marginBottom: 20 }}>음식 사진을 업로드하면 AI가 자동으로 영양 성분을 분석합니다.</p>

          <h3 style={{ fontSize: 12, fontWeight: 600, marginBottom: 10 }}>식사 유형</h3>
          <div style={{ display: "flex", gap: 8, marginBottom: 20 }}>
            {(Object.keys(MEAL_LABELS) as MealType[]).map(type => (
              <button key={type} onClick={() => setMealType(type)}
                style={{ flex: 1, padding: 10, border: `1.5px solid ${mealType === type ? "#1a1a1a" : "#ddd"}`,
                  borderRadius: 5, background: mealType === type ? "#f5f5f5" : "#fff",
                  fontSize: 11, fontWeight: mealType === type ? 700 : 400, cursor: "pointer" }}>
                {MEAL_LABELS[type]}
              </button>
            ))}
          </div>

          {/* 업로드 영역 */}
          <div
            onClick={() => setHasImage(true)}
            style={{ height: 200, border: `2px dashed ${hasImage ? "#1a1a1a" : "#ddd"}`, borderRadius: 8,
              display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center",
              cursor: "pointer", background: hasImage ? "#f5f5f5" : "#fafafa", marginBottom: 8 }}>
            {hasImage ? (
              <>
                <div style={{ fontSize: 40, marginBottom: 8 }}>🖼️</div>
                <p style={{ fontSize: 12, color: "#555" }}>이미지가 선택되었습니다</p>
              </>
            ) : (
              <>
                <div style={{ fontSize: 40, marginBottom: 8 }}>📸</div>
                <p style={{ fontSize: 12, color: "#888" }}>이미지를 드래그하거나 클릭하여 업로드</p>
              </>
            )}
          </div>
          <p style={{ fontSize: 11, color: "#aaa", textAlign: "center", marginBottom: 20 }}>JPG, PNG · 최대 10MB · 하루 최대 4회</p>

          <hr style={{ border: "none", borderTop: "1px solid #e0e0e0", margin: "0 0 16px" }} />

          <h3 style={{ fontSize: 12, fontWeight: 600, marginBottom: 10 }}>촬영 팁</h3>
          <div style={{ display: "flex", flexDirection: "column", gap: 6, marginBottom: 20 }}>
            {["음식이 잘 보이도록 정면에서 촬영해주세요", "밝은 곳에서 촬영하면 분석 정확도가 높아집니다", "여러 음식이 섞여있어도 괜찮습니다"].map((tip, i) => (
              <div key={i} style={{ display: "flex", gap: 8, alignItems: "flex-start" }}>
                <span style={{ fontSize: 11, color: "#2e7d32", marginTop: 1 }}>✓</span>
                <span style={{ fontSize: 11, color: "#888" }}>{tip}</span>
              </div>
            ))}
          </div>

          <div style={{ display: "flex", gap: 10, marginBottom: 12 }}>
            <button onClick={() => setHasImage(true)}
              style={{ padding: "8px 16px", border: "none", borderRadius: 8, background: "#1a1a1a", color: "#fff", fontSize: 12, cursor: "pointer" }}>
              사진 선택
            </button>
            <button style={{ padding: "8px 16px", border: "1.5px solid #ddd", borderRadius: 8, background: "#fff", fontSize: 12, cursor: "pointer" }}>
              카메라 촬영
            </button>
          </div>
          <button onClick={handleStartAnalysis} disabled={!hasImage}
            style={{ width: "100%", height: 40, border: "none", borderRadius: 8,
              background: hasImage ? "#1a1a1a" : "#ccc", color: "#fff",
              fontSize: 13, fontWeight: 600, cursor: hasImage ? "pointer" : "not-allowed" }}>
            분석 시작
          </button>
        </div>
      )}

      {/* ── 2단계: 분석 진행중 ── */}
      {step === "analyzing" && (
        <div style={{ background: "#fff", border: "1px solid #e0e0e0", borderRadius: 10, padding: 32, textAlign: "center" }}>
          <div style={{ width: 96, height: 96, borderRadius: "50%", background: "#f5f5f5", border: "1.5px solid #ddd",
            display: "flex", alignItems: "center", justifyContent: "center", margin: "0 auto 20px", fontSize: 36 }}>
            ⏳
          </div>
          <h2 style={{ fontSize: 15, fontWeight: 600, marginBottom: 8 }}>AI가 식단을 분석하고 있습니다...</h2>
          <p style={{ fontSize: 12, color: "#888", marginBottom: 24 }}>잠시만 기다려주세요.</p>

          <div style={{ height: 8, background: "#f0f0f0", borderRadius: 4, marginBottom: 20 }}>
            <div style={{ width: "65%", height: "100%", background: "#1a1a1a", borderRadius: 4,
              animation: "progress 2s ease-in-out" }} />
          </div>

          <div style={{ display: "flex", flexDirection: "column", gap: 8, alignItems: "center", marginBottom: 24 }}>
            <p style={{ fontSize: 11, fontWeight: 600, color: "#2e7d32", margin: 0 }}>✓ 음식 인식 완료</p>
            <div style={{ display: "flex", gap: 6, alignItems: "center" }}>
              <span style={{ fontSize: 11 }}>⏳</span>
              <p style={{ fontSize: 11, fontWeight: 600, margin: 0 }}>영양 성분 분석 중...</p>
            </div>
            <p style={{ fontSize: 11, color: "#aaa", margin: 0 }}>○ 결과 생성 대기</p>
          </div>

          <button onClick={() => setStep("upload")}
            style={{ display: "flex", alignItems: "center", gap: 8, background: "none", border: "none", cursor: "pointer", margin: "0 auto" }}>
            <div style={{ width: 28, height: 28, borderRadius: "50%", border: "1.5px solid #ddd",
              display: "flex", alignItems: "center", justifyContent: "center", fontSize: 14 }}>×</div>
            <span style={{ fontSize: 11, color: "#888" }}>취소</span>
          </button>
        </div>
      )}

      {/* ── 3단계: 분석 결과 ── */}
      {step === "result" && (
        <div style={{ display: "grid", gridTemplateColumns: "1fr 320px", gap: 14 }}>
          {/* 좌측 */}
          <div>
            <div style={{ background: "#fff", border: "1px solid #e0e0e0", borderRadius: 10, padding: 20, marginBottom: 14 }}>
              <h3 style={{ fontSize: 13, fontWeight: 600, marginBottom: 14 }}>인식된 음식</h3>
              <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 10 }}>
                {DUMMY_RESULT.foods.map((food, i) => (
                  <div key={i} style={{ display: "flex", gap: 8, padding: 8, border: "1px solid #e0e0e0", borderRadius: 6, position: "relative", alignItems: "center" }}>
                    <div style={{ width: 40, height: 40, background: "#f5f5f5", borderRadius: 6, display: "flex", alignItems: "center", justifyContent: "center", fontSize: 20, flexShrink: 0 }}>🍚</div>
                    <div style={{ flex: 1 }}>
                      <p style={{ fontSize: 12, fontWeight: 600, margin: 0 }}>{food.name}</p>
                      <p style={{ fontSize: 10, color: "#888", margin: "2px 0 0" }}>1인분</p>
                    </div>
                    <div style={{ position: "absolute", top: 6, right: 6, padding: "2px 6px",
                      background: "#f5f5f5", borderRadius: 10, fontSize: 9, color: "#555" }}>
                      {food.confidence}%
                    </div>
                  </div>
                ))}
              </div>
            </div>

            <div style={{ background: "#fff", border: "1px solid #e0e0e0", borderRadius: 10, padding: 20 }}>
              <h3 style={{ fontSize: 13, fontWeight: 600, marginBottom: 14 }}>영양 성분 분석</h3>
              <div style={{ display: "grid", gridTemplateColumns: "repeat(4, 1fr)", gap: 12, marginBottom: 14 }}>
                {[
                  { label: "칼로리", val: DUMMY_RESULT.nutrition.calories, unit: "kcal", bg: "#e8f5e9", color: "#2e7d32", border: "#a5d6a7" },
                  { label: "탄수화물", val: DUMMY_RESULT.nutrition.carbs_g, unit: "g", bg: "#fff8e1", color: "#f57f17", border: "#ffe082" },
                  { label: "단백질", val: DUMMY_RESULT.nutrition.protein_g, unit: "g", bg: "#e3f2fd", color: "#1565c0", border: "#90caf9" },
                  { label: "지방", val: DUMMY_RESULT.nutrition.fat_g, unit: "g", bg: "#fce4ec", color: "#c2185b", border: "#f48fb1" },
                ].map(item => (
                  <div key={item.label} style={{ textAlign: "center", padding: "10px 12px", background: item.bg, borderRadius: 8, border: `1.5px solid ${item.border}` }}>
                    <div style={{ fontSize: 10, color: item.color, marginBottom: 4 }}>{item.label}</div>
                    <div style={{ fontSize: 18, fontWeight: 700, color: item.color }}>
                      {item.val}<span style={{ fontSize: 10, fontWeight: 400, color: "#aaa" }}>{item.unit}</span>
                    </div>
                  </div>
                ))}
              </div>
              <hr style={{ border: "none", borderTop: "1px solid #e0e0e0", margin: "0 0 14px" }} />
              <h3 style={{ fontSize: 12, fontWeight: 600, marginBottom: 10 }}>미량 영양소</h3>
              <div style={{ display: "grid", gridTemplateColumns: "repeat(3, 1fr)", gap: 10 }}>
                {[
                  { label: "나트륨", val: `${DUMMY_RESULT.nutrition.sodium_mg.toLocaleString()} mg` },
                  { label: "식이섬유", val: `${DUMMY_RESULT.nutrition.fiber_g} g` },
                  { label: "당류", val: `${DUMMY_RESULT.nutrition.sugar_g} g` },
                ].map(item => (
                  <div key={item.label} style={{ padding: 8 }}>
                    <p style={{ fontSize: 11, color: "#888", margin: "0 0 2px" }}>{item.label}</p>
                    <p style={{ fontSize: 13, fontWeight: 700, margin: 0 }}>{item.val}</p>
                  </div>
                ))}
              </div>
            </div>
          </div>

          {/* 우측 */}
          <div>
            <div style={{ background: "#fff", border: "1px solid #e0e0e0", borderRadius: 10, padding: 16, marginBottom: 14 }}>
              <h3 style={{ fontSize: 12, fontWeight: 600, marginBottom: 10 }}>분석 이미지</h3>
              <div style={{ height: 180, background: "#f5f5f5", borderRadius: 8, display: "flex", alignItems: "center", justifyContent: "center", fontSize: 40 }}>🖼️</div>
            </div>

            <div style={{ background: "#fff", border: "1px solid #e0e0e0", borderRadius: 10, padding: 16, marginBottom: 14 }}>
              <h3 style={{ fontSize: 12, fontWeight: 600, marginBottom: 10 }}>건강 평가</h3>
              <div style={{ display: "flex", gap: 6, marginBottom: 10, flexWrap: "wrap" }}>
                <span style={{ padding: "3px 8px", background: "#e8f5e9", border: "1px solid #a5d6a7", borderRadius: 12, fontSize: 10, color: "#2e7d32" }}>균형잡힌 식단</span>
                {DUMMY_RESULT.risk_flags.map(flag => (
                  <span key={flag} style={{ padding: "3px 8px", background: "#fff8e1", border: "1px solid #ffe082", borderRadius: 12, fontSize: 10, color: "#f57f17" }}>{flag}</span>
                ))}
              </div>
              {DUMMY_RESULT.nutrition.sodium_mg >= 2000 && (
                <div style={{ padding: "8px 12px", background: "#ffebee", border: "1px solid #ef9a9a", borderRadius: 6, display: "flex", gap: 6, alignItems: "flex-start", marginBottom: 8 }}>
                  <span>⚠️</span>
                  <p style={{ fontSize: 10, color: "#c62828", margin: 0 }}>나트륨이 1일 권장량(2000mg)을 초과했습니다.</p>
                </div>
              )}
              {DUMMY_RESULT.nutrition.sugar_g >= 25 && (
                <div style={{ padding: "8px 12px", background: "#fff3e0", border: "1px solid #ffcc80", borderRadius: 6, display: "flex", gap: 6, alignItems: "flex-start" }}>
                  <span>⚠️</span>
                  <p style={{ fontSize: 10, color: "#f57f17", margin: 0 }}>당류가 1일 권장량(25g)을 초과했습니다.</p>
                </div>
              )}
            </div>

            <div style={{ background: "#fff", border: "1px solid #e0e0e0", borderRadius: 10, padding: 16, marginBottom: 14 }}>
              <h3 style={{ fontSize: 12, fontWeight: 600, marginBottom: 10 }}>개선 제안</h3>
              <div style={{ display: "flex", flexDirection: "column", gap: 6 }}>
                {["나트륨 섭취 줄이기", "채소 반찬 추가", "단백질 보충 권장"].map(s => (
                  <p key={s} style={{ fontSize: 11, color: "#888", margin: 0 }}>• {s}</p>
                ))}
              </div>
            </div>

            <button onClick={handleSaveResult} disabled={saveState !== "IDLE"}
              style={{ width: "100%", height: 40, border: "none", borderRadius: 8, fontSize: 13, fontWeight: 600, cursor: saveState === "IDLE" ? "pointer" : "default",
                background: saveState === "SUCCESS" ? "#2e7d32" : saveState === "LOADING" ? "#888" : "#1a1a1a",
                color: "#fff" }}>
              {saveState === "LOADING" ? "저장 중..." : saveState === "SUCCESS" ? "저장 완료 ✓" : "기록으로 저장"}
            </button>
            {saveState === "ERROR" && <p style={{ fontSize: 11, color: "#c62828", textAlign: "center", marginTop: 8 }}>저장에 실패했습니다. 다시 시도해주세요.</p>}
          </div>
        </div>
      )}

      {/* ── 분석 실패 ── */}
      {step === "failure" && (
        <div style={{ background: "#fff", border: "1px solid #e0e0e0", borderRadius: 10, padding: 32 }}>
          <div style={{ textAlign: "center", marginBottom: 24 }}>
            <div style={{ width: 96, height: 96, borderRadius: "50%", background: "#fdecea", border: "1.5px solid #e8a8a8",
              display: "flex", alignItems: "center", justifyContent: "center", margin: "0 auto 20px", fontSize: 36 }}>
              😥
            </div>
            <h2 style={{ fontSize: 16, fontWeight: 600, marginBottom: 8 }}>식단 분석에 실패했습니다</h2>
            <p style={{ fontSize: 12, color: "#888" }}>음식 사진을 인식하지 못했습니다. 아래 안내에 따라 다시 시도해 주세요.</p>
          </div>

          <div style={{ background: "#fdecea", border: "1px solid #e8a8a8", borderRadius: 6, padding: "12px 16px", display: "flex", gap: 10, alignItems: "flex-start", marginBottom: 20 }}>
            <div style={{ width: 18, height: 18, borderRadius: "50%", background: "#c0392b", color: "#fff",
              display: "flex", alignItems: "center", justifyContent: "center", fontSize: 11, fontWeight: 600, flexShrink: 0, marginTop: 1 }}>!</div>
            <div>
              <p style={{ fontSize: 11, fontWeight: 600, color: "#c0392b", margin: "0 0 3px" }}>분석 오류</p>
              <p style={{ fontSize: 11, color: "#888", margin: 0 }}>이미지에서 음식을 감지할 수 없습니다. 음식이 명확하게 보이는 사진으로 다시 시도해 주세요.</p>
            </div>
          </div>

          <hr style={{ border: "none", borderTop: "1px solid #e0e0e0", margin: "0 0 20px" }} />

          <h3 style={{ fontSize: 12, fontWeight: 600, marginBottom: 10 }}>재시도 전 확인해 보세요</h3>
          <div style={{ display: "flex", flexDirection: "column", gap: 6, marginBottom: 24 }}>
            {["음식이 화면 중앙에 명확하게 나오도록 촬영했나요?", "사진이 너무 어둡거나 흐릿하지 않나요?", "JPG 또는 PNG 형식의 이미지 파일인가요?"].map((tip, i) => (
              <div key={i} style={{ display: "flex", gap: 8, alignItems: "flex-start" }}>
                <span style={{ fontSize: 11, color: "#2e7d32", marginTop: 1 }}>✓</span>
                <span style={{ fontSize: 11, color: "#888" }}>{tip}</span>
              </div>
            ))}
          </div>

          <div style={{ display: "flex", gap: 10 }}>
            <button onClick={() => onNavigate("/food")}
              style={{ flex: 1, height: 40, border: "1.5px solid #ddd", borderRadius: 8, background: "#fff", fontSize: 13, cursor: "pointer" }}>
              홈으로
            </button>
            <button onClick={() => setStep("upload")}
              style={{ flex: 1, height: 40, border: "none", borderRadius: 8, background: "#1a1a1a", color: "#fff", fontSize: 13, fontWeight: 600, cursor: "pointer" }}>
              다시 시도
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
