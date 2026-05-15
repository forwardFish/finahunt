import Link from "next/link";

import { Icon, RankPanel, SamplePreviewCard } from "@/components/PrototypeUI";
import { RunLowPositionButton } from "@/components/RunLowPositionButton";
import { loadDailySnapshot, optionalTargetDate } from "@/lib/dailySnapshot";
import { loadLowPositionWorkbench, optionalWorkbenchDate } from "@/lib/lowPositionWorkbench";
import { sampleSeeds } from "@/lib/uiSeedData";
import { buildHref, formatIso, formatScore, lowPositionThemeName, safeText, validationLabel } from "@/lib/webView";

type PageProps = { searchParams?: Promise<Record<string, string | string[] | undefined>> };

const sampleTabs = ["全部", "行业研究", "产业链", "政策分析", "公司研究", "市场策略", "专题报告"];

export default async function ResearchPage({ searchParams }: PageProps) {
  const params = searchParams ? await searchParams : {};
  const date = optionalWorkbenchDate(params.date);
  const snapshot = await loadDailySnapshot(optionalTargetDate(params.date));
  const workbench = await loadLowPositionWorkbench(date);
  const activeDate = workbench.date || snapshot.date;
  const runtimeSamples = workbench.themes.slice(0, 3).map((theme) => ({
    kind: validationLabel(theme.validation_bucket),
    title: `${lowPositionThemeName(theme)}低位研究卡`,
    description: safeText(theme.low_position_reason, "基于公开事件、题材发酵与候选标的映射生成的研究观察卡。"),
    locked: true,
  }));
  const samples = [...runtimeSamples, ...sampleSeeds].slice(0, 9);

  return (
    <>
      <div className="breadcrumb">首页 / 样例</div>
      <main className="sample-list">
        <section className="card sample-main">
          <h1 className="page-title">样例列表</h1>
          <p className="page-subtitle">精选高质量研究样例，覆盖行业研究、产业链梳理、政策分析、公司深度等多种类型</p>
          <div className="tabs sample-tabs">{sampleTabs.map((tab, index) => <span className={index === 0 ? "active" : ""} key={tab}>{tab}</span>)}</div>
          <div className="sample-grid research-sample-grid">
            {samples.map((sample) => <SamplePreviewCard key={sample.title} sample={sample} />)}
          </div>
        </section>

        <aside className="side">
          <RankPanel themes={snapshot.themes} date={activeDate} title="热门样例" />
          <section className="card side-card">
            <h3 className="side-title">最近更新</h3>
            <div className="recent-list">
              {samples.slice(0, 5).map((sample, index) => (
                <div key={`recent-${sample.title}`}>{sample.title}<span>{formatIso(workbench.createdAt).slice(5, 10) || `05-${19 - index}`}</span></div>
              ))}
            </div>
          </section>
          <section className="card side-card">
            <h3 className="side-title">研究链运行</h3>
            <div className="index-grid">
              <div className="index-box"><div className="idx-name">消息</div><div className="idx-val">{workbench.messageCount}</div><div className="idx-chg">可复核</div></div>
              <div className="index-box"><div className="idx-name">研究卡</div><div className="idx-val">{workbench.themeCount}</div><div className="idx-chg">+{workbench.themes.length}</div></div>
              <div className="index-box"><div className="idx-name">已验证</div><div className="idx-val">{workbench.validatedThemes.length}</div><div className="idx-chg">{formatScore(workbench.validatedThemes.length)}</div></div>
            </div>
            <div style={{ marginTop: 14 }}><RunLowPositionButton latestRunId={workbench.runId} /></div>
            <Link className="more block-more" href={buildHref("/workbench", { date: activeDate })}><Icon name="news" size={16} /> 打开研究工作台</Link>
          </section>
        </aside>
      </main>
    </>
  );
}
