import pytest
import asyncio
import json
import zipfile
from pathlib import Path
import tempfile
from src.trace_analyzer import PlaywrightTrace, analyze_trace, EnhancedTraceAnalyzer

# Sample enhanced trace data with new features
SAMPLE_ENHANCED_TRACE = {
    "action_context": {
        "before_state": {
            "element": "#login-button",
            "visible": True,
            "enabled": True,
            "text": "Log In"
        },
        "after_state": {
            "element": "#login-button",
            "visible": True,
            "enabled": True,
            "clicked": True
        },
        "interactive_elements": [
            {
                "selector": "#login-button",
                "confidence": 0.95,
                "chosen": True,
                "reason": "Primary login button with highest visibility"
            },
            {
                "selector": "#signup-button",
                "confidence": 0.45,
                "chosen": False,
                "reason": "Not relevant for login action"
            }
        ],
        "element_state_before": {
            "visible": True,
            "computed_styles": {
                "pointer-events": "auto",
                "opacity": "1",
                "z-index": "100"
            },
            "focus_state": "not-focused",
            "accessibility": {
                "aria-hidden": "false",
                "aria-disabled": "false"
            }
        },
        "element_state_after": {
            "visible": True,
            "focus_state": "focused",
            "triggered_events": ["click", "focus"],
            "accessibility": {
                "aria-hidden": "false",
                "aria-disabled": "false"
            }
        }
    },
    "decision_trail": {
        "reasoning": [
            "Identified login form as primary authentication method",
            "Located login button with high confidence",
            "Verified button is enabled and visible"
        ],
        "alternatives": [
            {
                "action": "click signup button",
                "rejected_reason": "Not aligned with login task"
            }
        ],
        "influential_features": ["button text", "aria-label", "position"],
        "confidence_threshold": 0.8,
        "attention_weights": {
            "element_text": 0.6,
            "aria_label": 0.3,
            "position": 0.1
        },
        "alternative_paths": [
            {
                "action": "click hamburger menu",
                "rejected_reason": "settings directly visible",
                "confidence": 0.4
            }
        ]
    },
    "element_identification": {
        "selectors": {
            "xpath": "//button[@id='login-button']",
            "css": "#login-button",
            "aria": "button[aria-label='Login']",
            "text": "button:has-text('Log In')"
        },
        "visual_position": {
            "x": 100,
            "y": 200,
            "width": 80,
            "height": 40
        },
        "relationships": {
            "parent": "form#login-form",
            "siblings": ["#username-input", "#password-input"]
        },
        "relative_position": {
            "from_top_nav": "20px from right",
            "from_viewport": "top-right quadrant",
            "nearest_landmarks": [
                {"element": "button.new-template", "distance": "40px left"},
                {"element": "div.user-menu", "distance": "60px right"}
            ]
        },
        "hierarchy": {
            "parent": "nav.top-bar",
            "siblings": ["button.new-template", "button.help"],
            "children": ["span.icon", "span.text"]
        }
    },
    "failure_analysis": {
        "state": "Element found but not clickable",
        "attempts": [
            {
                "strategy": "wait for visibility",
                "outcome": "success",
                "duration": 500
            }
        ],
        "dom_changes": [
            {
                "timestamp": 1000,
                "change": "overlay-removed"
            }
        ],
        "dom_mutations": [
            {
                "timestamp": "T+200ms",
                "type": "attribute_change",
                "element": "#settings-modal",
                "attribute": "aria-hidden",
                "old_value": "true",
                "new_value": "false"
            }
        ],
        "network_state": {
            "requests_in_flight": 2,
            "last_completed_request": "/api/settings",
            "pending_requests": [
                {
                    "url": "/api/user/preferences",
                    "method": "GET",
                    "duration_so_far": "150ms"
                }
            ]
        }
    },
    "session_context": {
        "url": "https://example.com/login",
        "route_changes": [
            {
                "from": "/",
                "to": "/login",
                "timestamp": 900
            }
        ],
        "network_requests": [
            {
                "url": "/api/auth",
                "method": "POST",
                "status": 200
            }
        ],
        "viewport": {
            "width": 1920,
            "height": 1080,
            "device_pixel_ratio": 2,
            "orientation": "landscape"
        },
        "performance_metrics": {
            "memory_usage": "120MB",
            "dom_node_count": 1250,
            "frame_rate": "60fps",
            "resource_timing": {
                "dns_lookup": "10ms",
                "connection": "50ms",
                "ttfb": "200ms"
            }
        },
        "browser_state": {
            "cookies_enabled": True,
            "javascript_enabled": True,
            "local_storage_used": "2.5MB",
            "active_service_workers": 2
        }
    },
    "recovery_info": {
        "checkpoints": [
            {
                "state": "pre-login",
                "timestamp": 800,
                "restorable": True
            }
        ],
        "alternative_selectors": [
            "#login-button",
            "button[aria-label='Login']"
        ],
        "state_restoration": {
            "checkpoints": [
                {
                    "timestamp": "T+0",
                    "state": "initial_load",
                    "restorable": True,
                    "snapshot": {
                        "url": "https://example.com/login",
                        "scroll_position": {"x": 0, "y": 0},
                        "form_data": {"username": "test", "password": "****"}
                    }
                },
                {
                    "timestamp": "T+1500ms",
                    "state": "settings_clicked",
                    "restorable": True,
                    "snapshot": {
                        "url": "https://example.com/settings",
                        "modal_open": True,
                        "selected_tab": "general"
                    }
                }
            ]
        },
        "fallback_sequences": [
            {
                "condition": "settings_button_not_visible",
                "actions": [
                    {
                        "step": "check_viewport_scroll",
                        "max_attempts": 3,
                        "delay_between_attempts": "500ms"
                    },
                    {
                        "step": "check_hamburger_menu",
                        "required_elements": ["button.menu", "div.dropdown"]
                    },
                    {
                        "step": "refresh_page",
                        "clear_cache": True
                    }
                ],
                "success_criteria": {
                    "element_visible": True,
                    "element_clickable": True,
                    "no_overlays": True
                }
            }
        ]
    },
    "model_data": {
        "input_tokens": 512,
        "output_tokens": 128,
        "vision_analysis": {
            "button_detected": True,
            "confidence": 0.98
        }
    },
    "temporal_context": {
        "action_start": 1000,
        "action_complete": 1500,
        "wait_conditions": [
            {
                "type": "animation",
                "duration": 200
            }
        ]
    },
    "element_reporting": {
        "current_step": {
            "number": 3,
            "description": "Locating settings button",
            "context": "Looking for interactive element with icon or label",
            "viewport_state": "Fully loaded, no overlays"
        },
        "element_selection": {
            "chosen_element": {
                "selector": "button.settings-icon",
                "confidence": 0.95,
                "action": "click",
                "description": "Settings button in top-right corner"
            },
            "alternative_candidates": [
                {
                    "selector": "div.menu-icon",
                    "confidence": 0.45,
                    "rejected_reason": "Not interactive element"
                },
                {
                    "selector": "span.gear-icon",
                    "confidence": 0.30,
                    "rejected_reason": "Hidden by overlay"
                }
            ],
            "selection_criteria": [
                "Visibility in viewport",
                "Interactive element",
                "Icon matching settings/gear pattern"
            ]
        }
    },
    "error_context": {
        "session_state": {
            "status": "reset_required",
            "reason": "No active session found",
            "action": "Creating new session with fresh context",
            "resolution": "Reinitialize successful"
        },
        "recovery_steps": [
            {
                "attempt": 1,
                "strategy": "clear_session",
                "outcome": "success"
            },
            {
                "attempt": 2,
                "strategy": "reinitialize",
                "outcome": "success"
            }
        ]
    },
    "timing_analysis": {
        "action_breakdown": {
            "element_search": "150ms",
            "interaction_delay": "50ms",
            "animation_duration": "200ms",
            "network_wait": "300ms"
        },
        "cumulative_timing": {
            "total_duration": "700ms",
            "user_perceived_latency": "250ms"
        },
        "performance_markers": {
            "first_paint": "100ms",
            "first_contentful_paint": "200ms",
            "time_to_interactive": "450ms"
        }
    },
    "visual_state": {
        "screenshot_diffs": {
            "before_click": "diff_1.png",
            "after_click": "diff_2.png",
            "changes_highlighted": True
        },
        "element_visibility": {
            "before": {
                "visible_area_percentage": 100,
                "obscured_by": [],
                "viewport_position": "center"
            },
            "after": {
                "visible_area_percentage": 100,
                "obscured_by": [],
                "viewport_position": "center"
            }
        },
        "layout_shifts": [
            {
                "timestamp": "T+100ms",
                "elements_moved": ["#settings-panel", "#main-content"],
                "cumulative_layout_shift": 0.1
            }
        ]
    },
    "error_recovery": {
        "retry_strategy": {
            "backoff": "exponential",
            "max_attempts": 3,
            "conditions": {
                "network_stable": True,
                "animations_complete": True,
                "viewport_stable": True
            }
        },
        "environment_factors": {
            "network_conditions": {
                "latency": "50ms",
                "bandwidth": "10Mbps",
                "stability": "stable"
            },
            "system_resources": {
                "cpu_utilization": "45%",
                "memory_available": "2GB",
                "gpu_utilization": "30%"
            }
        },
        "recovery_checkpoints": [
            {
                "timestamp": "T+0",
                "state": "pre_action",
                "snapshot": {
                    "dom_state": "hash1234",
                    "scroll_position": {"x": 0, "y": 0}
                }
            },
            {
                "timestamp": "T+500ms",
                "state": "post_action",
                "snapshot": {
                    "dom_state": "hash5678",
                    "scroll_position": {"x": 0, "y": 100}
                }
            }
        ]
    }
}

