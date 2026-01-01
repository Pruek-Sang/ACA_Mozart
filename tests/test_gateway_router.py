"""
Gateway Router Test - Test Intent Classification Logic
Catches: Routing bugs (design vs chat queries)

This test verifies:
1. Design keywords route to MOZART
2. Chat keywords route to AMADEUS  
3. Edge cases handled correctly
"""
import sys
import os
import pytest

# Add project root to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'Copilot-Mozart', 'ACA_Mozart-copilot[RAG]'))


class TestGatewayRouter:
    """Test Gateway LLM Router and Regex fallback."""
    
    @pytest.fixture
    def router(self):
        """Create router instance."""
        from gate_way_new import LLMRouter
        return LLMRouter()
    
    def test_design_keywords_route_to_mozart(self, router):
        """Design keywords should route to MOZART."""
        design_queries = [
            "ออกแบบบ้าน 2 ชั้น",
            "ห้องครัว มีเตาไฟฟ้า",
            "คำนวณ breaker size",
            "ห้องนอน 3 ห้อง",
            "ติดแอร์กี่ BTU",
            "ขนาดสายไฟสำหรับปั๊มน้ำ",
            "voltage drop คืออะไร",
            "มาตรฐาน วสท",
        ]
        
        for query in design_queries:
            decision = router._route_with_regex(query)
            assert decision.mode.value == "MOZART", \
                f"'{query}' should route to MOZART, got {decision.mode.value}"
    
    def test_chat_queries_route_to_amadeus(self, router):
        """General chat should route to AMADEUS."""
        chat_queries = [
            "สวัสดี",
            "เล่าเรื่องตลกหน่อย",
            "คุณคิดยังไงกับความหมายของชีวิต",
            "วันนี้อากาศเป็นอย่างไร",
        ]
        
        for query in chat_queries:
            decision = router._route_with_regex(query)
            assert decision.mode.value == "AMADEUS", \
                f"'{query}' should route to AMADEUS, got {decision.mode.value}"
    
    def test_confidence_increases_with_matches(self, router):
        """More keyword matches should increase confidence."""
        single_match = "ห้องนอน"
        multi_match = "ออกแบบบ้าน 2 ชั้น ห้องนอน 3 ห้อง มีแอร์"
        
        decision_single = router._route_with_regex(single_match)
        decision_multi = router._route_with_regex(multi_match)
        
        assert decision_multi.confidence >= decision_single.confidence


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
