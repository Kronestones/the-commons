"""Helper for describing the original post inside a share (kept separate to avoid circular imports)."""
from .database import PostStatus


def shared_summary(post):
    """For a share: a small dict describing the original post ({"available": False} if it is gone,
    hidden, or its author is deactivated). None if the post is not a share."""
    if not getattr(post, "shared_post_id", None):
        return None
    sp = post.shared_post
    if (sp is None or sp.status != PostStatus.PUBLISHED
            or sp.author is None or not sp.author.is_active):
        return {"available": False}
    return {
        "available":  True,
        "id":         sp.id,
        "author":     sp.author.username,
        "content":    sp.content,
        "post_type":  sp.post_type.value,
        "media_path": sp.media_path,
    }
