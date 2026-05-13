import { LinkButton, MetricCard, PageHero, SectionCard } from "@/components/FinancialUI";
import { loadDailySnapshot, resolveTargetDate } from "@/lib/dailySnapshot";
import { loadLowPositionWorkbench } from "@/lib/lowPositionWorkbench";
import { buildHref, formatIso, summarizeResearchState, summarizeSnapshotState } from "@/lib/webView";

type PageProps = { searchParams?: Promise<Record<string, string | string[] | undefined>> };

export default async function Sprint2CompatibilityPage({ searchParams }: PageProps) {
  const params = searchParams ? await searchParams : {};
  const date = resolveTargetDate(params.date);
  const snapshot = loadDailySnapshot(date);
  const workbench = loadLowPositionWorkbench(date);
  const snapshotState = summarizeSnapshotState(snapshot.stats.runCount, snapshot.themes.length, snapshot.events.length, snapshot.sources.length);
  const researchState = summarizeResearchState(workbench.state);
  return <main className="fi-page"><PageHero eyebrow="Sprint 2 Compatibility" title="Sprint 2 旧入口继续可访问，并汇总新 UI 的验收路径。" description="该路由不再只是重定向，方便最终验收时确认旧入口未被破坏，同时指向本轮重构后的主要页面。" side={<><h2>验收快照</h2><div className="fi-stat-grid"><MetricCard label="日期" value={date} /><MetricCard label="主线" value={snapshotState.label} tone={snapshotState.tone === "ready" ? "green" : "orange"} /><MetricCard label="低位" value={researchState.label} tone={researchState.tone === "ready" ? "green" : "orange"} /><MetricCard label="运行" value={formatIso(snapshot.runs[0]?.createdAt || workbench.createdAt)} /></div></>} /><SectionCard title="推荐验收路线" eyebrow="Acceptance Routes"><div className="fi-card-grid"><article className="fi-topic-card"><h3>首页资讯流</h3><p className="fi-muted">验证最新 docs/UI 首页结构、资讯列表、热门题材和样例预览。</p><LinkButton href={buildHref("/", { date })}>打开 /</LinkButton></article><article className="fi-topic-card"><h3>题材发酵</h3><p className="fi-muted">验证 topic-category / topic-detail 风格的题材卡与矩阵。</p><LinkButton href={buildHref("/fermentation", { date })}>打开 /fermentation</LinkButton></article><article className="fi-topic-card"><h3>低位研究</h3><p className="fi-muted">验证 samples / search 风格的低位研究样例库。</p><LinkButton href={buildHref("/research", { date })}>打开 /research</LinkButton></article><article className="fi-topic-card"><h3>工作台</h3><p className="fi-muted">验证完整表格、事件带和真实数据横向对照。</p><LinkButton href={buildHref("/workbench", { date })}>打开 /workbench</LinkButton></article></div></SectionCard></main>;
}
