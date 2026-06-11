import { useEffect, useState } from "react";

import type { AppRoute } from "../../App";
import { getStoredAccessToken } from "../../api/auth";
import {
  EXERCISE_TYPE_ICONS,
  EXERCISE_TYPE_LABELS,
  EXERCISE_TYPES,
  createExerciseLog,
  deleteExerciseLog,
  getExerciseLogs,
  type CreateExerciseBody,
  type ExerciseListData,
  type ExerciseLog,
  type ExerciseQuery,
  type ExerciseTypeCode,
} from "../../api/exercise";
import { ErrorState } from "../../components/common/ErrorState";
import { LoadingState } from "../../components/common/LoadingState";
import { localDateString, localDaysAgoString } from "../../utils/date";

type Tab = "input" | "list";
type QuickPeriod = "TODAY" | "7D" | "1M" | "3M";

function todayStr() {
  return localDateString();
}
function daysAgoStr(days: number) {
  return localDaysAgoString(days);
}
function formatDateShort(s: string) {
  const p = s.split("-");
  const today = todayStr();
  const yesterday = daysAgoStr(1);
  if (s === today) return "오늘";
  if (s === yesterday) return "어제";
  return `${p[1]}/${p[2]}`;
}

const fallbackData: ExerciseListData = {
  summary: { total_duration_minutes: 180, total_calories_burned: 1260, logged_days: 4, logged_count: 4 },
  total: 4,
  items: [
    { id: 1, exercise_type: "RUNNING", duration_minutes: 40, calories_burned: 320, memo: "공원에서 달리기", exercise_date: todayStr(), created_at: "" },
    { id: 2, exercise_type: "CYCLING", duration_minutes: 60, calories_burned: 360, memo: null, exercise_date: daysAgoStr(1), created_at: "" },
    { id: 3, exercise_type: "SWIMMING", duration_minutes: 45, calories_burned: 420, memo: "수영장", exercise_date: daysAgoStr(2), created_at: "" },
    { id: 4, exercise_type: "WALKING", duration_minutes: 30, calories_burned: 110, memo: null, exercise_date: daysAgoStr(3), created_at: "" },
  ],
};

type ExercisePageProps = {
  onNavigate?: (route: AppRoute) => void;
};

