"""Démo locale : données enregistrées par défaut, appels live explicites uniquement."""
import html,json,mimetypes,os,secrets,threading
from http.server import BaseHTTPRequestHandler,ThreadingHTTPServer
from pathlib import Path
from .pipeline import ROOT,load_corpus,run_source
from .engine import Client,APIError,load_env
from .report import CSS

PAGE='''<!doctype html><html lang="fr"><meta charset="utf-8"><title>A6 — Démonstration</title><style>CSS</style><main><p>A6 / G15</p><h1>Réécrire sans perdre les faits</h1><p>Choisir un texte et un objectif. Les résultats enregistrés sont accessibles sans clé et sans appel payant. Le bouton « Nouvelle génération » utilise le fournisseur configuré sur ce serveur local.</p><p><a href="/results/rapport.html">Résultats de la campagne</a> · <a href="/results/review.html">Revue humaine</a></p><label>Texte du corpus<select id="source"></select></label><label>Objectif<select id="attr"><option value="longueur">Raccourcir</option><option value="lisibilite">Simplifier</option><option value="registre">Rendre formel</option><option value="ton">Rendre chaleureux</option></select></label><h2>Texte source</h2><p id="original"></p><h3>Faits à conserver</h3><ul id="facts"></ul><button id="recorded">Afficher l’essai enregistré</button> <button id="live">Nouvelle génération (API)</button><p id="status" role="status"></p><div id="outputs"></div><p class="notice">Les scores du juge restent provisoires tant que la revue humaine n’est pas terminée. Une réécriture réussie doit atteindre l’objectif et conserver les faits.</p></main><script>
const token='TOKEN';let corpus=[],records=[];const el=id=>document.getElementById(id);const esc=s=>String(s).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
function update(){const x=corpus[Number(el('source').value)];el('original').textContent=x.source;el('facts').innerHTML=x.facts.map(f=>'<li>'+esc(f.text)+'</li>').join('');el('outputs').innerHTML=''}
function display(rows){el('outputs').innerHTML=rows.filter(r=>r.attribute===el('attr').value).map(r=>`<section><h2>${r.method==='baseline'?'Consigne simple':'Consigne structurée'}</h2><p>${esc(r.text||r.error||'Pas de sortie')}</p><p>${esc(r.judgment?.reason||'')}</p><p>Objectif atteint : ${r.metrics?.attribute_success??'non évalué'} / Faits conservés : ${r.metrics?.meaning_preserved??'non évalué'} / Réussite conjointe estimée : ${r.metrics?.joint_success_estimate??'non évalué'}</p></section>`).join('')}
fetch('/api/data').then(r=>r.json()).then(d=>{corpus=d.corpus;records=d.records;el('source').innerHTML=corpus.map((s,i)=>`<option value="${i}">${s.id} — ${esc(s.domain)}</option>`).join('');update()}).catch(()=>el('status').textContent='Impossible de charger les données locales.');
el('source').onchange=update;el('recorded').onclick=()=>{const id=corpus[Number(el('source').value)].id;display(records.filter(r=>r.source_id===id));el('status').textContent='Résultats enregistrés de la campagne ; aucun nouvel appel API.'};
el('live').onclick=async()=>{el('live').disabled=true;el('status').textContent='Appels au modèle en cours…';try{const r=await fetch('/api/run',{method:'POST',headers:{'Content-Type':'application/json','X-A6-Token':token},body:JSON.stringify({index:Number(el('source').value)})});const d=await r.json();if(!r.ok)throw new Error(d.error);display(d.records);el('status').textContent='Appel réel. Les réponses identiques déjà calculées peuvent venir du cache. Coût mesuré/réservé de cette session : '+d.cost+' USD.'}catch(e){el('status').textContent=e.message}finally{el('live').disabled=false}};
</script></html>'''

def serve(port=8765):
    if not 1024<=port<=65535:raise ValueError('Port hors plage')
    token=secrets.token_urlsafe(24);client=None;lock=threading.Lock()
    class Handler(BaseHTTPRequestHandler):
        def log_message(self,*args):pass
        def send(self,status,body,kind='application/json'):
            if not isinstance(body,bytes):body=(json.dumps(body,ensure_ascii=False) if kind=='application/json' else body).encode()
            self.send_response(status);self.send_header('Content-Type',kind+'; charset=utf-8');self.send_header('X-Content-Type-Options','nosniff');self.send_header('Cache-Control','no-store');self.end_headers();self.wfile.write(body)
        def do_GET(self):
            if self.path=='/':return self.send(200,PAGE.replace('CSS',CSS).replace('TOKEN',token),'text/html')
            if self.path=='/api/data':
                p=ROOT/'results/benchmark.json';r=json.loads(p.read_text()) if p.exists() else {'records':[]}
                return self.send(200,{'corpus':load_corpus(),'records':r['records']})
            if self.path.startswith('/results/'):
                allowed={'rapport.html','review.html','benchmark.json','rapport.json','annotation_template.csv'}
                name=self.path.split('/')[-1]
                if name not in allowed:return self.send(404,{'error':'Fichier indisponible'})
                p=ROOT/'results'/name
                if p.exists():return self.send(200,p.read_bytes(),mimetypes.guess_type(name)[0] or 'application/octet-stream')
            self.send(404,{'error':'Page inconnue'})
        def do_POST(self):
            nonlocal client
            if self.path!='/api/run' or self.headers.get('X-A6-Token')!=token:return self.send(403,{'error':'Requête non autorisée'})
            length=int(self.headers.get('Content-Length','0'))
            if not 0<length<2048:return self.send(400,{'error':'Requête invalide'})
            try:
                data=json.loads(self.rfile.read(length));i=data.get('index');corpus=load_corpus()
                if type(i) is not int or not 0<=i<len(corpus):return self.send(400,{'error':'Texte inconnu'})
                with lock:
                    if client is None:
                        load_env(ROOT/'.env');client=Client(ROOT/'.cache',budget=1.)
                    result=run_source(corpus[i],client,os.getenv('GENERATOR_MODEL','qwen/qwen3.8-flash'),os.getenv('JUDGE_MODEL','deepseek/deepseek-v4.1-flash'))
                self.send(200,{'records':result,'cost':round(client.cost,6)})
            except (APIError,ValueError) as e:self.send(400,{'error':str(e)})
            except Exception:self.send(500,{'error':'Erreur interne ; aucun résultat inventé.'})
    server=ThreadingHTTPServer(('127.0.0.1',port),Handler)
    print(f'Démo locale : http://127.0.0.1:{port} (Ctrl+C pour arrêter)',flush=True)
    try:server.serve_forever()
    except KeyboardInterrupt:server.server_close()
