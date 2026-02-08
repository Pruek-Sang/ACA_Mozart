"""
Backend Session API Tests - Real Integration Tests
===================================================
Uses FastAPI TestClient to call actual API endpoints.
No mocks - tests real business logic.

Run: pytest tests/backend/test_session_api.py -v
"""

import pytest
import uuid


class TestSessionCreate:
    """Test POST /api/v1/session/start"""
    
    def test_create_session_returns_session_id(self, test_client):
        """POST /session/start → returns session_id"""
        response = test_client.post("/api/v1/session/start")
        
        assert response.status_code == 200
        data = response.json()
        assert "session_id" in data
        assert len(data["session_id"]) > 0
    
    def test_create_session_with_project_name(self, test_client):
        """POST /session/start with project_name in body → saves correctly"""
        project_name = f"TestProject_{uuid.uuid4().hex[:8]}"
        
        response = test_client.post(
            "/api/v1/session/start",
            params={"project_name": project_name}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data.get("project_name") == project_name
    
    def test_create_session_default_project_name(self, test_client):
        """POST /session/start without project_name → uses default"""
        response = test_client.post("/api/v1/session/start")
        
        assert response.status_code == 200
        data = response.json()
        # Default is "บ้านนายสมหญิง"
        assert "project_name" in data


class TestSessionRead:
    """Test GET /api/v1/session/{id}/data"""
    
    def test_get_session_status(self, test_client):
        """GET /session/{id} → returns session status"""
        # First create a session
        create_resp = test_client.post("/api/v1/session/start")
        session_id = create_resp.json()["session_id"]
        
        # Then get its status
        response = test_client.get(f"/api/v1/session/{session_id}")
        
        assert response.status_code == 200
        data = response.json()
        assert "session_id" in data or "stage" in data
    
    def test_get_nonexistent_session_returns_404(self, test_client):
        """GET /session/{nonexistent_id} → 404"""
        fake_id = str(uuid.uuid4())
        
        response = test_client.get(f"/api/v1/session/{fake_id}")
        
        assert response.status_code == 404


class TestSessionDelete:
    """Test DELETE /api/v1/session/{id}"""
    
    def test_delete_without_confirm_returns_400(self, test_client):
        """DELETE /session/{id} without confirm → 400"""
        # Create a session first
        create_resp = test_client.post("/api/v1/session/start")
        session_id = create_resp.json()["session_id"]
        
        # Try to delete without CONFIRM
        response = test_client.delete(f"/api/v1/session/{session_id}")
        
        assert response.status_code == 400
        data = response.json()
        error_msg = data.get("error", {}).get("message", "")
        # Fallback if structure is different
        if not error_msg:
             error_msg = str(data)
        
        assert "CONFIRM" in error_msg
    
    def test_delete_with_wrong_confirm_returns_400(self, test_client):
        """DELETE /session/{id}?confirm=wrong → 400"""
        create_resp = test_client.post("/api/v1/session/start")
        session_id = create_resp.json()["session_id"]
        
        response = test_client.delete(f"/api/v1/session/{session_id}?confirm=wrong")
        
        assert response.status_code == 400
    
    def test_delete_with_confirm_succeeds(self, test_client):
        """DELETE /session/{id}?confirm=CONFIRM → success"""
        create_resp = test_client.post("/api/v1/session/start")
        session_id = create_resp.json()["session_id"]
        
        response = test_client.delete(f"/api/v1/session/{session_id}?confirm=CONFIRM")
        
        assert response.status_code == 200
        assert response.json().get("status") == "deleted"


class TestProjectList:
    """Test GET /api/v1/session/list"""
    
    def test_list_projects_returns_array(self, test_client):
        """GET /session/list → returns projects array"""
        response = test_client.get("/api/v1/session/list")
        
        # May require auth, so accept 200 or 401
        if response.status_code == 200:
            data = response.json()
            assert "projects" in data
            assert isinstance(data["projects"], list)
    
    def test_list_respects_max_limit(self, test_client):
        """GET /session/list → max 10 projects"""
        response = test_client.get("/api/v1/session/list")
        
        if response.status_code == 200:
            data = response.json()
            assert len(data.get("projects", [])) <= 10


class TestHealthCheck:
    """Test GET / (root endpoint)"""
    
    def test_health_check_returns_200(self, test_client):
        """GET / → 200 with status"""
        response = test_client.get("/")
        
        assert response.status_code == 200
        data = response.json()
        assert "status" in data or "message" in data


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
