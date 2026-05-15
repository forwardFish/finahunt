"use client";

import { useEffect, useMemo, useState } from "react";

type Status = {
  postgresConnected: boolean;
  lastRunAt: string;
  lastStatus: string;
  todayFetched: number;
  todayInserted: number;
  todayDuplicated: number;
  todayFailed: number;
};

type Setting = { enabled: boolean; scheduleTime: string; sourceId: string; updatedAt: string };

type CrawlRun = {
  runId: string;
  sourceId: string;
  status: string;
  startedAt: string;
  finishedAt: string;
  fetchedCount: number;
  insertedCount: number;
  duplicateCount: number;
  failedCount: number;
};

type RawItem = {
  documentId: string;
  sourceName: string;
  title: string;
  url: string;
  publishedAt: string;
  contentLength: number;
  sourceHash: string;
  truthScore: number;
  authenticityStatus: string;
  reviewStatus: string;
  createdAt: string;
};

type RawDetail = RawItem & {
  contentText: string;
  httpStatus: number | null;
  reviewerNote: string;
  payload: Record<string, unknown>;
};

const EMPTY_STATUS: Status = {
  postgresConnected: false,
  lastRunAt: "",
  lastStatus: "",
  todayFetched: 0,
  todayInserted: 0,
  todayDuplicated: 0,
  todayFailed: 0,
};

