"""Pydantic request/response schemas (input validation lives here)."""
from __future__ import annotations

import re
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator, model_validator

ALLERGY_OPTIONS = ["Peanut", "Tree nuts", "Milk", "Egg", "Soy", "Wheat", "Fish", "Shellfish", "Sesame", "Mustard"]
INTOLERANCE_OPTIONS = ["Lactose", "Gluten", "Fructose"]
PREFERENCE_OPTIONS = ["Vegetarian", "Vegan", "Jain", "Gluten-free", "Dairy-free", "Low-sodium", "Low-sugar", "High-protein"]
CONDITION_OPTIONS = [{"key": "diabetes", "label": "Diabetes / blood-sugar management"},
                     {"key": "hypertension", "label": "High blood pressure"},
                     {"key": "ckd", "label": "Kidney disease (CKD)"},
                     {"key": "pcos", "label": "PCOS"}]
GOAL_OPTIONS = [{"key": "reduce_sodium", "label": "Reduce sodium"}, {"key": "reduce_sugar", "label": "Reduce sugar"},
                {"key": "increase_fiber", "label": "Increase fiber"}, {"key": "increase_protein", "label": "Increase protein"},
                {"key": "improve_diversity", "label": "Improve food diversity"}]
GOAL_KEYS = {g["key"] for g in GOAL_OPTIONS}
CONDITION_KEYS = {c["key"] for c in CONDITION_OPTIONS}
MealType = Literal["breakfast", "lunch", "snack", "dinner"]
InputMethod = Literal["scan", "search", "manual", "eating_out"]

_TAG = re.compile(r"^[\w\s\-/&().,']{1,40}$", re.UNICODE)


def _clean_list(v: list[str], limit: int = 25) -> list[str]:
    out, seen = [], set()
    for x in v or []:
        x = re.sub(r"\s+", " ", str(x)).strip()
        if not x:
            continue
        if not _TAG.match(x):
            raise ValueError(f"'{x[:20]}' contains characters that aren't allowed.")
        if x.lower() not in seen:
            seen.add(x.lower())
            out.append(x)
    if len(out) > limit:
        raise ValueError("Too many items.")
    return out


