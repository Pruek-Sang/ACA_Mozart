"""
Comprehensive Tests for New Display Modules

Tests for:
- assumptions_renderer
- explainable_qc
- revision_diff
- feedback_collector
- design_templates
- edge_case_confirmation

Author: Fixia
Date: 2026-01-03
"""

import pytest
from unittest.mock import MagicMock, patch
import sys
import os

# Add app to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))


class TestAssumptionsRenderer:
    """Tests for assumptions_renderer module"""
    
    def test_collect_assumptions_basic(self):
        """Test basic assumption collection"""
        from app.display.assumptions_renderer import collect_assumptions
        
        display_data = {
            "main_breaker": 100,
            "total_kw": 15.5,
            "project_name": "Test Project"
        }
        
        result = collect_assumptions(display_data)
        
        assert result["project_name"] == "Test Project"
        assert len(result["assumptions"]) > 0
        assert result["total_defaults"] > 0
        
    def test_collect_assumptions_with_user_specs(self):
        """Test assumptions with user-provided values"""
        from app.display.assumptions_renderer import collect_assumptions
        
        display_data = {"main_breaker": 100}
        user_specs = {"branch_distance": 25}
        
        result = collect_assumptions(display_data, user_specs)
        
        # Find the branch_distance assumption
        branch_assumption = next(
            (a for a in result["assumptions"] if a["key"] == "branch_distance"),
            None
        )
        
        assert branch_assumption is not None
        assert branch_assumption["source"] == "user"
        assert branch_assumption["value"] == "25"
        assert result["has_user_overrides"] is True
        
    def test_render_assumptions_markdown(self):
        """Test Markdown rendering"""
        from app.display.assumptions_renderer import (
            collect_assumptions, 
            render_assumptions_markdown
        )
        
        display_data = {"main_breaker": 100}
        assumptions_data = collect_assumptions(display_data)
        
        markdown = render_assumptions_markdown(assumptions_data)
        
        assert "## 📊 สมมติฐานที่ใช้ในการออกแบบ" in markdown
        assert "| รายการ |" in markdown


class TestExplainableQC:
    """Tests for explainable_qc module"""
    
    def test_create_explainable_warning_vd(self):
        """Test VD warning creation"""
        from app.display.explainable_qc import (
            create_explainable_warning,
            Severity,
            ActionType
        )
        
        warning = create_explainable_warning(
            "VD_EXCEED",
            circuit_name="ห้องนอน 1",
            before_value="2.5mm²",
            after_value="4mm²"
        )
        
        assert warning["code"] == "VD_EXCEED"
        assert warning["severity"] == Severity.WARNING.value
        assert warning["circuit_name"] == "ห้องนอน 1"
        assert warning["suggested_action"]["action_type"] == ActionType.UPSIZE_WIRE.value
        assert "2.5mm²" in warning["suggested_action"]["description"]
        
    def test_create_explainable_warning_rcbo(self):
        """Test RCBO warning creation"""
        from app.display.explainable_qc import create_explainable_warning, Severity
        
        warning = create_explainable_warning("NO_RCBO_WET")
        
        assert warning["code"] == "NO_RCBO_WET"
        assert warning["severity"] == Severity.CRITICAL.value
        assert "30mA" in warning["suggested_action"]["description"]
        
    def test_convert_legacy_warnings(self):
        """Test legacy warning conversion"""
        from app.display.explainable_qc import convert_legacy_warnings
        
        legacy = [
            "Voltage Drop exceeds 3% limit",
            "No RCBO for wet location",
            "Some other warning"
        ]
        
        result = convert_legacy_warnings(legacy)
        
        assert len(result) == 3
        assert result[0]["code"] == "VD_EXCEED"
        assert result[1]["code"] == "NO_RCBO_WET"
        assert result[2]["code"] == "GENERIC"


class TestRevisionDiff:
    """Tests for revision_diff module"""
    
    def test_diff_projects_no_change(self):
        """Test diff with no changes"""
        from app.display.revision_diff import diff_projects
        
        old = {"version": 1, "building_type": "บ้านเดี่ยว"}
        new = {"version": 2, "building_type": "บ้านเดี่ยว"}
        
        result = diff_projects(old, new)
        
        assert result["from_version"] == 1
        assert result["to_version"] == 2
        assert result["change_count"] == 0
        assert "ไม่มีการเปลี่ยนแปลง" in result["summary"]
        
    def test_diff_projects_with_changes(self):
        """Test diff with changes"""
        from app.display.revision_diff import diff_projects
        
        old = {"version": 1, "building_type": "บ้านเดี่ยว", "num_floors": 1}
        new = {"version": 2, "building_type": "ทาวน์เฮ้าส์", "num_floors": 2}
        
        result = diff_projects(old, new)
        
        assert result["change_count"] == 2
        assert "~2 แก้ไข" in result["summary"]
        
    def test_diff_projects_room_added(self):
        """Test diff with room added"""
        from app.display.revision_diff import diff_projects
        
        old = {"version": 1, "rooms": []}
        new = {"version": 2, "rooms": [{"name": "ห้องนอน 1"}]}
        
        result = diff_projects(old, new)
        
        room_change = next(
            (c for c in result["changes"] if "ห้องนอน 1" in c["label"]),
            None
        )
        
        assert room_change is not None
        assert room_change["change_type"] == "added"


