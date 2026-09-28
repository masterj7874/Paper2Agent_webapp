"""Agent registry: reads the Paper2Agent-generated MCP servers registered in Claude Code (~/.claude.json)
and the installed paper skills (~/.claude/skills/*-paper). Everything is discovered at startup; nothing is hard-coded
except display metadata for the three agents produced in this workspace (falls back to generic metadata otherwise)."""
from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from pathlib import Path

WEBAPP_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = WEBAPP_ROOT / "data"
CLAUDE_JSON = Path(os.environ.get("PAPER2AGENT_CLAUDE_JSON", Path.home() / ".claude.json"))
SKILLS_DIR = Path(os.environ.get("PAPER2AGENT_SKILLS_DIR", Path.home() / ".claude" / "skills"))
UPLOAD_DIR = Path(os.environ.get("PAPER2AGENT_UPLOAD_DIR", DATA_DIR / "uploads"))
JOB_DIR = Path(os.environ.get("PAPER2AGENT_JOB_DIR", DATA_DIR / "jobs"))
PAPER_RUNS_DIR = Path(os.environ.get("PAPER2AGENT_PAPER_DIR", DATA_DIR / "paper_runs"))
LOCAL_AGENTS_FILE = Path(os.environ.get("PAPER2AGENT_REGISTRY", DATA_DIR / "agents.json"))
PAPER2AGENT_SKILL = Path(os.environ.get("PAPER2AGENT_SKILL", Path.home() / ".claude/skills/paper2agent/SKILL.md"))
# Only agents whose command lives under these roots are exposed (safety: never expose arbitrary MCP servers).
ALLOWED_ROOTS = [Path(p) for p in os.environ.get(
    "PAPER2AGENT_ALLOWED_ROOTS", str(WEBAPP_ROOT.parent / "Paper2Agent_out")
).split(":") if p]
ALLOWED_ROOTS += [WEBAPP_ROOT.parent / "MedKG", PAPER_RUNS_DIR]


def relocate(value):
    """Keep registrations usable when this checkout's disk mount has moved."""
    old = "/media/jerisuh/4,0TBDisk/"
    if isinstance(value, str) and value.startswith(old):
        candidate = str(WEBAPP_ROOT.parent / value[len(old):])
        return candidate if Path(candidate).exists() else value
    if isinstance(value, list):
        return [relocate(v) for v in value]
    if isinstance(value, dict):
        return {k: relocate(v) for k, v in value.items()}
    return value

DISPLAY = {
    "MedSAM": {
        "title": "MedSAM",
        "paper": "Segment anything in medical images",
        "venue": "Nature Communications 15:654 (2024)",
        "authors": "Ma, He, Li, Han, You, Wang",
        "doi": "10.1038/s41467-024-44824-z",
        "repo": "https://github.com/bowang-lab/MedSAM",
        "skill": "medsam-paper",
        "accent": "#22d3ee",
        "tagline": "Promptable segmentation across 10 imaging modalities",
        "icon": "scan",
    },
    "MedMNIST": {
        "title": "MedMNIST v2",
        "paper": "MedMNIST v2 - A large-scale lightweight benchmark for 2D and 3D biomedical image classification",
        "venue": "Scientific Data 10:41 (2023)",
        "authors": "Yang, Shi, Wei, Liu, Zhao, Ke, Pfister, Ni",
        "doi": "10.1038/s41597-022-01721-8",
        "repo": "https://github.com/MedMNIST/MedMNIST",
        "skill": "medmnist-paper",
        "accent": "#a78bfa",
        "tagline": "18 lightweight biomedical classification datasets",
        "icon": "grid",
    },
    "Cellpose": {
        "title": "Cellpose 2.0",
        "paper": "Cellpose 2.0: how to train your own model",
        "venue": "Nature Methods 19, 1634–1641 (2022)",
        "authors": "Pachitariu, Stringer",
        "doi": "10.1038/s41592-022-01663-4",
        "repo": "https://github.com/MouseLand/cellpose",
        "skill": "cellpose2-paper",
        "accent": "#34d399",
        "tagline": "Generalist cell segmentation you can fine-tune",
        "icon": "cell",
    },
    "HDBET": {
        "title": "HD-BET",
        "paper": "Automated brain extraction of multisequence MRI using artificial neural networks",
        "venue": "Human Brain Mapping 40, 4952–4964 (2019)",
        "authors": "Isensee, Schell, Pflueger, Brugnara, Bonekamp, Neuberger, Wick, Schlemmer, Heiland, Wick, Bendszus, Maier-Hein, Kickingereder",
        "doi": "10.1002/hbm.24750",
        "repo": "https://github.com/MIC-DKFZ/HD-BET",
        "skill": "hdbet-paper",
        "accent": "#fb923c",
        "tagline": "Skull-stripping for any MRI sequence, tumours included",
        "icon": "brain",
    },
    "nnUNet": {
        "title": "nnU-Net",
        "paper": "nnU-Net: a self-configuring method for deep learning-based biomedical image segmentation",
        "venue": "Nature Methods 18, 203–211 (2021)",
        "authors": "Isensee, Jaeger, Kohl, Petersen, Maier-Hein",
        "doi": "10.1038/s41592-020-01008-z",
        "repo": "https://github.com/MIC-DKFZ/nnUNet",
        "skill": "nnunet-paper",
        "accent": "#f472b6",
        "tagline": "Self-configuring segmentation: plan, train, predict, evaluate",
        "icon": "net",
    },
    "MedKG": {
        "title": "MedKG",
        "paper": "Medical-AI knowledge graph + advanced RAG over 236k Q1 papers",
        "venue": "Ontology-grounded Neo4j + Qdrant (built 2026-09-22)",
        "accent": "#facc15",
        "tagline": "Search, cite and reason over the corpus",
        "icon": "kg",
        "skill": None,
    },
}


