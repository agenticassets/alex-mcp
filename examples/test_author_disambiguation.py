"""
Test suite for disambiguate_author using the MCP server and pyalex.
Focus: Fiona M. Watt and Jorge Abreu Vicente.
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
from src.alex_mcp.server import _disambiguate_author_impl as disambiguate_author

def test_disambiguate_fiona_watt_name_only():
    result = disambiguate_author(name="Fiona M Watt")
    print(f"Disambiguation result for Fiona M Watt: {result}")
    assert result["most_likely"] is not None
    assert "A5068471552" in result["most_likely"]["author"]["id"]

def test_disambiguate_fiona_watt_with_institution():
    result = disambiguate_author(name="Fiona M Watt", affiliation="EMBO")
    print(f"Disambiguation result for Fiona M Watt: {result}")
    assert result["most_likely"] is not None
    assert "A5068471552" in result["most_likely"]["author"]["id"]

def test_disambiguate_fiona_watt_with_topic():
    result = disambiguate_author(name="Fiona M Watt", research_field="Stem Cells")
    print(f"Disambiguation result for Fiona M Watt: {result}")
    assert result["most_likely"] is not None
    assert "A5068471552" in result["most_likely"]["author"]["id"]

def test_disambiguate_jorge_abreu_name_only():
    result = disambiguate_author(name="Jorge Abreu Vicente")
    print(f"Disambiguation result for J. Abreu-Vicente: {result}")
    assert result["most_likely"] is not None
    assert "A5058921480" in result["most_likely"]["author"]["id"]

def test_disambiguate_jorge_abreu_with_institution():
    result = disambiguate_author(name="Jorge Abreu Vicente", affiliation="MPIA")
    print(f"Disambiguation result for J. Abreu-Vicente: {result}")
    assert result["most_likely"] is not None
    assert "A5058921480" in result["most_likely"]["author"]["id"]

def test_disambiguate_jorge_abreu_with_topic():
    result = disambiguate_author(name="Jorge Abreu Vicente", research_field="molecular clouds")
    print(f"Disambiguation result for J. Abreu-Vicente: {result}")
    assert result["most_likely"] is not None
    assert "A5058921480" in result["most_likely"]["author"]["id"]
