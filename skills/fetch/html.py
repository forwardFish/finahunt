from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from typing import Any

from bs4 import BeautifulSoup


@dataclass(slots=True)
class HtmlSnapshot:
    url: str
    html: str
    _soup: BeautifulSoup = field(init=False, repr=False)

    def __post_init__(self) -> None:
        self._soup = BeautifulSoup(self.html, "html.parser")

    def first_text(self, selectors: list[str]) -> str:
        for selector in selectors:
            node = self._soup.select_one(selector)
            if not node:
                continue
            if node.name == "meta":
                content = (node.get("content") or "").strip()
                if content:
                    return content
            text = node.get_text(" ", strip=True)
            if text:
                return text
        return ""

    def many_text(self, selectors: list[str], limit: int = 10) -> list[str]:
        results: list[str] = []
        for selector in selectors:
            for node in self._soup.select(selector):
                if node.name == "meta":
                    value = (node.get("content") or "").strip()
                else:
                    value = node.get_text(" ", strip=True)
                if value:
                    results.append(value)
                if len(results) >= limit:
                    return list(dict.fromkeys(results))
        return list(dict.fromkeys(results))


def extract_json_array_by_key(html: str, key: str) -> list[dict[str, Any]]:
    marker = f'{key}":['
    idx = html.find(marker)
    if idx == -1:
        raise ValueError(f"marker_not_found:{key}")
    start = idx + len(marker) - 1
    depth = 0
    end = None
    for index in range(start, len(html)):
        char = html[index]
        if char == "[":
            depth += 1
        elif char == "]":
            depth -= 1
            if depth == 0:
                end = index + 1
                break
    if end is None:
        raise ValueError(f"array_not_closed:{key}")
    return json.loads(html[start:end])


def extract_js_object_by_assignment(html: str, assignment: str) -> dict[str, Any]:
    idx = html.find(assignment)
    if idx == -1:
        raise ValueError(f"assignment_not_found:{assignment}")
    start = idx + len(assignment)
    while start < len(html) and html[start].isspace():
        start += 1
    if start >= len(html) or html[start] != "{":
        raise ValueError(f"object_not_found:{assignment}")

    depth = 0
    end = None
    for index in range(start, len(html)):
        char = html[index]
        if char == "{":
            depth += 1
        elif char == "}":
            depth -= 1
            if depth == 0:
                end = index + 1
                break
    if end is None:
        raise ValueError(f"object_not_closed:{assignment}")

    payload = re.sub(r":undefined([,}])", r":null\1", html[start:end])
    return json.loads(payload)


def decode_js_string(value: str) -> str:
    return (
        str(value or "")
        .replace("\\u002F", "/")
        .replace("\\n", " ")
        .replace("\\t", " ")
        .replace('\\"', '"')
        .replace("\\'", "'")
        .strip()
    )


def clean_text(value: str) -> str:
    return re.sub(r"\s+", " ", str(value or "")).strip()
