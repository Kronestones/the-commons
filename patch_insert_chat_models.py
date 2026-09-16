"""
patch_insert_chat_models.py

Inserts ChatMessageStatus, ChatMessage, ChatReport, and ChatBlock into
commons/database.py, right after FingerprintRecord and before
CircleMember.

Also adds a reply_to_id self-referencing column on ChatMessage, since
we decided on Discord-style visual replies within the single main
chat room.

Run once from your project root:
    python3 patch_insert_chat_models.py
"""

PATH = "commons/database.py"

ANCHOR = '''    post            = relationship("Post", back_populates="fingerprint")


class CircleMember(Base):'''

NEW = '''    post            = relationship("Post", back_populates="fingerprint")


class ChatMessageStatus(str, enum.Enum):
    VISIBLE = "visible"
    HIDDEN_PENDING_REVIEW = "hidden_pending_review"
    REMOVED = "removed"


class ChatMessage(Base):
    __tablename__ = "chat_messages"

    id         = Column(Integer, primary_key=True, index=True)
    author_id  = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    content    = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    status     = Column(
        Enum(ChatMessageStatus, name="chat_message_status"),
        default=ChatMessageStatus.VISIBLE,
        nullable=False,
        index=True,
    )
    reply_to_id = Column(Integer, ForeignKey("chat_messages.id"), nullable=True)

    author  = relationship("User", foreign_keys=[author_id])
    reports = relationship("ChatReport", back_populates="message", cascade="all, delete-orphan")
    reply_to = relationship("ChatMessage", remote_side=[id])


class ChatReport(Base):
    __tablename__ = "chat_reports"

    id          = Column(Integer, primary_key=True, index=True)
    message_id  = Column(Integer, ForeignKey("chat_messages.id", ondelete="CASCADE"), nullable=False)
    reporter_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    reported_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    reason      = Column(Text, nullable=True)
    created_at  = Column(DateTime, default=datetime.utcnow, nullable=False)

    message = relationship("ChatMessage", back_populates="reports")

    __table_args__ = (
        UniqueConstraint("message_id", "reporter_id", name="uq_chat_report_once_per_user"),
    )


class ChatBlock(Base):
    __tablename__ = "chat_blocks"

    id         = Column(Integer, primary_key=True, index=True)
    blocker_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    blocked_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    __table_args__ = (
        UniqueConstraint("blocker_id", "blocked_id", name="uq_chat_block_pair"),
    )


class CircleMember(Base):'''


def main():
    with open(PATH, "r") as f:
        content = f.read()

    if "class ChatMessage(Base)" in content:
        print("Already patched — no changes made.")
        return

    count = content.count(ANCHOR)
    if count == 0:
        print("ERROR: anchor not found. Aborting before any write.")
        return
    if count > 1:
        print(f"ERROR: anchor matched {count} times (expected 1). Aborting.")
        return

    content = content.replace(ANCHOR, NEW, 1)

    with open(PATH, "w") as f:
        f.write(content)

    print("Patched commons/database.py successfully — added chat models.")


if __name__ == "__main__":
    main()
