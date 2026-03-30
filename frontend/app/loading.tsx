export default function Loading() {
  return (
    <div
      style={{
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        justifyContent: "center",
        minHeight: "100vh",
        padding: "2rem",
        backgroundColor: "#f8f9fa",
        fontFamily: "system-ui, -apple-system, sans-serif"
      }}
      role="status"
      aria-live="polite"
      aria-label="页面加载中"
    >
      <div style={{ textAlign: "center" }}>
        <div
          style={{
            width: "48px",
            height: "48px",
            margin: "0 auto 1rem",
            border: "4px solid #e0e0e0",
            borderTop: "4px solid #1976d2",
            borderRadius: "50%",
            animation: "spin 1s linear infinite"
          }}
          aria-hidden="true"
        />
        <h2 style={{ fontSize: "1.5rem", color: "#333", marginBottom: "0.5rem" }}>
          加载中...
        </h2>
        <p style={{ color: "#666", fontSize: "0.95rem" }}>
          正在为您加载数据，请稍候
        </p>

        <style>{`
          @keyframes spin {
            to {
              transform: rotate(360deg);
            }
          }
        `}</style>
      </div>

      {/* Skeleton loaders for content preview */}
      <div
        style={{
          maxWidth: "800px",
          width: "100%",
          marginTop: "3rem"
        }}
        aria-hidden="true"
      >
        {[1, 2, 3].map((i) => (
          <div
            key={i}
            style={{
              marginBottom: "1rem",
              padding: "1rem",
              backgroundColor: "white",
              borderRadius: "8px",
              boxShadow: "0 2px 4px rgba(0,0,0,0.1)"
            }}
          >
            <div
              style={{
                height: "20px",
                backgroundColor: "#e0e0e0",
                borderRadius: "4px",
                marginBottom: "0.75rem",
                animation: "pulse 2s ease-in-out infinite"
              }}
            />
            <div
              style={{
                height: "16px",
                backgroundColor: "#f0f0f0",
                borderRadius: "4px",
                marginBottom: "0.75rem",
                animation: "pulse 2s ease-in-out infinite",
                animationDelay: "0.1s"
              }}
            />
            <div
              style={{
                height: "16px",
                backgroundColor: "#f0f0f0",
                borderRadius: "4px",
                width: "80%",
                animation: "pulse 2s ease-in-out infinite",
                animationDelay: "0.2s"
              }}
            />
          </div>
        ))}
      </div>

      <style>{`
        @keyframes pulse {
          0%, 100% {
            opacity: 1;
          }
          50% {
            opacity: 0.5;
          }
        }
      `}</style>
    </div>
  );
}
