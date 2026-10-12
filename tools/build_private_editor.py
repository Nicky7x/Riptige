#!/usr/bin/env python3
"""Builds a personal, offline HTML editor with local collision resources preloaded.

Reads only the user's original APF/XAPK. NEVER commit the generated HTML:
its embedded game resources belong to the game publisher.

python tools/build_private_editor.py --source /sdcard/Download/game.xapk --out /sdcard/Download/riptide-pessoal.html
"""
from __future__ import annotations
import argparse
import base64
import gzip
import json
import sys
from pathlib import Path
from export_collision import local_apf, decode_mesh_header
from inspect_xapk import parse_apf_index, decompress_payload

ROOT = Path(__file__).resolve().parents[1]
PREFIX = 'VuCollisionMeshAsset/Level/'

def build(source: Path, out: Path) -> dict:
    bundles: dict[str, dict] = {}
    errors=[]
    with local_apf(source) as apf:
        _, rows = parse_apf_index(apf)
        with apf.open('rb') as stream:
            for item in rows:
                if not item['name'].startswith(PREFIX):continue
                if item['usize'] > 64*1024*1024:
                    errors.append([item['name'],'too large']);continue
                try:
                    stream.seek(item['offset'])
                    content, _codec, _eof = decompress_payload(stream.read(item['csize']),item['usize'])
                    layout=decode_mesh_header(content)
                except Exception as err:
                    errors.append([item['name'],str(err)])
                    continue
                rest=item['name'][len(PREFIX):]
                arena, _, section=rest.partition('/')
                if not section:continue
                # deterministic gzip supports a single HTML under a few megabytes
                blob=base64.b64encode(gzip.compress(content,compresslevel=9,mtime=0)).decode('ascii')
                bundles.setdefault(arena,{})[section]={
                    'blob':blob,'size':len(content),'vertices':layout['vertices'],
                    'triangles':layout['triangles'],'source':item['name']}
    base=(ROOT/'web/index.html').read_text(encoding='utf-8')
    core=(ROOT/'web/collision_core.js').read_text(encoding='utf-8')
    app=(ROOT/'web/app.js').read_text(encoding='utf-8')
    if 'window.RiptideEditor=' not in app:
        raise RuntimeError('web/app.js lacks RiptideEditor API')
    panel='''<section class="panel section" id="bundled"><h2>01 · Arenas embutidas</h2>
    <p>Os recursos já vêm incluídos neste arquivo pessoal. Escolha a arena e o trecho; nenhuma seleção de arquivos.</p>
    <label style="margin-top:12px" for="arena-select">Arena</label>
    <select id="arena-select"></select>
    <label style="margin-top:11px" for="zone-select">Trecho / malha de colisão</label>
    <select id="zone-select"></select>
    <div class="stats"><div class="stat"><span class="muted">Arenas</span><b id="arena-count">—</b></div>
    <div class="stat"><span class="muted">Malhas</span><b id="mesh-count">—</b></div>
    <div class="stat"><span class="muted">Trechos alterados</span><b id="patch-count">0</b></div></div>
    <h2 style="margin-top:16px">Deslocamento rápido</h2>
    <p>Move todos os vértices da <strong>malha selecionada</strong>. Não altera texturas nem os pontos da IA.</p>
    <div class="positions" style="margin-top:10px">
    <div><label for="bulk-x">Mover X</label><input id="bulk-x" type="number" step="0.1" value="0"></div>
    <div><label for="bulk-y">Mover Y</label><input id="bulk-y" type="number" step="0.1" value="0"></div>
    <div><label for="bulk-z">Mover Z</label><input id="bulk-z" type="number" step="0.1" value="1"></div></div>
    <div class="buttonrow" style="margin-top:11px"><button id="bulk-apply" class="primary">Mover malha inteira</button><button id="bundle-export">Exportar alterações de todas as arenas</button></div>
    <p id="bundle-message" class="muted" style="margin-top:10px">Versão pessoal. Arquivos proprietários não devem ser publicados.</p></section>'''
    base=base.replace('<aside class="sidebar">','<aside class="sidebar">\n'+panel)
    # no user uploads requested in the personal variant
    base=base.replace('<div class="panel section"><h2>01 · Abrir malha</h2>', '<div class="panel section" style="display:none"><h2>01 · Abrir malha</h2>')
    base=base.replace('Carregue uma malha .bin local','Selecione uma arena no painel')
    base=base.replace('Escolha um <code>.bin</code> extraído do seu próprio APF','Os dados estão incorporados nesta versão pessoal')
    base=base.replace('<h1>Riptide Map Lab <span', '<h1>Riptide Map Lab Pessoal <span')
    base=base.replace('Editor experimental de vértices de colisão · 100% local','Arenas já carregadas · editor experimental de colisões · 100% offline')
    base=base.replace('Nenhum arquivo é enviado à internet.', 'Recursos originais estão embutidos SOMENTE nesta cópia pessoal. Não publique esta página.')
    base=base.replace('<script src="collision_core.js"></script><script src="app.js"></script>',
        '<script>\n'+core+'\n</script><script>\n'+app+'\n</script>\n'+
        '<script id="private-assets" type="application/json">'+json.dumps(bundles,separators=(',',':'))+'</script>\n'+
        '<script>\n'+(ROOT/'web/bundle_loader.js').read_text(encoding='utf-8')+'\n</script>')
    # Hide the file import from this personal build; no remote libraries or scripts
    if '<script src=' in base:
        raise RuntimeError('generated HTML has external script dependencies')
    out.parent.mkdir(parents=True,exist_ok=True)
    out.write_text(base, encoding='utf-8')
    return {'arenas':len(bundles),'meshes':sum(len(a) for a in bundles.values()),
            'skipped':errors,'html_bytes':out.stat().st_size,'out':str(out)}

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--source',type=Path,required=True)
    p.add_argument('--out',type=Path,required=True)
    args=p.parse_args()
    print(json.dumps(build(args.source,args.out),indent=2,ensure_ascii=False))