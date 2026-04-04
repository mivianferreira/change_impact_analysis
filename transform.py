#!/usr/bin/env python3
"""
transform.py
Splits each repo_*.html into:
  - repo_X.html          (light: accordions only, link to detail page)
  - details/repo_X__IDX.html  (detail page with cards in new format)
"""
import os, re, glob, html as htmllib
from pathlib import Path

DETAILS_DIR = Path('/home/mivian/workspace/change_impact_analysis/details')
DETAILS_DIR.mkdir(exist_ok=True)

# ─── CSS for detail pages ────────────────────────────────────────────────────
DETAIL_CSS = """
:root{--bg:#0d1117;--surface:#161b22;--surface2:#21262d;--border:#30363d;--text:#e6edf3;--text2:#8b949e;--accent:#58a6ff;--green:#3fb950;--orange:#e3b341;--red:#f85149;}
*{margin:0;padding:0;box-sizing:border-box;}
body{background:var(--bg);color:var(--text);font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Helvetica,Arial,sans-serif;line-height:1.5;padding:0;}
.page-header{background:var(--surface);border-bottom:1px solid var(--border);padding:16px 32px;position:sticky;top:0;z-index:100;display:flex;flex-wrap:wrap;align-items:center;gap:12px;}
.back-btn{color:var(--text2);font-size:13px;text-decoration:none;padding:6px 14px;border:1px solid var(--border);border-radius:6px;background:var(--surface2);}
.back-btn:hover{color:var(--accent);border-color:var(--accent);}
.page-header h1{color:var(--accent);font-size:18px;flex:1;}
.page-header .src-label{color:var(--text2);font-size:12px;}
.page-header .src-name-h{color:var(--text);font-weight:700;font-size:14px;}
.container{max-width:900px;margin:0 auto;padding:24px 32px;}

/* cards */
.cards-list{display:flex;flex-direction:column;gap:12px;}
.card{background:var(--surface);border:1px solid var(--border);border-radius:10px;overflow:hidden;transition:border-color .2s;}
.card.open{border-color:var(--accent);}
.card-header{padding:14px 18px;display:flex;align-items:center;gap:12px;cursor:pointer;user-select:none;}
.card-header:hover{background:var(--surface2);}
.source-target{display:flex;align-items:center;gap:8px;flex:1;min-width:0;}
.class-badge{padding:3px 10px;border-radius:5px;font-size:12px;font-weight:600;white-space:nowrap;max-width:220px;overflow:hidden;text-overflow:ellipsis;}
.class-badge.source{background:#1f3a5f;color:#79c0ff;border:1px solid #2d5a8e;}
.class-badge.target{background:#1a3d2b;color:#56d364;border:1px solid #238636;}
.arrow-icon{color:var(--text2);font-size:14px;flex-shrink:0;}
.metrics-mini{display:flex;gap:6px;flex-wrap:wrap;flex-shrink:0;}
.metric-pill{display:flex;flex-direction:column;align-items:center;background:var(--surface2);border:1px solid var(--border);border-radius:6px;padding:3px 8px;min-width:50px;}
.metric-pill .val{font-size:12px;font-weight:700;color:var(--text);}
.metric-pill .lbl{font-size:9px;color:var(--text2);text-transform:uppercase;}
.metric-pill.score .val{color:var(--green);}
.metric-pill.rank-m .val{color:var(--accent);}
.metric-pill.cochange .val{color:var(--orange);}
.toggle-icon{color:var(--text2);font-size:12px;transition:transform .2s;flex-shrink:0;}
.card.open .toggle-icon{transform:rotate(180deg);}
.card-body{display:none;padding:16px 18px;border-top:1px solid var(--border);}
.card.open .card-body{display:block;}
.path-section{margin-bottom:14px;}
.path-section h4{font-size:11px;color:var(--text2);text-transform:uppercase;letter-spacing:.05em;margin-bottom:6px;}
.path-text{font-size:12px;color:var(--accent);word-break:break-all;font-family:monospace;}
.coupling-section{margin-bottom:14px;}
.coupling-section h4{font-size:11px;color:var(--text2);text-transform:uppercase;letter-spacing:.05em;margin-bottom:6px;}
.coupling-tags{display:flex;flex-wrap:wrap;gap:5px;}
.coupling-tag{background:var(--surface2);border:1px solid var(--border);border-radius:4px;padding:2px 8px;font-size:10px;color:var(--text);}
.none-text{color:var(--text2);font-size:12px;font-style:italic;}
.meta-small{margin-top:12px;font-size:11px;color:var(--text2);}
.meta-small code{background:var(--surface2);padding:1px 5px;border-radius:3px;font-size:11px;color:var(--text);}

/* validation */
.validation-section{margin-top:16px;background:var(--surface2);border:1px solid var(--border);border-radius:8px;padding:14px;}
.validation-section h4{font-size:12px;color:var(--text2);margin-bottom:10px;text-transform:uppercase;letter-spacing:.05em;}
.vote-buttons{display:flex;gap:8px;margin-bottom:12px;flex-wrap:wrap;}
.vote-btn{padding:7px 16px;border-radius:7px;border:1px solid var(--border);background:var(--surface);color:var(--text);cursor:pointer;font-size:12px;font-weight:600;transition:all .15s;}
.vote-btn:hover{border-color:var(--accent);}
.vote-btn.correct.selected{background:#1a3d2b;border-color:#3fb950;color:#3fb950;}
.vote-btn.incorrect.selected{background:#3d1a1a;border-color:#f85149;color:#f85149;}
.vote-btn.unsure.selected{background:#3d2e1a;border-color:#e3b341;color:#e3b341;}
.validation-textarea{background:var(--bg);border:1px solid var(--border);border-radius:6px;padding:7px 10px;color:var(--text);font-size:12px;width:100%;font-family:inherit;resize:vertical;min-height:60px;}
.validation-textarea:focus{outline:none;border-color:var(--accent);}
.header-email-wrap{display:flex;flex-direction:column;gap:3px;}
.header-email-wrap label{font-size:11px;color:var(--text2);}
.header-email-input{background:var(--surface2);border:1px solid var(--border);border-radius:6px;padding:7px 12px;color:var(--text);font-size:13px;width:240px;font-family:inherit;}
.header-email-input:focus{outline:none;border-color:var(--accent);}
.header-email-input.invalid{border-color:var(--red);}
.submit-row{display:flex;justify-content:flex-end;align-items:center;gap:10px;margin-top:8px;}
.submit-btn{padding:7px 18px;border-radius:7px;border:none;background:var(--accent);color:#0d1117;font-weight:700;font-size:12px;cursor:pointer;}
.submit-btn:disabled{opacity:.4;cursor:default;}
.submit-btn:not(:disabled):hover{background:#79c0ff;}
.submit-status{font-size:12px;color:var(--green);}
.progress-bar-wrap{background:var(--surface2);border-radius:4px;height:6px;margin:16px 0 4px;overflow:hidden;}
.progress-bar{height:100%;background:var(--accent);border-radius:4px;transition:width .4s;}
.progress-label{font-size:11px;color:var(--text2);text-align:right;}
"""

