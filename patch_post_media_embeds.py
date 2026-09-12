"""
patch_post_media_embeds.py

Adds extractMediaEmbeds(text) to static/js/main.js: scans post content
for Twitch/Spotify/YouTube links and returns embed HTML to render below
the post. Does NOT touch linkify() or any fact-check/voting/Blessing
logic — purely additive display behavior.

To actually show the embeds, callers need to append the result of
extractMediaEmbeds(post.content) into the post's rendered HTML, after
the post-content div. This patch adds the function; wiring it into
each place posts render (index.html, profile.html) is a separate,
smaller patch once this is confirmed working.

Run once from your project root:
    python3 patch_post_media_embeds.py
"""

PATH = "static/js/main.js"

ANCHOR = """function linkify(text) {
  const urlRegex = /(https?:\\/\\/[^\\s<>"{}|\\\\^`\\[\\]]+)/g;
  return escapeHtml(text).replace(urlRegex, '<a href="$1" target="_blank" rel="noopener noreferrer" style="color:var(--green-dark);word-break:break-all;">$1</a>');
}"""

NEW_FUNCTIONS = """function linkify(text) {
  const urlRegex = /(https?:\\/\\/[^\\s<>"{}|\\\\^`\\[\\]]+)/g;
  return escapeHtml(text).replace(urlRegex, '<a href="$1" target="_blank" rel="noopener noreferrer" style="color:var(--green-dark);word-break:break-all;">$1</a>');
}

// ── Media embeds in post content (Twitch / Spotify / YouTube) ──────────────────
function extractMediaEmbeds(text) {
  if (!text) return '';
  const urlRegex = /(https?:\\/\\/[^\\s<>"{}|\\\\^`\\[\\]]+)/g;
  const urls = text.match(urlRegex) || [];
  let html = '';
  const seen = new Set();

  for (const url of urls) {
    if (seen.has(url)) continue;

    // Twitch channel: https://twitch.tv/channelname
    let m = url.match(/twitch\\.tv\\/([a-zA-Z0-9_]{3,25})(?:[/?]|$)/);
    if (m) {
      seen.add(url);
      html += '<div style="margin-top:10px;"><iframe src="https://player.twitch.tv/?channel=' + m[1] + '&parent=commonscommunity.org&autoplay=false" height="280" width="100%" allowfullscreen frameborder="0" scrolling="no"></iframe></div>';
      continue;
    }

    // Spotify: https://open.spotify.com/{type}/{id}
    m = url.match(/open\\.spotify\\.com\\/(track|album|artist|playlist|episode|show)\\/([a-zA-Z0-9]{22})/);
    if (m) {
      seen.add(url);
      html += '<div style="margin-top:10px;"><iframe src="https://open.spotify.com/embed/' + m[1] + '/' + m[2] + '" width="100%" height="152" frameborder="0" allow="autoplay; clipboard-write; encrypted-media; fullscreen; picture-in-picture" style="border-radius:12px;"></iframe></div>';
      continue;
    }

    // YouTube: youtube.com/watch?v=, youtu.be/, youtube.com/shorts/, youtube.com/embed/
    m = url.match(/(?:youtube\\.com\\/watch\\?v=|youtu\\.be\\/|youtube\\.com\\/shorts\\/|youtube\\.com\\/embed\\/)([a-zA-Z0-9_-]{11})/);
    if (m) {
      seen.add(url);
      html += '<div style="margin-top:10px;position:relative;padding-bottom:56.25%;height:0;overflow:hidden;"><iframe src="https://www.youtube.com/embed/' + m[1] + '" style="position:absolute;top:0;left:0;width:100%;height:100%;border:0;" allowfullscreen frameborder="0"></iframe></div>';
      continue;
    }
  }

  return html;
}"""


def main():
    with open(PATH, "r") as f:
        content = f.read()

    if "function extractMediaEmbeds" in content:
        print("Already patched — no changes made.")
        return

    count = content.count(ANCHOR)
    if count == 0:
        print("ERROR: anchor not found. Aborting before any write.")
        return
    if count > 1:
        print(f"ERROR: anchor matched {count} times (expected 1). Aborting.")
        return

    content = content.replace(ANCHOR, NEW_FUNCTIONS, 1)

    with open(PATH, "w") as f:
        f.write(content)

    print("Patched static/js/main.js successfully.")


if __name__ == "__main__":
    main()
