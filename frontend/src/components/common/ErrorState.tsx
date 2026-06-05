type ErrorStateProps = {
  title?: string;
  description?: string;
};

export function ErrorState({ title = "요청을 처리하지 못했습니다.", description }: ErrorStateProps) {
  return (
    <div className="state-box state-box-error">
      <strong>{title}</strong>
      {description && <p>{description}</p>}
    </div>
  );
}
