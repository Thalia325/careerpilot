import Link from "next/link";

export function AppHeader() {
  return (
    <header className="app-header">
      <div className="app-header__inner">
        <Link href="/" className="app-header__brand">
          <span className="app-header__logo">CP</span>
          <span>
            <strong>职航智策 CareerPilot</strong>
            <small>AI 职业规划助手</small>
          </span>
        </Link>
        <nav className="app-header__nav">
          <Link href="/#tasks">功能</Link>
          <Link href="/#examples">示例</Link>
          <Link href="/#help">帮助</Link>
        </nav>
        <div className="app-header__actions">
          <Link href="/teacher" className="app-header__text-link">
            教师端
          </Link>
          <Link href="/admin" className="app-header__text-link">
            管理后台
          </Link>
          <Link href="/login" className="app-header__button app-header__button--ghost">
            登录
          </Link>
          <Link href="/workspace" className="app-header__button">
            进入工作台
          </Link>
        </div>
      </div>
    </header>
  );
}

