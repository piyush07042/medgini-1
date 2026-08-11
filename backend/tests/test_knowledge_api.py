"""Knowledge API tests."""

from __future__ import annotations

from fastapi import status


def test_knowledge_index_and_query(client):
    response = client.post(
        "/api/v1/knowledge/index",
        json={
            "documents": ["Aspirin can interact with warfarin."],
            "metadatas": [{"source": "test_guideline"}],
            "ids": ["test_doc_1"],
        },
    )

    assert response.status_code == status.HTTP_200_OK
    body = response.json()
    assert body["success"] is True
    assert body["data"]["added"] == 1
    assert body["data"]["ids"] == ["test_doc_1"]

    query_response = client.post(
        "/api/v1/knowledge/query",
        json={"query_text": "warfarin interaction", "n_results": 1},
    )

    assert query_response.status_code == status.HTTP_200_OK
    query_body = query_response.json()
    assert query_body["success"] is True
    assert isinstance(query_body["data"]["results"], list)
    assert len(query_body["data"]["results"]) <= 1