# ─── JS for detail pages ─────────────────────────────────────────────────────
DETAIL_JS = r"""
const REPO = '__REPO__';
const SRC  = '__SRC__';
const TOTAL_CARDS = __TOTAL__;

function selectVote(id, vote, btn) {
  document.querySelectorAll('#validation_' + id + ' .vote-btn').forEach(b => b.classList.remove('selected'));
  btn.classList.add('selected');
  document.getElementById('vote_' + id).value = vote;
  document.getElementById('submitBtn_' + id).disabled = false;
}

function submitVote(id) {
  const vote    = document.getElementById('vote_' + id).value;
  const email   = document.getElementById('globalEmail').value.trim();
  const comment = document.getElementById('comment_'+ id).value.trim();
  if (!email || !email.includes('@')) {
    document.getElementById('globalEmail').classList.add('invalid');
    document.getElementById('globalEmail').focus();
    return;
  }
  document.getElementById('globalEmail').classList.remove('invalid');
  const repo   = document.getElementById('meta_repo_'    + id).value;
  const source = document.getElementById('meta_source_'  + id).value;
  const target = document.getElementById('meta_target_'  + id).value;
  const rank   = document.getElementById('meta_rank_'    + id).value;
  const score  = document.getElementById('meta_score_'   + id).value;
  const coch   = document.getElementById('meta_cochange_'+ id).value;
  const dist   = document.getElementById('meta_distance_'+ id).value;
  const key = 'vote_' + repo + '__' + id;
  localStorage.setItem('globalEmail', email);
  localStorage.setItem(key, JSON.stringify({
    Vote: vote, Email: email, Comment: comment,
    Repository: repo, Source: source, Target: target,
    Rank: rank, Score: score, CoChange: coch, Distance: dist,
    Timestamp: new Date().toISOString()
  }));
  const st = document.getElementById('status_' + id);
  st.textContent = '✓ Saved!';
  st.style.display = 'inline';
  setTimeout(() => { st.style.display = 'none'; }, 2500);
  updateProgress();
}

function updateProgress() {
  let done = 0;
  document.querySelectorAll('.validation-section').forEach(sec => {
    const id = sec.id.replace('validation_', '');
    if (localStorage.getItem('vote_' + REPO + '__' + id)) done++;
  });
  const pct = TOTAL_CARDS ? Math.round(done / TOTAL_CARDS * 100) : 0;
  const bar = document.getElementById('progressBar');
  const lbl = document.getElementById('progressLabel');
  if (bar) bar.style.width = pct + '%';
  if (lbl) lbl.textContent = done + ' / ' + TOTAL_CARDS + ' validated (' + pct + '%)';
}

function exportCSV() {
  const rows = [['Repository','Source','Target','Rank','Score','CoChange','Distance','Vote','Email','Comment','Timestamp']];
  document.querySelectorAll('.card').forEach(card => {
    const id = card.dataset.cardid;
    const saved = localStorage.getItem('vote_' + REPO + '__' + id);
    const v = saved ? JSON.parse(saved) : {};
    rows.push([
      card.dataset.repo||REPO, card.dataset.source||'', card.dataset.target||'',
      card.dataset.rank||'', card.dataset.score||'', card.dataset.cochange||'',
      card.dataset.distance||'', v.Vote||'', v.Email||'',
      v.Comment||'', v.Timestamp||''
    ]);
  });
  const csv = rows.map(r => r.map(c => '"' + String(c).replace(/"/g,'""') + '"').join(',')).join('\n');
  const blob = new Blob([csv], {type:'text/csv;charset=utf-8;'});
  const a = document.createElement('a'); a.href = URL.createObjectURL(blob);
  a.download = 'votes_' + REPO + '_' + SRC.replace(/[^a-zA-Z0-9]/g,'_') + '.csv';
  a.click();
}

document.addEventListener('DOMContentLoaded', () => {
  // restore global email
  const savedEmail = localStorage.getItem('globalEmail') || '';
  if (savedEmail) document.getElementById('globalEmail').value = savedEmail;
  // restore saved votes UI
  document.querySelectorAll('.validation-section').forEach(sec => {
    const id = sec.id.replace('validation_', '');
    const saved = localStorage.getItem('vote_' + REPO + '__' + id);
    if (!saved) return;
    const v = JSON.parse(saved);
    if (v.Vote) {
      const btn = sec.querySelector('.vote-btn.' + v.Vote);
      if (btn) { btn.classList.add('selected'); }
      document.getElementById('submitBtn_' + id).disabled = false;
      document.getElementById('vote_' + id).value = v.Vote;
    }
    if (v.Comment) document.getElementById('comment_'+ id).value = v.Comment;
  });
  updateProgress();
});
"""

