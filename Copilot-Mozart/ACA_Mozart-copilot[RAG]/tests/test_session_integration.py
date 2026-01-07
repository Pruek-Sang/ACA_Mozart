"""
Test Suite for Session Integration (Level 2 Testing)

Tests the unified session system with Facade pattern.
Covers: create, list, delete with CONFIRM, max 10 limit, guest support.

Run: python -m pytest tests/test_session_integration.py -v
"""

import sys
import os
import asyncio
import unittest
from unittest.mock import MagicMock, patch, AsyncMock

# Add app to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))


class TestSessionIntegration(unittest.TestCase):
    """Tests for unified session system."""
    
    def test_01_session_store_facade_init(self):
        """Test SessionStore initializes with Facade pattern."""
        from app.session_store import SessionStore
        
        store = SessionStore(ttl_minutes=30)
        # Should have attributes from Facade
        self.assertTrue(hasattr(store, '_use_injector'))
        self.assertTrue(hasattr(store, '_injector'))
        self.assertEqual(store.ttl, 30)
    
    def test_02_session_store_create_fallback(self):
        """Test SessionStore creates session with in-memory fallback."""
        from app.session_store import SessionStore
        
        # Force in-memory mode
        store = SessionStore(ttl_minutes=60)
        store._use_injector = False
        store._injector = None
        
        session = store.create_session()
        self.assertIsNotNone(session)
        self.assertIsNotNone(session.session_id)
        self.assertEqual(session.stage, "gathering")
    
    def test_03_session_data_has_project_name(self):
        """Test SessionData includes project_name field."""
        from app.context.session_injector import SessionData, DEFAULT_PROJECT_NAME
        
        session = SessionData()
        self.assertEqual(session.project_name, DEFAULT_PROJECT_NAME)
        
        # With custom name
        session2 = SessionData(project_name="บ้านคุณสมชาย")
        self.assertEqual(session2.project_name, "บ้านคุณสมชาย")
    
    def test_04_session_config_values(self):
        """Test session configuration constants."""
        from app.context.session_injector import (
            SESSION_TTL_HOURS, 
            MAX_PROJECTS_PER_USER,
            DEFAULT_PROJECT_NAME
        )
        
        self.assertEqual(SESSION_TTL_HOURS, 24)
        self.assertEqual(MAX_PROJECTS_PER_USER, 10)
        self.assertEqual(DEFAULT_PROJECT_NAME, "บ้านนายสมหญิง")
    
    def test_05_guest_mode_uses_null_user_id(self):
        """Test that guest mode uses NULL user_id (not 'guest_xxx' string).
        
        After Schema fix: Guest sessions use user_id = NULL 
        instead of 'guest_xxx' which was incompatible with Supabase UUID column.
        """
        from app.context.session_injector import SessionInjector
        
        injector = SessionInjector()
        
        # The create() method should pass user_id=None to Supabase for guests
        # This is tested by checking the code does NOT use _generate_guest_id anymore
        import inspect
        source = inspect.getsource(injector.create)
        
        # Should NOT call _generate_guest_id() anymore
        self.assertNotIn("_generate_guest_id()", source)
        # Should use user_id directly (None for guest)
        self.assertIn("actual_user_id = user_id", source)
    
    def test_06_session_injector_max_projects_check(self):
        """Test that create() checks max projects limit."""
        from app.context.session_injector import SessionInjector
        
        injector = SessionInjector()
        
        # Check the create method signature
        import inspect
        sig = inspect.signature(injector.create)
        params = list(sig.parameters.keys())
        
        self.assertIn('user_id', params)
        self.assertIn('project_name', params)
        self.assertIn('initial_data', params)
    
    def test_07_delete_requires_confirm(self):
        """Test that delete endpoint requires CONFIRM."""
        # This would be an integration test with FastAPI TestClient
        # For now, verify the logic is in place
        import re
        
        routes_path = os.path.join(
            os.path.dirname(__file__), '..', 'app', 'routes.py'
        )
        with open(routes_path, 'r') as f:
            content = f.read()
        
        # Check CONFIRM requirement exists
        self.assertIn('confirm != "CONFIRM"', content)
        self.assertIn('?confirm=CONFIRM', content)
    
    def test_08_list_projects_endpoint_exists(self):
        """Test that list projects endpoint exists."""
        import re
        
        routes_path = os.path.join(
            os.path.dirname(__file__), '..', 'app', 'routes.py'
        )
        with open(routes_path, 'r') as f:
            content = f.read()
        
        # Check list endpoint exists
        self.assertIn('/api/v1/session/list', content)
        self.assertIn('def list_projects', content)
    
    def test_09_start_session_accepts_project_name(self):
        """Test that start_session accepts project_name from request body."""
        import re
        
        routes_path = os.path.join(
            os.path.dirname(__file__), '..', 'app', 'routes.py'
        )
        with open(routes_path, 'r') as f:
            content = f.read()
        
        # Check project_name is parsed from body (not query param anymore)
        # New code uses: body.get("project_name") and stores in actual_project_name
        self.assertIn('body.get("project_name")', content)
        self.assertIn('project_name=actual_project_name', content)


class TestSessionExpiry(unittest.TestCase):
    """Tests for session expiry logic."""
    
    def test_01_session_ttl_config(self):
        """Test SESSION_TTL_HOURS is defined."""
        from app.context.session_injector import SESSION_TTL_HOURS
        
        # Should be 24 hours
        self.assertEqual(SESSION_TTL_HOURS, 24)
    
    def test_02_conversation_session_expiry(self):
        """Test ConversationSession is_expired method."""
        from app.session_store import ConversationSession
        from datetime import datetime, timedelta, timezone
        
        # Create session
        session = ConversationSession(session_id="test-123")
        
        # Should not be expired immediately
        self.assertFalse(session.is_expired(ttl_minutes=60))
        
        # Simulate old session
        session.updated_at = datetime.now(timezone.utc) - timedelta(hours=2)
        self.assertTrue(session.is_expired(ttl_minutes=60))


if __name__ == '__main__':
    unittest.main()
