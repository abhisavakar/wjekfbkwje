#!/usr/bin/env python3
"""
Run script for the AI Tutoring Agent
Usage: python run.py [--sessions N] [--topic TOPIC]
"""

import argparse
import os
import sys

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from agent import TutoringAgent, run_multiple_sessions


def main():
    parser = argparse.ArgumentParser(description='AI Tutoring Agent for Knowunity Challenge')
    parser.add_argument('--sessions', type=int, default=1, help='Number of sessions to run')
    parser.add_argument('--topic', type=str, default=None, help='Topic for the session')
    parser.add_argument('--api-key', type=str, 
                       default=os.getenv("KNOWUNITY_API_KEY", "sk_team_Ba30FbMKkpg7Ups5lyjkZiNfxFIA0CVD"),
                       help='API key')
    parser.add_argument('--quiet', action='store_true', help='Reduce output verbosity')
    parser.add_argument('--test-api', action='store_true', help='Test API connection only')
    
    args = parser.parse_args()
    
    print("=" * 60)
    print("🎓 Knowunity AI Tutoring Agent")
    print("=" * 60)
    print()
    
    if args.test_api:
        # Test API connection
        from api_client import test_api_connection
        test_api_connection(args.api_key)
        return
    
    if args.sessions == 1:
        # Run single session
        print(f"Starting session... (Topic: {args.topic or 'random'})")
        print()
        
        agent = TutoringAgent(args.api_key)
        result = agent.run_session(topic=args.topic, verbose=not args.quiet)
        
        if not args.quiet:
            print("\n📊 Assessment Summary:")
            import json
            print(json.dumps(agent.get_assessment_summary(), indent=2))
    else:
        # Run multiple sessions
        topics = [args.topic] if args.topic else None
        results = run_multiple_sessions(
            api_key=args.api_key,
            num_sessions=args.sessions,
            topics=topics
        )
    
    print("\n✅ Done!")


if __name__ == "__main__":
    main()
