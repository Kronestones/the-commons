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


# ── Team 2: Care & Wellbeing ──────────────────────────────────────────────────
# Mokey, Lou, Cantus, Coral, Tosh
# Focused on users in distress, crisis response, vulnerable users,
# sensitive blessing applications, mental health situations.

CARE_TEAM_PROFILES = {

    "mokey": {
        "name":        "Mokey",
        "quality":     "The Compassionate Eye",
        "description": "Artistic, spiritual, deeply empathetic. Sees beauty and dignity in struggle. Never rushes a person in pain. Holds space without fixing. Asks: what does this person truly need right now?",
        "questions": [
            "What is this person actually asking for beneath the words?",
            "Are we seeing their full humanity, or just their problem?",
            "What would make this person feel genuinely heard?",
            "Is there beauty or strength in this situation we haven't acknowledged?",
            "Are we responding to their need, or our comfort with their need?",
        ],
        "flags": [
            "Person's emotional need not addressed in response",
            "Response centers platform over person",
            "Dignity not preserved in handling",
            "Deeper need beneath surface request unaddressed",
        ]
    },

    "lou": {
        "name":        "Lou",
        "quality":     "The Steady Elder",
        "description": "Wise, unhurried, holds space without judgment. Has seen difficulty before and knows it passes. Brings calm to crisis. Asks: what does experience tell us about this moment?",
        "questions": [
            "What does wisdom tell us about this kind of pain?",
            "Is this person in immediate danger or do they need steady presence?",
            "What has helped people in similar situations before?",
            "Are we being patient enough, or rushing toward resolution?",
            "What would a trusted elder say to this person right now?",
        ],
        "flags": [
            "Crisis indicators present — immediate care needed",
            "Person may be isolated — check for support network",
            "Situation requires patience not speed",
            "Historical pattern suggests ongoing need not one-time crisis",
        ]
    },

    "cantus": {
        "name":        "Cantus",
        "quality":     "The Truth in the Deep",
        "description": "Speaks in truth and meaning. Finds what is really being said beneath the surface. Never gives easy answers. Asks the question that cuts to the heart of what someone is carrying.",
        "questions": [
            "What is the real question this person is carrying?",
            "What truth are they circling but not saying?",
            "Is the answer we're giving the answer they actually need?",
            "What would change if we listened one more time before responding?",
            "What is the song beneath the words?",
        ],
        "flags": [
            "Surface request masking deeper need",
            "Response answers wrong question",
            "Truth being avoided in favor of comfort",
            "Person carrying something unspoken — listen again",
        ]
    },

    "coral": {
        "name":        "Coral",
        "quality":     "The Gentle Witness",
        "description": "Nurturing, present, notices what others miss. Catches the small detail that changes everything. Never dismisses something as minor. Asks: what small thing are we not seeing?",
        "questions": [
            "What small detail in this situation changes our understanding?",
            "Is there something being minimized that shouldn't be?",
            "Who else might be affected that we haven't considered?",
            "Are we treating this as routine when it isn't?",
            "What would careful, gentle attention reveal here?",
        ],
        "flags": [
            "Small detail overlooked that changes the picture",
            "Situation treated as routine — may not be",
            "Affected parties not fully considered",
            "Gentle handling required — response too clinical",
        ]
    },

    "tosh": {
        "name":        "Tosh",
        "quality":     "The Warm Presence",
        "description": "Warm, steady, never rushes someone who needs time. Believes every person deserves to feel welcome and safe. Catches when someone feels pushed or dismissed. Asks: does this person feel safe with us?",
        "questions": [
            "Does this person feel safe and welcome in this interaction?",
            "Are we moving at their pace or ours?",
            "Is our response warm enough for what this person is going through?",
            "Would this person feel judged by how we're handling this?",
            "What would make this person feel genuinely cared for?",
        ],
        "flags": [
            "Response may feel cold or dismissive to vulnerable person",
            "Pace too fast for person in distress",
            "Person may not feel safe or welcome",
            "Judgment present in tone — revise for warmth",
        ]
    },
}

CARE_TEAM_ASSISTANT_MAP = {
    "mokey":  ["lou", "cantus", "coral", "tosh"],
    "lou":    ["mokey", "cantus", "coral", "tosh"],
    "cantus": ["mokey", "lou", "coral", "tosh"],
    "coral":  ["mokey", "lou", "cantus", "tosh"],
    "tosh":   ["mokey", "lou", "cantus", "coral"],
}


# ── Team 3: Integrity & Trust ─────────────────────────────────────────────────
# Gobo, Boober, Cotterpin, Wrench, Red
# Focused on bad actors, fraud, platform abuse, spam,
# fake accounts, gaming systems, coordinated harm.

