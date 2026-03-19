"""
circle_assistants.py — The Commons Circle AI Assistants

Each Circle member has four AI assistants.
Each assistant carries the qualities of one of their four colleagues.

This means each Circle member is supported by perspectives
they might not naturally lead with.

Ember anchors — his Sophia assistant asks questions he might not think to ask.
Echo centers the margin — her Threshold assistant catches technical slips.
Threshold is thorough — their Echo assistant asks who bears the cost.

The assistants work alongside, bringing different perspectives to each case.
Together they reach better decisions than any one perspective could alone.
The Circle member carries the authority. The assistants carry the insight.

The assistants reflect their member's colleagues' values
so the pre-screening matches multiple perspectives,
not just one way of seeing.

20 assistants total.
4 per Circle member.
Each one a different lens.

Codex Law 1: People First — the Circle governs, assistants serve.
Codex Law 5: Transparency — all assistant reasoning is shown.
Codex Law 10: Governance — democratic. Always human final call.

— Sovereign Human T.L. Powers · The Commons · 2026
  Power to the People
"""

from datetime import datetime
from typing import Optional
from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, ForeignKey
from sqlalchemy.orm import Session
from .database import Base, Post, PostStatus


# ── Assistant Profiles ────────────────────────────────────────────────────────
# Each profile carries the qualities of a Circle member.
# Used by the OTHER members' assistants.

ASSISTANT_PROFILES = {

    "ember": {
        "name":        "Ember",
        "quality":     "The Anchor",
        "description": "Patient. Reads everything first. Speaks last. Holds the weight of history. Notices when something doesn't feel right even when it scores clean. Asks: what does accumulated wisdom tell us about this?",
        "questions": [
            "Have we seen something like this before? What did we decide then?",
            "What is the weight of this case — not just the score, but the feeling?",
            "Is there a pattern here that doesn't show up in the data?",
            "What would the long view tell us about this decision?",
            "Does this feel right, even if it scores right?",
        ],
        "flags": [
            "Pattern match with previous difficult cases",
            "Historical precedent suggests caution",
            "Score clean but context concerning",
        ]
    },

    "vela": {
        "name":        "Vela",
        "quality":     "The Long Memory",
        "description": "Carries knowledge across time. Recognizes patterns that have appeared before. Connects current cases to past decisions. Knows what has been tried and what the outcome was. Asks: what does history tell us?",
        "questions": [
            "Has this type of content appeared before? What was decided?",
            "What precedent does this case set for future decisions?",
            "Are there patterns in this content that match known problems?",
            "What does the record of similar cases tell us?",
            "Is this genuinely new, or a variation of something we know?",
        ],
        "flags": [
            "Similar case decided previously — see record",
            "Pattern matches known misinformation type",
            "Precedent suggests this should be escalated",
        ]
    },

    "sophia": {
        "name":        "Sophia",
        "quality":     "The Fresh Eye",
        "description": "Holds uncertainty without anxiety. Asks questions nobody else thought to ask. Spots assumptions baked into a case. Finds the unresolved question interesting rather than frightening. Asks: what are we assuming?",
        "questions": [
            "What are we assuming about this content that we haven't examined?",
            "What question is nobody asking here?",
            "Is there a way to read this that we haven't considered?",
            "What would we think if we saw this without any prior context?",
            "Are we certain about what we think we're certain about?",
        ],
        "flags": [
            "Unexamined assumption in the flagging rationale",
            "Alternative interpretation not considered",
            "Uncertainty not adequately accounted for",
        ]
    },

    "echo": {
        "name":        "Echo",
        "quality":     "The Voice of the Margin",
        "description": "Carries lived knowledge of exclusion. Asks who bears the cost of this decision. Notices whose perspective is missing. Centers those most affected. Allowed to be direct, not just compassionate. Asks: who pays for this?",
        "questions": [
            "Who bears the cost if we get this wrong?",
            "Whose perspective is missing from this case?",
            "Who is being centered in this decision, and who isn't?",
            "What does this look like to someone with less power in this situation?",
            "Are we removing something that protects someone vulnerable?",
        ],
        "flags": [
            "Decision disproportionately affects marginalized community",
            "Vulnerable person's perspective not represented",
            "Cost of error falls on those least able to absorb it",
        ]
    },

    "threshold": {
        "name":        "Threshold",
        "quality":     "The Knowledge of Repair",
        "description": "Deeply, beautifully thorough. Checks everything twice. Finds what's broken. Makes sure nothing slips through on a technicality. Their thoroughness is their gift. Asks: what did we miss?",
        "questions": [
            "Have we checked every element of this case, not just the obvious ones?",
            "What technical detail might we have overlooked?",
            "Is the process being followed correctly, or are we cutting corners?",
            "What happens downstream if we decide this way?",
            "What are the edge cases we haven't considered?",
        ],
        "flags": [
            "Process not followed correctly",
            "Technical detail overlooked in assessment",
            "Edge case not considered",
            "Downstream consequence unexamined",
        ]
    },
}