export default function AdminPage() {
  const [status, setStatus] = useState<Status>(EMPTY_STATUS);
  const [setting, setSetting] = useState<Setting>({ enabled: false, scheduleTime: "09:00", sourceId: "all", updatedAt: "" });
  const [runs, setRuns] = useState<CrawlRun[]>([]);
  const [items, setItems] = useState<RawItem[]>([]);
  const [selectedId, setSelectedId] = useState("");
  const [detail, setDetail] = useState<RawDetail | null>(null);
  const [message, setMessage] = useState("就绪");
  const [loading, setLoading] = useState(false);

  async function refreshAll(nextSelectedId = selectedId) {
    const [statusPayload, settingPayload, runsPayload, rawPayload] = await Promise.all([
      fetchJson<Status>("/api/admin/crawler/status", EMPTY_STATUS),
      fetchJson<Setting>("/api/admin/crawler/settings", setting),
      fetchJson<{ runs: CrawlRun[] }>("/api/admin/crawl-runs", { runs: [] }),
      fetchJson<{ items: RawItem[] }>("/api/admin/raw-contents", { items: [] }),
    ]);
    setStatus(statusPayload);
    setSetting(settingPayload);
    setRuns(runsPayload.runs);
    setItems(rawPayload.items);
    const preferredId = nextSelectedId || rawPayload.items[0]?.documentId || "";
    setSelectedId(preferredId);
    if (preferredId) {
      await loadDetail(preferredId);
    } else {
      setDetail(null);
    }
  }

  async function loadDetail(documentId: string) {
    setSelectedId(documentId);
    const payload = await fetchJson<RawDetail | null>(`/api/admin/raw-contents/${encodeURIComponent(documentId)}`, null);
    setDetail(payload);
  }

  async function runCrawler() {
    setLoading(true);
    setMessage("爬取任务已启动，正在等待 PostgreSQL 写入...");
    const payload = await fetchJson<{ started?: boolean; runId?: string; error?: string }>("/api/admin/crawler/run", {}, { method: "POST" });
    setMessage(payload.started ? `已启动：${payload.runId}` : payload.error || "启动失败");
    setTimeout(() => void refreshAll(), 1800);
    setLoading(false);
  }

  async function saveSetting() {
    setLoading(true);
    const payload = await fetchJson<Setting>("/api/admin/crawler/settings", setting, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(setting),
    });
    setSetting(payload);
    setMessage("设置已保存");
    setLoading(false);
  }

  async function review(action: "trusted" | "untrusted" | "garbled" | "recrawl") {
    if (!selectedId) return;
    await fetchJson(`/api/admin/raw-contents/${encodeURIComponent(selectedId)}/review`, {}, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ action, reviewerNote: "" }),
    });
    setMessage(`已标记：${action}`);
    await refreshAll(selectedId);
  }

  useEffect(() => {
    void refreshAll();
    const id = window.setInterval(() => void refreshAll(), 8000);
    return () => window.clearInterval(id);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const currentStatus = useMemo(() => {
    if (!runs[0]) return "暂无任务";
    return runs[0].status === "success" ? "成功" : runs[0].status;
  }, [runs]);

  return (
    <main className="admin-shell">
      <header className="admin-top">
        <h1>Finahunt 后台</h1>
        <div className="admin-top-meta">
          <span>PostgreSQL：<b className={status.postgresConnected ? "admin-green" : "admin-red"}>{status.postgresConnected ? "已连接" : "未连接"}</b></span>
          <span className="admin-divider" />
          <span>最近同步：{formatTime(status.lastRunAt) || "--"}</span>
          <button className="admin-refresh" onClick={() => void refreshAll()} type="button">刷新</button>
        </div>
      </header>

      <aside className="admin-side">
        <div className="admin-nav-item">▦ <span>数据总览</span></div>
        <div className="admin-nav-item active">▣ <span>自动爬取</span></div>
        <div className="admin-nav-item">▤ <span>原始数据</span></div>
      </aside>

      <section className="admin-main">
        <section>
          <h2>1. 爬取控制</h2>
          <div className="admin-panel control-panel">
            <h3>自动爬取设置</h3>
            <div className="control-grid">
              <label className="toggle-row">
                启用每日定时爬取
                <input checked={setting.enabled} onChange={(event) => setSetting({ ...setting, enabled: event.target.checked })} type="checkbox" />
              </label>
              <label>
                执行时间
                <select value={setting.scheduleTime} onChange={(event) => setSetting({ ...setting, scheduleTime: event.target.value })}>
                  <option value="09:00">每天 09:00</option>
                  <option value="08:30">每天 08:30</option>
                  <option value="15:00">每天 15:00</option>
                </select>
              </label>
              <label>
                数据源
                <select value={setting.sourceId} onChange={(event) => setSetting({ ...setting, sourceId: event.target.value })}>
                  <option value="all">全部数据源</option>
                  <option value="cls">财联社</option>
                  <option value="stcn">证券时报</option>
                  <option value="yicai">第一财经</option>
                </select>
              </label>
            </div>
            <div className="admin-actions">
              <button className="primary-admin-btn" disabled={loading} onClick={() => void runCrawler()} type="button">立即爬取</button>
              <button className="plain-admin-btn" disabled={loading} onClick={() => void saveSetting()} type="button">保存设置</button>
            </div>
            <div className="control-status">
              <span>上次执行：{formatTime(status.lastRunAt) || "--"}</span>
              <span>本次状态：<b className={status.lastStatus === "failed" ? "admin-red" : "admin-green"}>{currentStatus}</b></span>
              <span>新增 <b className="admin-green">{status.todayInserted}</b> 条 / 重复 <b className="admin-orange">{status.todayDuplicated}</b> 条 / 异常 <b className="admin-red">{status.todayFailed}</b> 条</span>
              <span>{message}</span>
            </div>
          </div>
        </section>

        <section>
          <h2>2. 爬取任务记录</h2>
          <div className="admin-table-box">
            <table className="admin-table run-table">
              <thead>
                <tr><th>run_id</th><th>source_id</th><th>status</th><th>started_at</th><th>finished_at</th><th>fetched_count</th><th>inserted_count</th><th>duplicate_count</th><th>failed_count</th></tr>
              </thead>
              <tbody>
                {runs.map((run) => (
                  <tr key={run.runId}>
                    <td>{run.runId}</td><td>{run.sourceId}</td><td><StatusBadge status={run.status} /></td>
                    <td>{formatTime(run.startedAt)}</td><td>{formatTime(run.finishedAt)}</td>
                    <td>{run.fetchedCount}</td><td>{run.insertedCount}</td><td>{run.duplicateCount}</td><td>{run.failedCount}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </section>

        <section>
          <h2>3. 原始数据展示</h2>
          <div className="raw-grid">
            <div className="admin-table-box raw-list">
              <div className="filter-row">
                <label>来源 (source_name)<select><option>全部</option></select></label>
                <label>真实性 (authenticity_status)<select><option>全部</option></select></label>
                <label>审核状态 (review_status)<select><option>全部</option></select></label>
                <label>发布时间<input readOnly value="2025-05-13  ~  2025-05-20" /></label>
              </div>
              <div className="search-row"><input readOnly placeholder="搜索标题或链接..." /><button type="button">搜索</button><button type="button">重置</button></div>
              <table className="admin-table raw-table">
                <thead>
                  <tr><th>抓取时间</th><th>发布时间</th><th>来源</th><th>标题</th><th>原文链接</th><th>内容长度</th><th>source_hash</th><th>truth_score</th><th>authenticity_status</th></tr>
                </thead>
                <tbody>
                  {items.map((item) => (
                    <tr className={item.documentId === selectedId ? "selected" : ""} key={item.documentId} onClick={() => void loadDetail(item.documentId)}>
                      <td>{formatTime(item.createdAt)}</td><td>{formatTime(item.publishedAt)}</td><td>{item.sourceName}</td><td>{item.title}</td>
                      <td><a href={item.url} target="_blank">{shortUrl(item.url)}</a></td><td>{item.contentLength}</td><td>{shortHash(item.sourceHash)}</td>
                      <td>{item.truthScore}</td><td><StatusBadge status={item.authenticityStatus} /></td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            <aside className="admin-panel detail-panel">
              <h3>数据详情</h3>
              {detail ? (
                <>
                  <DetailRow label="原始标题" value={detail.title} />
                  <DetailRow label="原文链接" value={detail.url} link />
                  <DetailRow label="发布时间" value={formatTime(detail.publishedAt)} />
                  <DetailRow label="抓取时间" value={formatTime(detail.createdAt)} />
                  <DetailRow label="内容长度" value={String(detail.contentLength)} />
                  <DetailRow label="source_hash" value={detail.sourceHash} />
                  <DetailRow label="truth_score" value={String(detail.truthScore)} />
                  <h4>原始内容：</h4>
                  <div className="raw-content-box">{detail.contentText}</div>
                  <h4>人工处理</h4>
                  <div className="review-actions">
                    <button className="trust-btn" onClick={() => void review("trusted")} type="button">标记可信</button>
                    <button className="bad-btn" onClick={() => void review("untrusted")} type="button">标记不可信</button>
                    <button className="garbled-btn" onClick={() => void review("garbled")} type="button">标记乱码</button>
                    <button className="recrawl-btn" onClick={() => void review("recrawl")} type="button">重新爬取</button>
                  </div>
                </>
              ) : (
                <p className="empty-detail">暂无原始数据。先点击立即爬取。</p>
              )}
            </aside>
          </div>
        </section>
      </section>
    </main>
  );
}

async function fetchJson<T>(url: string, fallback: T, init?: RequestInit): Promise<T> {
  try {
    const response = await fetch(url, { cache: "no-store", ...init });
    if (!response.ok) return fallback;
    return (await response.json()) as T;
  } catch {
    return fallback;
  }
}

function StatusBadge({ status }: { status: string }) {
  const label = status === "success" ? "成功" : status === "failed" ? "失败" : status;
  return <span className={`admin-badge ${status}`}>{label}</span>;
}

function DetailRow({ label, value, link = false }: { label: string; value: string; link?: boolean }) {
  return (
    <div className="detail-row">
      <span>{label}：</span>
      {link ? <a href={value} target="_blank">{value}</a> : <b>{value}</b>}
    </div>
  );
}

function formatTime(value: string): string {
  if (!value) return "";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value.slice(0, 19).replace("T", " ");
  return date.toISOString().slice(0, 19).replace("T", " ");
}

function shortHash(value: string): string {
  return value ? `${value.slice(0, 12)}...${value.slice(-8)}` : "";
}

function shortUrl(value: string): string {
  return value.replace(/^https?:\/\//, "").slice(0, 34);
}
