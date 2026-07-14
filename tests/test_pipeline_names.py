from __future__ import annotations

import os

import pytest

from overseer_core import pipeline_names


def test_strip_yunex_prefix():
    assert pipeline_names.strip_display_prefixes("Yunex Traffic Flow") == "Traffic Flow"


def test_strip_prefix_case_insensitive():
    assert pipeline_names.strip_display_prefixes("yunex Traffic Flow") == "Traffic Flow"


def test_strip_custom_prefix_from_env(monkeypatch):
    monkeypatch.setenv("OVERSEER_NAME_PREFIX_STRIP", "Acme Corp ,")
    assert pipeline_names.strip_display_prefixes("Acme Corp Pipeline X") == "Pipeline X"


def test_build_catalog_picks_shorter_name():
    index = pipeline_names.build_catalog_name_index(
        [
            {"pipeline_id": "traffic_flow", "name": "Yunex Traffic Flow"},
            {"pipeline_id": "traffic_flow", "name": "Traffic Flow"},
        ]
    )
    assert index["traffic_flow"] == "Traffic Flow"


def test_resolve_prefers_catalog_over_raw():
    index = {"traffic_flow": "Traffic Flow"}
    assert (
        pipeline_names.resolve_display_name(
            "traffic_flow",
            "HOST1",
            "Yunex Traffic Flow",
            index,
        )
        == "Traffic Flow"
    )


def test_resolve_strips_without_catalog():
    assert (
        pipeline_names.resolve_display_name(
            "traffic_flow",
            "",
            "Yunex Traffic Flow",
            {},
        )
        == "Traffic Flow"
    )


def test_resolve_falls_back_to_pipeline_id():
    assert pipeline_names.resolve_display_name("my_pipe", "", None, {}) == "my_pipe"


def test_normalize_run_item():
    index = {"p1": "Short Name"}
    run = pipeline_names.normalize_run_item(
        {"pipeline_id": "p1", "host_id": "h1", "pipeline_name": "Yunex Short Name"},
        index,
    )
    assert run["pipeline_name"] == "Short Name"
