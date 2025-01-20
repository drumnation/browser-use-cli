import asyncio
from src.utils.task_logging import (
    TaskLogger, TaskStatus, ActionType, RetryConfig,
    ColorScheme, SeparatorStyle
)

async def demo_logging():
    # Initialize logger with custom styles
    logger = TaskLogger(
        "demo_task",
        "Demonstrate all logging features",
        color_scheme=ColorScheme(),
        separator_style=SeparatorStyle(
            task="★" * 40,
            phase="•" * 30,
            error="!" * 35
        )
    )
    
    # Start navigation phase
    logger.start_phase("Navigation Phase")
    logger.update_step(
        "Navigate to example.com",
        TaskStatus.RUNNING,
        action_type=ActionType.NAVIGATION,
        context={"url": "https://example.com"}
    )
    
    # Update browser state
    logger.update_browser_state(
        url="https://example.com",
        page_ready=True,
        dynamic_content_loaded=True,
        visible_elements=15,
        page_title="Example Domain"
    )
    
    # Complete navigation
    logger.update_step(
        "Page loaded successfully",
        TaskStatus.COMPLETE,
        action_type=ActionType.NAVIGATION,
        progress=0.25,
        results={"status": 200, "load_time": 0.5}
    )
    
    # Start interaction phase
    logger.start_phase("Interaction Phase")
    logger.update_step(
        "Click search button",
        TaskStatus.RUNNING,
        action_type=ActionType.INTERACTION,
        context={"element": "search_button"}
    )
    
    # Simulate error and retry
    async def failing_operation():
        raise ValueError("Search button not found")
    
    try:
        await logger.execute_with_retry(
            failing_operation,
            "click_search",
            RetryConfig(max_retries=2, base_delay=0.1)
        )
    except ValueError:
        pass
    
    # Start extraction phase
    logger.start_phase("Data Extraction Phase")
    logger.update_step(
        "Extract search results",
        TaskStatus.RUNNING,
        action_type=ActionType.EXTRACTION,
        progress=0.75
    )
    
    # Complete extraction
    logger.update_step(
        "Data extracted successfully",
        TaskStatus.COMPLETE,
        action_type=ActionType.EXTRACTION,
        progress=1.0,
        results={"items_found": 10}
    )
    
    # Display log history
    print("\nLog History:")
    print("=" * 80)
    for entry in logger.get_log_history():
        print(entry)
    print("=" * 80)
    
    # Log final state
    print("\nFinal State:")
    logger.log_state()

if __name__ == "__main__":
    asyncio.run(demo_logging()) 