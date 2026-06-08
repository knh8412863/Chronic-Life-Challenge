type ErrorStateProps = {
  title?: string;
  description?: string;
};

export function ErrorState({ title = "요청을 처리하지 못했습니다.", description }: ErrorStateProps) {
  return (
    <div style={{ textAlign: "center", padding: "60px 20px" }}>
      <div style={{ fontSize: 48, marginBottom: 16 }}>⚠️</div>
      <strong style={{ fontSize: 14, color: "#E74C3C", display: "block", marginBottom: 8 }}>{title}</strong>
      {description && <p style={{ fontSize: 12, color: "#aaa", margin: 0 }}>{description}</p>}
    </div>
  );
}