@pytest.fixture
def enhanced_trace_file():
    """Create a temporary trace file with enhanced sample data."""
    with tempfile.NamedTemporaryFile(suffix='.zip', delete=False) as temp_zip:
        with zipfile.ZipFile(temp_zip.name, 'w') as zf:
            zf.writestr('trace.enhanced', json.dumps(SAMPLE_ENHANCED_TRACE))
        yield temp_zip.name
        Path(temp_zip.name).unlink()

@pytest.mark.asyncio
async def test_action_context_analysis(enhanced_trace_file):
    """Test analysis of action context including before/after states."""
    analyzer = EnhancedTraceAnalyzer(enhanced_trace_file)
    context = await analyzer.analyze_action_context()
    
    assert context["interactive_elements_count"] == 2
    assert context["chosen_element"]["confidence"] > 0.9
    assert len(context["state_changes"]) > 0
    assert "clicked" in context["state_changes"][0]["after"]

@pytest.mark.asyncio
async def test_decision_trail_analysis(enhanced_trace_file):
    """Test analysis of decision making process."""
    analyzer = EnhancedTraceAnalyzer(enhanced_trace_file)
    trail = await analyzer.analyze_decision_trail()
    
    assert len(trail["reasoning_steps"]) == 3
    assert len(trail["alternative_actions"]) > 0
    assert len(trail["key_features"]) > 0

