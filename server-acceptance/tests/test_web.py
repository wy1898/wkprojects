import pytest
from server_acceptance import web

def test_web_app_routes_when_flask_available():
    pytest.importorskip("flask")
    client = web.create_app(".").test_client()
    assert client.get("/").status_code == 200
    assert b"Server Acceptance Platform" in client.get("/").data
    assert client.get("/health").get_json()["status"] == "ok"

def test_profile_list_is_complete():
    assert set(web.PROFILES) == {"demo", "generic", "gpu_server", "ai_server", "k8s_node"}
    assert web.PROFILE_LABELS["gpu_server"] == "GPU服务器"
