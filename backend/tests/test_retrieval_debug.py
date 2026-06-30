from __future__ import annotations

import warnings

warnings.filterwarnings(
    "ignore",
    message="Using `httpx` with `starlette.testclient` is deprecated.*",
)

from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_debug_retrieve_expected_chunks() -> None:
    cases = [
        ("arknights_amiya", "源石病", "amiya_oripathy_infected"),
        ("genshin_yae_miko", "轻小说投稿", "yae_publishing_house"),
        ("wuwa_jinhsi", "今州愿望", "jinhsi_wish_custom"),
        ("arknights_amiya", "阿米娅认识八重神子吗", "amiya_boundary_other_worlds"),
    ]

    for npc_id, query, expected_chunk_id in cases:
        response = client.get(
            "/api/v1/debug/retrieve",
            params={"npc_id": npc_id, "q": query},
        )

        assert response.status_code == 200, response.text
        body = response.json()
        chunk_ids = [chunk["chunk_id"] for chunk in body["chunks"]]
        assert expected_chunk_id in chunk_ids


def test_debug_retrieve_rejects_unknown_npc() -> None:
    response = client.get(
        "/api/v1/debug/retrieve",
        params={"npc_id": "missing_npc", "q": "test"},
    )

    assert response.status_code == 404
