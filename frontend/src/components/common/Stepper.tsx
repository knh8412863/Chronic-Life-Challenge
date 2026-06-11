interface StepperProps {
  steps: string[];
  current: number;
}

export function Stepper({ steps, current }: StepperProps) {
  return (
    <div style={{ display: "grid", gridTemplateColumns: `repeat(${steps.length}, 1fr)`, marginBottom: 20 }}>
      {steps.map((step, i) => (
        <div key={step} style={{ position: "relative", display: "flex", flexDirection: "column", alignItems: "center" }}>
          {i < steps.length - 1 && (
            <div style={{
              position: "absolute",
              top: 14,
              left: "50%",
              right: "-50%",
              height: 1,
              background: i < current ? "#1a1a1a" : "#e0e0e0",
              zIndex: 0,
            }} />
          )}
            <div style={{
              width: 28, height: 28, borderRadius: "50%",
              background: i <= current ? "#1a1a1a" : "#f0f0f0",
              color: i <= current ? "#fff" : "#aaa",
              display: "flex", alignItems: "center", justifyContent: "center",
              fontSize: 11, fontWeight: 600, marginBottom: 4, zIndex: 1,
            }}>
              {i < current ? "✓" : i + 1}
            </div>
            <span style={{
              fontSize: 9, color: i <= current ? "#1a1a1a" : "#aaa",
              textAlign: "center", whiteSpace: "nowrap",
            }}>
              {step}
            </span>
        </div>
      ))}
    </div>
  );
}