@pytest.mark.asyncio
async def test_element_identification_analysis(enhanced_trace_file):
    """Test analysis of element identification methods."""
    analyzer = EnhancedTraceAnalyzer(enhanced_trace_file)
    identification = await analyzer.analyze_element_identification()
    
    assert len(identification["selectors"]) >= 4
    assert "visual_position" in identification
    assert "element_relationships" in identification

@pytest.mark.asyncio
async def test_failure_analysis(enhanced_trace_file):
    """Test analysis of failure scenarios and recovery attempts."""
    analyzer = EnhancedTraceAnalyzer(enhanced_trace_file)
    failure = await analyzer.analyze_failures()
    
    assert "failure_state" in failure
    assert len(failure["recovery_attempts"]) > 0
    assert "dom_mutations" in failure

@pytest.mark.asyncio
async def test_session_context_analysis(enhanced_trace_file):
    """Test analysis of session-wide context."""
    analyzer = EnhancedTraceAnalyzer(enhanced_trace_file)
    session = await analyzer.analyze_session_context()
    
    assert "current_url" in session
    assert len(session["route_history"]) > 0
    assert len(session["network_activity"]) > 0

@pytest.mark.asyncio
async def test_recovery_info_analysis(enhanced_trace_file):
    """Test analysis of recovery information."""
    analyzer = EnhancedTraceAnalyzer(enhanced_trace_file)
    recovery = await analyzer.analyze_recovery_info()
    
    assert len(recovery["restore_points"]) > 0
    assert len(recovery["fallback_selectors"]) > 0

