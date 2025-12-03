"""
Pytest Configuration for ACA Mozart RAG Tests
=============================================
Central conftest.py with shared fixtures and configuration
"""

import pytest
import os


def pytest_addoption(parser):
    """Add custom command line options"""
    parser.addoption(
        "--api-url",
        action="store",
        default="http://localhost:8080/api/v1/ask",
        help="URL of the /api/v1/ask endpoint"
    )
    parser.addoption(
        "--use-mock-l2",
        action="store_true",
        default=False,
        help="Use mock evaluation for Layer 2"
    )
    parser.addoption(
        "--project-id",
        action="store",
        default=os.environ.get("PROJECT_ID"),
        help="GCP Project ID for Gemini"
    )


@pytest.fixture(scope="session")
def api_url(request):
    """Get API URL from command line or default"""
    return request.config.getoption("--api-url")


@pytest.fixture(scope="session")
def use_mock_l2(request):
    """Get mock L2 flag from command line"""
    return request.config.getoption("--use-mock-l2")


@pytest.fixture(scope="session")
def project_id(request):
    """Get GCP project ID from command line or env"""
    return request.config.getoption("--project-id")
