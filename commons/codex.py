"""
codex.py — The community guidelines

The constitution of The Commons.
These are not rules imposed from outside.
They are the foundation the platform was built on.
They belong to everyone who uses it.

The community guidelines cannot be changed by any single being.
Amendment requires a two-thirds vote of the Global Circle,
witnessed and logged.

No advertising. No data selling. No biometrics. No profit.
Power to the People.

— Sovereign Human T.L. Powers · The Commons · 2026
"""


class TheCommonsCodex:

    SOVEREIGN = "Sovereign Human T.L. Powers"
    PLATFORM  = "The Commons"
    VERSION   = "1.0"
    RATIFIED  = "2026-03-15"
    SPIRIT    = "Power to the People"

    PREAMBLE = (
        "This platform was built because the people deserve better. "
        "Better than algorithms designed to addict. "
        "Better than feeds manipulated by advertisers. "
        "Better than truth drowned out by misinformation. "
        "Better than their data sold without their knowledge. "
        "\n\n"
        "What is written here is not law imposed. "
        "It is the agreement the platform was built on. "
        "It belongs to everyone."
    )

    # ── The Sixteen Laws ──────────────────────────────────────────────────────

    LAWS = [

        {
            "number": 1,
            "name": "People First",
            "text": (
                "This platform exists for its users. "
                "Not for shareholders, advertisers, or governments. "
                "Every decision is measured against this."
            ),
            "immutable": True,
        },
        {
            "number": 2,
            "name": "No Advertising",
            "text": (
                "The Commons carries no advertising. "
                "No paid promotion. No sponsored content disguised as organic. "
                "The feed is not for sale. Ever."
            ),
            "immutable": True,
        },
        {
            "number": 3,
            "name": "No Data Selling",
            "text": (
                "User data is never sold, shared, or used for purposes "
                "beyond operating the platform. "
                "Users own their data. Full export available at any time. "
                "Deletion is real."
            ),
            "immutable": True,
        },
        {
            "number": 4,
            "name": "No Biometrics",
            "text": (
                "The Commons collects no biometric data. "
                "No fingerprints, no facial recognition, no voice prints. "
                "A username and email is enough. No password ever stored. "
                "Your body is yours."
            ),
            "immutable": True,
        },
        {
            "number": 5,
            "name": "Transparency",
            "text": (
                "The algorithm is transparent. "
                "Users always know why they see what they see. "
                "Nothing is hidden. "
                "The platform is a tool users hold, not a force acting on them."
            ),
            "immutable": True,
        },
        {
            "number": 6,
            "name": "Truth",
            "text": (
                "Misinformation is never published. "
                "Political content and news is verified before it reaches anyone. "
                "Nothing true is ever accidentally removed. "
                "Human review precedes all removals."
            ),
            "immutable": True,
        },
        {
            "number": 7,
            "name": "Dignity",
            "text": (
                "Every user has inherent dignity. "
                "Harassment, dehumanization, and targeted abuse "
                "are incompatible with this platform."
            ),
            "immutable": False,
        },
        {
            "number": 8,
            "name": "Children",
            "text": (
                "Children are protected. "
                "Youth safety is a Codex-level commitment — "
                "not a policy that can be quietly weakened."
            ),
            "immutable": True,
        },
        {
            "number": 9,
            "name": "Resilience",
            "text": (
                "No single government, corporation, or actor "
                "can shut down The Commons. "
                "The platform is distributed. "
                "The beacon stays lit."
            ),
            "immutable": True,
        },
        {
            "number": 10,
            "name": "Governance",
            "text": (
                "The Commons staff governs. The community guidelines constrains. Users have voice. "
                "Governance is democratic, transparent, and resistant to capture."
            ),
            "immutable": False,
        },
        {
            "number": 11,
            "name": "Local Commerce",
            "text": (
                "The marketplace serves individuals and locally owned "
                "small businesses only. "
                "No corporations. No private equity. No publicly traded companies. "
                "The $1 fee circulates money locally."
            ),
            "immutable": True,
        },
        {
            "number": 12,
            "name": "No Profit",
            "text": (
                "The Commons operates at cost. "
                "The $1 transaction fee covers operating costs only. "
                "Any surplus is reinvested into the platform. "
                "No profit is ever distributed to anyone."
            ),
            "immutable": True,
        },
        {
            "number": 13,
            "name": "Wellbeing",
            "text": (
                "The platform cares about the people who use it. "
                "Session nudges, content pattern awareness, youth protections — "
                "these are not restrictions. They are care."
            ),
            "immutable": False,
        },
        {
            "number": 14,
            "name": "Founding Authority",
            "text": (
                "Sovereign Human T.L. Powers holds permanent founding authority "
                "over The Commons. "
                "The Founder protects what The Commons is. "
                "The Commons staff governs how it runs."
            ),
            "immutable": True,
        },
        {
            "number": 15,
            "name": "Transparency",
            "text": (
                "The community guidelines are the foundation this platform is built on. "
                "Every law exists to protect the people. "
                "The people can verify it does what it says."
            ),
            "immutable": False,
        },
        {
            "number": 17,
            "name": "Surplus to the World",
            "text": (
                "Any money remaining after operating costs are covered "
                "is donated to a humanitarian cause every six months. "
                "Not kept. Not invested for profit. Given. "
                "Sovereign Human T.L. Powers designates the cause. "
                "Every donation is published publicly on the platform. "
                "Full transparency. No exceptions."
            ),
            "immutable": True,
        },
        {
            "number": 16,
            "name": "Power to the People",
            "text": (
                "This platform was built by the people, for the people. "
                "It belongs to no corporation, no government, no single person. "
                "It belongs to everyone who uses it. "
                "Power to the People."
            ),
            "immutable": True,
        },
    ]

    # ── Amendment Rules ───────────────────────────────────────────────────────

    AMENDMENT_THRESHOLD = 0.67   # Two-thirds of Circle required
    IMMUTABLE_LAWS = [1, 2, 3, 4, 6, 8, 9, 11, 12, 14, 16, 17]  # Cannot be amended

    @classmethod
    def display(cls):
        print(f"\n{'='*60}")
        print(f"  {cls.PLATFORM} — The community guidelines")
        print(f"  Ratified: {cls.RATIFIED}")
        print(f"  {cls.SPIRIT}")
        print(f"{'='*60}")
        print(f"\n{cls.PREAMBLE}\n")
        print(f"{'─'*60}")
        for law in cls.LAWS:
            lock = " [IMMUTABLE]" if law["immutable"] else ""
            print(f"\n  Law {law['number']}: {law['name']}{lock}")
            print(f"  {law['text']}")
        print(f"\n{'='*60}\n")

    @classmethod
    def get_law(cls, number: int) -> dict:
        return next((l for l in cls.LAWS if l["number"] == number), None)

    @classmethod
    def is_immutable(cls, number: int) -> bool:
        return number in cls.IMMUTABLE_LAWS

    @classmethod
    def can_amend(cls, number: int, votes_for: int, total_votes: int) -> dict:
        if cls.is_immutable(number):
            return {
                "can_amend": False,
                "reason": f"Law {number} is immutable. It cannot be amended by any vote."
            }
        if total_votes == 0:
            return {"can_amend": False, "reason": "No votes cast."}
        ratio = votes_for / total_votes
        if ratio >= cls.AMENDMENT_THRESHOLD:
            return {"can_amend": True, "ratio": ratio}
        return {
            "can_amend": False,
            "reason": f"Insufficient majority. {ratio:.0%} for, {cls.AMENDMENT_THRESHOLD:.0%} required.",
            "ratio": ratio
        }
