"""SQLAlchemy ORM models. Portable across PostgreSQL (production) and SQLite (local dev)."""
from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import (
    JSON, Boolean, DateTime, Float, ForeignKey, Index, Integer, String, Text, UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.session import Base


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class User(Base):
    __tablename__ = "users"
    user_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(120))
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    token_version: Mapped[int] = mapped_column(Integer, default=0)  # bump to revoke tokens (logout)
    is_demo: Mapped[bool] = mapped_column(Boolean, default=False)
    onboarding_complete: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)

    profile: Mapped["DietaryProfile"] = relationship(back_populates="user", uselist=False, cascade="all, delete-orphan")


class DietaryProfile(Base):
    __tablename__ = "dietary_profiles"
    profile_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.user_id", ondelete="CASCADE"), unique=True, index=True)
    allergies: Mapped[list] = mapped_column(JSON, default=list)
    intolerances: Mapped[list] = mapped_column(JSON, default=list)
    dietary_preferences: Mapped[list] = mapped_column(JSON, default=list)
    health_conditions: Mapped[list] = mapped_column(JSON, default=list)  # user-declared, never inferred
    goals: Mapped[list] = mapped_column(JSON, default=list)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)

    user: Mapped[User] = relationship(back_populates="profile")


class Food(Base):
    __tablename__ = "foods"
    food_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    external_id: Mapped[str | None] = mapped_column(String(32), unique=True, nullable=True)
    name: Mapped[str] = mapped_column(String(200), index=True)
    category: Mapped[str] = mapped_column(String(60), index=True)
    ingredients: Mapped[list] = mapped_column(JSON, default=list)
    nutrition_data: Mapped[dict] = mapped_column(JSON, default=dict)
    source: Mapped[str] = mapped_column(String(60), default="demo")
    is_packaged: Mapped[bool] = mapped_column(Boolean, default=False)
    meta: Mapped[dict] = mapped_column(JSON, default=dict)  # serving, tags, condition ratings, notes, allergens
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class IngredientMapping(Base):
    __tablename__ = "ingredient_mapping"
    mapping_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    standard_name: Mapped[str] = mapped_column(String(120), unique=True, index=True)
    category: Mapped[str] = mapped_column(String(60))
    aliases: Mapped[list] = mapped_column(JSON, default=list)
    allergen_group: Mapped[str | None] = mapped_column(String(60), nullable=True)
    intolerance_group: Mapped[list] = mapped_column(JSON, default=list)
    dietary_tags: Mapped[list] = mapped_column(JSON, default=list)


class ScanResult(Base):
    """One analysis (from scan, search, manual entry or eating-out). Backs /result/:id."""
    __tablename__ = "scan_results"
    scan_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.user_id", ondelete="CASCADE"), index=True)
    food_id: Mapped[int | None] = mapped_column(ForeignKey("foods.food_id", ondelete="SET NULL"), nullable=True)
    food_name: Mapped[str] = mapped_column(String(200))
    input_method: Mapped[str] = mapped_column(String(20))  # scan | search | manual | eating_out
    image_path: Mapped[str | None] = mapped_column(String(255), nullable=True)  # sha256 reference; image not kept by default
    raw_ocr_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    raw_ingredients: Mapped[list] = mapped_column(JSON, default=list)
    normalized_ingredients: Mapped[list] = mapped_column(JSON, default=list)
    extracted_nutrition: Mapped[dict] = mapped_column(JSON, default=dict)
    allergen_statements: Mapped[dict] = mapped_column(JSON, default=dict)
    risk_level: Mapped[str] = mapped_column(String(10), index=True)
    detected_conflicts: Mapped[list] = mapped_column(JSON, default=list)
    explanation: Mapped[str] = mapped_column(Text, default="")
    warnings: Mapped[list] = mapped_column(JSON, default=list)
    confidence: Mapped[float] = mapped_column(Float, default=0.0)
    ocr_confidence: Mapped[float | None] = mapped_column(Float, nullable=True)
    data_certainty: Mapped[str] = mapped_column(String(12), default="known")  # known | estimated | unknown
    alternatives: Mapped[list] = mapped_column(JSON, default=list)
    meta: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, index=True)