# ─── helpers ─────────────────────────────────────────────────────────────────
def short_name(full):
    """Last segment of a dotted class name."""
    return full.split('.')[-1] if full and full != 'NONE' else full

def make_card_html(repo, src_name, rank_str, target, score, cochange, distance, path_text, coupling_text, card_uid):
    """Generate one card div (minified)."""
    rank_num = rank_str.lstrip('#')
    cochange_display = cochange if cochange not in ('', '-1', None) else 'NONE'
    src_short = short_name(src_name)
    tgt_short = short_name(target)

    # path section
    if path_text and path_text not in ('—', '-', 'NONE', ''):
        path_html = f'<div class="path-section"><h4>Propagation Path</h4><div class="path-text">{htmllib.escape(path_text)}</div></div>'
    else:
        path_html = '<div class="path-section"><span class="none-text">Path: NONE — no path between source and target</span></div>'

    # coupling section
    if coupling_text and coupling_text not in ('—', '-', 'NONE', ''):
        tags = ''.join(f'<span class="coupling-tag">{htmllib.escape(t.strip())}</span>' for t in coupling_text.split(',') if t.strip())
        coupling_html = f'<div class="coupling-section"><h4>Coupling Types on Path</h4><div class="coupling-tags">{tags}</div></div>'
    else:
        coupling_html = '<div class="coupling-section"><h4>Coupling Types on Path</h4><span class="none-text">NONE</span></div>'

    meta_html = (f'<div class="meta-small"><div><strong>Source:</strong> <code>{htmllib.escape(src_name)}</code></div>'
                 f'<div><strong>Target:</strong> <code>{htmllib.escape(target)}</code></div></div>')

    val_html = f"""<div class="validation-section" id="validation_{card_uid}">
<h4>📋 Validation — Is this propagation correct?</h4>
<div class="vote-buttons">
<button class="vote-btn correct" onclick="selectVote('{card_uid}','correct',this)">✅ Correct</button>
<button class="vote-btn incorrect" onclick="selectVote('{card_uid}','incorrect',this)">❌ Incorrect</button>
<button class="vote-btn unsure" onclick="selectVote('{card_uid}','unsure',this)">❓ Unsure</button>
</div>
<textarea class="validation-textarea" id="comment_{card_uid}" placeholder="Optional comment..."></textarea>
<div class="submit-row">
<button class="submit-btn" id="submitBtn_{card_uid}" onclick="submitVote('{card_uid}')" disabled>Submit</button>
<span class="submit-status" id="status_{card_uid}" style="display:none"></span>
</div>
<input type="hidden" id="vote_{card_uid}" value="">
<input type="hidden" id="meta_repo_{card_uid}" value="{htmllib.escape(repo)}">
<input type="hidden" id="meta_source_{card_uid}" value="{htmllib.escape(src_name)}">
<input type="hidden" id="meta_target_{card_uid}" value="{htmllib.escape(target)}">
<input type="hidden" id="meta_rank_{card_uid}" value="{rank_num}">
<input type="hidden" id="meta_score_{card_uid}" value="{score}">
<input type="hidden" id="meta_cochange_{card_uid}" value="{cochange_display}">
<input type="hidden" id="meta_distance_{card_uid}" value="{distance}">
</div>"""

    card = (f'<div class="card" data-cardid="{card_uid}" data-repo="{htmllib.escape(repo)}" '
            f'data-source="{htmllib.escape(src_name)}" data-target="{htmllib.escape(target)}" '
            f'data-score="{score}" data-cochange="{cochange_display}" data-distance="{distance}" data-rank="{rank_num}">'
            f'<div class="card-header" onclick="this.parentElement.classList.toggle(\'open\')">'
            f'<div class="source-target">'
            f'<span class="class-badge source" title="{htmllib.escape(src_name)}">{htmllib.escape(src_short)}</span>'
            f'<span class="arrow-icon">→</span>'
            f'<span class="class-badge target" title="{htmllib.escape(target)}">{htmllib.escape(tgt_short)}</span>'
            f'</div>'
            f'<div class="metrics-mini">'
            f'<div class="metric-pill rank-m"><span class="val">#{rank_num}</span><span class="lbl">Rank</span></div>'
            f'<div class="metric-pill score"><span class="val">{score}</span><span class="lbl">Score</span></div>'
            f'<div class="metric-pill cochange"><span class="val">{htmllib.escape(cochange_display)}</span><span class="lbl">Co-change</span></div>'
            f'<div class="metric-pill dist"><span class="val">{distance}</span><span class="lbl">Distance</span></div>'
            f'</div>'
            f'<span class="toggle-icon">▼</span>'
            f'</div>'
            f'<div class="card-body">{path_html}{coupling_html}{meta_html}{val_html}</div>'
            f'</div>')
    return card


