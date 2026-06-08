type LoadingStateProps = {
  message?: string;
  skeletonCount?: number;
};

export function LoadingState({ message = "데이터를 불러오는 중입니다.", skeletonCount = 3 }: LoadingStateProps) {
  return (
    <div>
      <p style={{ textAlign: "center", fontSize: 12, color: "#aaa", marginBottom: 14 }}>{message}</p>
      <div style={{ display: "flex", flexDirection: "column", gap: 10 }}>
        {Array.from({ length: skeletonCount }).map((_, i) => (
          <div key={i} style={{ display: "flex", gap: 12, padding: 14, border: "1px solid #f0f0f0", borderRadius: 10, background: "#fff" }}>
            <div style={{ width: 40, height: 40, minWidth: 40, borderRadius: "50%", background: "#f0f0f0" }} />
            <div style={{ flex: 1, display: "flex", flexDirection: "column", gap: 8, justifyContent: "center" }}>
              <div style={{ height: 10, background: "#f0f0f0", borderRadius: 4, width: "40%" }} />
              <div style={{ height: 12, background: "#f0f0f0", borderRadius: 4, width: "80%" }} />
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
