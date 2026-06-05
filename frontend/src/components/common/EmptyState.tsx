type EmptyStateProps = {
  title: string;
  description?: string;
};

export function EmptyState({ title, description }: EmptyStateProps) {
  return (
    <div className="state-box">
      <strong>{title}</strong>
      {description && <p>{description}</p>}
    </div>
  );
}