@dataclass
class AgentSpec:
    name: str
    command: str
    args: list[str]
    env: dict[str, str] = field(default_factory=dict)
    cwd: str | None = None
    display: dict = field(default_factory=dict)
    skill_dir: Path | None = None

    @property
    def package_dir(self) -> Path:
        # <pkg>/src/<server>.py -> <pkg>
        return Path(self.args[0]).resolve().parent.parent if self.args else Path(self.command).parent


def _under_allowed(p: str) -> bool:
    """True when the path (as written, without following symlinks — venv pythons link into uv's store) lies under an allowed root."""
    rp = Path(os.path.abspath(p))
    return any(rp.is_relative_to(Path(os.path.abspath(root))) for root in ALLOWED_ROOTS)


def load_agents() -> dict[str, AgentSpec]:
    agents: dict[str, AgentSpec] = {}
    data = json.loads(CLAUDE_JSON.read_text()) if CLAUDE_JSON.exists() else {}
    for name, original in (data.get("mcpServers") or {}).items():
        cfg = relocate(original)
        if cfg.get("type", "stdio") != "stdio":
            continue
        cmd, args = cfg.get("command"), cfg.get("args") or []
        if not cmd or not args or not (_under_allowed(cmd) and _under_allowed(args[0])):
            continue
        disp = dict(DISPLAY.get(name) or {"title": name, "paper": name, "accent": "#f472b6", "tagline": "Paper2Agent MCP server", "icon": "dot", "skill": None})
        skill = SKILLS_DIR / disp["skill"] if disp.get("skill") else None
        agents[name] = AgentSpec(name=name, command=cmd, args=list(args), env=dict(cfg.get("env") or {}),
                                 cwd=cfg.get("cwd"), display=disp, skill_dir=skill if skill and skill.exists() else None)
    if LOCAL_AGENTS_FILE.exists():
        local = json.loads(LOCAL_AGENTS_FILE.read_text())
        for name, cfg in local.items():
            args = cfg.get("args") or []
            command = cfg.get("command", "")
            if not args or not Path(args[0]).resolve().is_relative_to(PAPER_RUNS_DIR.resolve()):
                continue
            backend_python = os.path.abspath(WEBAPP_ROOT / "backend/.venv/bin/python")
            if not (_under_allowed(command) or os.path.abspath(command) == backend_python):
                continue
            if name in agents:
                continue
            agents[name] = AgentSpec(name=name, command=command, args=args,
                                    env=cfg.get("env", {}), cwd=cfg.get("cwd"),
                                    display=cfg.get("display", {}),
                                    skill_dir=Path(cfg["skill_dir"]) if cfg.get("skill_dir") else None)
    return agents


def save_local_agent(spec: AgentSpec) -> None:
    """Persist only this application's agents; leave the user's Claude config alone."""
    from dataclasses import asdict
    LOCAL_AGENTS_FILE.parent.mkdir(parents=True, exist_ok=True)
    registry = json.loads(LOCAL_AGENTS_FILE.read_text()) if LOCAL_AGENTS_FILE.exists() else {}
    item = asdict(spec)
    item["skill_dir"] = str(spec.skill_dir) if spec.skill_dir else None
    registry[spec.name] = item
    tmp = LOCAL_AGENTS_FILE.with_suffix(".tmp")
    tmp.write_text(json.dumps(registry, ensure_ascii=False, indent=2))
    tmp.chmod(0o600)
    tmp.replace(LOCAL_AGENTS_FILE)
