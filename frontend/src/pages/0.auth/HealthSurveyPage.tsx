import { useState, useEffect } from "react";
import type { AppRoute } from "../../App";
import { getStoredAccessToken } from "../../api/auth";
import { createHealthSurveyInput } from "../../api/predictions";
import { getCurrentUser } from "../../api/users";
import { Stepper } from "../../components/common/Stepper";

interface HealthSurveyPageProps {
  onNavigate: (route: AppRoute) => void;
}

const SIGNUP_DRAFT_KEY = "auth.signupDraft";
const ONBOARDING_PROFILE_KEY = "auth.onboardingProfile";

type HealthSurveySignupDraft = {
  birth_date?: string;
  gender?: "MALE" | "FEMALE";
  managed_diseases?: string[];
};

const SURVEY_STEPS = ["기본 정보", "건강 상태", "생활 습관"];

function RequiredNotice() {
  return <span style={{ fontSize: 10, color: "#E24B4A", fontWeight: 600 }}>* 필수 입력</span>;
}

function RequiredMark() {
  return <span style={{ color: "#E24B4A", marginLeft: 3 }}>*</span>;
}

function OptionButton({ label, selected, onClick }: { label: string; selected: boolean; onClick: () => void }) {
  return (
    <button onClick={onClick} style={{ padding: "10px 14px", border: `1.5px solid ${selected ? "#1a1a1a" : "#ddd"}`, borderRadius: 8, background: selected ? "#1a1a1a" : "#fff", fontSize: 12, fontWeight: selected ? 600 : 400, color: selected ? "#fff" : "#555", cursor: "pointer", height: 40, display: "flex", alignItems: "center", justifyContent: "center", width: "100%" }}>
      {label}
    </button>
  );
}

function SurveyPageWrapper({
  children,
  surveyStep,
}: {
  children: React.ReactNode;
  surveyStep: number;
}) {
  return (
    <div style={{ minHeight: "100vh", background: "#fafafa", display: "flex", alignItems: "center", justifyContent: "center", padding: 40, overflowY: "auto" }}>
      <div style={{ width: "100%", maxWidth: surveyStep >= 2 ? 720 : 680 }}>
        <div style={{ textAlign: "center", marginBottom: 24 }}>
          <img src="/logo.png" alt="All4Health" style={{ height: 36, margin: "0 auto 16px", display: "block" }} onError={e => { (e.target as HTMLImageElement).style.display = "none"; }} />
          <h2 style={{ fontSize: 18, fontWeight: 600, color: "#1a1a1a", margin: "0 0 8px" }}>건강 설문</h2>
          <p style={{ fontSize: 12, color: "#888", margin: 0 }}>정확한 건강 관리를 위한 기본 정보를 입력해주세요</p>
        </div>
        <Stepper steps={SURVEY_STEPS} current={Math.min(surveyStep, 2)} />
        {children}
      </div>
    </div>
  );
}

function SurveyNavButtons({
  onPrev,
  onNext,
  nextLabel = "다음",
  nextDisabled = false,
}: {
  onPrev: () => void;
  onNext: () => void;
  nextLabel?: string;
  nextDisabled?: boolean;
}) {
  return (
    <div style={{ display: "flex", justifyContent: "space-between", marginTop: 20, gap: 12 }}>
      <button onClick={onPrev} style={{ padding: "8px 20px", border: "1.5px solid #ddd", borderRadius: 8, fontSize: 13, color: "#555", cursor: "pointer", background: "#fff", height: 36 }}>이전</button>
      <button onClick={onNext} disabled={nextDisabled} style={{ padding: "8px 20px", border: "none", borderRadius: 8, fontSize: 13, color: "#fff", cursor: nextDisabled ? "not-allowed" : "pointer", background: nextDisabled ? "#ccc" : "#1a1a1a", height: 36, fontWeight: 600 }}>{nextLabel}</button>
    </div>
  );
}

function optionalNumber(value: string): number | null {
  if (!value.trim()) return null;
  const parsed = Number(value);
  return Number.isNaN(parsed) ? null : parsed;
}

function medicationCodes(items: string[]) {
  const map: Record<string, string | null> = {
    "고혈압 약": "HYPERTENSION",
    "당뇨 약": "DIABETES",
    "복용중인 약 없음": null,
  };
  return items.map(item => map[item]).filter((item): item is string => Boolean(item));
}

function smokingCode(value: string): 0 | 1 | 2 {
  if (value === "예") return 2;
  if (value === "과거 흡연") return 1;
  return 0;
}

