import json
from fastapi import FastAPI
from pydantic import BaseModel
from typing import List
from fastapi.responses import HTMLResponse

app = FastAPI()

# ----------- Load Data -----------

with open("data.json", "r") as f:
    catalog = json.load(f)

# ----------- Models -----------

class Message(BaseModel):
    role: str
    content: str

class ChatRequest(BaseModel):
    messages: List[Message]

# ----------- Routes -----------

@app.get("/health")
def health():
    return {"status": "ok"}


# ----------- UI ROUTE -----------

@app.get("/", response_class=HTMLResponse)
def home():
    with open("index.html", "r") as f:
        return f.read()


# ----------- CHATBOT -----------

@app.post("/chat")
def chat(request: ChatRequest):

    # ✅ USE ONLY LATEST USER MESSAGE (FIXED)
    user_messages = [m.content.lower() for m in request.messages if m.role == "user"]
    full_text = user_messages[-1] if user_messages else ""

    # ----------- OUT OF SCOPE (FIXED) -----------

    out_of_scope_keywords = [
        "diet", "workout", "recipe", "movie", "weather",
        "relationship", "politics"
    ]

    is_out_of_scope = any(word in full_text for word in out_of_scope_keywords)

    is_hiring_context = any(word in full_text for word in [
        "developer", "engineer", "analyst", "java", "python", "sql"
    ])

    if is_out_of_scope and not is_hiring_context:
        return {
            "reply": "I can only help with SHL assessments. Please ask about hiring assessments.",
            "recommendations": [],
            "end_of_conversation": False
        }

    # ----------- COMPARISON -----------

    if "difference" in full_text or "compare" in full_text:
        found = []

        for item in catalog:
            if item["name"].lower().split()[0] in full_text:
                found.append(item)

        if len(found) >= 2:
            item1, item2 = found[0], found[1]

            return {
                "reply": f"{item1['name']} focuses on {item1['description']}. "
                         f"Whereas {item2['name']} focuses on {item2['description']}.",
                "recommendations": [],
                "end_of_conversation": False
            }
        else:
            return {
                "reply": "Please specify two assessments you want to compare.",
                "recommendations": [],
                "end_of_conversation": False
            }

    # ----------- DETECT INFO -----------

    has_skill = any(word in full_text for word in ["java", "python", "sql"])
    has_role = any(word in full_text for word in ["developer", "engineer", "analyst"])
    has_level = any(word in full_text for word in ["junior", "mid", "senior"])

    wants_personality = "personality" in full_text
    wants_aptitude = any(word in full_text for word in ["aptitude", "reasoning"])

    info_count = sum([has_skill, has_role, has_level])

    # ----------- ASK CLARIFICATION -----------

    if info_count < 2:
        return {
            "reply": "Can you specify the role, required skills, and experience level?",
            "recommendations": [],
            "end_of_conversation": False
        }

    # ----------- RECOMMEND -----------

    matched = []

    for item in catalog:

        skill_match = any(skill in full_text for skill in item["skills"])

        if wants_personality and item["test_type"] != "P":
            continue

        if wants_aptitude and item["test_type"] != "A":
            continue

        if skill_match:
            matched.append(item)

    # fallback
    if not matched:
        for item in catalog:
            if wants_personality and item["test_type"] == "P":
                matched.append(item)
            elif wants_aptitude and item["test_type"] == "A":
                matched.append(item)

    return {
        "reply": "Here are the final recommended assessments based on your requirements.",
        "recommendations": matched[:5],
        "end_of_conversation": True
    }