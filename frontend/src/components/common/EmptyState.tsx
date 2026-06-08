type EmptyStateProps = {
  title: string;
  description?: string;
  icon?: string;
};

export function EmptyState({ title, description, icon = "🔔" }: EmptyStateProps) {
  return (
    <div style={{ textAlign: "center", padding: "60px 20px" }}>
      <div style={{ fontSize: 48, marginBottom: 16 }}>{icon}</div>
      <strong style={{ fontSize: 14, color: "#888", display: "block", marginBottom: 8 }}>{title}</strong>
      {description && <p style={{ fontSize: 12, color: "#aaa", margin: 0 }}>{description}</p>}
    </div>
  );
}
