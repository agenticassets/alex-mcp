"""
Test suite for resolve_institution using the MCP server and pyalex.
Focus: EMBO, MPIA, IRAM.
"""

import pytest
import pyalex

pyalex.config.email = "test@example.com"
pyalex.config.max_retries = 2
pyalex.config.retry_backoff_factor = 0.1
pyalex.config.retry_http_codes = [429, 500, 503]

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from src.alex_mcp.server import _resolve_institution_impl as resolve_institution

def test_resolve_institution_embo():
    result = resolve_institution("EMBO")
    assert result["best_match"] is not None
    assert "i1303691731" in result["best_match"]["id"].lower() or "I1303691731" in result["best_match"]["id"]

def test_resolve_institution_mpia():
    result = resolve_institution("MPIA")
    assert result["best_match"] is not None
    assert "i4210109156" in result["best_match"]["id"].lower() or "I4210109156" in result["best_match"]["id"]

def test_resolve_institution_iram():
    result = resolve_institution("IRAM")
    assert result["best_match"] is not None
    assert "i4210096876" in result["best_match"]["id"].lower() or "I4210096876" in result["best_match"]["id"]
