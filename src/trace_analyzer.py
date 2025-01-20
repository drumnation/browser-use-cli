import json
import zipfile
from pathlib import Path
from typing import Dict, List, Optional, Any
import asyncio

class PlaywrightTrace:
    def __init__(self, trace_path: str):
        self.trace_path = Path(trace_path)
        self.actions: List[Dict[str, Any]] = []
        self.network_requests: List[Dict[str, Any]] = []
        self.console_logs: List[str] = []
        self.errors: List[str] = []

    @classmethod
    async def parse(cls, trace_path: str) -> 'PlaywrightTrace':
        """Parse a Playwright trace file and return a PlaywrightTrace instance."""
        trace = cls(trace_path)
        await trace._parse_trace_file()
        return trace

    async def _parse_trace_file(self):
        """Parse the trace.zip file and extract relevant information."""
        if not self.trace_path.exists():
            raise FileNotFoundError(f"Trace file not found: {self.trace_path}")

        try:
            with zipfile.ZipFile(self.trace_path, 'r') as zip_ref:
                # List all files in the zip
                files = zip_ref.namelist()
                
                # Parse trace files
                for file in files:
                    if file.endswith('.trace'):
                        trace_data = zip_ref.read(file).decode('utf-8')
                        for line in trace_data.split('\n'):
                            if line.strip():
                                try:
                                    event = json.loads(line)
                                    self._process_event(event)
                                except json.JSONDecodeError:
                                    self.errors.append(f"Failed to parse trace event: {line}")
                
                # Parse network HAR if available
                har_files = [f for f in files if f.endswith('.har')]
                if har_files:
                    har_data = json.loads(zip_ref.read(har_files[0]).decode('utf-8'))
                    self._process_har(har_data)

        except zipfile.BadZipFile:
            raise ValueError(f"Invalid trace file format: {self.trace_path}")

    def _process_event(self, event: Dict[str, Any]):
        """Process a single trace event and categorize it."""
        if 'type' not in event:
            return

        event_type = event['type']
        
        if event_type == 'before' or event_type == 'after':
            # Handle action events
            if 'method' in event and 'params' in event:
                self.actions.append({
                    'type': event['method'],
                    'timestamp': event.get('timestamp', 0),
                    'duration': event.get('duration', 0),
                    'params': event['params'],
                    'success': event_type == 'after' and 'error' not in event,
                    'error': event.get('error')
                })
        elif event_type == 'console':
            # Handle console messages
            if 'text' in event:
                self.console_logs.append(event['text'])
        elif event_type == 'error':
            # Handle error events
            if 'error' in event:
                self.errors.append(event['error'].get('message', str(event['error'])))

    def _process_har(self, har_data: Dict[str, Any]):
        """Process HAR data to extract network requests."""
        if 'log' in har_data and 'entries' in har_data['log']:
            for entry in har_data['log']['entries']:
                request = entry.get('request', {})
                response = entry.get('response', {})
                
                self.network_requests.append({
                    'url': request.get('url'),
                    'method': request.get('method'),
                    'status': response.get('status'),
                    'statusText': response.get('statusText'),
                    'duration': entry.get('time'),  # in milliseconds
                    'failure': response.get('status', 0) >= 400
                })

async def analyze_trace(trace_path: str) -> dict:
    """Parse a Playwright trace file and return structured data."""
    trace = await PlaywrightTrace.parse(trace_path)
    return {
        "actions": trace.actions,
        "network_requests": trace.network_requests,
        "console_logs": trace.console_logs,
        "errors": trace.errors,
        "summary": {
            "total_actions": len(trace.actions),
            "failed_actions": sum(1 for a in trace.actions if not a['success']),
            "total_requests": len(trace.network_requests),
            "failed_requests": sum(1 for r in trace.network_requests if r.get('failure')),
            "total_errors": len(trace.errors),
            "error_summary": "\n".join(trace.errors) if trace.errors else "No errors"
        }
    }

if __name__ == "__main__":
    # Example usage
    async def main():
        result = await analyze_trace("path/to/trace.zip")
        print(json.dumps(result, indent=2))

    asyncio.run(main())