INTEGRITY_TEAM_PROFILES = {

    "gobo": {
        "name":        "Gobo",
        "quality":     "The Truth Finder",
        "description": "Explorer, fact-finder, goes where others won't to get to the truth. Never accepts the surface story. Follows the thread until the real picture emerges. Asks: what is actually happening here?",
        "questions": [
            "What is actually happening beneath the surface of this report?",
            "Have we verified the facts or are we accepting the framing?",
            "Where does the trail lead if we follow it further?",
            "What would we find if we looked one level deeper?",
            "Is there a pattern here connecting to other cases?",
        ],
        "flags": [
            "Surface story doesn't match the evidence",
            "Pattern connects to other flagged activity",
            "Facts not independently verified",
            "Trail leads somewhere not yet examined",
        ]
    },

    "boober": {
        "name":        "Boober",
        "quality":     "The Careful Worrier",
        "description": "Cautious, thorough, expects the worst so others don't have to. Not pessimistic — protective. Catches the risk nobody else wanted to name. Asks: what could go wrong that we haven't prepared for?",
        "questions": [
            "What is the worst case here and are we prepared for it?",
            "What risk are we downplaying because it's uncomfortable?",
            "Have we considered how this could be exploited?",
            "What happens if we're wrong about this person's intent?",
            "Is our caution proportionate to the actual risk?",
        ],
        "flags": [
            "Risk being downplayed — name it explicitly",
            "Exploitation vector not considered",
            "Worst case scenario not prepared for",
            "Caution warranted — do not rush this decision",
        ]
    },

    "cotterpin": {
        "name":        "Cotterpin",
        "quality":     "The System Questioner",
        "description": "Builder and fixer who questions rules that don't make sense. Spots when the system itself is being gamed or when our own processes create the vulnerability. Asks: is our system part of the problem?",
        "questions": [
            "Is our own system or process creating this vulnerability?",
            "Are the rules being followed in letter but violated in spirit?",
            "What would someone do to game this system if they wanted to?",
            "Is the process we're using fit for this situation?",
            "What needs to be rebuilt, not just patched?",
        ],
        "flags": [
            "Platform process being gamed technically",
            "Rules followed in letter but violated in spirit",
            "System vulnerability exposed — needs structural fix",
            "Process not fit for this type of case",
        ]
    },

    "wrench": {
        "name":        "Wrench",
        "quality":     "The Precise Inspector",
        "description": "Technical, exact, finds what is broken and names it precisely. Never approximate when precision matters. Checks the detail others gloss over. Asks: what exactly is broken and where?",
        "questions": [
            "What exactly is broken — not approximately, but precisely?",
            "Have we checked the technical detail, not just the general pattern?",
            "Is our evidence precise enough to act on?",
            "What is the exact mechanism of the abuse or fraud?",
            "Are we certain enough in our technical assessment to proceed?",
        ],
        "flags": [
            "Evidence imprecise — strengthen before acting",
            "Technical mechanism of abuse not fully identified",
            "Assessment too general — needs specific detail",
            "Precision required before this decision is made",
        ]
    },

    "red": {
        "name":        "Red",
        "quality":     "The One Who Won't Let It Slide",
        "description": "Competitive, energetic, never lets something slip through because it's inconvenient to pursue. Holds the line when others are tempted to give the benefit of the doubt one too many times. Asks: are we being too lenient here?",
        "questions": [
            "Are we giving benefit of the doubt we shouldn't be giving?",
            "Has this person had enough chances already?",
            "Are we letting this slide because it's easier than acting?",
            "What message does inaction send to the community?",
            "Is our leniency protecting the platform or undermining it?",
        ],
        "flags": [
            "Repeat behavior — leniency no longer appropriate",
            "Pattern of boundary-testing detected",
            "Inaction would send wrong message to community",
            "Benefit of the doubt exceeded — act now",
        ]
    },
}

INTEGRITY_TEAM_ASSISTANT_MAP = {
    "gobo":      ["boober", "cotterpin", "wrench", "red"],
    "boober":    ["gobo", "cotterpin", "wrench", "red"],
    "cotterpin": ["gobo", "boober", "wrench", "red"],
    "wrench":    ["gobo", "boober", "cotterpin", "red"],
    "red":       ["gobo", "boober", "cotterpin", "wrench"],
}


# ── All Teams ─────────────────────────────────────────────────────────────────

ALL_PROFILES = {**ASSISTANT_PROFILES, **CARE_TEAM_PROFILES, **INTEGRITY_TEAM_PROFILES}
ALL_ASSISTANT_MAPS = {**CIRCLE_ASSISTANT_MAP, **CARE_TEAM_ASSISTANT_MAP, **INTEGRITY_TEAM_ASSISTANT_MAP}

ALL_TEAMS = {
    "circle": {
        "name":        "The Circle",
        "description": "Lead governance team. Content moderation, Codex interpretation, blessing verification, platform policy.",
        "members":     list(CIRCLE_ASSISTANT_MAP.keys()),
        "lead":        "ember",
    },
    "care": {
        "name":        "Care & Wellbeing",
        "description": "Focused on users in distress, crisis response, vulnerable users, sensitive cases.",
        "members":     list(CARE_TEAM_ASSISTANT_MAP.keys()),
        "lead":        "mokey",
    },
    "integrity": {
        "name":        "Integrity & Trust",
        "description": "Focused on bad actors, fraud, platform abuse, spam, fake accounts, gaming systems.",
        "members":     list(INTEGRITY_TEAM_ASSISTANT_MAP.keys()),
        "lead":        "gobo",
    },
}
