import pytest
import asyncio
import json
import zipfile
from pathlib import Path
import tempfile
from src.trace_analyzer import PlaywrightTrace, analyze_trace

# Sample trace data
SAMPLE_TRACE_DATA = [
    # Action event (before)
    {
        "type": "before",
        "method": "goto",
        "params": {"url": "https://example.com"},
        "timestamp": 1000,
        "duration": 500
    },
    # Action event (after - success)
    {
        "type": "after",
        "method": "goto",
        "params": {"url": "https://example.com"},
        "timestamp": 1500,
        "duration": 500
    },
    # Action event (after - error)
    {
        "type": "after",
        "method": "click",
        "params": {"selector": "#missing-button"},
        "timestamp": 2000,
        "duration": 100,
        "error": {"message": "Element not found"}
    },
    # Console event
    {
        "type": "console",
        "text": "Test console message"
    },
    # Error event
    {
        "type": "error",
        "error": {"message": "Test error message"}
    }
]

# Sample HAR data
SAMPLE_HAR_DATA = {
    "log": {
        "entries": [
            {
                "request": {
                    "url": "https://example.com",
                    "method": "GET"
                },
                "response": {
                    "status": 200,
                    "statusText": "OK"
                },
                "time": 150
            },
            {
                "request": {
                    "url": "https://example.com/missing",
                    "method": "GET"
                },
                "response": {
                    "status": 404,
                    "statusText": "Not Found"
                },
                "time": 100
            }
        ]
    }
}

@pytest.fixture
def sample_trace_file():
    """Create a temporary trace file with sample data."""
    with tempfile.NamedTemporaryFile(suffix='.zip', delete=False) as temp_zip:
        with zipfile.ZipFile(temp_zip.name, 'w') as zf:
            # Add trace data
            trace_data = '\n'.join(json.dumps(event) for event in SAMPLE_TRACE_DATA)
            zf.writestr('trace.trace', trace_data)
            
            # Add HAR data
            zf.writestr('trace.har', json.dumps(SAMPLE_HAR_DATA))
        
        yield temp_zip.name
        Path(temp_zip.name).unlink()

@pytest.mark.asyncio
async def test_trace_parsing(sample_trace_file):
    """Test basic trace file parsing."""
    trace = await PlaywrightTrace.parse(sample_trace_file)
    
    # Check actions
    assert len(trace.actions) == 3
    assert any(a['type'] == 'goto' and a['success'] for a in trace.actions)
    assert any(a['type'] == 'click' and not a['success'] for a in trace.actions)
    
    # Check console logs
    assert len(trace.console_logs) == 1
    assert trace.console_logs[0] == "Test console message"
    
    # Check errors
    assert len(trace.errors) == 1
    assert "Test error message" in trace.errors[0]
    
    # Check network requests
    assert len(trace.network_requests) == 2
    assert any(r['status'] == 200 for r in trace.network_requests)
    assert any(r['status'] == 404 for r in trace.network_requests)

@pytest.mark.asyncio
async def test_analyze_trace(sample_trace_file):
    """Test the analyze_trace function."""
    result = await analyze_trace(sample_trace_file)
    
    assert "actions" in result
    assert "network_requests" in result
    assert "console_logs" in result
    assert "errors" in result
    assert "summary" in result
    
    summary = result["summary"]
    assert summary["total_actions"] == 3
    assert summary["failed_actions"] == 1
    assert summary["total_requests"] == 2
    assert summary["failed_requests"] == 1
    assert summary["total_errors"] == 1

@pytest.mark.asyncio
async def test_invalid_trace_file():
    """Test handling of invalid trace files."""
    with tempfile.NamedTemporaryFile(suffix='.zip', delete=False) as temp_file:
        temp_file.write(b"Invalid zip data")
    
    with pytest.raises(ValueError, match="Invalid trace file format"):
        await PlaywrightTrace.parse(temp_file.name)
    
    Path(temp_file.name).unlink()

@pytest.mark.asyncio
async def test_missing_trace_file():
    """Test handling of missing trace files."""
    with pytest.raises(FileNotFoundError):
        await PlaywrightTrace.parse("nonexistent_file.zip")

@pytest.mark.asyncio
async def test_malformed_trace_data(sample_trace_file):
    """Test handling of malformed trace data."""
    with tempfile.NamedTemporaryFile(suffix='.zip', delete=False) as temp_zip:
        with zipfile.ZipFile(temp_zip.name, 'w') as zf:
            zf.writestr('trace.trace', 'Invalid JSON data\n{"type": "console", "text": "Valid event"}')
        
        trace = await PlaywrightTrace.parse(temp_zip.name)
        assert len(trace.errors) == 1  # One error for the invalid JSON
        assert len(trace.console_logs) == 1  # One valid console event
        
        Path(temp_zip.name).unlink() 