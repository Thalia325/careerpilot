"use client";

import { useEffect } from "react";

export default function ErrorBoundary({
  error,
  reset
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  useEffect(() => {
    // Log the error for debugging purposes
    console.error("[Error Boundary]", error);
  }, [error]);

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
      role="alert"
      aria-live="assertive"
    >
      <main
        style={{
          maxWidth: "600px",
          backgroundColor: "white",
          padding: "2rem",
          borderRadius: "8px",
          boxShadow: "0 2px 8px rgba(0,0,0,0.1)",
          textAlign: "center"
        }}
      >
        <h1 style={{ fontSize: "2rem", color: "#d32f2f", marginBottom: "1rem" }}>
          出错了
        </h1>
        <p style={{ fontSize: "1rem", color: "#666", marginBottom: "1.5rem" }}>
          抱歉，应用程序遇到了一个意外错误。请尝试刷新页面或返回首页。
        </p>

        {process.env.NODE_ENV === "development" && (
          <details
            style={{
              marginBottom: "2rem",
              textAlign: "left",
              padding: "1rem",
              backgroundColor: "#f5f5f5",
              borderRadius: "4px",
              border: "1px solid #ddd"
            }}
          >
            <summary style={{ cursor: "pointer", fontWeight: "bold" }}>
              错误详情（开发环境可见）
            </summary>
            <pre
              style={{
                marginTop: "1rem",
                padding: "0.5rem",
                backgroundColor: "#fff",
                borderRadius: "4px",
                overflow: "auto",
                fontSize: "0.85rem"
              }}
            >
              {error.message}
              {error.stack && `\n\n${error.stack}`}
            </pre>
          </details>
        )}

        <div style={{ display: "flex", gap: "1rem", justifyContent: "center" }}>
          <button
            onClick={() => reset()}
            style={{
              padding: "0.75rem 2rem",
              backgroundColor: "#1976d2",
              color: "white",
              border: "none",
              borderRadius: "4px",
              cursor: "pointer",
              fontSize: "1rem",
              fontWeight: "500",
              transition: "background-color 0.2s"
            }}
            onMouseOver={(e) =>
              ((e.target as HTMLElement).style.backgroundColor = "#1565c0")
            }
            onMouseOut={(e) =>
              ((e.target as HTMLElement).style.backgroundColor = "#1976d2")
            }
          >
            重试
          </button>
          <a
            href="/"
            style={{
              padding: "0.75rem 2rem",
              backgroundColor: "#757575",
              color: "white",
              border: "none",
              borderRadius: "4px",
              cursor: "pointer",
              fontSize: "1rem",
              fontWeight: "500",
              textDecoration: "none",
              display: "inline-block",
              transition: "background-color 0.2s"
            }}
            onMouseOver={(e) =>
              ((e.target as HTMLElement).style.backgroundColor = "#616161")
            }
            onMouseOut={(e) =>
              ((e.target as HTMLElement).style.backgroundColor = "#757575")
            }
          >
            返回首页
          </a>
        </div>
      </main>
    </div>
  );
}