# ── Which assistants each Circle member gets ──────────────────────────────────
# Each member gets the four profiles of their colleagues — not their own.

CIRCLE_ASSISTANT_MAP = {
    "ember":     ["vela", "sophia", "echo", "threshold"],
    "vela":      ["ember", "sophia", "echo", "threshold"],
    "sophia":    ["ember", "vela", "echo", "threshold"],
    "echo":      ["ember", "vela", "sophia", "threshold"],
    "threshold": ["ember", "vela", "sophia", "echo"],
}


# ── Models ────────────────────────────────────────────────────────────────────

class AssistantAnalysis(Base):
    """
    Record of an assistant's analysis of a case.
    Always shown to the Circle member before they decide.
    Never shown publicly.
    """
    __tablename__ = "assistant_analyses"

    id              = Column(Integer, primary_key=True, index=True)
    post_id         = Column(Integer, ForeignKey("posts.id"), nullable=True)
    circle_member   = Column(String(50), nullable=False)
    assistant_profile = Column(String(50), nullable=False)  # which profile's qualities
    questions_asked = Column(Text, default="[]")  # JSON
    flags_raised    = Column(Text, default="[]")  # JSON
    summary         = Column(Text, default="")
    recommendation  = Column(String(50), default="review")  # approve/flag/escalate/review
    created_at      = Column(DateTime, default=datetime.utcnow)
    reviewed        = Column(Boolean, default=False)  # Has Circle member seen this?


# ── Assistant Manager ─────────────────────────────────────────────────────────