function alcoholFrequencyCode(value: string): 0 | 1 | 3 {
  if (value === "주 3회 이상") return 3;
  if (value === "월 1~2회" || value === "주 1~2회") return 1;
  return 0;
}

function alcoholAmountCode(value: string): number | null {
  const map: Record<string, number> = {
    "1~2잔": 1,
    "3~4잔": 2,
    "5~6잔": 3,
    "7~9잔": 4,
    "10잔 이상": 5,
  };
  return map[value] ?? null;
}

function walkingDaysValue(value: string): number | null {
  const map: Record<string, number> = {
    "주 0일": 0,
    "주 1~2일": 2,
    "주 3~4일": 4,
    "주 5~6일": 6,
    "매일": 7,
  };
  return map[value] ?? null;
}

function exerciseFrequencyValue(value: string): number {
  const map: Record<string, number> = {
    "거의 안 함": 0,
    "주 1~2회": 2,
    "주 3~4회": 4,
    "거의 매일": 7,
  };
  return map[value] ?? 0;
}

function sleepHoursValue(value: string): number | null {
  const map: Record<string, number> = {
    "5시간 이하": 5,
    "6~7시간": 6.5,
    "8시간 이상": 8,
  };
  return map[value] ?? null;
}

function sedentaryHoursValue(value: string): number | null {
  const map: Record<string, number> = {
    "2시간 미만": 1,
    "2~5시간": 3.5,
    "5~8시간": 6.5,
    "8~10시간": 9,
    "10시간 이상": 10,
  };
  return map[value] ?? null;
}

function dietScoreValue(mealPatterns: string[], foodPreferences: string[]): number | null {
  if (mealPatterns.length === 0 && foodPreferences.length === 0) return null;
  let score = 6;
  if (mealPatterns.includes("규칙적인 식사")) score += 2;
  if (mealPatterns.some(item => ["야식 자주 섭취", "끼니를 거르는 편"].includes(item))) score -= 2;
  if (foodPreferences.includes("채소 섭취가 많은 편")) score += 2;
  if (foodPreferences.some(item => ["단 음식 선호", "짠 음식 선호", "기름진 음식 선호"].includes(item))) score -= 2;
  return Math.max(0, Math.min(10, score));
}

function toggleSelection(items: string[], item: string) {
  return items.includes(item) ? items.filter(value => value !== item) : [...items, item];
}

