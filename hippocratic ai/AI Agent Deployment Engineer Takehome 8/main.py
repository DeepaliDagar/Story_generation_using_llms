"""
Story generation using LangGraph with user feedback support.

Before submitting the assignment, describe here in a few sentences what you would
have built next if you spent 2 more hours on this project:
Answer: If I had two more hours to work on this project, I'd add a text to audio generation 
using bark library, I'd also introduce the option for generating 
shorter stories tailored for very young listeners as well as longer, more detailed stories for older 
children, allowing users to specify a desired story length. Enhancements would include more 
personalization by allowing references to specific characters, places, or events that users care about.
"""
from graph import app


def collect_user_feedback(story: str, round_num: int, evaluation: dict) -> str:
    """Collect feedback from user interactively."""
    print("\n" + "="*60)
    print(f"ROUND {round_num} : Story Preview")
    print("="*60)
    print(story[:500] + "..." if len(story) > 500 else story)
    print("\n" + "="*60)
    
    if evaluation:
        score = evaluation.get("overall_score", "n/a")
        age_score = evaluation.get("age_appropriateness", "n/a")
        summary = evaluation.get("summary", "").strip()
        
        print(f"\nJudge Scores:")
        print(f"  Overall: {score}/10")
        print(f"  Age Appropriateness: {age_score}/10 (highest priority)")
        if age_score and float(age_score) < 7:
            print(f"  Note: Age appropriateness is below threshold - story will be revised")
        
        if summary:
            print(f"\nJudge Summary: {summary}")
    
    print("\nWould you like to provide feedback or request changes?")
    print("(Press Enter to finish, or type your feedback and press Enter)")
    feedback = input("Your feedback: ").strip()
    
    return feedback


def should_continue(state: dict) -> bool:
    """Check if workflow should continue."""
    ev = state.get("evaluation", {})
    score = float(ev.get("overall_score", 0) or 0)
    age_score = float(ev.get("age_appropriateness", 0) or 0)
    round_num = state.get("round", 0)
    
    # If age_appropriateness is low, continue revising
    if age_score < 7 and round_num < state.get("max_rounds", 3):
        return True
    
    if score >= state.get("target_score", 8.5) or round_num >= state.get("max_rounds", 3):
        return False
    
    return bool(ev.get("improvement_instructions"))


def main():
    """Main entry point for story generation with interactive feedback."""
    user_input = input("What kind of story do you want to hear? ")
    
    # Initialize state
    state = {
        "user_request": user_input,
        "category": "",
        "story": "",
        "evaluation": {},
        "user_feedback": "",
        "round": 0,
        "max_rounds": 3,
        "target_score": 8.5,
        "evaluations": [],
    }
    
    config = {"recursion_limit": 10}
    
    # Main loop
    while True:
        state = app.invoke(state, config)
        
        # Showing the category on the first round
        if state.get("round", 0) == 1:
            category = state.get("category", "general")
            print(f"\n Detected story category: {category.title()}\n")
        
        if not should_continue(state):
            break
        
        evaluation = state.get("evaluation", {})
        user_feedback = collect_user_feedback(state["story"], state.get("round", 0), evaluation)
        
        if not user_feedback or user_feedback.lower() in ['done', 'stop', 'finish', 'end']:
            break
        
        state["user_feedback"] = user_feedback
        print(f"\n→ Continuing to round {state.get('round', 0) + 1}...\n")
    
    # final story
    print("\n" + "="*60)
    print("--- Your Final Story ---")
    print("="*60)
    rounds = len(state["evaluations"])
    best = max((e.get("overall_score", 0) or 0) for e in state["evaluations"]) if state["evaluations"] else "n/a"
    print(f"(After {rounds} round(s), best score: {best})\n")
    print(state["story"])
    
    # judge feedback
    print("\n" + "="*60)
    print("--- Judge Feedback ---")
    print("="*60)
    for idx, ev in enumerate(state["evaluations"], 1):
        print(f"\nRound {idx} | Overall Score: {ev.get('overall_score', 'n/a')}/10")
        print(f"  Age Appropriateness: {ev.get('age_appropriateness', 'n/a')}/10")
        if ev.get("summary"):
            print(f"  Summary: {ev.get('summary')}")


if __name__ == "__main__":
    main()
