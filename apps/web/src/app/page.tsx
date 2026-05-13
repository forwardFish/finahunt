import Link from "next/link";

import { RefreshLatestButton } from "@/components/RefreshLatestButton";
import { Badge, DateSwitch, EmptyState, LinkButton, MetricCard, PageControls, PageHero, ScoreMeter, SectionCard } from "@/components/FinancialUI";
import { loadDailySnapshot, resolveTargetDate } from "@/lib/dailySnapshot";
import { buildHref, featuredEvents, formatIso, formatScore, lowPositionThemes, safeText, sourceLabel, summarizeSnapshotState, themeName, topThemes } from "@/lib/webView";

type PageProps = { searchParams?: Promise<Record<string, string | string[] | undefined>> };
const tabs = ["全部", "宏观", "产业", "公司", "政策", "全球"];

export default async function TodayEntryPage({ searchParams }: PageProps) {
  const params = searchParams ? await searchParams : {};
  const date = resolveTargetDate(params.date);
  const snapshot = loadDailySnapshot(date);
  const state = summarizeSnapshotState(snapshot.stats.runCount, snapshot.themes.length, snapshot.events.length, snapshot.sources.length);
  const themes = topThemes(snapshot.themes, 10);
  const cards = topThemes(snapshot.themes, 6);
  const lowThemes = lowPositionThemes(snapshot.themes, 3);
  const events = featuredEvents(snapshot.events, 7);
  const latestRun = snapshot.runs[0];

  return (
    <main className="fi-page">
      <PageHero eyebrow="今日总览" title="把公开资讯、题材热度和研究入口放回同一张金融信息首页。" description="参考 docs/UI 的金融资讯认知系统原型，首页回到资讯流、热门题材与题材机会结构，同时保留 daily snapshot 的真实数据读取与刷新动作。" side={<><h2>今日运行摘要</h2><div className="fi-stat-grid"><MetricCard label="页面状态" value={state.label} note={state.description} tone={state.tone === "ready" ? "green" : state.tone === "partial" ? "orange" : "slate"} /><MetricCard label="运行批次" value={snapshot.stats.runCount} /><MetricCard label="主题" value={snapshot.stats.themeCount} /><MetricCard label="事件" value={snapshot.stats.canonicalEventCount} /></div><RefreshLatestButton latestRunId={latestRun?.runId ?? ""} successPath="/" /></>}><DateSwitch action="/" date={snapshot.date} /></PageHero>

      <div className="fi-main-grid">
        <section className="fi-card"><div className="fi-section-head"><div><span className="fi-kicker">News Feed</span><h2>今日资讯</h2></div><Link className="fi-section-action" href={buildHref("/workbench", { date: snapshot.date })}>更多资讯 ›</Link></div><div className="fi-tabs">{tabs.map((tab, index) => <span key={tab} className={index === 0 ? "active" : ""}>{tab}</span>)}</div><div className="fi-news-list">{events.length ? events.map((event, index) => <article className="fi-news-item" key={event.key}><div className="fi-news-time">{formatIso(event.eventTime).slice(11, 16) || "--:--"}</div><div><div className="fi-news-title"><Badge tone={index % 5 === 0 ? "red" : index % 5 === 1 ? "orange" : index % 5 === 2 ? "blue" : index % 5 === 3 ? "green" : "purple"}>{safeText(event.eventType, "资讯")}</Badge><strong>{safeText(event.title, "未命名事件")}</strong></div><p>{safeText(event.summary, "暂无事件摘要。")}</p><div className="fi-tags"><span className="fi-tag">{sourceLabel(event.sourceId || event.sourceName)}</span>{(event.themes || []).slice(0, 3).map((tag) => <span className="fi-tag" key={`${event.key}-${tag}`}>{safeText(tag, "主题")}</span>)}</div></div></article>) : <EmptyState title="暂无资讯">当前日期没有可展示事件，可刷新最新快照或切换日期。</EmptyState>}</div><PageControls totalLabel={`共 ${snapshot.events.length} 条`} /></section>
        <aside className="fi-side"><SectionCard title="热门题材" eyebrow="Hot Topics" action="更多 ›"><div className="fi-rank-list"><div className="fi-rank-head"><span>排名</span><span>题材</span><span className="fi-right">热度</span><span className="fi-right">发酵</span></div>{themes.map((theme, index) => <div className="fi-rank-row" key={theme.key}><span className="fi-rank-num">{index + 1}</span><b>{themeName(theme)}</b><span className="fi-right">{formatScore(theme.heatScore)}</span><span className="fi-right fi-red">{formatScore(theme.fermentationScore)}</span></div>)}</div><p className="fi-rank-note">更新时间：{formatIso(latestRun?.createdAt)}</p></SectionCard><SectionCard title="题材分类" eyebrow="Categories"><div className="fi-tags">{["AI", "机器人", "低空经济", "半导体", "新能源", "金融科技", "军工", "消费电子", "新基建"].map((tag) => <span className="fi-tag" key={tag}>{tag}</span>)}</div></SectionCard></aside>
      </div>

      <SectionCard title="题材机会" eyebrow="Opportunity Board" action={<Link href={buildHref("/fermentation", { date: snapshot.date })}>更多机会 ›</Link>}><div className="fi-card-grid">{cards.map((theme) => <article className="fi-topic-card" key={theme.key}><div className="fi-topic-head"><div className="fi-topic-title"><span className="fi-topic-icon">◆</span><h3>{themeName(theme)}</h3></div><span className="fi-red">{formatScore(theme.fermentationScore)}</span></div><p>{safeText(theme.coreNarrative, "暂无核心叙事。")}</p><ScoreMeter value={theme.fermentationScore} label="发酵分" /><div className="fi-tags">{theme.latestCatalysts.slice(0, 2).map((item) => <span className="fi-tag" key={item.title}>{safeText(item.title, "催化")}</span>)}</div></article>)}</div></SectionCard>
      <SectionCard title="样例预览" eyebrow="Research Samples" action={<Link href={buildHref("/research", { date: snapshot.date })}>更多样例 ›</Link>}><div className="fi-sample-grid">{(lowThemes.length ? lowThemes : cards.slice(0, 3)).map((theme) => <article className="fi-sample-card" key={`sample-${theme.key}`}><Badge tone="blue">复盘</Badge><h3>{themeName(theme)} 产业链复盘</h3><p>{safeText(theme.lowPositionReason || theme.researchPositioningNote || theme.coreNarrative, "登录后查看完整研究样例与候选公司映射。")}</p><div className="fi-blur-strip" /><span className="fi-lock-art">🔒</span></article>)}</div></SectionCard>
      <SectionCard title="风险边界" eyebrow="Risk Boundary"><div className="fi-card-grid"><article className="fi-table-card"><h3>导读页不替代工作台</h3><p className="fi-muted">首页只给出今日入口、主线摘要、低位摘要和关键事件入口；完整矩阵、完整证据带和全量候选公司请进入工作台或研究页。</p></article><article className="fi-table-card"><h3>研究结论需复核</h3><p className="fi-muted">公开资讯、题材热度和候选公司映射仅供研究观察，不构成投资建议；异常数据、空状态和部分状态保持显式展示。</p></article></div></SectionCard>
      <section className="fi-card fi-section-head"><div><span className="fi-kicker">Next Step</span><h2>从首页继续进入研究链路</h2></div><div className="fi-link-row"><LinkButton href={buildHref("/fermentation", { date: snapshot.date })} variant="secondary">查看题材发酵</LinkButton><LinkButton href={buildHref("/workbench", { date: snapshot.date })}>进入工作台</LinkButton></div></section>
    </main>
  );
}
