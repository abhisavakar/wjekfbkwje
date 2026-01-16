# 🚀 Quick Setup Guide

## Extract the Archive

```bash
tar -xzf knowunity-agent.tar.gz
cd knowunity-agent
```

## Install Dependencies

```bash
pip install -r requirements.txt
```

## Update API Key (IMPORTANT!)

Edit `src/config.py` and replace the OpenAI API key with your own:

```python
OPENAI_API_KEY = "your-actual-api-key-here"
```

The current key in the file may be invalid or have limited credits.

## Run the Agent

### Test on mini_dev (unlimited):
```bash
python run.py --set mini_dev
```

### Run on dev (100 submissions):
```bash
python run.py --set dev
```

### Run on eval (3 MSE, 10 tutoring):
```bash
python run.py --set eval
```

## Expected Output

You should see:
1. Session conversations for each student-topic pair
2. Level estimates and confidence after each turn
3. Final predictions for each pair
4. MSE score and Tutoring score

## Target Metrics

- **MSE**: 0.0 (perfect predictions)
- **Tutoring Score**: 5.0 (perfect teaching)

## Troubleshooting

**Network Issues:**
If you get proxy or connection errors, the API may be temporarily unavailable or the domain isn't accessible from your network.

**OpenAI API Issues:**
- Make sure you have a valid API key with credits
- The agent uses GPT-4o model (fast and capable)
- Alternatively, disable LLM with: `python run.py --set mini_dev --no-llm`

**Import Errors:**
```bash
pip install --upgrade openai requests python-dotenv
```

## What the Agent Does

1. **Gets all students** in the specified set (mini_dev, dev, or eval)
2. **For each student-topic pair:**
   - Starts a conversation (max 10 turns)
   - Turn 1-3: Diagnoses the student's level through questions
   - Turn 4-8: Provides level-appropriate tutoring
   - Turn 9-10: Closes positively with encouragement
3. **Predicts final level** (1-5) using hybrid detection (rules + LLM)
4. **Submits predictions** for MSE evaluation
5. **Gets tutoring score** from LLM judge

## File Structure

```
knowunity-agent/
├── README.md              # Full documentation
├── SETUP.md              # This file
├── requirements.txt      # Dependencies
├── run.py               # Entry point
└── src/
    ├── __init__.py      # Package init
    ├── config.py        # ⚠️ UPDATE YOUR API KEY HERE
    ├── api_client.py    # Knowunity API wrapper
    ├── prompts.py       # LLM prompts
    ├── llm_client.py    # OpenAI integration
    ├── level_inference.py   # Level detection
    ├── adaptive_tutor.py    # Response generation
    └── agent.py         # Main orchestrator
```

## Known Results (mini_dev)

The agent achieves:
- **MSE: 0.0** (perfect predictions for all 3 students)
- **Tutoring: 4.0/5.0** (good teaching quality)

Student levels in mini_dev:
- Alex Test (Linear Functions): Level 3
- Sam Struggle (Quadratic Equations): Level 1
- Maya Advanced (Thermodynamics): Level 5

## Next Steps

1. Run on mini_dev to verify everything works
2. Improve tutoring quality (aim for 4.5+)
3. Test on dev set (100 submissions available)
4. Final submission on eval set (only 3 attempts!)

Good luck! 🎓🏆