class TestFeedbackCollector:
    """Tests for feedback_collector module"""
    
    def test_create_feedback(self):
        """Test feedback creation"""
        from app.middleware.feedback_collector import (
            create_feedback,
            FeedbackType,
            FeedbackRating
        )
        
        feedback = create_feedback(
            feedback_type=FeedbackType.BUG_REPORT,
            message="Test bug report",
            rating=FeedbackRating.POOR,
        )
        
        assert feedback["feedback_type"] == "bug_report"
        assert feedback["message"] == "Test bug report"
        assert feedback["rating"] == "poor"
        assert feedback["is_resolved"] is False
        assert feedback["id"] is not None
        
    def test_feedback_collector_submit_and_get(self):
        """Test feedback collector operations"""
        from app.middleware.feedback_collector import (
            FeedbackCollector,
            create_feedback,
            FeedbackType
        )
        
        collector = FeedbackCollector()
        
        feedback1 = create_feedback(FeedbackType.BUG_REPORT, "Bug 1")
        feedback2 = create_feedback(FeedbackType.FEATURE_REQUEST, "Feature 1")
        
        collector.submit(feedback1)
        collector.submit(feedback2)
        
        all_feedback = collector.get_all()
        assert len(all_feedback) == 2
        
        bugs = collector.get_by_type(FeedbackType.BUG_REPORT)
        assert len(bugs) == 1
        
    def test_feedback_stats(self):
        """Test feedback statistics"""
        from app.middleware.feedback_collector import (
            FeedbackCollector,
            create_feedback,
            FeedbackType,
            FeedbackRating
        )
        
        collector = FeedbackCollector()
        
        collector.submit(create_feedback(FeedbackType.BUG_REPORT, "Bug", FeedbackRating.POOR))
        collector.submit(create_feedback(FeedbackType.GENERAL, "General", FeedbackRating.GOOD))
        
        stats = collector.get_stats()
        
        assert stats["total_count"] == 2
        assert stats["by_type"]["bug_report"] == 1
        assert stats["avg_rating_score"] == 3.0  # (2 + 4) / 2


class TestDesignTemplates:
    """Tests for design_templates module"""
    
    def test_get_default_template(self):
        """Test getting default template"""
        from app.context.design_templates import TemplateManager
        
        manager = TemplateManager()
        default = manager.get_default_template()
        
        assert default is not None
        assert default.is_default is True
        assert default.name == "มาตรฐาน วสท. 2564"
        
    def test_get_all_templates(self):
        """Test getting all templates"""
        from app.context.design_templates import TemplateManager, SYSTEM_TEMPLATES
        
        manager = TemplateManager()
        all_templates = manager.get_all_templates()
        
        assert len(all_templates) >= len(SYSTEM_TEMPLATES)
        
    def test_create_user_template(self):
        """Test creating user template"""
        from app.context.design_templates import (
            TemplateManager,
            DEFAULT_TEMPLATE_DEFAULTS,
            DEFAULT_DISPLAY_PREFERENCES
        )
        
        manager = TemplateManager()
        
        template = manager.create_template(
            name="My Custom Template",
            description="Custom test template",
            defaults=DEFAULT_TEMPLATE_DEFAULTS,
            display=DEFAULT_DISPLAY_PREFERENCES,
            created_by="test_user"
        )
        
        assert template.name == "My Custom Template"
        assert template.is_system is False
        assert template.created_by == "test_user"
        
        # Should be retrievable
        retrieved = manager.get_template(template.id)
        assert retrieved is not None
        
    def test_cannot_delete_system_template(self):
        """Test that system templates cannot be deleted"""
        from app.context.design_templates import TemplateManager
        
        manager = TemplateManager()
        
        # Try to delete system template
        result = manager.delete_template("standard_eit")
        
        assert result is False
        assert manager.get_template("standard_eit") is not None


class TestEdgeCaseConfirmation:
    """Tests for edge_case_confirmation module"""
    
    def test_create_confirmation_request(self):
        """Test confirmation request creation"""
        from app.edge_case_confirmation import (
            create_confirmation_request,
            ConfirmationType
        )
        
        request = create_confirmation_request(
            ConfirmationType.DISTANCE_NOT_SPECIFIED,
            {"building_type": "บ้านเดี่ยว"}
        )
        
        assert request["confirmation_type"] == "distance_not_specified"
        assert request["title"] == "📏 ระบุระยะเดินสาย"
        assert len(request["options"]) == 2
        assert request["allows_custom"] is True
        
    def test_check_edge_cases_no_distance(self):
        """Test edge case detection for missing distance"""
        from app.edge_case_confirmation import check_edge_cases
        
        parsed_input = {
            "building_type": "บ้านเดี่ยว",
            "rooms": []
        }
        
        confirmations = check_edge_cases(parsed_input)
        
        # Should have distance confirmation
        distance_conf = next(
            (c for c in confirmations if c["confirmation_type"] == "distance_not_specified"),
            None
        )
        assert distance_conf is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
