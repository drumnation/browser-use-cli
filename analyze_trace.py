from src.trace_analyzer import EnhancedTraceAnalyzer
import asyncio
import json

async def main():
    analyzer = EnhancedTraceAnalyzer('traces/enhanced-test.json')
    result = await analyzer.analyze_all()
    print(json.dumps(result, indent=2))

if __name__ == "__main__":
    asyncio.run(main()) 