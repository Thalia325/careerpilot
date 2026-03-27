import Link from "next/link";

export default function LoginPage() {
  return (
    <div className="landing">
      <section className="landing-hero">
        <div className="landing-panel">
          <p className="eyebrow">登录入口</p>
          <h1>统一身份接入</h1>
          <p>比赛演示默认提供三类账号，后端保留 `/auth/login` 接口，可继续扩展真实认证体系。</p>
          <div className="plain-list">
            <div>学生端：student_demo / demo123</div>
            <div>教师端：teacher_demo / demo123</div>
            <div>管理端：admin_demo / demo123</div>
          </div>
        </div>
        <div className="landing-side">
          <h2>快速进入</h2>
          <div className="plain-list">
            <Link href="/student/dashboard">作为学生查看</Link>
            <Link href="/teacher">作为教师查看</Link>
            <Link href="/admin">作为管理员查看</Link>
          </div>
        </div>
      </section>
    </div>
  );
}

