import requests
import streamlit as st

BASE_URL="http://localhost:8000/api/v1"

def _headers(token: str | None = None):
    headers = {}

    if token:
        headers["Authorization"] = f"Bearer {token}"

    return headers

def _handle_response(response):
    if response.status_code >= 400:
        # Try JSON first, fall back to raw text
        try:
            detail = response.json().get("detail", "API Error")
        except ValueError:
            detail = response.text or f"HTTP {response.status_code} (no body)"
        raise Exception(f"[{response.status_code}] {detail}")
    
    try:
        return response.json()
    except ValueError:
        raise Exception(f"Backend returned non-JSON: {response.text[:500]}")

#auth

def register(email:str,password:str,display_name:str)->dict:
    response=requests.post(
        f"{BASE_URL}/auth/register",
        json={
            "email":email,
            "password":password,
            "display_name":display_name
        },
        headers=_headers()
    )

    if response.status_code!=200:
        raise Exception(response.json().get("detail","Registration failed"))

    return response.json()

def login(email:str,password:str)->dict:
    response=requests.post(
        f"{BASE_URL}/auth/login",
        json={
            "email":email,
            "password":password
        },
        headers=_headers()
    )

    if response.status_code!=200:
        raise Exception(response.json().get("detail","Login failed"))
    
    return response.json()

def get_me(token:str)->dict:
    response=requests.get(
        f"{BASE_URL}/auth/me",
        headers=_headers(token)
    )

    if response.status_code!=200:
        raise Exception("failed to fetch user")
    
    return response.json()

#documents

def upload_document(file, filename:str,token:str)->dict:
    files={
        "file":(filename,file)
    }

    response=requests.post(
        f"{BASE_URL}/documents/upload",
        files=files,
        headers=_headers(token)
    )

    if response.status_code !=200:
        raise Exception(response.json().get("detail", "upload failed"))
    
    return response.json()

def get_documents(token: str) -> list:
    response = requests.get(
        f"{BASE_URL}/documents/",
        headers=_headers(token)
    )
    return _handle_response(response)

def get_document_topics(doc_id:str, token:str)->list:
    response=requests.get(
        f"{BASE_URL}/documents/{doc_id}/topics",
        headers=_headers(token)
    )

    if response.status_code!=200:
        raise Exception("Failed to fetch topics")
    return response.json()

def delete_document(document_id: str, token: str):
    response = requests.delete(
        f"{BASE_URL}/documents/{document_id}",
        headers=_headers(token)
    )

    if response.status_code != 200:
        raise Exception("Failed to delete document")

    return response.json()

def generate_quiz(topic_id, quiz_type, difficulty, num_questions, token):
    res=requests.post(
        f"{BASE_URL}/quizzes/generate",
        headers=_headers(token),
        json={
            "topic_id": topic_id,
            "quiz_type": quiz_type,
            "difficulty":difficulty,
            "num_questions":num_questions
        }
    )
    return _handle_response(res)

def get_quiz(quiz_id, token):
    res=requests.get(
        f"{BASE_URL}/quizzes/{quiz_id}",
        headers=_headers(token)
    )
    return _handle_response(res)

def get_quiz_results(quiz_id, token):
    res=requests.get(
        f"{BASE_URL}/quizzes/{quiz_id}/results",
        headers=_headers(token)
    )
    return _handle_response(res)

def submit_quiz(quiz_id, answers, token):
    res = requests.post(
        f"{BASE_URL}/quizzes/{quiz_id}/submit",
        headers=_headers(token),
        json={"answers": answers}
    )
    return _handle_response(res)

def create_chat_session(document_id, token):
    res=requests.post(
        f"{BASE_URL}/chat/sessions",
        headers=_headers(token),
        json={"document_id": document_id}
    )
    return _handle_response(res)

def ask_question(session_id, question,token):
    res=requests.post(
        f"{BASE_URL}/chat/sessions/{session_id}/ask",
        headers=_headers(token),
        json={"question":question}
    )
    return _handle_response(res)

def get_chat_history(session_id, token):
    res = requests.get(
        f"{BASE_URL}/chat/sessions/{session_id}/history",
        headers=_headers(token)
    )
    return _handle_response(res)

def create_group(name, token):
    res = requests.post(
        f"{BASE_URL}/groups/",
        headers=_headers(token),
        json={"name": name},
    )
    return _handle_response(res)


def join_group(invite_code, token):
    res = requests.post(
        f"{BASE_URL}/groups/join",
        headers=_headers(token),
        json={"invite_code": invite_code},
    )
    return _handle_response(res)


def get_groups(token):
    res = requests.get(
        f"{BASE_URL}/groups/",
        headers=_headers(token),
    )
    return _handle_response(res)


def share_document(group_id, document_id, token):
    res = requests.post(
        f"{BASE_URL}/groups/{group_id}/share",
        headers=_headers(token),
        json={"document_id": document_id},
    )
    return _handle_response(res)


def get_group_documents(group_id, token):
    res = requests.get(
        f"{BASE_URL}/groups/{group_id}/documents",
        headers=_headers(token),
    )
    return _handle_response(res)

def get_dashboard(token):
    res = requests.get(
        f"{BASE_URL}/progress/dashboard",
        headers=_headers(token),
    )
    return _handle_response(res)


def get_topic_mastery(token):
    res = requests.get(
        f"{BASE_URL}/progress/topics",
        headers=_headers(token),
    )
    return _handle_response(res)


def get_recommendations(token):
    res = requests.get(
        f"{BASE_URL}/progress/recommendations",
        headers=_headers(token),
    )
    return _handle_response(res)