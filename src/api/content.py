# src/api/content.py
"""
Content personalization and translation API endpoints.
Uses OpenAI's GPT-4o-mini model.
"""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from openai import OpenAI
from src.api.security import get_api_key
from src.core.config import settings

router = APIRouter()

# --- FIX: Switch to Standard OpenAI Client ---
client = OpenAI(
    api_key=settings.OPENAI_API_KEY
    # base_url ki ab zaroorat nahi, ye original OpenAI par jayega
)


class UserBackground(BaseModel):
    """User's software and hardware background for personalization."""
    programming_experience: str = Field(
        ..., 
        description="Level: beginner, intermediate, or advanced"
    )
    robotics_experience: str = Field(
        ..., 
        description="Level: none, hobbyist, or professional"
    )
    preferred_languages: list[str] = Field(
        default=[], 
        description="Programming languages the user knows"
    )
    hardware_access: list[str] = Field(
        default=[], 
        description="Hardware the user has access to"
    )


class PersonalizeRequest(BaseModel):
    """Request to personalize content."""
    content: str = Field(..., max_length=50000, description="The chapter content to personalize")
    user_background: UserBackground = Field(..., description="User's background information")


class PersonalizeResponse(BaseModel):
    """Response with personalized content."""
    personalized_content: str
    original_length: int
    personalized_length: int


class TranslateRequest(BaseModel):
    """Request to translate content."""
    content: str = Field(..., max_length=50000, description="The content to translate")
    target_language: str = Field(default="urdu", description="Target language for translation")


class TranslateResponse(BaseModel):
    """Response with translated content."""
    translated_content: str
    source_language: str
    target_language: str


@router.post("/personalize", response_model=PersonalizeResponse, dependencies=[Depends(get_api_key)])
async def personalize_content(request: PersonalizeRequest):
    """
    Personalize chapter content based on user's background.
    """
    try:
        # Build personalization prompt
        background_summary = f"""
User Background:
- Programming Experience: {request.user_background.programming_experience}
- Robotics Experience: {request.user_background.robotics_experience}
- Known Languages: {', '.join(request.user_background.preferred_languages) or 'Not specified'}
- Hardware Access: {', '.join(request.user_background.hardware_access) or 'Not specified'}
"""
        
        system_prompt = """You are an expert educational content adapter for a Physical AI & Humanoid Robotics textbook.
Your task is to personalize the given content based on the user's background.

Guidelines:
- For beginners: Add more explanations, analogies, and step-by-step breakdowns
- For intermediate: Keep technical depth but add practical tips
- For advanced: Focus on nuances, edge cases, and advanced techniques
- Reference the user's known programming languages when giving code examples
- Mention relevant hardware the user has access to when discussing practical applications
- Maintain the original structure (headings, code blocks, etc.)
- Keep all technical accuracy intact
- Preserve markdown formatting"""

        response = client.chat.completions.create(
            model="gpt-4o-mini",  # FIX: Switched to OpenAI model
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"{background_summary}\n\nContent to personalize:\n\n{request.content}"}
            ],
            temperature=0.7,
            max_tokens=8000
        )
        
        personalized = response.choices[0].message.content
        
        return PersonalizeResponse(
            personalized_content=personalized,
            original_length=len(request.content),
            personalized_length=len(personalized)
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Personalization failed: {str(e)}")


@router.post("/translate", response_model=TranslateResponse, dependencies=[Depends(get_api_key)])
async def translate_content(request: TranslateRequest):
    """
    Translate chapter content to the target language (default: Urdu).
    """
    try:
        system_prompt = f"""You are an expert translator specializing in technical and educational content.
Translate the following content to {request.target_language}.

CRITICAL GUIDELINES:
- Translate ONLY the text content, NOT the markdown formatting
- DO NOT include any markdown syntax in your translation (no #, **, `, etc.)
- Programming code should remain in English
- Translate comments in code blocks if helpful
- Keep proper nouns and brand names (ROS 2, NVIDIA Isaac, etc.) in English
- Ensure the translation reads naturally in {request.target_language}
- For Urdu: Use proper Urdu script and right-to-left text flow"""

        response = client.chat.completions.create(
            model="gpt-4o-mini",  # FIX: Switched to OpenAI model
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Translate to {request.target_language}:\n\n{request.content}"}
            ],
            temperature=0.3,
            max_tokens=8000
        )
        
        translated = response.choices[0].message.content
        
        return TranslateResponse(
            translated_content=translated,
            source_language="english",
            target_language=request.target_language
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Translation failed: {str(e)}")