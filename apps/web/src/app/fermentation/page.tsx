import Link from "next/link";

import { Icon, RankPanel, TopicOpportunityCard, TrendPanel } from "@/components/PrototypeUI";
import { loadDailySnapshot, optionalTargetDate } from "@/lib/dailySnapshot";
import { topicCards } from "@/lib/uiSeedData";
import { buildHref, formatScore, safeText, themeName, topThemes } from "@/lib/webView";

type PageProps = { searchParams?: Promise<Record<string, string | string[] | undefined>> };

const topicTabs = ["全部", "AI应用", "低空经济", "智能制造", "新能源", "半导体", "消费电子", "更多⌄"];

export default async function FermentationPage({ searchParams }: PageProps) {
  const params = searchParams ? await searchParams : {};
  const date = optionalTargetDate(params.date);
  const query = typeof params.q === "string" ? params.q : "";
  const snapshot = await loadDailySnapshot(date);
  const activeDate = snapshot.date;
  const themes = topThemes(snapshot.themes, 10);
  const filteredCards = query ? topicCards.filter((topic) => topic.name.includes(query) || topic.tags.some((tag) => tag.includes(query))) : topicCards;

  return (
    <>
      <div className="breadcrumb">首页 / 题材</div>
      <main className="topic-page">
        <section className="card topic-main">
          <div className="section-title">
            <div>
              <h2 className="page-title">题材发现</h2>
              <p className="page-subtitle">聚焦产业与市场热点，洞察资金关注方向，发现具有研究价值的题材主题</p>
            </div>
            <Link className="page-no page-size" href={buildHref("/workbench", { date: activeDate })}>默认排序⌄</Link>
          </div>
          <div className="tabs topic-tabs">{topicTabs.map((tab, index) => <span key={tab} className={index === 0 ? "active" : ""}>{tab}</span>)}</div>
          <div className="topic-list-grid">
            {filteredCards.map((topic) => <TopicOpportunityCard key={topic.name} topic={topic} />)}
            {themes.slice(0, 2).map((theme) => (
              <Link className="topic-card" href={buildHref("/workbench", { q: themeName(theme), date: activeDate })} key={`db-${theme.key}`}>
                <div className="topic-icon"><Icon name="shield" /></div>
                <div>
                  <h3 style={{ margin: 0, fontSize: 21 }}>{themeName(theme)}<span className="red topic-heat">热度 {formatScore(theme.heatScore)} ↑</span></h3>
                  <p>{safeText(theme.coreNarrative, "来自数据库的题材聚合结果，仍需继续核验证据链。")}</p>
                  <div className="topic-count">关联事件 {theme.relatedEventsCount} 条</div>
                  <div className="tags"><span className="tag">{safeText(theme.fermentationStage, "观察")}</span><span className="tag">来源 {theme.sourceCount}</span></div>
                </div>
              </Link>
            ))}
          </div>
          <div className="loadmore">加载更多题材⌄</div>
        </section>

        <aside className="side">
          <RankPanel themes={themes} date={activeDate} />
          <section className="card new-topic-card">
            <div className="section-title">
              <div className="left"><Icon name="news" /><h2>今日新增题材</h2></div>
              <Link className="more" href={buildHref("/workbench", { date: activeDate })}>更多 ›</Link>
            </div>
            <div className="new-topic-list">
              <div>脑机接口 <span className="green">NEW 36.8 ↑2.4</span></div>
              <div>机器人灵巧手 <span className="green">NEW 28.1 ↑2.1</span></div>
              <div>AI PC <span className="green">NEW 27.3 ↑1.9</span></div>
            </div>
          </section>
          <TrendPanel />
        </aside>
      </main>
    </>
  );
}