@pytest.mark.asyncio
async def test_model_data_analysis(enhanced_trace_file):
    """Test analysis of model-specific data."""
    analyzer = EnhancedTraceAnalyzer(enhanced_trace_file)
    model_data = await analyzer.analyze_model_data()
    
    assert "token_usage" in model_data
    assert "vision_results" in model_data
    assert model_data["token_usage"]["total"] == model_data["token_usage"]["input"] + model_data["token_usage"]["output"]

@pytest.mark.asyncio
async def test_temporal_context_analysis(enhanced_trace_file):
    """Test analysis of temporal information."""
    analyzer = EnhancedTraceAnalyzer(enhanced_trace_file)
    temporal = await analyzer.analyze_temporal_context()
    
    assert "duration" in temporal
    assert len(temporal["wait_events"]) > 0
    assert temporal["duration"] == temporal["end_time"] - temporal["start_time"]

@pytest.mark.asyncio
async def test_comprehensive_trace_analysis(enhanced_trace_file):
    """Test end-to-end analysis of enhanced trace data."""
    analyzer = EnhancedTraceAnalyzer(enhanced_trace_file)
    result = await analyzer.analyze_all()
    
    # Verify all major components are present
    assert "action_context" in result
    assert "decision_trail" in result
    assert "element_identification" in result
    assert "failure_analysis" in result
    assert "session_context" in result
    assert "recovery_info" in result
    assert "model_data" in result
    assert "temporal_context" in result
    
    # Verify relationships between components
    assert result["action_context"]["timestamp"] <= result["temporal_context"]["end_time"]
    
    # Debug prints
    print("\nFallback selectors:", result["recovery_info"]["fallback_selectors"])
    print("Element selectors:", result["element_identification"]["selectors"].values())
    
    # Verify that at least one selector is in the fallback selectors
    assert any(selector in result["recovery_info"]["fallback_selectors"] 
              for selector in result["element_identification"]["selectors"].values())

@pytest.mark.asyncio
async def test_enhanced_element_reporting(enhanced_trace_file):
    """Test enhanced element reporting with detailed selection context."""
    analyzer = EnhancedTraceAnalyzer(enhanced_trace_file)
    reporting = await analyzer.analyze_element_reporting()
    
    # Verify step context
    assert reporting["current_step"]["number"] == 3
    assert "description" in reporting["current_step"]
    assert "context" in reporting["current_step"]
    assert "viewport_state" in reporting["current_step"]
    
    # Verify element selection details
    selection = reporting["element_selection"]
    assert selection["chosen_element"]["confidence"] > 0.9
    assert len(selection["alternative_candidates"]) >= 2
    assert len(selection["selection_criteria"]) >= 3
    
    # Verify detailed element information
    chosen = selection["chosen_element"]
    assert "selector" in chosen
    assert "description" in chosen
    assert "action" in chosen

@pytest.mark.asyncio
async def test_enhanced_error_context(enhanced_trace_file):
    """Test enhanced error context and session state reporting."""
    analyzer = EnhancedTraceAnalyzer(enhanced_trace_file)
    error_context = await analyzer.analyze_error_context()
    
    # Verify session state information
    assert "status" in error_context["session_state"]
    assert "reason" in error_context["session_state"]
    assert "action" in error_context["session_state"]
    assert "resolution" in error_context["session_state"]
    
    # Verify recovery steps
    assert len(error_context["recovery_steps"]) >= 2
    for step in error_context["recovery_steps"]:
        assert "attempt" in step
        assert "strategy" in step
        assert "outcome" in step