def make_detail_page(repo, src_name, src_idx, cards_html_list, back_file):
    total = len(cards_html_list)
    js = (DETAIL_JS
          .replace('__REPO__', repo)
          .replace('__SRC__',  src_name.replace("'", "\\'"))
          .replace('__TOTAL__', str(total)))
    cards_joined = '\n'.join(cards_html_list)
    page = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1.0">
<title>{htmllib.escape(repo)} — {htmllib.escape(src_name)}</title>
<style>{DETAIL_CSS}</style>
</head>
<body>
<div class="page-header">
  <a class="back-btn" href="../{back_file}">← Back</a>
  <div>
    <div class="src-label">Source class</div>
    <div class="src-name-h">{htmllib.escape(src_name)}</div>
  </div>
  <div style="flex:1"></div>
  <div class="header-email-wrap">
    <label for="globalEmail">✉️ Your email <span style="color:var(--red)">*</span></label>
    <input type="email" class="header-email-input" id="globalEmail" placeholder="your@email.com" oninput="localStorage.setItem('globalEmail',this.value);this.classList.remove('invalid')">
  </div>
  <button onclick="exportCSV()" style="padding:7px 14px;border-radius:6px;border:1px solid var(--border);background:var(--surface2);color:var(--text);cursor:pointer;font-size:12px;">📥 Export CSV</button>
