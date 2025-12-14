import json
import re
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]


def _read(rel: str) -> str:
    return (REPO_ROOT / rel).read_text(encoding="utf-8")


def test_frontend_vite_engine_compatible_with_github_actions_node_version() -> None:
    """Reproduces the GH Actions failure mode: Node version too low for Vite."""

    lock_path = REPO_ROOT / "Copilot-Mozart/ACA_Mozart-copilot[RAG]/frontend_UI_UX/mozart-chat/package-lock.json"
    lock = json.loads(lock_path.read_text(encoding="utf-8"))

    vite_pkg = lock["packages"]["node_modules/vite"]
    engine = vite_pkg["engines"]["node"]

    # Current frontend stack (Vite 7) requires Node >=20.19.0 (or >=22.12.0)
    assert "^20.19.0" in engine or ">=22.12.0" in engine

    workflow_text = _read(".github/workflows/docker-build.yml")

    # Find the node-version configured for the frontend build job
    match = re.search(r"node-version:\s*'([^']+)'", workflow_text)
    assert match, "workflow missing node-version setting"

    node_version = match.group(1).strip()

    # Minimal contract: must satisfy Vite's engines requirement
    assert node_version in {"20.19.0", "22.12.0"}, (
        f"workflow node-version={node_version} is incompatible with Vite engines ({engine}); "
        "use 20.19.0 or 22.12.0"
    )


def test_fullstack_compose_mounts_exist_and_gateway_env_matches_code() -> None:
    fullstack = _read("docker-compose.fullstack.yml")

    # Fullstack frontend mounts these. They must exist in repo for one-command startup.
    assert (REPO_ROOT / "frontend-dist/index.html").exists(), "frontend-dist/index.html missing"
    assert (REPO_ROOT / "Docker/nginx.conf").exists(), "Docker/nginx.conf missing"

    # Contract: gateway container must configure the env var the gateway code actually reads.
    assert "MOZART_ENDPOINT" in fullstack, "fullstack compose must set MOZART_ENDPOINT for gateway"


def test_prod_compose_includes_gateway_and_frontend_for_one_command_full_system() -> None:
    prod = _read("docker-compose.prod.yml")

    # Contract: prod compose must include gateway + frontend (not only mcp-core + rag)
    assert re.search(r"^\s*gateway:\s*$", prod, flags=re.MULTILINE), "prod compose missing gateway service"
    assert re.search(r"^\s*frontend:\s*$", prod, flags=re.MULTILINE), "prod compose missing frontend service"

    # Contract: prod compose should be runnable without local builds (pull images)
    assert "acatest01/mozart-gateway" in prod, "prod compose should reference mozart-gateway image"
    assert "acatest01/mozart-frontend" in prod, "prod compose should reference mozart-frontend image"

    # Also ensure core services still exist
    assert re.search(r"^\s*mcp-core:\s*$", prod, flags=re.MULTILINE)
    assert re.search(r"^\s*mozart-rag:\s*$", prod, flags=re.MULTILINE)