@pytest.mark.asyncio
async def test_comprehensive_analysis_with_enhancements(enhanced_trace_file):
    """Test comprehensive analysis including new enhanced features."""
    analyzer = EnhancedTraceAnalyzer(enhanced_trace_file)
    result = await analyzer.analyze_all()
    
    # Verify new components are present
    assert "element_reporting" in result
    assert "error_context" in result
    
    # Verify element reporting structure
    reporting = result["element_reporting"]
    assert reporting["current_step"]["description"] == "Locating settings button"
    assert reporting["element_selection"]["chosen_element"]["selector"] == "button.settings-icon"
    
    # Verify error context structure
    error = result["error_context"]
    assert error["session_state"]["status"] == "reset_required"
    assert len(error["recovery_steps"]) == 2

@pytest.mark.asyncio
async def test_enhanced_action_context_state(enhanced_trace_file):
    """Test enhanced action context with detailed element state tracking."""
    analyzer = EnhancedTraceAnalyzer(enhanced_trace_file)
    context = await analyzer.analyze_action_context()
    
    # Verify element state before action
    before_state = context["element_state_before"]
    assert before_state["visible"] is True
    assert "pointer-events" in before_state["computed_styles"]
    assert before_state["focus_state"] == "not-focused"
    assert "aria-hidden" in before_state["accessibility"]
    
    # Verify element state after action
    after_state = context["element_state_after"]
    assert "focus_state" in after_state
    assert len(after_state["triggered_events"]) >= 2
    assert after_state["accessibility"]["aria-hidden"] == "false"

@pytest.mark.asyncio
async def test_enhanced_decision_trail(enhanced_trace_file):
    """Test enhanced decision trail with confidence and attention weights."""
    analyzer = EnhancedTraceAnalyzer(enhanced_trace_file)
    trail = await analyzer.analyze_decision_trail()
    
    # Verify confidence threshold
    assert trail["confidence_threshold"] > 0.7
    
    # Verify attention weights
    weights = trail["attention_weights"]
    assert abs(sum(weights.values()) - 1.0) < 0.01  # Should sum to approximately 1
    assert weights["element_text"] > weights["position"]  # Text should have higher weight
    
    # Verify alternative paths
    alternatives = trail["alternative_paths"]
    assert len(alternatives) > 0
    assert all("confidence" in path for path in alternatives)
    assert all("rejected_reason" in path for path in alternatives)

@pytest.mark.asyncio
async def test_comprehensive_analysis_with_state_tracking(enhanced_trace_file):
    """Test comprehensive analysis including state tracking enhancements."""
    analyzer = EnhancedTraceAnalyzer(enhanced_trace_file)
    result = await analyzer.analyze_all()
    
    # Verify enhanced action context
    context = result["action_context"]
    assert "element_state_before" in context
    assert "element_state_after" in context
    assert "computed_styles" in context["element_state_before"]
    
    # Verify enhanced decision trail
    trail = result["decision_trail"]
    assert "confidence_threshold" in trail
    assert "attention_weights" in trail
    assert "alternative_paths" in trail 

@pytest.mark.asyncio
async def test_enhanced_element_identification(enhanced_trace_file):
    """Test enhanced element identification with relative positioning and hierarchy."""
    analyzer = EnhancedTraceAnalyzer(enhanced_trace_file)
    identification = await analyzer.analyze_element_identification()
    
    # Verify relative positioning
    position = identification["relative_position"]
    assert "from_top_nav" in position
    assert "from_viewport" in position
    assert len(position["nearest_landmarks"]) >= 2
    
    # Verify element hierarchy
    hierarchy = identification["hierarchy"]
    assert hierarchy["parent"] == "nav.top-bar"
    assert len(hierarchy["siblings"]) >= 2
    assert len(hierarchy["children"]) >= 1
    
    # Verify relationships
    assert all(isinstance(sibling, str) for sibling in hierarchy["siblings"])
    assert all(isinstance(child, str) for child in hierarchy["children"])