</div>
<div class="container">
  <div class="progress-bar-wrap"><div class="progress-bar" id="progressBar" style="width:0%"></div></div>
  <div class="progress-label" id="progressLabel">0 / {total} validated</div>
  <div class="cards-list" style="margin-top:16px;">
{cards_joined}
  </div>
</div>
<script>{js}</script>
</body>
</html>"""
    return page


# ─── main parser ─────────────────────────────────────────────────────────────
def parse_and_split(html_file):
    path = Path(html_file)
    repo_slug = path.stem.replace('repo_', '')  # e.g. 0x727_BypassPro
    back_file = path.name

    with open(path, 'rb') as f:
        raw = f.read().decode('utf-8', errors='replace')

    # Extract all src-blocks
    src_blocks = re.split(r'(?=<div class="src-block")', raw)

    # Find the part before first src-block and after last
    # We'll rebuild the main HTML by finding blocks
    block_pattern = re.compile(
        r'<div class="src-block" id="src_(\d+)">(.*?)</div>\s*</div>\s*(?=<div class="src-block"|<!-- General|</div>\s*\n\s*<!--)',
        re.DOTALL
    )

    # Better: extract src-blocks individually
    block_re = re.compile(
        r'(<div class="src-block" id="src_(\d+)">.*?'
        r'<button class="src-header"[^>]*>.*?'
        r'<span class="src-name">(.*?)</span>.*?'
        r'</button>)'          # end of header
        r'(.*?)'               # body div
        r'(?=<div class="src-block"|<!-- General|</div>\s*\n\s*\n\s*<!--\s*General)',
        re.DOTALL
    )

    # Simpler: split by src-block divs
    # Find each src-block start/end
    src_block_starts = [m.start() for m in re.finditer(r'<div class="src-block"', raw)]

    # Find where accordion section ends (general-section)
    general_start = raw.find('<!-- General analysis -->')
    if general_start == -1:
        general_start = raw.find('<div class="general-section">')

    blocks_region = raw[src_block_starts[0]:general_start] if src_block_starts else ''
    before_blocks = raw[:src_block_starts[0]] if src_block_starts else raw[:general_start]
    after_blocks  = raw[general_start:]

    # Parse each src-block
    single_block_re = re.compile(
        r'<div class="src-block" id="src_(\d+)">\s*'
        r'<button class="src-header"[^>]*>\s*'
        r'<span class="src-name">(.*?)</span>(.*?)</button>\s*'
        r'<div class="src-body"[^>]*>(.*?)</div>\s*</div>',
        re.DOTALL
    )

    new_blocks_html = []
    detail_pages_created = []

    for m in single_block_re.finditer(blocks_region):
        idx       = m.group(1)
        src_name  = m.group(2).strip()
        meta_html = m.group(3)   # badges etc inside the button (includes old chevron)
        body_html = m.group(4)
        # Extract only the badge spans (strip old chevron)
        badges_html = re.sub(r'<span class="chevron"[^>]*>.*?</span>', '', meta_html, flags=re.DOTALL).strip()

        # Extract textarea analysis part (keep it)
        analysis_match = re.search(
            r'<div class="analysis-row">.*?</div>\s*</div>',
            body_html, re.DOTALL
        )
        analysis_block = analysis_match.group(0) if analysis_match else ''
        # Fix: analysis-row ends at the textarea closing, not nested div
        analysis_match2 = re.search(
            r'(<div class="analysis-row">.*?</textarea>\s*</div>)',
            body_html, re.DOTALL
        )
        analysis_block = analysis_match2.group(1) if analysis_match2 else ''

        # Extract rows from affected-table
        rows = []
        row_re = re.compile(
            r'<tr>\s*'
            r'<td class="rank">(.*?)</td>\s*'
            r'<td class="vname">(.*?)</td>\s*'
            r'<td class="score">(.*?)</td>\s*'
            r'<td class="cochange">(.*?)</td>\s*'
            r'<td class="dist">(.*?)</td>\s*'
            r'<td class="path-cell"><span class="path">(.*?)</span><br><span class="coupling">(.*?)</span></td>\s*'
            r'</tr>',
            re.DOTALL
        )
        for rm in row_re.finditer(body_html):
            rows.append({
                'rank':     rm.group(1).strip(),
                'target':   rm.group(2).strip(),
                'score':    rm.group(3).strip(),
                'cochange': rm.group(4).strip(),
                'distance': rm.group(5).strip(),
                'path':     rm.group(6).strip(),
                'coupling': rm.group(7).strip(),
            })

        no_affected = '<p class="no-affected">' in body_html

        # Build cards for detail page
        cards = []
        if no_affected or not rows:
            # No affected: single self-card
            card_uid = f'{repo_slug}__{idx}_0'
            card = make_card_html(repo_slug, src_name, '#1', src_name, '1.0', 'NONE', '0', 'NONE', 'NONE', card_uid)
            cards.append(card)
        else:
            for ci, row in enumerate(rows):
                card_uid = f'{repo_slug}__{idx}_{ci}'
                card = make_card_html(
                    repo_slug, src_name,
                    row['rank'], row['target'], row['score'],
                    row['cochange'], row['distance'],
                    row['path'], row['coupling'],
                    card_uid
                )
                cards.append(card)

        # Write detail page
        detail_fname = f'repo_{repo_slug}__{idx}.html'
        detail_path  = DETAILS_DIR / detail_fname
        detail_html  = make_detail_page(repo_slug, src_name, idx, cards, back_file)
        with open(detail_path, 'w', encoding='utf-8') as f:
            f.write(detail_html)
        detail_pages_created.append(detail_fname)

        # Build new lightweight src-block (no table, just link to detail page)
        # Prefer count from rows (original HTML); fall back to badge "Affected N"
        if rows:
            n_affected = len(rows)
        else:
            badge_m = re.search(r'Affected\s+(\d+)', badges_html)
            n_affected = int(badge_m.group(1)) if badge_m else len(cards)
        detail_link = f'details/{detail_fname}'
        new_body = f'''      <div class="src-body" id="body_{idx}" style="display:none">
        {analysis_block}
        <a class="detail-link" href="{detail_link}" target="_blank">
          📋 View {n_affected} affected class{"es" if n_affected != 1 else ""} →
        </a>
      </div>'''

        new_block = f'''    <div class="src-block" id="src_{idx}">
      <button class="src-header" onclick="toggleBlock({idx})">
        <span class="src-name">{htmllib.escape(src_name)}</span>
        <span class="src-meta">{badges_html}</span>
        <span class="chevron" id="chev_{idx}">▶</span>
      </button>
{new_body}
    </div>'''
        new_blocks_html.append(new_block)

    # Add .detail-link CSS to main page <style>
    extra_css = """
