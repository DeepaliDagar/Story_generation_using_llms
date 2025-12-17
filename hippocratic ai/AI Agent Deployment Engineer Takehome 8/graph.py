"""
LangGraph workflow for story generation with judge evaluation.
"""
import json
import os
from typing import Literal, TypedDict

from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, END

load_dotenv()

class StoryState(TypedDict):
    """State for the story generation workflow."""
    user_request: str
    category: str
    story: str
    evaluation: dict
    user_feedback: str
    short_story: bool
    round: int
    max_rounds: int
    target_score: float
    evaluations: list


llm = ChatOpenAI(model="gpt-3.5-turbo", temperature=0.7, api_key=os.getenv("OPENAI_API_KEY"))
judge_llm = ChatOpenAI(model="gpt-3.5-turbo", temperature=0.1, api_key=os.getenv("OPENAI_API_KEY"))

# Defining the categories
CATEGORIES = {
    "adventure": "exciting journeys and brave characters",
    "fantasy": "magic, fairies, and enchanted worlds",
    "friendship": "helping others and working together",
    "animals": "talking animals and nature",
    "bedtime": "calming and peaceful",
    "educational": "learning and discovery",
    "general": "warm and positive",
}

# llm to categorize the request
def categorize_request(state: StoryState) -> StoryState:
    """Categorize the user request."""
    if state.get("category"):
        return {}
    
    prompt = f"""Categorize this story request into one word: adventure, fantasy, friendship, animals, bedtime, educational, or general.

Request: {state["user_request"]}
Category:"""
    
    response = llm.invoke(prompt)
    category = response.content.strip().lower().split()[0]
    return {"category": category if category in CATEGORIES else "general"}

# llm to generate the story
def generate_story(state: StoryState) -> StoryState:
    """Generate or revise story."""
    category = state.get("category", "general")
    
    if not state.get("story"):
        prompt = f"""Write a {category} bedtime story for children about: {state["user_request"]}

Requirements:
- Safe, positive, and age-appropriate for children age 5 to 10
- Clear beginning, middle, and end
- incorporate story arc and characters
- Length: 500-800 words

Write the story with a title on the first line."""
    else:
        # Revision of the story
        feedback = state.get("evaluation", {}).get("improvement_instructions", "") or state.get("user_feedback", "")
        prompt = f"""Revise this {category} story for children age 5 to 10 based on the feedback:

Original story:
{state["story"]}

Feedback: {feedback}

Make meaningful improvements while keeping it appropriate for children age 5 to 10.
Write the revised story with a title."""
    
    response = llm.invoke(prompt)
    return {"story": response.content, "user_feedback": ""}

# llm to evaluate the story
def evaluate_story(state: StoryState) -> StoryState:
    """Evaluate story with age-appropriateness as priority."""
    
    prompt = f"""Evaluate this bedtime story for children age 5 to 10. Be STRICT in your scoring:

Request: {state["user_request"]}
Story: {state["story"]}

SCORING GUIDELINES (be conservative):
- age_appropriateness: Score 8-10 ONLY if perfectly safe, appropriate, and suitable. Score 5-7 for good but needs minor improvements. Score 0-4 for any concerns.
- overall_score: Should be conservative. Score 7-8 for good stories, 9-10 only for exceptional quality. First drafts typically score 6-7.
- Be critical: Look for areas to improve (language complexity, story structure, engagement, clarity)

Respond in JSON with: overall_score (0-10), age_appropriateness (0-10), clarity (0-10), 
engagement (0-10), structure (0-10), summary (2-4 sentences), improvement_instructions (list of improvements)."""
    
    response = judge_llm.invoke(prompt)
    
    try:
        evaluation = json.loads(response.content)
        
        # Guardrail: If age_appropriateness is low, cap overall_score
        age_score = float(evaluation.get("age_appropriateness", 0) or 0)
        overall = float(evaluation.get("overall_score", 0) or 0)
        
        # Stricter guardrail: Cap overall_score based on age_appropriateness
        if age_score < 7:
            evaluation["overall_score"] = min(overall, age_score + 1.0)
        elif age_score < 8:
            # Even if age is good, don't let overall exceed age by more than 1
            evaluation["overall_score"] = min(overall, age_score + 1.5)
        else:
            # If age is 8+, still cap overall at reasonable level for first drafts
            evaluation["overall_score"] = min(overall, 8.5)
        
    except json.JSONDecodeError:
        evaluation = {
            "overall_score": 0.0,
            "age_appropriateness": 0.0,
            "clarity": 0.0,
            "engagement": 0.0,
            "structure": 0.0,
            "summary": "Judge returned non-JSON output.",
            "improvement_instructions": response.content,
        }
    
    # Updating the evaluations list and round counter
    evaluations = state.get("evaluations", [])
    evaluations.append(evaluation)
    round_num = state.get("round", 0) + 1
    
    return {"evaluation": evaluation, "evaluations": evaluations, "round": round_num}


def should_continue(state: StoryState) -> Literal["revise", "end"]:
    """Decide whether to continue revising or end."""
    return "end"


# Building the graph
workflow = StateGraph(StoryState)

workflow.add_node("categorize", categorize_request)
workflow.add_node("generate", generate_story)
workflow.add_node("evaluate", evaluate_story)

# entry point
workflow.set_entry_point("categorize")

# edges
workflow.add_edge("categorize", "generate")
workflow.add_edge("generate", "evaluate")
workflow.add_conditional_edges(
    "evaluate",
    should_continue,
    {
        "revise": "generate",
        "end": END,
    }
)

app = workflow.compile()

