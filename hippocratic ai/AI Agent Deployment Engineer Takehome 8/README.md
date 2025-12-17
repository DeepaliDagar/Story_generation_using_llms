# Hippocratic AI Coding Assignment
Welcome to the [Hippocratic AI](https://www.hippocraticai.com) coding assignment

## Setup & Usage

### Prerequisites
- OpenAI API key

### Installation
1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Create a `.env` file in the project root:
   ```
   OPENAI_API_KEY=your_api_key_here
   ```

### Running the Application
```bash
python main.py
```

### How It Works
1. Enter your story request (e.g., "a story about a brave knight")
2. The system categorizes your request (adventure, fantasy, friendship, etc.)
3. A story is generated and evaluated by an AI judge
4. Review the story and judge feedback
5. Provide feedback (optional) or press Enter to finalize
6. The system revises based on feedback (up to 3 rounds)

### Configuration
- `max_rounds`: Maximum revision rounds (default: 3)
- `target_score`: Target quality score to stop revisions (default: 8.5)
- Adjust these in `main.py` if needed

### Story Categories
The system automatically categorizes requests into:
- **adventure**: Exciting journeys and brave characters
- **fantasy**: Magic, fairies, and enchanted worlds
- **friendship**: Helping others and working together
- **animals**: Talking animals and nature
- **bedtime**: Calming and peaceful
- **educational**: Learning and discovery
- **general**: Warm and positive

---

## Block Diagram (storyteller + judge)

```
User request
    |
    v
Categorize request (detect story category)
    |
    v
Storyteller.generate_story (category-specific storytelling prompt, gpt-3.5-turbo)
    |
    v
Judge.evaluate_story (rubric scoring, JSON feedback, gpt-3.5-turbo)
    |
    v
Show category & story + judge feedback to user
    |
    |-- Does story meet target score OR no improvement suggestions?
    |         | 
    |         -- Yes --> Final Story (with evaluations)
    |
    |         -- No  --> User provides feedback (optional)
    |                      |
    |                      v
    |         Storyteller.revise_story (uses all feedback & judge suggestions)
    |                      |
    |                      v
    |         Judge.evaluate_story (re-score)
    |______________________|
    |
    |-- Loop up to max_rounds (3) or until target_score met
    |
    v
Final Story (+ all judge evaluations & best version)

Key prompts:
- Storyteller prompt: warm, safe, age 5–10, clear beginning/middle/end, gentle lesson.
- Judge prompt: scores (overall, age_appropriateness, clarity, engagement, structure) and returns `improvement_instructions` as strict JSON.

---

## Safety Guardrails

This system places the highest priority on age appropriateness and content safety:

### Age Appropriateness (Highest Priority)
- Stories are required to be suitable for children ages 5–10.
- Judge scoring is strict: age_appropriateness receives a score of 0–4 if there are any safety concerns, and 8–10 only if the story is perfectly appropriate.
- If `age_appropriateness` is below 7, then `overall_score` is automatically capped at (age_score + 1.0). If it is between 7 and 8, the cap is (age_score + 1.5).
- Stories with low age_appropriateness scores are revised automatically, up to a maximum number of rounds.

### Content Safety
- Stories must not feature violence, scary content, or inappropriate themes.
- Only positive messages and safe activities are allowed.
- Language and concepts must be age-appropriate.

### Automatic Revision
- If age_appropriateness < 7, the system automatically proceeds to revise the story (up to max_rounds).
- The system will not end with a final story unless a sufficiently high age appropriateness score is achieved or the maximum number of rounds is reached. This ensures safety standards for all output stories.

---
