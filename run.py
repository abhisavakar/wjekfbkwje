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

from agent import TutoringAgent


def main():
    parser = argparse.ArgumentParser(description='AI Tutoring Agent for Knowunity Challenge')
    parser.add_argument('--set', type=str, choices=['mini_dev', 'dev', 'eval'], 
                       help='Run on a specific evaluation set')
    parser.add_argument('--no-llm', action='store_true', help='Disable LLM (use templates)')
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
    
    # If --set is provided, use the agent.py workflow
    if args.set:
        agent = TutoringAgent(use_llm=not args.no_llm)
        
        # Run all sessions
        print(f"🚀 Running sessions for {args.set} set...")
        predictions = agent.run_all_sessions(args.set, verbose=not args.quiet)
        
        # Submit and evaluate
        print(f"\n📤 Submitting {len(predictions)} predictions...")
        results = agent.submit_and_evaluate(predictions, args.set)
        
        print(f"\n{'='*60}")
        print("FINAL RESULTS")
        print(f"{'='*60}")
        print(f"MSE Score: {results['mse']['mse_score']}")
        print(f"Tutoring Score: {results['tutoring']['score']}")
        print(f"{'='*60}")
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
        print("⚠️  Multiple sessions mode not yet implemented. Use --set instead.")
    
    print("\n✅ Done!")


if __name__ == "__main__":
    main()