@pytest.mark.asyncio
async def test_enhanced_failure_analysis(enhanced_trace_file):
    """Test enhanced failure analysis with DOM mutations and network state."""
    analyzer = EnhancedTraceAnalyzer(enhanced_trace_file)
    failure = await analyzer.analyze_failures()
    
    # Verify DOM mutations
    mutations = failure["dom_mutations"]
    assert len(mutations) > 0
    mutation = mutations[0]
    assert "timestamp" in mutation
    assert "type" in mutation
    assert "element" in mutation
    assert "old_value" in mutation
    assert "new_value" in mutation
    
    # Verify network state
    network = failure["network_state"]
    assert "requests_in_flight" in network
    assert "last_completed_request" in network
    assert len(network["pending_requests"]) > 0
    
    # Verify request details
    pending = network["pending_requests"][0]
    assert "url" in pending
    assert "method" in pending
    assert "duration_so_far" in pending

@pytest.mark.asyncio
async def test_comprehensive_analysis_with_enhanced_identification(enhanced_trace_file):
    """Test comprehensive analysis including enhanced identification features."""
    analyzer = EnhancedTraceAnalyzer(enhanced_trace_file)
    result = await analyzer.analyze_all()
    
    # Verify enhanced element identification
    identification = result["element_identification"]
    assert "relative_position" in identification
    assert "hierarchy" in identification
    assert identification["hierarchy"]["parent"] == "nav.top-bar"
    
    # Verify enhanced failure analysis
    failure = result["failure_analysis"]
    assert "dom_mutations" in failure
    assert "network_state" in failure
    assert failure["network_state"]["requests_in_flight"] > 0 

@pytest.mark.asyncio
async def test_enhanced_session_context(enhanced_trace_file):
    """Test enhanced session context with viewport and performance metrics."""
    analyzer = EnhancedTraceAnalyzer(enhanced_trace_file)
    session = await analyzer.analyze_session_context()
    
    # Verify viewport information
    viewport = session["viewport"]
    assert viewport["width"] == 1920
    assert viewport["height"] == 1080
    assert viewport["device_pixel_ratio"] == 2
    assert viewport["orientation"] == "landscape"
    
    # Verify performance metrics
    metrics = session["performance_metrics"]
    assert "memory_usage" in metrics
    assert "dom_node_count" in metrics
    assert "frame_rate" in metrics
    assert all(timing in metrics["resource_timing"] for timing in ["dns_lookup", "connection", "ttfb"])
    
    # Verify browser state
    browser = session["browser_state"]
    assert browser["cookies_enabled"] is True
    assert browser["javascript_enabled"] is True
    assert "local_storage_used" in browser
    assert "active_service_workers" in browser

@pytest.mark.asyncio
async def test_enhanced_recovery_info(enhanced_trace_file):
    """Test enhanced recovery information with state restoration and fallback sequences."""
    analyzer = EnhancedTraceAnalyzer(enhanced_trace_file)
    recovery = await analyzer.analyze_recovery_info()
    
    # Verify state restoration
    restoration = recovery["state_restoration"]
    assert len(restoration["checkpoints"]) >= 2
    
    # Verify checkpoint details
    checkpoint = restoration["checkpoints"][0]
    assert "timestamp" in checkpoint
    assert "state" in checkpoint
    assert "restorable" in checkpoint
    assert "snapshot" in checkpoint
    assert all(key in checkpoint["snapshot"] for key in ["url", "scroll_position"])
    
    # Verify fallback sequences
    sequences = recovery["fallback_sequences"]
    assert len(sequences) > 0
    sequence = sequences[0]
    assert "condition" in sequence
    assert len(sequence["actions"]) >= 3
    assert "success_criteria" in sequence
    
    # Verify action details
    action = sequence["actions"][0]
    assert "step" in action
    assert "max_attempts" in action
    assert "delay_between_attempts" in action

@pytest.mark.asyncio
async def test_comprehensive_analysis_with_enriched_context(enhanced_trace_file):
    """Test comprehensive analysis including enriched session context and recovery info."""
    analyzer = EnhancedTraceAnalyzer(enhanced_trace_file)
    result = await analyzer.analyze_all()
    
    # Verify enriched session context
    session = result["session_context"]
    assert "viewport" in session
    assert "performance_metrics" in session
    assert "browser_state" in session
    assert session["viewport"]["width"] == 1920
    
    # Verify enhanced recovery info
    recovery = result["recovery_info"]
    assert "state_restoration" in recovery
    assert "fallback_sequences" in recovery
    assert len(recovery["state_restoration"]["checkpoints"]) >= 2
    assert all("success_criteria" in seq for seq in recovery["fallback_sequences"]) 