export function HealthSurveyPage({ onNavigate }: HealthSurveyPageProps) {
  const [surveyStep, setSurveyStep] = useState(0); // 0: 기본정보, 1: 건강상태, 2: 생활습관1, 3: 생활습관2

  // 기본 정보
  const [birthDate, setBirthDate] = useState("");
  const [gender, setGender] = useState<"MALE" | "FEMALE" | "">("");
  const [height, setHeight] = useState("170");
  const [weight, setWeight] = useState("65");
  const [waist, setWaist] = useState("");
  const [bmi, setBmi] = useState<number | null>(null);

  // 건강 상태
  const [medications, setMedications] = useState<string[]>([]);
  const [lastCheckup, setLastCheckup] = useState(""); // 최근 건강검진
  const [systolic, setSystolic] = useState("130");
  const [diastolic, setDiastolic] = useState("80");
  const [fastingGlucose, setFastingGlucose] = useState("100");

  // 가족력
  const [fhDiabetesFather, setFhDiabetesFather] = useState(false);
  const [fhDiabetesMother, setFhDiabetesMother] = useState(false);
  const [fhDiabetesSibling, setFhDiabetesSibling] = useState(false);
  const [fhHypertensionFather, setFhHypertensionFather] = useState(false);
  const [fhHypertensionMother, setFhHypertensionMother] = useState(false);
  const [fhHypertensionSibling, setFhHypertensionSibling] = useState(false);
  const [fhCkd, setFhCkd] = useState(false);

  // 생활습관1
  const [exerciseFreq, setExerciseFreq] = useState("");
  const [physicalActivityMin, setPhysicalActivityMin] = useState(""); // 주간 운동 총 시간(분)
  const [walkingDays, setWalkingDays] = useState("");
  const [sleepTime, setSleepTime] = useState("");
  const [smoking, setSmoking] = useState("");
  const [drinking, setDrinking] = useState("");
  const [drinkingAmount, setDrinkingAmount] = useState(""); // 1회 평균 음주량

  // 생활습관2
  const [mealPatterns, setMealPatterns] = useState<string[]>([]);
  const [foodPreferences, setFoodPreferences] = useState<string[]>([]);
  const [sittingTime, setSittingTime] = useState("");
  const [stressLevel, setStressLevel] = useState(2);
  const [isSavingSurvey, setIsSavingSurvey] = useState(false);
  const [surveyError, setSurveyError] = useState("");

  useEffect(() => {
    const rawDraft = sessionStorage.getItem(ONBOARDING_PROFILE_KEY) ?? sessionStorage.getItem(SIGNUP_DRAFT_KEY);

    if (rawDraft) {
      try {
        const draft = JSON.parse(rawDraft) as HealthSurveySignupDraft;
        if (draft.birth_date) setBirthDate(draft.birth_date);
        if (draft.gender) setGender(draft.gender);
        if (draft.birth_date && draft.gender) return;
      } catch {
        // 저장된 회원가입 임시 정보가 깨진 경우에는 사용자 정보 API로 보완합니다.
      }
    }

    const token = getStoredAccessToken();
    if (!token) return;

    getCurrentUser(token)
      .then(user => {
        setBirthDate(user.birthday);
        setGender(user.gender);
      })
      .catch(() => {
        // 사용자 정보를 불러오지 못하면 화면의 "회원가입 정보 없음" 상태를 유지합니다.
      });
  }, []);

  useEffect(() => {
    const h = parseFloat(height);
    const w = parseFloat(weight);
    if (h > 0 && w > 0) setBmi(w / Math.pow(h / 100, 2));
    else setBmi(null);
  }, [height, weight]);

  const getBmiStatus = (val: number | null) => {
    if (!val) return { label: "입력 대기 중", color: "#aaa" };
    if (val < 18.5) return { label: "저체중", color: "#2196F3" };
    if (val < 25) return { label: "정상", color: "#2e7d32" };
    if (val < 30) return { label: "과체중", color: "#FFC107" };
    return { label: "비만", color: "#F44336" };
  };

  const bmiStatus = getBmiStatus(bmi);

  // ── 기본 정보 ──
  if (surveyStep === 0) {
    return (
      <SurveyPageWrapper surveyStep={surveyStep}>
        <div style={{ background: "#fff", border: "1px solid #e0e0e0", borderRadius: 10, padding: 24, marginTop: 20 }}>
          <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: 16 }}>
            <h3 style={{ fontSize: 13, fontWeight: 600, color: "#1a1a1a", margin: 0 }}>기본 정보</h3>
            <RequiredNotice />
          </div>
          <div style={{ display: "flex", flexDirection: "column", gap: 16 }}>
            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 14 }}>
              <div>
                <label style={{ fontSize: 10, color: "#555", display: "block", marginBottom: 4 }}>생년월일<RequiredMark /></label>
                <div style={{ height: 34, border: "1.5px dashed #ddd", borderRadius: 5, padding: "0 10px", display: "flex", alignItems: "center", justifyContent: "space-between", background: "#fafafa" }}>
                  <span style={{ fontSize: 11, color: birthDate ? "#333" : "#aaa" }}>{birthDate || "회원가입 정보 없음"}</span>
                  <span style={{ fontSize: 9, color: "#aaa" }}>(회원가입 시 입력)</span>
                </div>
              </div>
              <div>
                <label style={{ fontSize: 10, color: "#555", display: "block", marginBottom: 4 }}>성별<RequiredMark /></label>
                <div style={{ height: 34, border: "1.5px dashed #ddd", borderRadius: 5, padding: "0 10px", display: "flex", alignItems: "center", justifyContent: "space-between" }}>
                  <span style={{ fontSize: 11, color: gender ? "#333" : "#aaa" }}>
                    {gender === "MALE" ? "남성" : gender === "FEMALE" ? "여성" : "회원가입 정보 없음"}
                  </span>
                  <span style={{ fontSize: 9, color: "#aaa" }}>(회원가입 시 입력)</span>
                </div>
              </div>
            </div>

            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 14 }}>
              <div>
                <label style={{ fontSize: 10, color: "#555", display: "block", marginBottom: 4 }}>신장 (cm)<RequiredMark /></label>
                <input type="number" value={height} onChange={e => setHeight(e.target.value)} placeholder="170"
                  style={{ width: "100%", height: 34, border: "1.5px solid #ddd", borderRadius: 5, padding: "0 10px", fontSize: 11, boxSizing: "border-box", outline: "none" }} />
              </div>
              <div>
                <label style={{ fontSize: 10, color: "#555", display: "block", marginBottom: 4 }}>체중 (kg)<RequiredMark /></label>
                <input type="number" value={weight} onChange={e => setWeight(e.target.value)} placeholder="65"
                  style={{ width: "100%", height: 34, border: "1.5px solid #ddd", borderRadius: 5, padding: "0 10px", fontSize: 11, boxSizing: "border-box", outline: "none" }} />
              </div>
            </div>

            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 14 }}>
              <div>
                <label style={{ fontSize: 10, color: "#555", display: "block", marginBottom: 4 }}>BMI (자동 계산)</label>
                <div style={{ height: 34, border: `2px solid ${bmiStatus.color}`, borderRadius: 5, padding: "0 12px", display: "flex", alignItems: "center", gap: 8, background: "#fafafa" }}>
                  <span style={{ fontSize: 14, fontWeight: 700, color: "#1a1a1a" }}>{bmi ? bmi.toFixed(1) : "—"}</span>
                  <span style={{ fontSize: 11, fontWeight: 600, color: bmiStatus.color }}>{bmiStatus.label}</span>
                </div>
              </div>
              <div>
                <label style={{ fontSize: 10, color: "#555", display: "block", marginBottom: 4 }}>허리둘레 (cm) - 선택</label>
                <input type="number" value={waist} onChange={e => setWaist(e.target.value)} placeholder="예: 80"
                  style={{ width: "100%", height: 34, border: "1.5px solid #ddd", borderRadius: 5, padding: "0 10px", fontSize: 11, boxSizing: "border-box", outline: "none" }} />
              </div>
            </div>
          </div>
        </div>
        <SurveyNavButtons onPrev={() => onNavigate("/email-verify")} onNext={() => setSurveyStep(1)} />
      </SurveyPageWrapper>
    );
  }

  // ── 건강 상태 ──
  if (surveyStep === 1) {
    const MED_OPTIONS = [
      { name: "고혈압 약", color: "#df8aac", bg: "#fce4ec" },
      { name: "당뇨 약", color: "#f57f17", bg: "#fff9c4" },
      { name: "복용중인 약 없음", color: "#555", bg: "#fafafa" },
    ];
    const toggleItem = (arr: string[], item: string, setFn: (v: string[]) => void) => {
      setFn(arr.includes(item) ? arr.filter(x => x !== item) : [...arr, item]);
    };

    return (
      <SurveyPageWrapper surveyStep={surveyStep}>
        <div style={{ background: "#fff", border: "1px solid #e0e0e0", borderRadius: 10, padding: 20, marginTop: 20 }}>
          <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: 12 }}>
            <h3 style={{ fontSize: 13, fontWeight: 600, color: "#1a1a1a", margin: 0 }}>건강 상태</h3>
            <RequiredNotice />
          </div>
          <div style={{ display: "flex", flexDirection: "column", gap: 14 }}>
            {/* 현재 복용약 */}
            <div>
              <label style={{ fontSize: 10, fontWeight: 500, color: "#555", display: "block", marginBottom: 8 }}>현재 복용 중인 약</label>
              <div style={{ display: "grid", gridTemplateColumns: "repeat(3, 1fr)", gap: 8 }}>
                {MED_OPTIONS.map(m => (
                  <button key={m.name} onClick={() => toggleItem(medications, m.name, setMedications)}
                    style={{ padding: "9px 6px", border: `1.5px solid ${medications.includes(m.name) ? m.color : "#ddd"}`, borderRadius: 5, background: medications.includes(m.name) ? m.color : m.bg, textAlign: "center", fontSize: 10, color: medications.includes(m.name) ? "#fff" : m.color, cursor: "pointer" }}>
                    {m.name}
                  </button>
                ))}
              </div>
              <p style={{ fontSize: 9, color: "#aaa", margin: "4px 0 0" }}>※ 현재 복용 중인 약이 없다면 '복용중인 약 없음'을 선택해주세요.</p>
            </div>

            {/* 최근 건강검진 */}
            <div>
              <label style={{ fontSize: 10, fontWeight: 500, color: "#555", display: "block", marginBottom: 8 }}>최근 건강검진</label>
              <div style={{ display: "grid", gridTemplateColumns: "repeat(4, 1fr)", gap: 8 }}>
                {[
                  { label: "6개월 미만", value: "UNDER_6_MONTHS" },
                  { label: "6개월~1년 미만", value: "UNDER_1_YEAR" },
                  { label: "1년 이상", value: "OVER_1_YEAR" },
                  { label: "한 적 없음", value: "NEVER" },
                ].map(opt => (
                  <button key={opt.value} onClick={() => setLastCheckup(opt.value)}
                    style={{ padding: "9px 6px", border: `1.5px solid ${lastCheckup === opt.value ? "#1a1a1a" : "#ddd"}`, borderRadius: 5, background: lastCheckup === opt.value ? "#1a1a1a" : "#fafafa", textAlign: "center", fontSize: 10, color: lastCheckup === opt.value ? "#fff" : "#555", cursor: "pointer" }}>
                    {opt.label}
                  </button>
                ))}
              </div>
              <p style={{ fontSize: 9, color: "#aaa", margin: "4px 0 0" }}>※ 최근 검진 시기를 기준으로 건강관리 안내에 활용됩니다.</p>
            </div>

            {/* 가족력 */}
            <div>
              <label style={{ fontSize: 10, fontWeight: 500, color: "#555", display: "block", marginBottom: 8 }}>가족력</label>
              <div style={{ display: "grid", gridTemplateColumns: "repeat(3, 1fr)", gap: 8 }}>
                {/* 고혈압 가족력 */}
                <div style={{ background: "#fce4ec", border: "1px solid #c2185b", borderRadius: 6, padding: "8px 10px" }}>
                  <p style={{ fontSize: 10, fontWeight: 600, color: "#c2185b", margin: "0 0 6px" }}>고혈압</p>
                  {[
                    { label: "아버지", state: fhHypertensionFather, setState: setFhHypertensionFather },
                    { label: "어머니", state: fhHypertensionMother, setState: setFhHypertensionMother },
                    { label: "형제/자매", state: fhHypertensionSibling, setState: setFhHypertensionSibling },
                  ].map(item => (
                    <label key={item.label} style={{ display: "flex", alignItems: "center", gap: 6, marginBottom: 4, cursor: "pointer" }}>
                      <input type="checkbox" checked={item.state} onChange={e => item.setState(e.target.checked)} style={{ width: 12, height: 12 }} />
                      <span style={{ fontSize: 11, color: "#333" }}>{item.label}</span>
                    </label>
                  ))}
                </div>
                {/* 당뇨 가족력 */}
                <div style={{ background: "#fff9c4", border: "1px solid #f57f17", borderRadius: 6, padding: "8px 10px" }}>
                  <p style={{ fontSize: 10, fontWeight: 600, color: "#f57f17", margin: "0 0 6px" }}>당뇨</p>
                  {[
                    { label: "아버지", state: fhDiabetesFather, setState: setFhDiabetesFather },
                    { label: "어머니", state: fhDiabetesMother, setState: setFhDiabetesMother },
                    { label: "형제/자매", state: fhDiabetesSibling, setState: setFhDiabetesSibling },
                  ].map(item => (
                    <label key={item.label} style={{ display: "flex", alignItems: "center", gap: 6, marginBottom: 4, cursor: "pointer" }}>
                      <input type="checkbox" checked={item.state} onChange={e => item.setState(e.target.checked)} style={{ width: 12, height: 12 }} />
                      <span style={{ fontSize: 11, color: "#333" }}>{item.label}</span>
                    </label>
                  ))}
                </div>
                {/* 신장질환 가족력 */}
                <div style={{ background: "#e3f2fd", border: "1px solid #1565c0", borderRadius: 6, padding: "8px 10px" }}>
                  <p style={{ fontSize: 10, fontWeight: 600, color: "#1565c0", margin: "0 0 6px" }}>신장질환</p>
                  {[
                    { label: "있음", state: fhCkd, setState: setFhCkd },
                    { label: "없음", state: !fhCkd, setState: (v: boolean) => setFhCkd(!v) },
                  ].map(item => (
                    <label key={item.label} style={{ display: "flex", alignItems: "center", gap: 6, marginBottom: 4, cursor: "pointer" }}>
                      <input type="checkbox" checked={item.state} onChange={e => item.setState(e.target.checked)} style={{ width: 12, height: 12 }} />
                      <span style={{ fontSize: 11, color: "#333" }}>{item.label}</span>
                    </label>
                  ))}
                </div>
              </div>
            </div>

            {/* 혈압 / 공복혈당 */}
            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 20 }}>
              <div>
                <label style={{ fontSize: 10, fontWeight: 500, color: "#c2185b", display: "block", marginBottom: 6 }}>혈압 (mmHg)</label>
                <div style={{ display: "grid", gridTemplateColumns: "1fr auto 1fr", gap: 8, alignItems: "center" }}>
                  <input type="number" value={systolic} onChange={e => setSystolic(e.target.value)} style={{ height: 32, border: "1.5px solid #c2185b", borderRadius: 5, padding: "0 10px", fontSize: 11, background: "#fce4ec", outline: "none" }} />
                  <span style={{ textAlign: "center", fontSize: 11, color: "#555" }}>/</span>
                  <input type="number" value={diastolic} onChange={e => setDiastolic(e.target.value)} style={{ height: 32, border: "1.5px solid #1565c0", borderRadius: 5, padding: "0 10px", fontSize: 11, background: "#e3f2fd", outline: "none" }} />
                </div>
              </div>
              <div>
                <label style={{ fontSize: 10, fontWeight: 500, color: "#f57f17", display: "block", marginBottom: 6 }}>공복혈당 (mg/dL)</label>
                <input type="number" value={fastingGlucose} onChange={e => setFastingGlucose(e.target.value)} style={{ width: "100%", height: 32, border: "1.5px solid #f57f17", borderRadius: 5, padding: "0 10px", fontSize: 11, background: "#fff9c4", outline: "none", boxSizing: "border-box" }} />
              </div>
            </div>
          </div>
        </div>
        <SurveyNavButtons onPrev={() => setSurveyStep(0)} onNext={() => setSurveyStep(2)} />
      </SurveyPageWrapper>
    );
  }

  // ── 생활습관 1 ──
  if (surveyStep === 2) {
    return (
      <SurveyPageWrapper surveyStep={surveyStep}>
        <div style={{ background: "#fff", border: "1px solid #e0e0e0", borderRadius: 12, padding: 28, marginTop: 24 }}>
          <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: 24 }}>
            <h3 style={{ fontSize: 15, fontWeight: 600, color: "#1a1a1a", margin: 0 }}>신체활동 영역</h3>
            <RequiredNotice />
          </div>
          <div style={{ marginBottom: 28 }}>
            <label style={{ fontSize: 12, fontWeight: 600, color: "#1a1a1a", display: "block", marginBottom: 12 }}>운동 빈도</label>
            <div style={{ display: "grid", gridTemplateColumns: "repeat(4, 1fr)", gap: 10 }}>
              {["거의 안 함", "주 1~2회", "주 3~4회", "거의 매일"].map(d => <OptionButton key={d} label={d} selected={exerciseFreq === d} onClick={() => setExerciseFreq(d)} />)}
            </div>
          </div>
          <div style={{ marginBottom: 28 }}>
            <label style={{ fontSize: 12, fontWeight: 600, color: "#1a1a1a", display: "block", marginBottom: 12 }}>걷기 일수</label>
            <div style={{ display: "grid", gridTemplateColumns: "repeat(5, 1fr)", gap: 10 }}>
              {["주 0일", "주 1~2일", "주 3~4일", "주 5~6일", "매일"].map(d => <OptionButton key={d} label={d} selected={walkingDays === d} onClick={() => setWalkingDays(d)} />)}
            </div>
          </div>
          <div style={{ marginBottom: 28 }}>
            <label style={{ fontSize: 12, fontWeight: 600, color: "#1a1a1a", display: "block", marginBottom: 8 }}>주간 운동 총 시간 (분)</label>
            <p style={{ fontSize: 11, color: "#888", margin: "0 0 10px" }}>이번 주 총 운동 시간을 분 단위로 입력해주세요. (예: 150)</p>
            <input
              type="number" value={physicalActivityMin} onChange={e => setPhysicalActivityMin(e.target.value)}
              placeholder="예: 150"
              style={{ width: "100%", height: 36, border: "1.5px solid #ddd", borderRadius: 8, padding: "0 12px", fontSize: 12, outline: "none", boxSizing: "border-box" }}
            />
            <p style={{ fontSize: 9, color: "#aaa", margin: "4px 0 0" }}>※ 선택 입력 항목입니다.</p>
          </div>
          <div style={{ marginBottom: 28 }}>
            <label style={{ fontSize: 12, fontWeight: 600, color: "#1a1a1a", display: "block", marginBottom: 12 }}>평균 수면 시간</label>
            <div style={{ display: "grid", gridTemplateColumns: "repeat(3, 1fr)", gap: 10 }}>
              {["5시간 이하", "6~7시간", "8시간 이상"].map(d => <OptionButton key={d} label={d} selected={sleepTime === d} onClick={() => setSleepTime(d)} />)}
            </div>
          </div>
          <hr style={{ border: "none", borderTop: "1px solid #eee", margin: "0 0 24px" }} />
          <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: 24 }}>
            <h3 style={{ fontSize: 15, fontWeight: 600, color: "#1a1a1a", margin: 0 }}>기호습관 영역</h3>
            <RequiredNotice />
          </div>
          <div style={{ marginBottom: 28 }}>
            <label style={{ fontSize: 12, fontWeight: 600, color: "#1a1a1a", display: "block", marginBottom: 14 }}>현재 흡연 중이신가요?</label>
            <div style={{ display: "flex", gap: 24 }}>
              {["예", "아니오", "과거 흡연"].map(opt => (
                <label key={opt} style={{ display: "flex", alignItems: "center", gap: 8, cursor: "pointer" }}>
                  <input type="radio" checked={smoking === opt} onChange={() => setSmoking(opt)} style={{ width: 16, height: 16 }} />
                  <span style={{ fontSize: 12, color: "#333" }}>{opt}</span>
                </label>
              ))}
            </div>
          </div>
          <div style={{ marginBottom: drinking !== "안 마심" ? 28 : 0 }}>
            <label style={{ fontSize: 12, fontWeight: 600, color: "#1a1a1a", display: "block", marginBottom: 14 }}>현재 음주를 하시나요?</label>
            <div style={{ display: "flex", gap: 24 }}>
              {["안 마심", "월 1~2회", "주 1~2회", "주 3회 이상"].map(opt => (
                <label key={opt} style={{ display: "flex", alignItems: "center", gap: 8, cursor: "pointer" }}>
                  <input type="radio" checked={drinking === opt} onChange={() => { setDrinking(opt); if (opt === "안 마심") setDrinkingAmount(""); }} style={{ width: 16, height: 16 }} />
                  <span style={{ fontSize: 12, color: "#333" }}>{opt}</span>
                </label>
              ))}
            </div>
          </div>
          {drinking !== "" && drinking !== "안 마심" && (
            <div>
              <label style={{ fontSize: 12, fontWeight: 600, color: "#1a1a1a", display: "block", marginBottom: 14 }}>1회 평균 음주량 <span style={{ fontSize: 11, color: "#888", fontWeight: 400 }}>(소주 기준)</span><RequiredMark /></label>
              <div style={{ display: "grid", gridTemplateColumns: "repeat(5, 1fr)", gap: 10 }}>
                {["1~2잔", "3~4잔", "5~6잔", "7~9잔", "10잔 이상"].map(opt => (
                  <OptionButton key={opt} label={opt} selected={drinkingAmount === opt} onClick={() => setDrinkingAmount(opt)} />
                ))}
              </div>
              <p style={{ fontSize: 9, color: "#aaa", margin: "4px 0 0" }}>※ alcohol_amount: 1~5 (음주 없음이면 미입력)</p>
            </div>
          )}
        </div>
        <SurveyNavButtons onPrev={() => setSurveyStep(1)} onNext={() => setSurveyStep(3)} />
      </SurveyPageWrapper>
    );
  }

  // ── 생활습관 2 ──
  const stressEmojis = ["😄", "🙂", "😐", "😟", "😫"];
  const stressLabels = ["매우 낮음", "낮음", "보통", "높음", "매우 높음"];

  const handleComplete = async () => {
    setSurveyError("");
    const token = getStoredAccessToken();
    if (!token) {
      setSurveyError("로그인이 필요합니다. 다시 로그인해주세요.");
      return;
    }

    const alcoholFrequency = alcoholFrequencyCode(drinking);
    const alcoholAmount = alcoholFrequency === 0 ? null : alcoholAmountCode(drinkingAmount);
    if (alcoholFrequency !== 0 && alcoholAmount === null) {
      setSurveyError("1회 평균 음주량을 선택해주세요.");
      return;
    }

    setIsSavingSurvey(true);
    try {
      await createHealthSurveyInput(
        {
          input_mode: "DEEP",
          birth_date: birthDate,
          height: Number(height),
          weight: Number(weight),
          waist_circumference: optionalNumber(waist),
          diagnosed_diseases: [],
          medications: medicationCodes(medications),
          last_checkup_period: lastCheckup || null,
          sbp: optionalNumber(systolic),
          dbp: optionalNumber(diastolic),
          glucose_fasting: optionalNumber(fastingGlucose),
          fh_diabetes_father: fhDiabetesFather,
          fh_diabetes_mother: fhDiabetesMother,
          fh_diabetes_sibling: fhDiabetesSibling,
          fh_hypertension_father: fhHypertensionFather,
          fh_hypertension_mother: fhHypertensionMother,
          fh_hypertension_sibling: fhHypertensionSibling,
          family_history_ckd: fhCkd,
          smoking_status: smokingCode(smoking),
          alcohol_frequency: alcoholFrequency,
          alcohol_amount: alcoholAmount,
          walking_days: walkingDaysValue(walkingDays),
          sedentary_hours: sedentaryHoursValue(sittingTime),
          exercise_frequency: exerciseFrequencyValue(exerciseFreq),
          physical_activity_min: optionalNumber(physicalActivityMin),
          sleep_hours: sleepHoursValue(sleepTime),
          stress_level: stressLevel + 1,
          diet_score: dietScoreValue(mealPatterns, foodPreferences),
        },
        token,
      );
      sessionStorage.removeItem(ONBOARDING_PROFILE_KEY);
      onNavigate("/onboarding-complete");
    } catch {
      setSurveyError("건강 설문 저장에 실패했습니다. 입력값을 확인해주세요.");
    } finally {
      setIsSavingSurvey(false);
    }
  };

  return (
    <SurveyPageWrapper surveyStep={surveyStep}>
      <div style={{ background: "#fff", border: "1px solid #e0e0e0", borderRadius: 12, padding: 28, marginTop: 24 }}>
        <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: 24 }}>
          <h3 style={{ fontSize: 15, fontWeight: 600, color: "#1a1a1a", margin: 0 }}>식습관 영역</h3>
          <RequiredNotice />
        </div>
        <div style={{ marginBottom: 28 }}>
          <label style={{ fontSize: 12, fontWeight: 600, color: "#1a1a1a", display: "block", marginBottom: 12 }}>식사 패턴</label>
          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 10 }}>
            {["규칙적인 식사", "아침 식사 자주 생략", "야식 자주 섭취", "끼니를 거르는 편"].map(d => <OptionButton key={d} label={d} selected={mealPatterns.includes(d)} onClick={() => setMealPatterns(prev => toggleSelection(prev, d))} />)}
          </div>
        </div>
        <div style={{ marginBottom: 28 }}>
          <label style={{ fontSize: 12, fontWeight: 600, color: "#1a1a1a", display: "block", marginBottom: 12 }}>음식 성향</label>
          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 10 }}>
            {["채소 섭취가 많은 편", "단 음식 선호", "짠 음식 선호", "기름진 음식 선호"].map(d => <OptionButton key={d} label={d} selected={foodPreferences.includes(d)} onClick={() => setFoodPreferences(prev => toggleSelection(prev, d))} />)}
          </div>
        </div>
        <div style={{ marginBottom: 28 }}>
          <label style={{ fontSize: 12, fontWeight: 600, color: "#1a1a1a", display: "block", marginBottom: 6 }}>하루 평균 앉아있는 시간</label>
          <p style={{ fontSize: 11, color: "#888", margin: "0 0 12px" }}>직장 및 학습 환경을 기준으로 선택해주세요.</p>
          <div style={{ display: "grid", gridTemplateColumns: "repeat(5, 1fr)", gap: 8 }}>
            {["2시간 미만", "2~5시간", "5~8시간", "8~10시간", "10시간 이상"].map(d => <OptionButton key={d} label={d} selected={sittingTime === d} onClick={() => setSittingTime(d)} />)}
          </div>
        </div>
      </div>

      <div style={{ background: "#fff", border: "1px solid #e0e0e0", borderRadius: 12, padding: 28, marginTop: 16 }}>
        <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: 20 }}>
          <h3 style={{ fontSize: 15, fontWeight: 600, color: "#1a1a1a", margin: 0 }}>정신건강 영역</h3>
          <RequiredNotice />
        </div>
        <label style={{ fontSize: 12, fontWeight: 600, color: "#1a1a1a", display: "block", marginBottom: 16 }}>스트레스 수준</label>
        <div style={{ padding: "24px 20px", background: "#f8f9fa", borderRadius: 8 }}>
          <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 20 }}>
            {stressEmojis.map((emoji, i) => (
              <div key={i} style={{ textAlign: "center", flex: 1 }}>
                <div style={{ fontSize: 28, marginBottom: 6, opacity: stressLevel === i ? 1 : 0.3 }}>{emoji}</div>
                <div style={{ fontSize: 10, color: stressLevel === i ? "#1a1a1a" : "#aaa", fontWeight: stressLevel === i ? 600 : 400 }}>{stressLabels[i]}</div>
              </div>
            ))}
          </div>
          <input type="range" min="0" max="4" value={stressLevel} onChange={e => setStressLevel(Number(e.target.value))}
            style={{ width: "100%", cursor: "pointer" }} />
        </div>
      </div>

      {surveyError && (
        <p style={{ fontSize: 12, color: "#E24B4A", margin: "12px 0 0", textAlign: "right" }}>{surveyError}</p>
      )}
      <SurveyNavButtons
        onPrev={() => setSurveyStep(2)}
        onNext={handleComplete}
        nextLabel={isSavingSurvey ? "저장 중..." : "설문 완료"}
        nextDisabled={isSavingSurvey || !birthDate || !height || !weight}
      />
    </SurveyPageWrapper>
  );
}
