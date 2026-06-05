interface StepperProps {
  steps: string[];
  current: number;
}

export function Stepper({ steps, current }: StepperProps) {
  return (
    <div style={{ display: "flex", alignItems: "center", marginBottom: 20 }}>
      {steps.map((step, i) => (
        <div key={step} style={{ display: "flex", alignItems: "center", flex: 1 }}>
          <div style={{ display: "flex", flexDirection: "column", alignItems: "center", flex: 1 }}>
            <div style={{
              width: 28, height: 28, borderRadius: "50%",
              background: i <= current ? "#1a1a1a" : "#f0f0f0",
              color: i <= current ? "#fff" : "#aaa",
              display: "flex", alignItems: "center", justifyContent: "center",
              fontSize: 11, fontWeight: 600, marginBottom: 4,
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
          {i < steps.length - 1 && (
            <div style={{
              height: 1, flex: 1,
              background: i < current ? "#1a1a1a" : "#e0e0e0",
              margin: "0 4px", marginBottom: 18,
            }} />
          )}
        </div>
      ))}
    </div>
  );
}