@pytest.mark.asyncio
async def test_interaction_timing_analysis(enhanced_trace_file):
    """Test detailed interaction timing analysis."""
    analyzer = EnhancedTraceAnalyzer(enhanced_trace_file)
    timing = await analyzer.analyze_timing()
    
    # Verify action breakdown
    breakdown = timing["action_breakdown"]
    assert "element_search" in breakdown
    assert "interaction_delay" in breakdown
    assert "animation_duration" in breakdown
    assert "network_wait" in breakdown
    
    # Verify cumulative timing
    cumulative = timing["cumulative_timing"]
    assert "total_duration" in cumulative
    assert "user_perceived_latency" in cumulative
    
    # Verify performance markers
    markers = timing["performance_markers"]
    assert all(marker in markers for marker in ["first_paint", "first_contentful_paint", "time_to_interactive"])

@pytest.mark.asyncio
async def test_visual_state_tracking(enhanced_trace_file):
    """Test visual state tracking and analysis."""
    analyzer = EnhancedTraceAnalyzer(enhanced_trace_file)
    visual = await analyzer.analyze_visual_state()
    
    # Verify screenshot diffs
    diffs = visual["screenshot_diffs"]
    assert "before_click" in diffs
    assert "after_click" in diffs
    assert diffs["changes_highlighted"] is True
    
    # Verify element visibility
    visibility = visual["element_visibility"]
    assert "before" in visibility
    assert "after" in visibility
    assert "visible_area_percentage" in visibility["before"]
    assert "viewport_position" in visibility["before"]
    
    # Verify layout shifts
    shifts = visual["layout_shifts"]
    assert len(shifts) > 0
    assert "timestamp" in shifts[0]
    assert "elements_moved" in shifts[0]
    assert "cumulative_layout_shift" in shifts[0]

@pytest.mark.asyncio
async def test_enhanced_error_recovery(enhanced_trace_file):
    """Test enhanced error recovery capabilities."""
    analyzer = EnhancedTraceAnalyzer(enhanced_trace_file)
    recovery = await analyzer.analyze_error_recovery()
    
    # Verify retry strategy
    strategy = recovery["retry_strategy"]
    assert strategy["backoff"] == "exponential"
    assert strategy["max_attempts"] == 3
    assert all(condition in strategy["conditions"] for condition in ["network_stable", "animations_complete"])
    
    # Verify environment factors
    env = recovery["environment_factors"]
    assert "network_conditions" in env
    assert "system_resources" in env
    assert all(metric in env["system_resources"] for metric in ["cpu_utilization", "memory_available"])
    
    # Verify recovery checkpoints
    checkpoints = recovery["recovery_checkpoints"]
    assert len(checkpoints) >= 2
    assert all(key in checkpoints[0] for key in ["timestamp", "state", "snapshot"])
    assert "dom_state" in checkpoints[0]["snapshot"]

@pytest.mark.asyncio
async def test_comprehensive_analysis_with_all_features(enhanced_trace_file):
    """Test comprehensive analysis including all enhanced features."""
    analyzer = EnhancedTraceAnalyzer(enhanced_trace_file)
    result = await analyzer.analyze_all()
    
    # Verify new components are present
    assert "timing_analysis" in result
    assert "visual_state" in result
    assert "error_recovery" in result
    
    # Verify timing analysis
    timing = result["timing_analysis"]
    assert "action_breakdown" in timing
    assert "cumulative_timing" in timing
    
    # Verify visual state
    visual = result["visual_state"]
    assert "screenshot_diffs" in visual
    assert "element_visibility" in visual
    
    # Verify error recovery
    recovery = result["error_recovery"]
    assert "retry_strategy" in recovery
    assert "environment_factors" in recovery
    assert recovery["retry_strategy"]["backoff"] == "exponential" 