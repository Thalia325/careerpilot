import Link from "next/link";

export default function NotFound() {
  return (
    <div className="landing">
      <section className="landing-hero" style={{ alignItems: "center" }}>
        <div
          className="landing-panel"
          style={{
            gridColumn: "1 / -1",
            textAlign: "center",
            padding: "64px 48px"
          }}
        >
          <p className="eyebrow">404 错误</p>
          <h1 style={{ fontSize: "3.5rem", marginBottom: "16px" }}>页面未找到</h1>
          <p style={{ fontSize: "1.1rem", marginBottom: "32px", color: "var(--subtle)" }}>
            抱歉，您访问的页面不存在或已被移除。
          </p>

          <div
            style={{
              display: "flex",
              gap: "16px",
              justifyContent: "center",
              flexWrap: "wrap"
            }}
          >
            <Link
              href="/"
              style={{
                display: "inline-flex",
                alignItems: "center",
                justifyContent: "center",
                minHeight: "48px",
                padding: "12px 32px",
                borderRadius: "14px",
                background: "linear-gradient(120deg, var(--brand), var(--brand-2))",
                color: "white",
                fontWeight: 700,
                textDecoration: "none",
                transition: "transform 0.2s ease, box-shadow 0.2s ease"
              }}
            >
              返回首页
            </Link>
            <Link
              href="/student/dashboard"
              style={{
                display: "inline-flex",
                alignItems: "center",
                justifyContent: "center",
                minHeight: "48px",
                padding: "12px 32px",
                borderRadius: "14px",
                background: "rgba(255, 255, 255, 0.94)",
                color: "var(--brand)",
                fontWeight: 700,
                textDecoration: "none",
                border: "1px solid rgba(23, 63, 138, 0.14)",
                transition: "transform 0.2s ease, box-shadow 0.2s ease"
              }}
            >
              进入学生平台
            </Link>
          </div>
        </div>
      </section>
    </div>
  );
}
