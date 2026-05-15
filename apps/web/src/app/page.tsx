import Link from "next/link";

import { Icon, Pager, RankPanel, SamplePreviewCard, TopicOpportunityCard } from "@/components/PrototypeUI";
import { RefreshLatestButton } from "@/components/RefreshLatestButton";
import { loadDailySnapshot, optionalTargetDate } from "@/lib/dailySnapshot";
import { categorySeeds, sampleSeeds, topicCards } from "@/lib/uiSeedData";
import { buildHref, formatIso, formatScore, safeText, themeName, topThemes } from "@/lib/webView";

type PageProps = { searchParams?: Promise<Record<string, string | string[] | undefined>> };

const tabs = ["全部", "宏观", "产业", "公司", "政策", "环球"];

export default async function TodayEntryPage({ searchParams }: PageProps) {
  const params = searchParams ? await searchParams : {};
  const date = optionalTargetDate(params.date);
  const snapshot = await loadDailySnapshot(date);
  const activeDate = snapshot.date;
  const themes = topThemes(snapshot.themes, 10);
  const latestRun = snapshot.runs[0];

  return (
    <main className="page">
      <div className="main-grid">
        <section className="card news-panel">
          <div className="news-head">
            <div className="section-title" style={{ marginBottom: 0 }}>
              <div className="left"><Icon name="news" /><h2>今日资讯</h2>{snapshot.dataMode === "seed" ? <span className="data-mode-note">演示数据</span> : null}</div>
            </div>
            <Link className="more" href={buildHref("/workbench", { date: activeDate })}>更多资讯 →</Link>
          </div>
          <div className="news-tabs">
            <div className="tabs">{tabs.map((tab, index) => <span key={tab} className={index === 0 ? "active" : ""}>{tab}</span>)}</div>
          </div>
          {snapshot.events.map((event, index) => (
            <article className="news-item" key={event.key}>
              <div className="time">{formatIso(event.eventTime).slice(11, 16) || "--:--"}</div>
              <div>
                <div style={{ display: "flex", alignItems: "center", gap: 10, flexWrap: "wrap" }}>
                  <span className={`badge ${index % 3 === 0 ? "b-red" : index % 3 === 1 ? "b-orange" : "b-blue"}`}>{safeText(event.eventType, "事件")}</span>
                  <Link className="headline" href={buildHref("/workbench", { q: event.eventSubject, date: activeDate })}>{safeText(event.title, "未命名事件")}</Link>
                </div>
                <p className="desc">{safeText(event.summary, "暂无摘要")}</p>
                <div className="tags">
                  {event.themes.slice(0, 3).map((tag) => <span className="tag" key={`${event.key}-${tag}`}>{tag}</span>)}
                </div>
              </div>
            </article>
          ))}
          <Pager total={snapshot.stats.rawDocumentCount} />
        </section>

        <aside className="side">
          <RankPanel themes={themes} date={activeDate} />

          <section className="card cat-card">
            <div className="section-title">
              <div className="left"><Icon name="tags" /><h2>题材分类</h2></div>
              <Link className="more" href={buildHref("/fermentation", { date: activeDate })}>更多 →</Link>
            </div>
            {categorySeeds.map((category) => (
              <div className="cat-row" key={category.title}>
                <div className="cat-title">{category.title}</div>
                <div className="cat-tags">{category.tags.map((tag) => <span className="pill" key={`${category.title}-${tag}`}>{tag}</span>)}</div>
              </div>
            ))}
          </section>
        </aside>
      </div>

      <section className="card topic-section">
        <div className="section-title">
          <div className="left"><Icon name="tags" /><h2>题材机会</h2></div>
          <Link className="more" href={buildHref("/fermentation", { date: activeDate })}>更多机会 →</Link>
        </div>
        <div className="home-topic-grid">
          {topicCards.map((topic) => <TopicOpportunityCard key={topic.name} topic={topic} compact />)}
        </div>
      </section>

      <section className="card topic-section">
        <div className="section-title">
          <div className="left"><Icon name="lock" /><h2>样例预览</h2></div>
          <Link className="more" href={buildHref("/research", { date: activeDate })}>更多样例 →</Link>
        </div>
        <div className="sample-grid">
          {sampleSeeds.slice(0, 3).map((sample) => <SamplePreviewCard key={sample.title} sample={sample} />)}
        </div>
      </section>
    </main>
  );
}
