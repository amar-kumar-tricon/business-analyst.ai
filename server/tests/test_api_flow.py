from __future__ import annotations

from fastapi.testclient import TestClient

from app.main import create_app


def test_project_run_resume_approve_flow() -> None:
    with TestClient(create_app()) as client:
        created = client.post(
            "/api/projects",
            json={"name": "Demo", "additional_context": "System must support approval workflow."},
        )
        assert created.status_code == 200
        project_id = created.json()["project_id"]

        run_res = client.post(f"/api/projects/{project_id}/run")
        assert run_res.status_code == 200

        current_question = run_res.json().get("current_question")
        if current_question is not None:
            ans_res = client.post(
                f"/api/projects/{project_id}/discovery/answer",
                json={"answer": "Use phased rollout", "status": "answered"},
            )
            assert ans_res.status_code == 200

        approve_res = client.post(f"/api/projects/{project_id}/approve", json={})
        assert approve_res.status_code == 200
        assert approve_res.json()["final_doc_pdf_s3_key"] is not None

        events = client.get(f"/api/projects/{project_id}/events")
        assert events.status_code == 200
        assert isinstance(events.json()["events"], list)