.detail-link {
  display:inline-block; margin-top:8px; padding:8px 18px;
  background:var(--surface2); border:1px solid var(--border); border-radius:7px;
  color:var(--accent); font-size:13px; text-decoration:none; font-weight:600;
}
.detail-link:hover { border-color:var(--accent); background:#1f3a5f; }
"""
    new_main = (before_blocks
                + '\n'.join(new_blocks_html) + '\n'
                + after_blocks)
    new_main = new_main.replace('</style>', extra_css + '</style>', 1)

    with open(path, 'w', encoding='utf-8') as f:
        f.write(new_main)

    return len(detail_pages_created), [d for d in detail_pages_created]


# ─── run ─────────────────────────────────────────────────────────────────────
if __name__ == '__main__':
    base = '/home/mivian/workspace/change_impact_analysis'
    files = sorted(glob.glob(f'{base}/repo_*.html'))
    total_details = 0
    for fpath in files:
        size_mb = os.path.getsize(fpath) / 1024 / 1024
        print(f'Processing {Path(fpath).name} ({size_mb:.1f} MB)...', flush=True)
        n, names = parse_and_split(fpath)
        new_size = os.path.getsize(fpath) / 1024 / 1024
        total_details += n
        print(f'  → {n} detail pages created, main now {new_size:.1f} MB')
    print(f'\nDone. Total detail pages: {total_details}')
    print(f'Detail pages in: {DETAILS_DIR}')
