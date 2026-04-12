import { SectionCard } from "@/components/SectionCard";
import { UploadLab } from "@/components/UploadLab";

export default function StudentUploadPage() {
  return (
    <div style={{ maxWidth: 1000, margin: "0 auto", padding: "24px" }}>
      <SectionCard title="文档识别工具">
        <UploadLab />
      </SectionCard>
      <SectionCard title="推荐上传清单">
        <ul className="plain-list">
          <li>个人简历：项目、技能、实习、证书。</li>
          <li>证书材料：语言证书、专项技能认证、竞赛获奖。</li>
          <li>成绩单：用于补充学习能力与专业基础判断。</li>
          <li>招聘材料：用于反向解析企业岗位要求。</li>
        </ul>
      </SectionCard>
    </div>
  );
}
