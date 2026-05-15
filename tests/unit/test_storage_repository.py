from packages.storage import JsonLegacyRepository, PostgresRepository, get_runtime_repository


def test_default_repository_uses_local_postgres(monkeypatch):
    monkeypatch.delenv("DATABASE_BACKEND", raising=False)
    monkeypatch.delenv("DATABASE_URL", raising=False)
    monkeypatch.delenv("FINAHUNT_LOCAL_DATABASE_URL", raising=False)

    repository = get_runtime_repository()

    assert isinstance(repository, PostgresRepository)
    assert repository.database_url == "postgresql+psycopg://finahunt:finahunt_local@127.0.0.1:54329/finahunt"


def test_json_backend_remains_explicit_opt_out(monkeypatch):
    monkeypatch.setenv("DATABASE_BACKEND", "json")

    repository = get_runtime_repository()

    assert isinstance(repository, JsonLegacyRepository)


def test_postgres_repository_projects_runtime_artifacts_for_web(tmp_path):
    repository = PostgresRepository(f"sqlite:///{tmp_path / 'runtime.db'}")
    artifacts = {
        "raw_documents.json": [
            {
                "document_id": "raw-1",
                "source_id": "cls-telegraph",
                "source_name": "财联社",
                "title": "机器人产业政策持续落地",
                "url": "https://example.test/raw-1",
                "published_at": "2026-05-14T09:00:00+08:00",
                "content_text": "机器人主题热度提升。",
            }
        ],
        "normalized_documents.json": [
            {
                "document_id": "raw-1",
                "source_id": "cls-telegraph",
                "source_name": "财联社",
                "title": "机器人产业政策持续落地",
                "url": "https://example.test/raw-1",
                "published_at": "2026-05-14T09:00:00+08:00",
            }
        ],
        "canonical_events.json": [
            {
                "event_id": "event-1",
                "title": "机器人产业政策持续落地",
                "event_type": "政策",
                "event_subject": "机器人",
                "event_time": "2026-05-14T09:00:00+08:00",
                "summary": "政策催化进入观察窗口。",
                "related_themes": ["机器人"],
                "related_industries": ["智能制造"],
                "source_refs": ["https://example.test/raw-1"],
                "metadata": {"source_id": "cls-telegraph"},
            }
        ],
        "theme_heat_snapshots.json": [
            {
                "theme_candidate_id": "theme-robot",
                "cluster_id": "cluster-robot",
                "theme_name": "机器人",
                "heat_score": 81,
                "catalyst_score": 76,
                "continuity_score": 70,
                "fermentation_score": 73,
                "fermentation_stage": "early",
                "latest_event_time": "2026-05-14T09:00:00+08:00",
                "mention_count": 1,
                "source_count": 1,
            }
        ],
        "low_position_opportunities.json": [
            {
                "theme_name": "机器人",
                "low_position_score": 66,
                "low_position_reason": "政策催化强，位置仍需观察。",
                "risk_notice": "仅供研究观察，不构成投资建议。",
                "candidate_stocks": [
                    {
                        "stock_code": "300001",
                        "stock_name": "示例智能",
                        "candidate_purity_score": 72,
                        "mapping_reason": "公开信息显示与机器人链条相关。",
                    }
                ],
            }
        ],
        "daily_message_workbench.json": {
            "status": "success",
            "message_count": 1,
            "messages": [{"message": {"message_id": "msg-1", "title": "机器人催化"}}],
        },
        "daily_theme_workbench.json": {
            "status": "success",
            "theme_count": 1,
            "themes": [
                {
                    "theme_name": "机器人",
                    "low_position_score": 66,
                    "low_position_reason": "政策催化强，位置仍需观察。",
                    "validation_bucket": "validated",
                    "candidate_stocks": [{"stock_code": "300001", "stock_name": "示例智能"}],
                    "messages": [{"message_id": "msg-1", "title": "机器人催化"}],
                }
            ],
        },
        "manifest.json": {"created_at": "2026-05-14T10:00:00+08:00"},
    }

    status = repository.save_runtime_projection(
        run_id="run-storage-test",
        trace_id="trace-storage-test",
        artifact_batch_dir="workspace/artifacts/runtime/run-storage-test",
        artifacts=artifacts,
    )

    assert status.status == "PASS"
    snapshot = repository.load_daily_snapshot("2026-05-14")
    assert snapshot is not None
    assert snapshot["dataMode"] == "postgres"
    assert snapshot["stats"]["rawDocumentCount"] == 1
    assert snapshot["themes"][0]["themeName"] == "机器人"
    assert snapshot["events"][0]["eventId"] == "event-1"

    workbench = repository.load_low_position_workbench("2026-05-14")
    assert workbench is not None
    assert workbench["dataMode"] == "postgres"
    assert workbench["messageCount"] == 1
    assert workbench["validatedThemes"][0]["theme_name"] == "机器人"
