from packages.storage import JsonLegacyRepository, PostgresRepository, get_runtime_repository
from packages.storage.admin_audit import authenticity_status_for_score, calculate_truth_score, create_source_hash, has_garbled_text


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
                "source_name": "CLS",
                "title": "Robot industry policy continues",
                "url": "https://example.test/raw-1",
                "published_at": "2026-05-14T09:00:00+08:00",
                "content_text": "Robot theme heat is improving with public market policy catalysts and supply-chain evidence.",
                "http_status": 200,
            }
        ],
        "normalized_documents.json": [
            {
                "document_id": "raw-1",
                "source_id": "cls-telegraph",
                "source_name": "CLS",
                "title": "Robot industry policy continues",
                "url": "https://example.test/raw-1",
                "published_at": "2026-05-14T09:00:00+08:00",
            }
        ],
        "canonical_events.json": [
            {
                "event_id": "event-1",
                "title": "Robot industry policy continues",
                "event_type": "policy",
                "event_subject": "robot",
                "event_time": "2026-05-14T09:00:00+08:00",
                "summary": "Policy catalyst entered observation window.",
                "related_themes": ["robot"],
                "related_industries": ["manufacturing"],
                "source_refs": ["https://example.test/raw-1"],
                "metadata": {"source_id": "cls-telegraph"},
            }
        ],
        "theme_heat_snapshots.json": [
            {
                "theme_candidate_id": "theme-robot",
                "cluster_id": "cluster-robot",
                "theme_name": "robot",
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
                "theme_name": "robot",
                "low_position_score": 66,
                "low_position_reason": "Policy catalyst is strong; position still needs observation.",
                "risk_notice": "Research observation only.",
                "candidate_stocks": [
                    {
                        "stock_code": "300001",
                        "stock_name": "Example Intelligence",
                        "candidate_purity_score": 72,
                        "mapping_reason": "Public information maps it to the robot chain.",
                    }
                ],
            }
        ],
        "daily_message_workbench.json": {
            "status": "success",
            "message_count": 1,
            "messages": [{"message": {"message_id": "msg-1", "title": "robot catalyst"}}],
        },
        "daily_theme_workbench.json": {
            "status": "success",
            "theme_count": 1,
            "themes": [
                {
                    "theme_name": "robot",
                    "low_position_score": 66,
                    "low_position_reason": "Policy catalyst is strong; position still needs observation.",
                    "validation_bucket": "validated",
                    "candidate_stocks": [{"stock_code": "300001", "stock_name": "Example Intelligence"}],
                    "messages": [{"message_id": "msg-1", "title": "robot catalyst"}],
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
    assert snapshot["themes"][0]["themeName"] == "robot"
    assert snapshot["events"][0]["eventId"] == "event-1"

    workbench = repository.load_low_position_workbench("2026-05-14")
    assert workbench is not None
    assert workbench["dataMode"] == "postgres"
    assert workbench["messageCount"] == 1
    assert workbench["validatedThemes"][0]["theme_name"] == "robot"


def test_admin_audit_scores_and_flags_garbled_text():
    item = {
        "source_id": "cls",
        "source_name": "CLS",
        "title": "Central bank liquidity support",
        "url": "https://example.test/a",
        "published_at": "2026-05-15T09:00:00+08:00",
        "content_text": "A long public-market research note with enough original text to pass the content length threshold and support manual review.",
        "http_status": 200,
    }

    source_hash = create_source_hash(item)
    score = calculate_truth_score({**item, "source_hash": source_hash})

    assert len(source_hash) == 64
    assert score == 100
    assert authenticity_status_for_score(score) == "trusted"
    assert has_garbled_text("\ufffd\ufffd") is True


def test_admin_repository_tracks_raw_content_reviews_runs_and_duplicates(tmp_path):
    repository = PostgresRepository(f"sqlite:///{tmp_path / 'admin.db'}")
    run_id = "admin-test-run"
    row = {
        "document_id": "admin-doc-1",
        "source_id": "cls",
        "source_name": "CLS",
        "title": "Central bank liquidity support",
        "url": "https://example.test/admin-doc-1",
        "published_at": "2026-05-15T09:00:00+08:00",
        "content_text": "A long public-market research note with enough original text to pass the content length threshold and support manual review.",
        "http_status": 200,
    }

    repository.create_crawl_run(run_id, "all")
    first = repository.save_admin_raw_contents(run_id, [row])
    second = repository.save_admin_raw_contents(run_id, [row])
    repository.finish_crawl_run(
        run_id,
        "success",
        first.fetched_count + second.fetched_count,
        first.inserted_count + second.inserted_count,
        first.duplicate_count + second.duplicate_count,
        first.failed_count + second.failed_count,
        "",
    )

    assert first.inserted_count == 1
    assert second.duplicate_count == 1
    raw_rows = repository.list_admin_raw_contents()
    assert len(raw_rows) == 1
    assert raw_rows[0]["sourceHash"]
    assert raw_rows[0]["contentLength"] == len(row["content_text"])
    assert raw_rows[0]["truthScore"] == 100
    assert raw_rows[0]["authenticityStatus"] == "trusted"

    detail = repository.get_admin_raw_content("admin-doc-1")
    assert detail is not None
    assert detail["contentText"] == row["content_text"]

    reviewed = repository.review_admin_raw_content("admin-doc-1", "garbled", "bad encoding")
    assert reviewed is not None
    assert reviewed["reviewStatus"] == "garbled"
    assert reviewed["authenticityStatus"] == "blocked"

    setting = repository.save_admin_crawler_setting(True, "09:00", "all")
    assert setting["enabled"] is True
    assert setting["scheduleTime"] == "09:00"

    runs = repository.list_admin_crawl_runs()
    assert runs[0]["runId"] == run_id
    assert runs[0]["duplicateCount"] == 1
