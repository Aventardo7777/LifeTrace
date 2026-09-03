"""API tests using FastAPI's TestClient."""

from __future__ import annotations

from datetime import date

from app.seed import seed_demo_data


def test_health(client):
    res = client.get("/health")
    assert res.status_code == 200
    assert res.json()["status"] == "ok"


def test_dashboard_page(client):
    res = client.get("/")
    assert res.status_code == 200
    assert "概览" in res.text


def test_record_page(client):
    res = client.get("/record")
    assert res.status_code == 200
    assert "记录" in res.text


def test_analysis_page(client):
    res = client.get("/analysis")
    assert res.status_code == 200
    assert "相关性分析" in res.text


def test_data_page(client):
    res = client.get("/data")
    assert res.status_code == 200


def test_create_record_via_api(client, db):
    payload = {
        "date": "2026-05-10",
        "sleep_hours": 7.0,
        "study_hours": 5.5,
        "exercise_hours": 1.0,
        "entertainment_hours": 2.0,
        "social_count": 2,
        "spending": 120.0,
        "mood": 8,
        "stress": 4,
        "stay_up_late": False,
        "plan_completed": True,
        "weather": "晴",
    }
    res = client.post("/api/records", json=payload)
    assert res.status_code == 200
    body = res.json()
    assert body["date"] == "2026-05-10"

    got = client.get("/api/records/date/2026-05-10")
    assert got.status_code == 200
    assert got.json()["mood"] == 8


def test_list_records(client, db):
    seed_demo_data(db, days=10)
    res = client.get("/api/records")
    assert res.status_code == 200
    assert res.json()["total"] >= 10


def test_export_csv(client, db):
    seed_demo_data(db, days=5)
    res = client.get("/api/export/csv")
    assert res.status_code == 200
    assert "text/csv" in res.headers["content-type"]


def test_export_json(client, db):
    seed_demo_data(db, days=5)
    res = client.get("/api/export/json")
    assert res.status_code == 200
    assert res.json()["count"] >= 1


def test_whatif_api(client, db):
    seed_demo_data(db, days=60)
    res = client.get("/api/analysis/whatif?feature=sleep_hours&current=5&target=7")
    assert res.status_code == 200
    data = res.json()
    assert "error" not in data
    assert len(data["outcomes"]) > 0


def test_timeseries_api(client, db):
    res = client.get("/api/analysis/timeseries?metric=mood&granularity=week")
    assert res.status_code == 200
    assert "series" in res.json()


def test_scatter_api(client, db):
    res = client.get("/api/analysis/scatter?x=sleep_hours&y=mood")
    assert res.status_code == 200
    assert "chart" in res.json()
