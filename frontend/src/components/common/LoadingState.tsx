type LoadingStateProps = {
  message?: string;
};

export function LoadingState({ message = "데이터를 불러오는 중입니다." }: LoadingStateProps) {
  return <div className="state-box">{message}</div>;
}