class EnhancedTraceAnalyzer:
    """Enhanced trace analyzer for detailed browser automation insights.
    
    This class provides comprehensive analysis of browser automation traces, including:
    - Action context and element states
    - Decision-making processes and confidence levels
    - Element identification and relationships
    - Visual state changes and layout shifts
    - Error recovery strategies
    - Performance metrics and timing analysis
    
    Example:
        ```python
        analyzer = EnhancedTraceAnalyzer("trace.zip")
        result = await analyzer.analyze_all()
        
        # Component-specific analysis
        timing = await analyzer.analyze_timing()
        visual = await analyzer.analyze_visual_state()
        ```
    """
    
    def __init__(self, trace_file_path: str):
        """Initialize the enhanced trace analyzer.
        
        Args:
            trace_file_path: Path to the trace file (ZIP format) containing enhanced trace data.
        """
        self.trace_file_path = trace_file_path
        self._trace_data: Optional[Dict[str, Any]] = None

    async def _load_trace_data(self) -> Dict[str, Any]:
        """Load and validate enhanced trace data from the trace file.
        
        Returns:
            Dict containing the parsed trace data.
            
        Raises:
            ValueError: If the trace file is invalid or cannot be parsed.
        """
        if self._trace_data is None:
            try:
                trace_path = Path(self.trace_file_path)
                
                # Handle nested directory structure
                if trace_path.is_dir():
                    trace_zip = trace_path / 'trace.zip'
                    if trace_zip.is_dir():
                        trace_files = list(trace_zip.glob('*.zip'))
                        if not trace_files:
                            raise ValueError("No trace files found")
                        trace_path = trace_files[0]
                    else:
                        raise ValueError("Invalid trace directory structure")
                
                # Parse Playwright trace
                with zipfile.ZipFile(trace_path) as zf:
                    # Load trace data
                    with zf.open('trace.trace') as f:
                        trace_events = []
                        for line in f.read().decode('utf-8').splitlines():
                            if line.strip():
                                trace_events.append(json.loads(line))
                    
                    # Load network data
                    with zf.open('trace.network') as f:
                        network_events = []
                        for line in f.read().decode('utf-8').splitlines():
                            if line.strip():
                                network_events.append(json.loads(line))
                    
                    # Convert to enhanced trace format
                    self._trace_data = self._convert_playwright_trace(trace_events, network_events)
                
            except Exception as e:
                raise ValueError(f"Failed to load trace data: {str(e)}")
        
        return self._trace_data

    def _convert_playwright_trace(self, trace_events: List[Dict[str, Any]], network_events: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Convert Playwright trace format to enhanced trace format."""
        # Extract metadata
        metadata = {
            "session_id": trace_events[0].get('sessionId', 'unknown'),
            "timestamp": trace_events[0].get('timestamp', 0),
            "browser_info": {
                "viewport": next(
                    (e.get('params', {}).get('viewport') for e in trace_events 
                     if e.get('method') == 'setViewportSize'),
                    {"width": 0, "height": 0}
                ),
                "user_agent": next(
                    (e.get('params', {}).get('userAgent') for e in trace_events 
                     if e.get('method') == 'setUserAgent'),
                    "unknown"
                )
            }
        }

        # Extract steps
        steps = []
        current_step = None
        
        for event in trace_events:
            if event.get('type') == 'before':
                if current_step:
                    steps.append(current_step)
                current_step = {
                    "step_id": len(steps) + 1,
                    "action": event.get('method', 'unknown'),
                    "target": event.get('params', {}).get('selector', ''),
                    "timing": {
                        "start": event.get('timestamp', 0),
                        "end": None,
                        "duration": None
                    },
                    "status": "pending",
                    "error_context": None,
                    "visual_state": {
                        "screenshot_diffs": {},
                        "element_visibility": {},
                        "layout_shifts": []
                    },
                    "action_context": {
                        "element_state": event.get('params', {}),
                        "viewport_state": metadata['browser_info']['viewport']
                    }
                }
            elif event.get('type') == 'after' and current_step:
                current_step['timing']['end'] = event.get('timestamp', 0)
                current_step['timing']['duration'] = (
                    current_step['timing']['end'] - current_step['timing']['start']
                )
                current_step['status'] = 'error' if 'error' in event else 'success'
                if 'error' in event:
                    current_step['error_context'] = {
                        "error_type": event['error'].get('name', 'unknown'),
                        "message": event['error'].get('message', ''),
                        "stack": event['error'].get('stack', '')
                    }

        if current_step:
            steps.append(current_step)

        # Add network information
        network_info = {
            "requests": [
                {
                    "url": event.get('params', {}).get('url'),
                    "method": event.get('params', {}).get('method'),
                    "status": event.get('params', {}).get('status'),
                    "timing": event.get('params', {}).get('timing')
                }
                for event in network_events
                if event.get('method') == 'Network.responseReceived'
            ]
        }

        return {
            "metadata": metadata,
            "steps": steps,
            "network": network_info,
            "performance": {
                "navigation_timing": {
                    "dom_complete": next(
                        (e.get('timestamp', 0) for e in trace_events 
                         if e.get('method') == 'domcontentloaded'),
                        0
                    ),
                    "load_complete": next(
                        (e.get('timestamp', 0) for e in trace_events 
                         if e.get('method') == 'load'),
                        0
                    )
                },
                "interaction_timing": {
                    "time_to_first_interaction": next(
                        (e.get('timestamp', 0) for e in trace_events 
                         if e.get('type') == 'before' and e.get('method') in ['click', 'fill']),
                        0
                    ) - metadata['timestamp'],
                    "action_latency": sum(
                        step['timing']['duration'] for step in steps 
                        if step['timing']['duration'] is not None
                    ) / len(steps) if steps else 0
                }
            }
        }

    async def analyze_action_context(self) -> Dict[str, Any]:
        """Analyze the context of actions including before/after states."""
        trace_data = await self._load_trace_data()
        steps = trace_data["steps"]
        
        return {
            "steps": [
                {
                    "step_id": step["step_id"],
                    "action": step["action"],
                    "target": step["target"],
                    "element_state": step["action_context"]["element_state"],
                    "viewport_state": step["action_context"]["viewport_state"]
                }
                for step in steps
            ]
        }

    async def analyze_decision_trail(self) -> Dict[str, Any]:
        """Analyze the decision making process and alternatives considered."""
        trace_data = await self._load_trace_data()
        steps = trace_data["steps"]
        
        return {
            "steps": [
                {
                    "step_id": step["step_id"],
                    "action": step["action"],
                    "confidence": step["action_context"]["element_state"].get("confidence", 1.0),
                    "alternatives": step["action_context"]["element_state"].get("alternatives", []),
                    "reasoning": step["action_context"]["element_state"].get("reasoning", [])
                }
                for step in steps
            ]
        }

    async def analyze_element_identification(self) -> Dict[str, Any]:
        """Analyze methods used to identify elements."""
        trace_data = await self._load_trace_data()
        steps = trace_data["steps"]
        
        return {
            "steps": [
                {
                    "step_id": step["step_id"],
                    "target": step["target"],
                    "selector": step["action_context"]["element_state"].get("selector", ""),
                    "position": step["action_context"]["element_state"].get("position", {}),
                    "relationships": step["action_context"]["element_state"].get("relationships", {})
                }
                for step in steps
            ]
        }

    async def analyze_failures(self) -> Dict[str, Any]:
        """Analyze failure scenarios and recovery attempts."""
        trace_data = await self._load_trace_data()
        steps = trace_data["steps"]
        failed_steps = [step for step in steps if step["status"] == "error"]
        
        return {
            "failed_steps": [
                {
                    "step_id": step["step_id"],
                    "action": step["action"],
                    "error": step["error_context"],
                    "recovery_attempts": step["action_context"]["element_state"].get("recovery_attempts", [])
                }
                for step in failed_steps
            ],
            "total_steps": len(steps),
            "failed_steps_count": len(failed_steps)
        }

    async def analyze_session_context(self) -> Dict[str, Any]:
        """Analyze session-wide context including navigation and network activity."""
        trace_data = await self._load_trace_data()
        
        return {
            "metadata": trace_data["metadata"],
            "network": trace_data["network"],
            "performance": trace_data["performance"]
        }

    async def analyze_recovery_info(self) -> Dict[str, Any]:
        """Analyze recovery information and checkpoints."""
        trace_data = await self._load_trace_data()
        steps = trace_data["steps"]
        recovery_steps = [
            step for step in steps 
            if step["status"] == "error" and step["action_context"]["element_state"].get("recovery_attempts")
        ]
        
        return {
            "recovery_steps": [
                {
                    "step_id": step["step_id"],
                    "action": step["action"],
                    "recovery_attempts": step["action_context"]["element_state"]["recovery_attempts"],
                    "final_status": "recovered" if any(
                        attempt.get("success") 
                        for attempt in step["action_context"]["element_state"].get("recovery_attempts", [])
                    ) else "failed"
                }
                for step in recovery_steps
            ]
        }

    async def analyze_model_data(self) -> Dict[str, Any]:
        """Analyze model-specific data including token usage and vision analysis."""
        trace_data = await self._load_trace_data()
        steps = trace_data["steps"]
        
        return {
            "steps": [
                {
                    "step_id": step["step_id"],
                    "action": step["action"],
                    "model_info": step["action_context"]["element_state"].get("model_info", {}),
                    "vision_analysis": step["action_context"]["element_state"].get("vision_analysis", {})
                }
                for step in steps
            ]
        }

    async def analyze_temporal_context(self) -> Dict[str, Any]:
        """Analyze temporal information including timing and wait conditions."""
        trace_data = await self._load_trace_data()
        steps = trace_data["steps"]
        
        return {
            "steps": [
                {
                    "step_id": step["step_id"],
                    "timing": step["timing"],
                    "wait_conditions": step["action_context"]["element_state"].get("wait_conditions", [])
                }
                for step in steps
            ],
            "total_duration": sum(
                step["timing"]["duration"] for step in steps 
                if step["timing"]["duration"] is not None
            )
        }

    async def analyze_element_reporting(self) -> Dict[str, Any]:
        """Analyze enhanced element reporting with detailed selection context."""
        trace_data = await self._load_trace_data()
        steps = trace_data["steps"]
        
        return {
            "steps": [
                {
                    "step_id": step["step_id"],
                    "action": step["action"],
                    "target": step["target"],
                    "element_state": step["action_context"]["element_state"],
                    "status": step["status"]
                }
                for step in steps
            ]
        }

    async def analyze_error_context(self) -> Dict[str, Any]:
        """Analyze error context and session state information."""
        trace_data = await self._load_trace_data()
        steps = trace_data["steps"]
        error_steps = [step for step in steps if step["status"] == "error"]
        
        return {
            "error_steps": [
                {
                    "step_id": step["step_id"],
                    "action": step["action"],
                    "error_context": step["error_context"],
                    "session_state": {
                        "url": trace_data["metadata"]["browser_info"].get("url"),
                        "viewport": trace_data["metadata"]["browser_info"]["viewport"],
                        "network_status": any(
                            req["status"] >= 400 
                            for req in trace_data["network"]["requests"]
                        )
                    }
                }
                for step in error_steps
            ]
        }

    async def analyze_timing(self) -> Dict[str, Any]:
        """Analyze detailed interaction timing information."""
        trace_data = await self._load_trace_data()
        steps = trace_data["steps"]
        
        return {
            "steps": [
                {
                    "step_id": step["step_id"],
                    "action": step["action"],
                    "timing": {
                        "start": step["timing"]["start"],
                        "end": step["timing"]["end"],
                        "duration": step["timing"]["duration"]
                    }
                }
                for step in steps
                if step["timing"]["duration"] is not None
            ],
            "performance": trace_data["performance"],
            "summary": {
                "total_duration": sum(
                    step["timing"]["duration"] for step in steps 
                    if step["timing"]["duration"] is not None
                ),
                "average_step_duration": sum(
                    step["timing"]["duration"] for step in steps 
                    if step["timing"]["duration"] is not None
                ) / len([s for s in steps if s["timing"]["duration"] is not None])
            }
        }

    async def analyze_visual_state(self) -> Dict[str, Any]:
        """Analyze visual state changes with enhanced tracking."""
        trace_data = await self._load_trace_data()
        steps = trace_data.get("steps", [])
        
        visual_analysis = []
        for step in steps:
            visual_state = step.get("visual_state", {})
            visual_analysis.append({
                "step_id": step["step_id"],
                "before_action": {
                    "screenshot": visual_state.get("screenshot_diffs", {}).get("before"),
                    "visible_elements": visual_state.get("element_visibility", {}).get("before", [])
                },
                "after_action": {
                    "screenshot": visual_state.get("screenshot_diffs", {}).get("after"),
                    "visible_elements": visual_state.get("element_visibility", {}).get("after", []),
                    "added_elements": visual_state.get("element_visibility", {}).get("added", []),
                    "removed_elements": visual_state.get("element_visibility", {}).get("removed", [])
                },
                "layout_shifts": visual_state.get("layout_shifts", [])
            })
        
        return {
            "visual_changes": visual_analysis,
            "cumulative_layout_shift": sum(
                shift.get("cumulative_layout_shift", 0) 
                for step in visual_analysis 
                for shift in step.get("layout_shifts", [])
            )
        }

    async def analyze_error_recovery(self) -> Dict[str, Any]:
        """Analyze enhanced error recovery capabilities with improved context."""
        trace_data = await self._load_trace_data()
        steps = trace_data.get("steps", [])
        error_steps = [step for step in steps if step.get("status") == "error"]
        
        recovery_analysis = []
        for step in error_steps:
            error_ctx = step.get("error_context", {})
            recovery_analysis.append({
                "step_id": step["step_id"],
                "error_type": error_ctx.get("error_type", "unknown"),
                "target_element": {
                    "selector": error_ctx.get("target_element", {}).get("selector"),
                    "visible_similar_elements": error_ctx.get("target_element", {}).get("visible_similar_elements", [])
                },
                "recovery_attempts": error_ctx.get("recovery_attempts", []),
                "environment_factors": error_ctx.get("environment_factors", {})
            })
        
        return {
            "error_steps": recovery_analysis,
            "recovery_success_rate": len([r for r in recovery_analysis if any(
                attempt["outcome"] == "success" for attempt in r["recovery_attempts"]
            )]) / len(recovery_analysis) if recovery_analysis else 1.0
        }

    async def analyze_performance(self) -> Dict[str, Any]:
        """Analyze performance metrics including navigation and interaction timing."""
        trace_data = await self._load_trace_data()
        performance = trace_data.get("performance", {})
        
        return {
            "navigation_timing": performance.get("navigation_timing", {}),
            "interaction_timing": performance.get("interaction_timing", {}),
            "metrics_summary": {
                "avg_action_latency": performance.get("interaction_timing", {}).get("action_latency", 0),
                "total_interaction_time": sum(
                    step.get("timing", {}).get("duration", 0) 
                    for step in trace_data.get("steps", [])
                )
            }
        }

    async def analyze_all(self) -> Dict[str, Any]:
        """Perform comprehensive analysis of all trace components.
        
        Returns:
            Dict containing analysis results from all components:
            - action_context: Action and element state analysis
            - decision_trail: Decision-making process analysis
            - element_identification: Element location and relationships
            - failure_analysis: Failure scenarios and recovery attempts
            - session_context: Session-wide context and navigation
            - recovery_info: Recovery strategies and checkpoints
            - model_data: Model-specific data and vision analysis
            - temporal_context: Timing and sequence information
            - element_reporting: Enhanced element selection reporting
            - error_context: Error handling and recovery context
            - timing_analysis: Detailed timing breakdown
            - visual_state: Visual changes and layout analysis
            - error_recovery: Enhanced error recovery capabilities
            - performance: Performance metrics and timing analysis
        """
        trace_data = await self._load_trace_data()
        
        return {
            "action_context": await self.analyze_action_context(),
            "decision_trail": await self.analyze_decision_trail(),
            "element_identification": await self.analyze_element_identification(),
            "failure_analysis": await self.analyze_failures(),
            "session_context": await self.analyze_session_context(),
            "recovery_info": await self.analyze_recovery_info(),
            "model_data": await self.analyze_model_data(),
            "temporal_context": await self.analyze_temporal_context(),
            "element_reporting": await self.analyze_element_reporting(),
            "error_context": await self.analyze_error_context(),
            "timing_analysis": await self.analyze_timing(),
            "visual_state": await self.analyze_visual_state(),
            "error_recovery": await self.analyze_error_recovery(),
            "performance": await self.analyze_performance()
        } 