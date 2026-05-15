import Link from "next/link";

import { Icon } from "@/components/PrototypeUI";

type PageProps = { searchParams?: Promise<Record<string, string | string[] | undefined>> };

function firstParam(value: string | string[] | undefined): string {
  return Array.isArray(value) ? value[0] ?? "" : value ?? "";
}

export default async function UnlockPage({ searchParams }: PageProps) {
  const params = searchParams ? await searchParams : {};
  const sampleTitle = firstParam(params.sample).trim() || "人形机器人产业链复盘";

  return (
    <>
      <div className="breadcrumb">首页 / 样例 / {sampleTitle} / 解锁完整内容</div>
      <main className="unlock-page">
        <section className="card unlock-card">
          <div className="unlock-hero">
            <div className="unlock-icon"><Icon name="lock" size={34} /></div>
            <h1>解锁完整内容</h1>
            <p>登录后查看完整研究卡、证据链、后续观察信号和历史相似样例。</p>
          </div>

          <div className="price-grid">
            <section className="price-card">
              <h2>单篇解锁</h2>
              <p>解锁当前样例的完整内容。</p>
              <div className="price">¥9.90 <span>/ 篇</span></div>
              <div className="check">查看完整题材详情</div>
              <div className="check">查看样例全文</div>
              <div className="check muted">持续追踪题材动态</div>
              <Link className="blue-button unlock-action" href="/workbench">立即解锁</Link>
            </section>

            <section className="price-card featured">
              <span className="badge b-blue">更划算</span>
              <h2>包月会员</h2>
              <p>解锁全部题材和样例内容。</p>
              <div className="price">¥39.90 <span>/ 月</span></div>
              <div className="check">查看完整题材详情</div>
              <div className="check">查看样例全文</div>
              <div className="check">持续追踪题材动态</div>
              <div className="check">解锁全部样例内容</div>
              <Link className="blue-button unlock-action" href="/workbench">立即开通</Link>
            </section>

            <section className="price-card benefits-card">
              <h2>会员权益</h2>
              <div className="benefit-list">
                <div>
                  <b>完整题材详情</b>
                  <p>解锁题材背景、产业链、候选标的映射和风险提示。</p>
                </div>
                <div>
                  <b>样例全文</b>
                  <p>阅读完整复盘和研究卡，保留证据链上下文。</p>
                </div>
                <div>
                  <b>持续追踪</b>
                  <p>跟踪题材最新动态，区分事件事实与交易想象空间。</p>
                </div>
              </div>
            </section>
          </div>

          <div className="unlock-footer-note">
            已有账号？<Link href="/workbench">先进入工作台</Link>
          </div>
        </section>
      </main>
    </>
  );
}
