"""
Integration tests for JARVIS OS module imports and basic functionality.
"""

import pytest


def test_agents_import():
    from agents import AgentOrchestrator, get_orchestrator
    orch = get_orchestrator()
    assert isinstance(orch, AgentOrchestrator)
    assert orch.list_agents() == []


def test_memory_import():
    from memory import VectorStore, get_vector_store
    vs = get_vector_store()
    assert isinstance(vs, VectorStore)


def test_voice_import():
    from voice import SpeechToText, TextToSpeech, get_stt, get_tts
    stt = get_stt()
    tts = get_tts()
    assert isinstance(stt, SpeechToText)
    assert isinstance(tts, TextToSpeech)


def test_vision_import():
    from vision import OCREngine, get_ocr_engine
    ocr = get_ocr_engine()
    assert isinstance(ocr, OCREngine)


def test_automation_import():
    from automation import DesktopAutomation, get_desktop_automation
    auto = get_desktop_automation()
    assert isinstance(auto, DesktopAutomation)


def test_browser_import():
    from browser import BrowserAgent, get_browser_agent
    # get_browser_agent is async, so we just check the class
    assert BrowserAgent is not None


def test_coding_import():
    from coding import CodingAgent, get_coding_agent
    agent = get_coding_agent()
    assert isinstance(agent, CodingAgent)


def test_learning_import():
    from learning import LearningPipeline, get_learning_pipeline
    lp = get_learning_pipeline()
    assert isinstance(lp, LearningPipeline)


def test_plugins_import():
    from plugins import PluginLoader, get_plugin_loader
    pl = get_plugin_loader()
    assert isinstance(pl, PluginLoader)
