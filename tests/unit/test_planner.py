"""Multi-step mission planner tests."""

from __future__ import annotations

import pytest

from agents.planner import split_mission, get_planner
from core.security import get_permission_manager, Permission


@pytest.fixture(autouse=True)
def _grants():
    pm = get_permission_manager()
    for p in Permission:
        try:
            if not pm.has_permission(p):
                pm.grant(p, reason="test")
        except Exception:
            pass


def test_split_and():
    parts = split_mission("open youtube and set a timer for 5 minutes")
    assert len(parts) == 2
    assert "youtube" in parts[0].lower()
    assert "timer" in parts[1].lower()


def test_split_then():
    parts = split_mission("search for iron man then open gmail")
    assert len(parts) >= 2


def test_no_split_simple():
    parts = split_mission("Open YouTube")
    assert parts == ["Open YouTube"]


@pytest.mark.asyncio
async def test_mission_multi():
    planner = get_planner()
    result = await planner.run(
        "open youtube and calculate 2+2",
        dry_run=True,
    )
    assert result.multi is True
    assert len(result.steps) == 2
    assert result.handled
    assert "Mission" in result.reply or "step" in result.reply.lower() or "sir" in result.reply.lower()


@pytest.mark.asyncio
async def test_mission_single():
    planner = get_planner()
    result = await planner.run("Open YouTube", dry_run=True)
    assert result.multi is False
    assert result.steps[0].skill == "browser.open_youtube"
