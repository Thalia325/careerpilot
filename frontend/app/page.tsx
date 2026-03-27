import { AppFooter } from "@/components/home/AppFooter";
import { AppHeader } from "@/components/home/AppHeader";
import { HomeHero } from "@/components/home/HomeHero";
import { QuickTaskCards } from "@/components/home/QuickTaskCards";
import { RecentTasksPanel } from "@/components/home/RecentTasksPanel";
import { SamplePreviewPanel } from "@/components/home/SamplePreviewPanel";
import { SecondaryAccessSection } from "@/components/home/SecondaryAccessSection";
import { WorkflowSection } from "@/components/home/WorkflowSection";
import {
  composerRoleTags,
  quickTaskTemplates,
  recentTasks,
  samplePreviews,
  secondaryAccessCards,
  workflowSteps
} from "@/lib/home-data";

export default function HomePage() {
  return (
    <div className="home-page">
      <AppHeader />
      <main className="home-container">
        <HomeHero roleTags={composerRoleTags} />
        <QuickTaskCards items={quickTaskTemplates} />
        <section className="home-dashboard">
          <RecentTasksPanel items={recentTasks} />
          <SamplePreviewPanel items={samplePreviews} />
        </section>
        <WorkflowSection items={workflowSteps} />
        <SecondaryAccessSection items={secondaryAccessCards} />
      </main>
      <AppFooter />
    </div>
  );
}