export function ExercisePage({ onNavigate: _onNavigate }: ExercisePageProps) {
  const [tab, setTab] = useState<Tab>("input");
  const [data, setData] = useState<ExerciseListData>(fallbackData);
  const [isLoading, setIsLoading] = useState(false);
  const [hasApiError, setHasApiError] = useState(false);
  const [fromDate, setFromDate] = useState(daysAgoStr(6));
  const [toDate, setToDate] = useState(todayStr());
  const [quickPeriod, setQuickPeriod] = useState<QuickPeriod>("7D");

  function fetchData(q: ExerciseQuery) {
    const token = getStoredAccessToken();
    if (!token) return;
    setIsLoading(true);
    getExerciseLogs(q, token)
      .then((res) => { setData(res.data); setHasApiError(false); })
      .catch(() => setHasApiError(true))
      .finally(() => setIsLoading(false));
  }

  useEffect(() => {
    fetchData({ from: fromDate, to: toDate, limit: 50 });
  }, [fromDate, toDate]);

  function applyQuickPeriod(p: QuickPeriod) {
    setQuickPeriod(p);
    const today = todayStr();
    if (p === "TODAY") { setFromDate(today); setToDate(today); }
    else if (p === "7D") { setFromDate(daysAgoStr(6)); setToDate(today); }
    else if (p === "1M") { setFromDate(daysAgoStr(29)); setToDate(today); }
    else { setFromDate(daysAgoStr(89)); setToDate(today); }
  }

  async function handleDelete(log: ExerciseLog) {
    const token = getStoredAccessToken();
    if (!window.confirm("이 기록을 삭제하시겠습니까?")) return;
    try {
      await deleteExerciseLog(log.id, token ?? undefined);
      fetchData({ from: fromDate, to: toDate });
    } catch {
      alert("삭제에 실패했습니다.");
    }
  }

  if (isLoading) return <LoadingState message="운동 기록을 불러오는 중입니다." />;

  const { summary } = data;

  return (
    <div className="exercise-page page-stack">
      <section className="section-header-row page-heading-row">
        <div className="page-heading">
          <p className="eyebrow">건강 관리</p>
          <h1>운동기록</h1>
        </div>
        {tab === "list" && (
          <div className="button-row">
            <button type="button" className="green-button" onClick={() => setTab("input")}>
              +
            </button>
          </div>
        )}
      </section>

      {/* 탭 */}
      <div className="ex-tabs">
        <button
          type="button"
          className={`ex-tab ${tab === "input" ? "ex-tab--active" : ""}`}
          onClick={() => setTab("input")}
        >
          🏃 운동 기록 입력
        </button>
        <button
          type="button"
          className={`ex-tab ${tab === "list" ? "ex-tab--active" : ""}`}
          onClick={() => setTab("list")}
        >
          📋 운동 기록 목록
        </button>
      </div>

      {tab === "input" && (
        <ExerciseInputForm
          onSave={() => { fetchData({ from: fromDate, to: toDate }); setTab("list"); }}
          onCancel={() => setTab("list")}
        />
      )}

      {tab === "list" && (
        <>
          {hasApiError && (
            <ErrorState title="데이터를 불러오지 못했습니다." description="예시 데이터로 표시됩니다." />
          )}

          {/* 기간 필터 */}
          <section className="dashboard-card ex-filter-card">
            <div className="ex-date-row">
              <input type="date" className="vi-date-input" value={fromDate} max={toDate} onChange={(e) => setFromDate(e.target.value)} />
              <span className="ex-date-sep">~</span>
              <input type="date" className="vi-date-input" value={toDate} min={fromDate} onChange={(e) => setToDate(e.target.value)} />
            </div>
            <div className="ex-quick-tabs">
              {(["TODAY", "7D", "1M", "3M"] as QuickPeriod[]).map((p) => (
                <button
                  key={p}
                  type="button"
                  className={`period-tab ${quickPeriod === p ? "period-tab--active" : ""}`}
                  onClick={() => applyQuickPeriod(p)}
                >
                  {p === "TODAY" ? "오늘" : p === "7D" ? "7일" : p === "1M" ? "1개월" : "3개월"}
                </button>
              ))}
            </div>
          </section>

          {/* 요약 */}
          <div className="ex-summary-title">
            <h2>최근 7일 운동 기록</h2>
          </div>
          <div className="ex-summary-grid">
            <div className="ex-summary-card ex-summary-blue">
              <span className="field-label">총 운동 시간</span>
              <strong className="ex-summary-val">{summary.total_duration_minutes}<small>분</small></strong>
            </div>
            <div className="ex-summary-card ex-summary-yellow">
              <span className="field-label">소모 칼로리</span>
              <strong className="ex-summary-val">{summary.total_calories_burned.toLocaleString()}<small>kcal</small></strong>
            </div>
            <div className="ex-summary-card ex-summary-pink">
              <span className="field-label">운동 일수</span>
              <strong className="ex-summary-val">{summary.logged_days}<small>일</small></strong>
            </div>
            <div className="ex-summary-card ex-summary-neutral">
              <span className="field-label">운동 횟수</span>
              <strong className="ex-summary-val">{summary.logged_count}<small>회</small></strong>
            </div>
          </div>
          <p className="goal-section-note" style={{ margin: "0 0 4px" }}>
            * 프론트엔드 로딩 집계 (선택한 기간 기준)
          </p>

          {/* 기록 테이블 */}
          <div className="table-card">
            <table>
              <thead>
                <tr>
                  <th>운동 종류</th>
                  <th>시간</th>
                  <th>칼로리</th>
                  <th>메모</th>
                  <th>날짜</th>
                  <th>수정/삭제</th>
                </tr>
              </thead>
              <tbody>
                {data.items.length === 0 ? (
                  <tr>
                    <td colSpan={6} className="empty-hint" style={{ textAlign: "center", padding: "32px" }}>
                      해당 기간에 기록이 없습니다.
                    </td>
                  </tr>
                ) : (
                  data.items.map((log) => (
                    <tr key={log.id}>
                      <td>
                        {EXERCISE_TYPE_ICONS[log.exercise_type as ExerciseTypeCode] ?? ""}{" "}
                        {EXERCISE_TYPE_LABELS[log.exercise_type as ExerciseTypeCode] ?? log.exercise_type}
                      </td>
                      <td>{log.duration_minutes}분</td>
                      <td>{log.calories_burned != null ? `${log.calories_burned}kcal` : "—"}</td>
                      <td className="vl-memo-cell">{log.memo ?? "—"}</td>
                      <td>{formatDateShort(log.exercise_date)}</td>
                      <td>
                        <div className="vl-action-row">
                          <button type="button" className="vl-action-btn">수정</button>
                          <button
                            type="button"
                            className="vl-action-btn vl-delete-btn"
                            onClick={() => handleDelete(log)}
                          >
                            삭제
                          </button>
                        </div>
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
          <p className="goal-section-note">과거 기록은 수정·삭제가 불가합니다. (당일 기록만 허용)</p>
        </>
      )}
    </div>
  );
}

/* ── 운동 기록 입력 폼 ──────────────────────────── */
type ExerciseInputFormProps = {
  onSave: () => void;
  onCancel: () => void;
};

function ExerciseInputForm({ onSave, onCancel }: ExerciseInputFormProps) {
  const [selectedType, setSelectedType] = useState<ExerciseTypeCode>("RUNNING");
  const [date, setDate] = useState(todayStr());
  const [minutes, setMinutes] = useState(30);
  const [calories, setCalories] = useState("");
  const [memo, setMemo] = useState("");
  const [isSaving, setIsSaving] = useState(false);

  async function handleSave() {
    const token = getStoredAccessToken();
    const body: CreateExerciseBody = {
      exercise_type: selectedType,
      duration_minutes: minutes,
      exercise_date: date,
    };
    if (calories) body.calories_burned = Number(calories);
    if (memo.trim()) body.memo = memo.trim();

    setIsSaving(true);
    try {
      await createExerciseLog(body, token ?? undefined);
      onSave();
    } catch {
      alert("저장에 실패했습니다. 다시 시도해 주세요.");
    } finally {
      setIsSaving(false);
    }
  }

  return (
    <div className="ex-input-body">
      {/* 운동 종류 */}
      <section className="dashboard-card vi-section">
        <h2>운동 종류</h2>
        <div className="ex-type-grid">
          {EXERCISE_TYPES.map((t) => (
            <button
              key={t}
              type="button"
              className={`ex-type-btn ${selectedType === t ? "ex-type-btn--active" : ""}`}
              onClick={() => setSelectedType(t)}
            >
              <span className="ex-type-icon">{EXERCISE_TYPE_ICONS[t]}</span>
              <span>{EXERCISE_TYPE_LABELS[t]}</span>
            </button>
          ))}
        </div>
        {selectedType === "ETC" && (
          <p className="goal-section-note" style={{ margin: "12px 0 4px" }}>
            * 기타 운동은 메모에 상세 내용을 입력해 주세요.
          </p>
        )}
      </section>

      {/* 운동 정보 */}
      <section className="dashboard-card vi-section">
        <h2>운동 정보</h2>
        <div className="ex-info-row">
          <div className="vi-field" style={{ flex: 1 }}>
            <span className="field-label">운동 날짜</span>
            <input
              type="date"
              className="vi-date-input"
              value={date}
              max={todayStr()}
              onChange={(e) => setDate(e.target.value)}
            />
            <p className="goal-section-note">* 운동한 날짜와 시간을 선택해주세요.</p>
          </div>
          <div className="vi-field">
            <span className="field-label">운동 시간 (분)</span>
            <div className="ex-stepper">
              <button type="button" className="ex-stepper-btn" onClick={() => setMinutes((m) => Math.max(1, m - 5))}>−</button>
              <span className="ex-stepper-val">{minutes}</span>
              <button type="button" className="ex-stepper-btn" onClick={() => setMinutes((m) => Math.min(720, m + 5))}>+</button>
              <span className="field-label">분</span>
            </div>
          </div>
        </div>
      </section>

      {/* 소모 칼로리 */}
      <section className="dashboard-card vi-section">
        <h2>소모 칼로리 (선택)</h2>
        <div className="vi-field">
          <span className="field-label">칼로리 (kcal)</span>
          <input
            type="number"
            className="vi-date-input"
            placeholder="예: 180"
            value={calories}
            onChange={(e) => setCalories(e.target.value)}
          />
          <p className="goal-section-note">* 소모 칼로리를 알고 있다면 입력해주세요.</p>
        </div>
      </section>

      {/* 운동 메모 */}
      <section className="dashboard-card vi-section">
        <h2>운동 메모 (선택)</h2>
        <textarea
          className="vi-memo-input"
          placeholder="운동 중에 느낀 점을 기록하세요..."
          value={memo}
          onChange={(e) => setMemo(e.target.value)}
        />
      </section>

      <div className="goal-edit-actions">
        <button type="button" className="wide-subtle-button" onClick={onCancel}>취소</button>
        <button type="button" className="green-button" onClick={handleSave} disabled={isSaving}>
          {isSaving ? "저장 중..." : "저장"}
        </button>
      </div>
    </div>
  );
}