# ---------------- auth ----------------
class SignupIn(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    confirm_password: str

    @field_validator("name")
    @classmethod
    def _name(cls, v):
        v = v.strip()
        if not v:
            raise ValueError("Name is required.")
        return v

    @field_validator("password")
    @classmethod
    def _pw(cls, v):
        if not re.search(r"[A-Za-z]", v) or not re.search(r"\d", v):
            raise ValueError("Password must contain at least one letter and one number.")
        return v

    @model_validator(mode="after")
    def _match(self):
        if self.password != self.confirm_password:
            raise ValueError("Passwords don't match.")
        return self


class LoginIn(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1, max_length=128)


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    user_id: int
    name: str
    email: str
    is_demo: bool
    onboarding_complete: bool
    created_at: datetime


class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserOut


# ---------------- profile ----------------
class ProfileIn(BaseModel):
    allergies: list[str] = []
    intolerances: list[str] = []
    dietary_preferences: list[str] = []
    health_conditions: list[str] = []
    goals: list[str] = []
    complete_onboarding: bool = False

    @field_validator("allergies", "intolerances", "dietary_preferences")
    @classmethod
    def _lists(cls, v):
        return _clean_list(v)

    @field_validator("health_conditions")
    @classmethod
    def _conds(cls, v):
        v = [x.lower() for x in _clean_list(v)]
        bad = [x for x in v if x not in CONDITION_KEYS]
        if bad:
            raise ValueError(f"Unknown health consideration: {bad[0]}")
        return v

    @field_validator("goals")
    @classmethod
    def _goals(cls, v):
        v = [x.lower() for x in _clean_list(v)]
        bad = [x for x in v if x not in GOAL_KEYS]
        if bad:
            raise ValueError(f"Unknown goal: {bad[0]}")
        return v


# ---------------- analysis ----------------
class Nutrition(BaseModel):
    calories: float | None = Field(default=None, ge=0, le=10000)
    protein: float | None = Field(default=None, ge=0, le=1000)
    carbohydrates: float | None = Field(default=None, ge=0, le=2000)
    fat: float | None = Field(default=None, ge=0, le=1000)
    sugar: float | None = Field(default=None, ge=0, le=1000)
    fiber: float | None = Field(default=None, ge=0, le=500)
    sodium: float | None = Field(default=None, ge=0, le=50000)
    potassium: float | None = Field(default=None, ge=0, le=50000)
    basis: str | None = Field(default=None, max_length=40)
    serving_size: str | None = Field(default=None, max_length=40)


class AllergenStatements(BaseModel):
    contains: list[str] = []
    may_contain: list[str] = []


class AnalyzeIn(BaseModel):
    input_method: InputMethod
    food_name: str = Field(min_length=1, max_length=200)
    ingredients: list[str] = Field(default_factory=list, max_length=150)
    nutrition: Nutrition = Nutrition()
    allergen_statements: AllergenStatements = AllergenStatements()
    food_id: int | None = None
    dish_name: str | None = Field(default=None, max_length=200)   # eating-out
    meal_type: MealType | None = None
    ocr_scan_token: str | None = Field(default=None, max_length=200)  # links a reviewed OCR extraction
    raw_ocr_text: str | None = Field(default=None, max_length=20000)
    ocr_confidence: float | None = Field(default=None, ge=0, le=1)

    @field_validator("ingredients")
    @classmethod
    def _ings(cls, v):
        out = []
        for x in v:
            x = re.sub(r"\s+", " ", str(x)).strip()
            if x:
                if len(x) > 200:
                    raise ValueError("An ingredient entry is too long.")
                out.append(x)
        return out

    @field_validator("food_name")
    @classmethod
    def _fn(cls, v):
        v = re.sub(r"\s+", " ", v).strip()
        if not v:
            raise ValueError("Food name is required.")
        return v


# ---------------- logs ----------------
class LogIn(BaseModel):
    scan_id: int
    meal_type: MealType
    quantity: float = Field(default=1.0, gt=0, le=10)
    consumed_at: datetime | None = None


class LogUpdate(BaseModel):
    meal_type: MealType | None = None
    quantity: float | None = Field(default=None, gt=0, le=10)
    consumed_at: datetime | None = None


class SymptomIn(BaseModel):
    food_log_id: int
    severity: Literal["none", "mild", "moderate", "severe"]
    symptom: str = Field(default="", max_length=200)
    notes: str = Field(default="", max_length=1000)


class GoalIn(BaseModel):
    goal_type: str
    target: float | None = Field(default=None, ge=0)
    active: bool = True

    @field_validator("goal_type")
    @classmethod
    def _g(cls, v):
        if v not in GOAL_KEYS:
            raise ValueError("Unknown goal type.")
        return v


class GoalUpdate(BaseModel):
    target: float | None = Field(default=None, ge=0)
    active: bool | None = None


# ---------------- settings / account ----------------
class NotificationSettingsIn(BaseModel):
    weekly_reports: bool | None = None
    biweekly_reports: bool | None = None
    monthly_reports: bool | None = None
    push_enabled: bool | None = None
    email_enabled: bool | None = None


class InputPrefsIn(BaseModel):
    default_input_method: Literal["scan", "search", "manual"] | None = None
    ocr_language: Literal["eng", "hin", "eng+hin"] | None = None
    auto_log: bool | None = None


class AccessibilityIn(BaseModel):
    text_size: Literal["normal", "large", "xlarge"] | None = None
    high_contrast: bool | None = None
    voice_assistance: bool | None = None


class SettingsIn(BaseModel):
    notifications: NotificationSettingsIn | None = None
    input_prefs: InputPrefsIn | None = None
    accessibility: AccessibilityIn | None = None


class AccountUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=120)
    email: EmailStr | None = None
    current_password: str | None = Field(default=None, max_length=128)


class PasswordConfirm(BaseModel):
    password: str = Field(min_length=1, max_length=128)
    confirm_text: str = Field(max_length=40)


class HouseholdIn(BaseModel):
    text: str = Field(min_length=1, max_length=5000)