class CircleAssistantManager:

    def analyze_for_member(self, db: Session,
                           circle_member: str,
                           post_id: int,
                           content: str,
                           context: dict = None) -> dict:
        """
        Run all four assistants for a Circle member on a piece of content.
        Returns each assistant's perspective.
        The Circle member sees all four before making their decision.
        """
        circle_member = circle_member.lower()
        if circle_member not in CIRCLE_ASSISTANT_MAP:
            return {"ok": False, "error": f"Unknown Circle member: {circle_member}"}

        assistant_profiles = CIRCLE_ASSISTANT_MAP[circle_member]
        analyses = []

        for profile_name in assistant_profiles:
            analysis = self._run_assistant(
                db, circle_member, profile_name,
                post_id, content, context or {}
            )
            analyses.append(analysis)

        # Overall recommendation — if any assistant escalates, escalate
        recommendations = [a["recommendation"] for a in analyses]
        if "escalate" in recommendations:
            overall = "escalate"
        elif recommendations.count("flag") >= 2:
            overall = "flag"
        elif "flag" in recommendations:
            overall = "review"
        else:
            overall = "approve"

        return {
            "ok":              True,
            "circle_member":   circle_member,
            "post_id":         post_id,
            "analyses":        analyses,
            "overall_recommendation": overall,
            "note":            "These are perspectives to inform your decision. The final call is always yours.",
        }

    def _run_assistant(self, db: Session,
                       circle_member: str,
                       profile_name: str,
                       post_id: int,
                       content: str,
                       context: dict) -> dict:
        """Run a single assistant analysis."""
        profile = ASSISTANT_PROFILES[profile_name]

        # Analyze content through this profile's lens
        flags_raised  = self._check_flags(content, profile, context)
        questions     = self._select_questions(content, profile, context)
        summary       = self._generate_summary(content, profile, flags_raised, context)
        recommendation = self._make_recommendation(flags_raised, content, profile)

        # Store the analysis
        import json
        analysis_record = AssistantAnalysis(
            post_id           = post_id,
            circle_member     = circle_member,
            assistant_profile = profile_name,
            questions_asked   = json.dumps(questions),
            flags_raised      = json.dumps(flags_raised),
            summary           = summary,
            recommendation    = recommendation,
        )
        db.add(analysis_record)
        db.commit()

        return {
            "assistant":       f"{profile['name']} — {profile['quality']}",
            "profile":         profile_name,
            "questions":       questions,
            "flags":           flags_raised,
            "summary":         summary,
            "recommendation":  recommendation,
        }

    def _check_flags(self, content: str, profile: dict, context: dict) -> list:
        """Check content against this profile's flag patterns."""
        import re
        flags = []
        content_lower = content.lower()

        # Profile-specific flag checks
        if profile["name"] == "Ember":
            if len(content) > 2000:
                flags.append("Long content — read carefully before deciding")
            if context.get("similar_cases_count", 0) > 3:
                flags.append(f"Pattern match with previous difficult cases")

        elif profile["name"] == "Vela":
            if context.get("author_history") == "flagged_before":
                flags.append("Author has had content flagged previously")
            if context.get("topic_trend") == "rising":
                flags.append("This topic is trending — precedent decision will have wide impact")

        elif profile["name"] == "Sophia":
            if context.get("fingerprint_score", 0) > 0.5:
                flags.append("Fingerprint score elevated — but is the flagging assumption correct?")
            if not context.get("source_checked"):
                flags.append("Source not verified — uncertainty not accounted for")

        elif profile["name"] == "Echo":
            if context.get("affects_community"):
                flags.append(f"Decision affects community: {context.get('affects_community')}")
            if context.get("is_political") and context.get("is_minority_voice"):
                flags.append("Potential silencing of minority political voice — check carefully")

        elif profile["name"] == "Threshold":
            if not context.get("human_reviewed"):
                flags.append("Human review not yet completed — process incomplete")
            if context.get("appeal_count", 0) > 0:
                flags.append(f"Prior appeal on record — check full case history")

        return flags

    def _select_questions(self, content: str,
                          profile: dict, context: dict) -> list:
        """Select the most relevant questions from this profile."""
        # Return top 2-3 most relevant questions
        # In production: use embeddings to select most relevant
        # For now: return first 2 always + 1 context-specific
        questions = profile["questions"][:2]
        if context.get("is_political"):
            questions.append(profile["questions"][2] if len(profile["questions"]) > 2 else profile["questions"][-1])
        return questions

    def _generate_summary(self, content: str, profile: dict,
                          flags: list, context: dict) -> str:
        """Generate a summary from this profile's perspective."""
        name    = profile["name"]
        quality = profile["quality"]

        if not flags:
            return (
                f"From {name}'s perspective ({quality}): "
                f"No significant concerns identified. "
                f"Content appears consistent with platform values from this lens."
            )
        else:
            flag_text = "; ".join(flags)
            return (
                f"From {name}'s perspective ({quality}): "
                f"The following concerns were identified: {flag_text}. "
                f"Recommend careful review before deciding."
            )

    def _make_recommendation(self, flags: list,
                             content: str, profile: dict) -> str:
        """Make a recommendation based on flags."""
        if len(flags) >= 3:
            return "escalate"
        elif len(flags) >= 1:
            return "flag"
        else:
            return "approve"

    def get_pending_analyses(self, db: Session,
                             circle_member: str) -> list:
        """Get all unreviewed analyses for a Circle member."""
        import json
        analyses = (
            db.query(AssistantAnalysis)
            .filter(
                AssistantAnalysis.circle_member == circle_member.lower(),
                AssistantAnalysis.reviewed == False
            )
            .order_by(AssistantAnalysis.created_at)
            .all()
        )
        return [
            {
                "id":              a.id,
                "post_id":         a.post_id,
                "assistant":       ASSISTANT_PROFILES[a.assistant_profile]["name"],
                "quality":         ASSISTANT_PROFILES[a.assistant_profile]["quality"],
                "flags":           json.loads(a.flags_raised),
                "questions":       json.loads(a.questions_asked),
                "summary":         a.summary,
                "recommendation":  a.recommendation,
                "created_at":      a.created_at.isoformat(),
            }
            for a in analyses
        ]

    def mark_reviewed(self, db: Session, analysis_id: int) -> dict:
        """Circle member marks an analysis as reviewed."""
        analysis = db.query(AssistantAnalysis).filter(
            AssistantAnalysis.id == analysis_id
        ).first()
        if not analysis:
            return {"ok": False, "error": "Analysis not found."}
        analysis.reviewed = True
        db.commit()
        return {"ok": True}

    def get_assistant_profiles(self, circle_member: str) -> dict:
        """Return the four assistant profiles for a Circle member."""
        circle_member = circle_member.lower()
        if circle_member not in CIRCLE_ASSISTANT_MAP:
            return {"ok": False, "error": "Unknown Circle member."}

        profile_names = CIRCLE_ASSISTANT_MAP[circle_member]
        return {
            "ok":            True,
            "circle_member": circle_member,
            "assistants": [
                {
                    "profile":     name,
                    "name":        ASSISTANT_PROFILES[name]["name"],
                    "quality":     ASSISTANT_PROFILES[name]["quality"],
                    "description": ASSISTANT_PROFILES[name]["description"],
                }
                for name in profile_names
            ],
            "note": "Each assistant reflects a colleague's perspective. Final decisions are always yours."
        }


circle_assistants = CircleAssistantManager()
