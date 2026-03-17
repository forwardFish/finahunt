from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[2]
BACKLOG_DIR = ROOT / "tasks" / "backlog_v1"
CONTRACT_KEYS = ("story_inputs", "story_process", "story_outputs", "verification_basis")


def test_all_story_cards_define_non_empty_story_contracts() -> None:
    story_files = sorted(BACKLOG_DIR.rglob("S*.yaml"))
    assert story_files, "No story files found under backlog_v1."

    for story_file in story_files:
        payload = yaml.safe_load(story_file.read_text(encoding="utf-8"))
        story_id = payload.get("story_id") or payload.get("task_id") or story_file.stem
        for key in CONTRACT_KEYS:
            value = payload.get(key)
            assert isinstance(value, list), f"{story_id} missing list field {key}"
            assert value, f"{story_id} has empty field {key}"
            assert all(str(item).strip() for item in value), f"{story_id} has blank items in {key}"
