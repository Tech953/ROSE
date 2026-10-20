"""Read-only live HTTP verification of source routes and whitelist boundaries."""
from pathlib import Path
import hashlib
import json
import sys
import threading
import urllib.error
import urllib.request

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
import server
import biomes

http=server.ThreadingHTTPServer(('127.0.0.1',0),server.Handler)
worker=threading.Thread(target=http.serve_forever,daemon=True)
worker.start()
base=f'http://127.0.0.1:{http.server_address[1]}'
checks=[]
try:
    routes={'/lore-transport.html':ROOT/'static/lore-transport.html',
            '/lore-transport-catalog.json':ROOT/'reference/lore-transport/catalog.json',
            '/lore-transport-guide.txt':ROOT/'docs/LORE-TRANSPORT-INTEGRATION.md'}
    if (ROOT/'docs/WEATHER-RESPONSE-GUIDE.md').is_file():
        routes['/weather-response-guide.txt']=ROOT/'docs/WEATHER-RESPONSE-GUIDE.md'
        routes['/weather.js']=ROOT/'static/weather.js'
    for i,ref in enumerate(biomes.RECORD['visual_references']):
        routes[f'/lore-transport-image-{i}.png']=ROOT/'reference/lore-transport'/ref['file']
    for route,path in routes.items():
        with urllib.request.urlopen(base+route,timeout=5) as response:
            data=response.read()
            assert response.status==200
            assert data==path.read_bytes(),route
            assert response.headers['X-Content-Type-Options']=='nosniff'
            assert "default-src 'self'" in response.headers['Content-Security-Policy']
            checks.append(dict(route=route,status='PASS',bytes=len(data),sha256=hashlib.sha256(data).hexdigest()))
    with urllib.request.urlopen(base+'/health',timeout=5) as response:
        assert json.load(response)['version']==server.world.VERSION
    with urllib.request.urlopen(base+'/',timeout=5) as response:
        assert b'href="/lore-transport.html"' in response.read()
    for route in ['/lore-transport-image-99.png','/lore-transport/../engine.py','/lore-transport.html?file=engine.py']:
        try:
            urllib.request.urlopen(base+route,timeout=5)
        except urllib.error.HTTPError as error:
            assert error.code==404
            checks.append(dict(route=route,status='PASS',response=404))
        else:
            raise AssertionError('Unexpected public source route: '+route)
finally:
    http.shutdown()
    http.server_close()
    worker.join(2)

report=dict(engine_version=server.world.VERSION,status='PASS',routes=checks,health='PASS',atlas_link='PASS')
tag='v'+''.join(server.world.VERSION.split('.')[:2])
(ROOT/('docs/lore-transport-http-'+tag+'.json')).write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(dict(status='PASS',positive_source_routes=len(routes),rejected_routes=3,health='PASS',atlas_link='PASS')))
