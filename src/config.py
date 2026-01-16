"""Configuration for the AI Tutoring Agent"""

# Knowunity API
KNOWUNITY_API_KEY = "sk_team_Ba30FbMKkpg7Ups5lyjkZiNfxFIA0CVD"
KNOWUNITY_BASE_URL = "https://knowunity-agent-olympics-2026-api.vercel.app"

# OpenAI API (for intelligent responses)
OPENAI_API_KEY = "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"

# Agent Settings
MAX_TURNS = 10
ASSESSMENT_TURNS = 3      # Turns 1-3 for assessment
TUTORING_TURNS = 5        # Turns 4-8 for tutoring  
CLOSING_TURNS = 2         # Turns 9-10 for closing

# Set to use
DEFAULT_SET = "mini_dev"  # Change to "dev" or "eval" when ready
