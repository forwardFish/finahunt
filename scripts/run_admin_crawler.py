from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from packages.storage import PostgresRepository, get_runtime_repository


SHANGHAI_TZ = ZoneInfo("Asia/Shanghai")


def _seed_items(run_id: str, source: str) -> list[dict[str, object]]:
    now = datetime.now(SHANGHAI_TZ).replace(microsecond=0)
    sources = [
        ("cls", "财联社"),
        ("stcn", "证券时报"),
        ("yicai", "第一财经"),
        ("sina", "新浪财经"),
        ("wallstreetcn", "华尔街见闻"),
    ]
    titles = [
        "央行开展公开市场操作维持流动性合理充裕",
        "机器人产业链订单回暖核心零部件关注度提升",
        "半导体设备国产替代进程提速多家公司披露新进展",
        "低空经济应用场景扩容产业链进入验证窗口",
        "新能源储能项目集中落地电网侧需求持续释放",
        "创新药海外授权活跃医药板块研发价值重估",
        "消费电子新品周期临近上游材料厂商排产改善",
        "算力基础设施投资延续液冷服务器关注度上升",
        "农业种业政策支持力度加大龙头企业加快布局",
        "工业软件订单恢复制造业数字化项目推进",
    ]
    items: list[dict[str, object]] = []
    for index, title in enumerate(titles):
        source_id, source_name = sources[index % len(sources)]
        if source != "all" and source_id != source:
            continue
        published = now - timedelta(minutes=18 * index + 5)
        content = (
            f"{title}。公开资料显示，相关政策、订单、产业链验证和公司公告正在形成交叉印证。"
            f"本条资讯用于 Finahunt 后台爬虫入库验收，保留原始标题、来源、发布时间和正文，便于人工检查真实性、准确性与乱码情况。"
            f"后续正式爬虫可替换 seed 数据源，但数据库字段、评分和审核流程保持一致。"
        )
        items.append(
            {
                "document_id": f"admin-seed-{index + 1:02d}",
                "run_id": run_id,
                "source_id": source_id,
                "source_name": source_name,
                "title": title,
                "url": f"https://example.finahunt.local/news/{index + 1:02d}",
                "published_at": published.isoformat(),
                "content_text": content,
                "http_status": 200,
                "license_status": "seed",
            }
        )
    return items


def main() -> int:
    parser = argparse.ArgumentParser(description="Run the Finahunt admin seed crawler.")
    parser.add_argument("--source", default="all", help="Source id to crawl, or all.")
    parser.add_argument("--run-id", default="", help="Optional run id for API-triggered runs.")
    args = parser.parse_args()

    repository = get_runtime_repository()
    if not isinstance(repository, PostgresRepository):
        print(json.dumps({"ok": False, "error": "DATABASE_BACKEND=json cannot write admin crawler data"}, ensure_ascii=False))
        return 1

    run_id = args.run_id or datetime.now(SHANGHAI_TZ).strftime("admin-%Y%m%d%H%M%S")
    source_id = args.source.strip() or "all"
    repository.create_crawl_run(run_id, source_id)
    try:
        rows = _seed_items(run_id, source_id)
        stats = repository.save_admin_raw_contents(run_id, rows)
        status = "success" if stats.failed_count == 0 else "partial"
        result = repository.finish_crawl_run(
            run_id,
            status,
            stats.fetched_count,
            stats.inserted_count,
            stats.duplicate_count,
            stats.failed_count,
            "",
        )
        payload = {
            "ok": True,
            "runId": run_id,
            "sourceId": source_id,
            "status": status,
            "fetchedCount": stats.fetched_count,
            "insertedCount": stats.inserted_count,
            "duplicateCount": stats.duplicate_count,
            "failedCount": stats.failed_count,
            "crawlRun": result,
        }
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        return 0
    except Exception as exc:
        repository.finish_crawl_run(run_id, "failed", 0, 0, 0, 1, str(exc))
        print(json.dumps({"ok": False, "runId": run_id, "error": str(exc)}, ensure_ascii=False, indent=2))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
