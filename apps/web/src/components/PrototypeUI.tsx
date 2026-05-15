import Link from "next/link";

import type { DailyTheme } from "@/lib/dailySnapshot";
import type { TopicCardSeed, SampleSeed } from "@/lib/uiSeedData";
import { buildHref, formatIso, formatScore, safeText, themeName, topThemes } from "@/lib/webView";

export function Icon({ name, size = 20 }: { name: string; size?: number }) {
  return (
    <svg className="icon" width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <use href={`#i-${name}`} />
    </svg>
  );
}

export function RankPanel({ themes, date, title = "热门题材" }: { themes: DailyTheme[]; date: string; title?: string }) {
  const ranked = topThemes(themes, 10);
  return (
    <section className="card rank-card">
      <div className="section-title">
        <div className="left"><Icon name="flame" /><h2>{title}</h2></div>
        <Link className="more" href={buildHref("/fermentation", { date })}>更多 ›</Link>
      </div>
      <div className="rank-head"><span>排名</span><span>题材</span><span className="right">热度</span><span className="right">涨跌</span></div>
      {ranked.map((theme, index) => (
        <div className="rank-row" key={theme.key}>
          <span className={`rank-num ${index === 0 ? "r1" : index === 1 ? "r2" : index === 2 ? "r3" : "plain"}`}>{index + 1}</span>
          <b>{themeName(theme)}</b>
          <span className="right">{formatScore(theme.heatScore)}</span>
          <span className={`right ${index < 5 ? "red" : "green"}`}>+{Math.max(0.3, 8.5 - index * 0.7).toFixed(1)}%</span>
        </div>
      ))}
      <div style={{ marginTop: 12, fontSize: 12, color: "#94a3b8" }}>更新时间：{formatIso(ranked[0]?.latestSeenTime).slice(5, 16)}</div>
    </section>
  );
}

export function TopicOpportunityCard({ topic, compact = false }: { topic: TopicCardSeed; compact?: boolean }) {
  const icon = topic.icon === "plane" ? "plane" : topic.icon === "cpu" ? "cpu" : topic.icon === "battery" ? "battery" : topic.icon === "activity" ? "activity" : "robot";
  return (
    <Link href={buildHref("/fermentation", { q: topic.name })} className="topic-card">
      <div className="topic-icon"><Icon name={icon} /></div>
      <div>
        <h3 style={{ margin: 0, fontSize: compact ? 17 : 21 }}>
          {topic.name}
          {!compact ? <span className="red topic-heat">热度 {topic.heat.toFixed(1)} ↑ {topic.change.replace("+", "").replace("%", "")}</span> : null}
        </h3>
        <p>{topic.description}</p>
        {compact ? <div>热度 <b>{topic.heat.toFixed(1)}</b> <span className="red">↑ {topic.change.replace("+", "")}</span></div> : <div className="topic-count">最新相关资讯 128 条</div>}
        <div className="tags">{topic.tags.map((tag) => <span className="tag" key={`${topic.name}-${tag}`}>{tag}</span>)}</div>
      </div>
    </Link>
  );
}

export function SamplePreviewCard({ sample }: { sample: SampleSeed }) {
  return (
    <Link href={buildHref("/unlock", { sample: sample.title })} className="sample-card">
      <span className="badge b-blue">{sample.kind}</span>
      <h3>{sample.title}</h3>
      <p>{sample.description}</p>
      <div className="blur-img" />
      <div className="lock-round"><Icon name="lock" size={16} /></div>
      <div className="locked-note">解锁全文</div>
    </Link>
  );
}

export function Pager({ total = 218 }: { total?: number }) {
  return (
    <div className="pager">
      <div className="pages">
        <button className="page-no" type="button">‹</button>
        {[1, 2, 3, 4, 5].map((item) => <button className={`page-no ${item === 1 ? "active" : ""}`} key={item} type="button">{item}</button>)}
        <span>...</span>
        <button className="page-no" type="button">22</button>
        <button className="page-no" type="button">›</button>
      </div>
      <div className="pager-total">
        <span>共 {total} 条</span>
        <button className="page-no page-size" type="button">10 条/页</button>
      </div>
    </div>
  );
}

export function TrendPanel() {
  return (
    <section className="card trend-card">
      <div className="section-title">
        <div className="left"><Icon name="activity" /><h2>热门题材趋势</h2></div>
        <span className="more">更多 ›</span>
      </div>
      <svg viewBox="0 0 330 160" className="trend-svg" aria-hidden="true">
        <path d="M0 120 C35 90,55 65,85 70 S130 100,160 72 S210 75,250 58 S300 42,330 36" fill="none" stroke="#0f63ff" strokeWidth="3" />
        <path d="M0 135 C42 110,78 95,110 100 S150 105,180 88 S235 96,330 72" fill="none" stroke="#f59e0b" strokeWidth="3" />
        <path d="M0 145 C40 125,85 132,120 110 S170 130,220 112 S285 104,330 88" fill="none" stroke="#10b981" strokeWidth="3" />
      </svg>
    </section>
  );
}

export function safeTopicText(value: string | null | undefined, fallback: string) {
  return safeText(value, fallback);
}
