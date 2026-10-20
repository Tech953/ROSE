"""Build the static archive from its reviewed catalog; runtime needs no image library."""
from pathlib import Path
import html
import json

ROOT=Path(__file__).resolve().parents[1]
CATEGORIES={'architecture':'Tower architecture','combat':'Combat scenarios','framework':'Framework concepts',
            'infrastructure':'Infrastructure and transit','products':'Products and materials','regions':'Named biome studies',
            'reported_landscapes':'Reported landscapes','unassigned':'Unassigned studies'}
esc=html.escape
def listing(values):return '<ul>'+''.join('<li>'+esc(v)+'</li>' for v in values)+'</ul>'

def build():
    d=json.loads((ROOT/'reference/visual-corpus/catalog.json').read_text(encoding='utf-8'));c=d['coverage']
    parts=['<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">'
      '<title>Rose — visual reference archive</title><link rel="stylesheet" href="/style.css"><link rel="stylesheet" href="/visual-references.css">'
      '<script src="/visual-references.js" defer></script></head><body><main class="reference-archive">'
      '<p class="overline">ROSE / VISUAL SOURCE RECORD</p><h1>Materials. Light. Immense scale.</h1>'
      '<p>Reviewed references for the druid / nano / neon spectrum. Search original names, subjects, material notes or variant caveats. '
      'Each image retains its original encoding.</p><p><a href="/">Return to Rose</a> · <a href="/lore-transport.html">Lore archive</a> · '
      '<a href="/visual-reference-catalog.json">Complete source register (JSON)</a> · <a href="/visual-reference-review.txt">Review and production guide</a></p>'
      f'<p class="reference-intake">{c["uploaded_files"]} uploaded names · {c["unique_payloads"]} unique images · {c["duplicate_aliases"]} duplicate aliases · '
      f'{c["previous_pixel_matches"]} pixel matches to recovered references. Complete Designer supplied separately. The earlier ZIP recovery remains partial.</p>'
      '<p>Source variants, schematic scales and unassigned scenes retain their status. Browsing changes no world state. '
      'New unit modeling and directional animation bakes remain production work.</p>'
      '<div id="reference-controls" hidden><div class="reference-filters"><label for="reference-search">Find a reference'
      '<input id="reference-search" type="search" placeholder="Original filename, material, region…"></label>'
      '<label for="reference-category">Subject<select id="reference-category"><option value="">All subjects</option>']
    parts.extend(f'<option value="{k}">{v}</option>' for k,v in CATEGORIES.items())
    parts.append('</select></label></div><p id="reference-count" role="status" aria-live="polite"></p>'
      '<p class="subtle">Preview one original at a time. Full-size links work without JavaScript.</p></div>'
      '<p id="preview-status" class="sr" role="status" aria-live="polite"></p>')
    for r in d['references']:
        i=r['id'];preview=i+'-preview'
        parts.append(f'<article class="reference-card" data-reference="{i}" data-category="{r["category"]}" '
          f'data-width="{r["width"]}" data-height="{r["height"]}"><p class="overline">{CATEGORIES[r["category"]]}</p><h2>{esc(r["title"])}</h2>'
          f'<p class="reference-meta">{esc(r["status"].replace("_"," "))} · {r["width"]} × {r["height"]} · {r["bytes"]/1048576:.2f} MiB</p>'
          f'<p data-observation>{esc(" ".join(r["observed"]))}</p><p><strong>Generation use</strong></p>{listing(r["generation_use"])}'
          f'<details><summary>Original names, provenance and caveats</summary>{listing(r["aliases"])}'
          f'<p>Association: {esc(", ".join(r["profiles"]) or "Unassigned / conceptual")}. Review: {esc(r["review"])}.</p>'
          f'<p><code>SHA256 {r["sha256"]}</code></p>')
        if 'pixel_identical_to' in r:parts.append('<p>Decoded pixels match '+esc(r['pixel_identical_to'])+'; incoming PNG bytes are preserved separately.</p>')
        parts.append(listing(r['constraints']+[d['conflict_register'][k] for k in r['conflicts']]))
        parts.append(f'</details><div class="reference-actions"><a data-original href="{r["url"]}" target="_blank" rel="noopener">Open original image</a>'
          f'<button data-preview hidden type="button" aria-expanded="false" aria-controls="{preview}">Preview image</button></div>'
          f'<div class="reference-preview" id="{preview}"></div></article>')
    parts.append('<p class="subtle">Rose 0.17.1 · Play retains the prepared sprites and authoritative navigation, material and physics systems.</p></main></body></html>')
    (ROOT/'static/visual-references.html').write_text(''.join(parts),encoding='utf-8')

if __name__=='__main__':build()