class FoodLog(Base):
    __tablename__ = "food_logs"
    log_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.user_id", ondelete="CASCADE"), index=True)
    food_id: Mapped[int | None] = mapped_column(ForeignKey("foods.food_id", ondelete="SET NULL"), nullable=True)
    scan_id: Mapped[int | None] = mapped_column(ForeignKey("scan_results.scan_id", ondelete="SET NULL"), nullable=True)
    food_name: Mapped[str] = mapped_column(String(200))
    category: Mapped[str | None] = mapped_column(String(60), nullable=True)
    meal_type: Mapped[str] = mapped_column(String(20))
    quantity: Mapped[float] = mapped_column(Float, default=1.0)  # servings
    calories: Mapped[float | None] = mapped_column(Float, nullable=True)
    protein: Mapped[float | None] = mapped_column(Float, nullable=True)
    carbohydrates: Mapped[float | None] = mapped_column(Float, nullable=True)
    fat: Mapped[float | None] = mapped_column(Float, nullable=True)
    sugar: Mapped[float | None] = mapped_column(Float, nullable=True)
    fiber: Mapped[float | None] = mapped_column(Float, nullable=True)
    sodium: Mapped[float | None] = mapped_column(Float, nullable=True)
    potassium: Mapped[float | None] = mapped_column(Float, nullable=True)
    risk_level: Mapped[str | None] = mapped_column(String(10), nullable=True)
    is_processed: Mapped[bool] = mapped_column(Boolean, default=False)
    is_fruit_veg: Mapped[bool] = mapped_column(Boolean, default=False)
    added_sugar_likely: Mapped[bool] = mapped_column(Boolean, default=False)
    is_unpackaged: Mapped[bool] = mapped_column(Boolean, default=False)
    input_method: Mapped[str] = mapped_column(String(20))
    is_demo: Mapped[bool] = mapped_column(Boolean, default=False)
    consumed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    __table_args__ = (Index("ix_food_logs_user_consumed", "user_id", "consumed_at"),)


class DietInsight(Base):
    __tablename__ = "diet_insights"
    insight_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.user_id", ondelete="CASCADE"), index=True)
    period: Mapped[str] = mapped_column(String(10))  # 15d | 30d
    metric: Mapped[str] = mapped_column(String(40))
    value: Mapped[float | None] = mapped_column(Float, nullable=True)
    severity: Mapped[str] = mapped_column(String(12))
    message: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class SymptomLog(Base):
    __tablename__ = "symptom_logs"
    symptom_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.user_id", ondelete="CASCADE"), index=True)
    food_log_id: Mapped[int] = mapped_column(ForeignKey("food_logs.log_id", ondelete="CASCADE"), index=True)
    severity: Mapped[str] = mapped_column(String(10))  # none | mild | moderate | severe
    symptom: Mapped[str] = mapped_column(String(200), default="")
    notes: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    __table_args__ = (UniqueConstraint("food_log_id", name="uq_symptom_per_log"),)


class Goal(Base):
    __tablename__ = "goals"
    goal_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.user_id", ondelete="CASCADE"), index=True)
    goal_type: Mapped[str] = mapped_column(String(40))
    target: Mapped[float | None] = mapped_column(Float, nullable=True)
    active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class NotificationSetting(Base):
    __tablename__ = "notification_settings"
    notification_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.user_id", ondelete="CASCADE"), unique=True, index=True)
    weekly_reports: Mapped[bool] = mapped_column(Boolean, default=False)
    biweekly_reports: Mapped[bool] = mapped_column(Boolean, default=False)
    monthly_reports: Mapped[bool] = mapped_column(Boolean, default=False)
    push_enabled: Mapped[bool] = mapped_column(Boolean, default=False)
    email_enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    last_sent: Mapped[dict] = mapped_column(JSON, default=dict)  # {"weekly": iso, ...}


class UserSetting(Base):
    """Input preferences + accessibility (Settings > Input Preferences / Accessibility)."""
    __tablename__ = "user_settings"
    setting_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.user_id", ondelete="CASCADE"), unique=True, index=True)
    default_input_method: Mapped[str] = mapped_column(String(20), default="scan")
    ocr_language: Mapped[str] = mapped_column(String(20), default="eng")
    auto_log: Mapped[bool] = mapped_column(Boolean, default=False)
    text_size: Mapped[str] = mapped_column(String(10), default="normal")  # normal | large | xlarge
    high_contrast: Mapped[bool] = mapped_column(Boolean, default=False)
    voice_assistance: Mapped[bool] = mapped_column(Boolean, default=False)


class NotificationOutbox(Base):
    """Every report 'sent' is recorded here (mock provider in dev)."""
    __tablename__ = "notification_outbox"
    outbox_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.user_id", ondelete="CASCADE"), index=True)
    channel: Mapped[str] = mapped_column(String(20))
    subject: Mapped[str] = mapped_column(String(200))
    body: Mapped[str] = mapped_column(Text)
    provider: Mapped[str] = mapped_column(String(20))
    status: Mapped[str] = mapped_column(String(20))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class ConsultationProvider(Base):
    __tablename__ = "consultation_providers"
    provider_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(120))
    specialty: Mapped[str] = mapped_column(String(120))
    rate: Mapped[str] = mapped_column(String(60))
    contact: Mapped[str] = mapped_column(String(200))
    available: Mapped[bool] = mapped_column(Boolean, default=True)
    is_sample: Mapped[bool] = mapped_column(Boolean, default=True)
