"""Rapports reproductibles et revue humaine, lisibles sans service externe."""
import csv,html,json,random,statistics
from pathlib import Path
from .metrics import ATTRIBUTES

def paired_interval(rows,attribute,rounds=2000):
    pairs={}
    for r in rows:
        if r['attribute']==attribute:pairs.setdefault(r['source_id'],{})[r['method']]=int(r.get('metrics',{}).get('joint_success_estimate',False))
    differences=[p['structuree']-p['baseline'] for p in pairs.values() if set(p)=={'baseline','structuree'}]
    if not differences:return None
    rng=random.Random(20261027);means=sorted(sum(rng.choice(differences) for _ in differences)/len(differences) for _ in range(rounds))
    return dict(n_pairs=len(differences),delta_pp=round(statistics.mean(differences)*100,2),ci95_pp=[round(means[int(rounds*.025)]*100,2),round(means[int(rounds*.975)]*100,2)])

def summarize(result):
    rows=result['records'];out=[]
    for split in ('dev','test'):
        for attr in ATTRIBUTES:
            for method in ('baseline','structuree'):
                sub=[r for r in rows if r['split']==split and r['attribute']==attr and r['method']==method]
                evaluated=[r for r in sub if r['status']=='evaluated'];n=len(sub)
                vals=lambda field:[r['metrics'][field] for r in evaluated if r['metrics'].get(field) is not None]
                avg=lambda field:round(statistics.mean(vals(field)),4) if vals(field) else None
                count=lambda field:sum(bool(r.get('metrics',{}).get(field)) for r in sub)
                drift=sum(r['metrics'].get('factual_drift_estimate') is True for r in evaluated)
                out.append(dict(split=split,attribute=attr,method=method,n=n,n_evaluated=len(evaluated),
                    attribute_success=count('attribute_success'),joint_success_estimate=count('joint_success_estimate'),
                    joint_rate_estimate=round(count('joint_success_estimate')/n,4) if n else None,
                    factual_drift_estimated=drift,factual_drift_denominator=len(evaluated),
                    target_gap_mean=avg('target_gap'),semantic_judge_mean=avg('judge_semantic_similarity'),
                    semantic_cosine_mean=avg('semantic_cosine'),word_ratio_mean=avg('word_ratio')))
    consistency=0
    for sid in {r['source_id'] for r in rows}:
        judged=[r.get('judgment',{}) for r in rows if r['source_id']==sid and r['status']=='evaluated']
        if judged and (len({j['source_formality'] for j in judged})>1 or len({j['source_warmth'] for j in judged})>1):consistency+=1
    return {'groups':out,'paired_bootstrap_test':{a:paired_interval([r for r in rows if r['split']=='test'],a) for a in ATTRIBUTES},
        'source_style_scores_inconsistent_count':consistency,'human_validation':'pending',
        'warning':'Taux conjoints provisoires : juge IA non validé sur annotations humaines indépendantes.'}

CSS='''body{font-family:system-ui,sans-serif;margin:0;color:#20252c;background:#f6f4f1}main{max-width:1140px;margin:auto;padding:32px}h1{font-size:36px;line-height:1.1}h2{margin-top:34px}p,li{line-height:1.6}.notice{background:#fff0cf;border-left:5px solid #9e6700;padding:16px}table{border-collapse:collapse;width:100%;background:white;font-size:14px}td,th{padding:12px;border-bottom:1px solid #ddd;text-align:left}th{background:#244f4b;color:white}details{background:white;border-bottom:1px solid #ddd;padding:15px}summary{cursor:pointer;font-weight:600}pre{white-space:pre-wrap;font:inherit;line-height:1.5}button,select,input,textarea{font:inherit;padding:10px;border:1px solid #aaa;border-radius:4px}button{background:#244f4b;color:white;cursor:pointer}textarea{width:96%;min-height:100px}label{display:block;margin:14px 0 5px}a{color:#205c58}.tag{color:#555;font-size:14px}.grid{display:grid;grid-template-columns:1fr 1fr;gap:20px}@media(max-width:700px){.grid{display:block}main{padding:16px}table{font-size:11px}td,th{padding:6px}}'''

def render_report(result,path):
    e=html.escape;s=summarize(result);Path(path).with_suffix('.json').write_text(json.dumps(s,ensure_ascii=False,indent=2))
    header=f'''<!doctype html><html lang="fr"><meta charset="utf-8"><title>A6 — Résultats G15</title><style>{CSS}</style><main><p class="tag">A6 / G15 / Campagne réelle enregistrée</p><h1>Changer le style,<br>conserver les informations</h1><p>Comparaison d’une consigne simple et d’une consigne structurée sur {result['corpus_size']} textes synthétiques et quatre objectifs indépendants.</p><div class="notice"><strong>Résultats provisoires.</strong> Les scores de ton, de registre et de fidélité viennent d’un juge IA. La validation humaine indépendante reste à faire. La similarité affichée est une estimation du juge, pas une similarité cosinus d’embeddings.</div><p>Générateur : {e(result['generator'])}. Juge : {e(result['judge'])}. {result['live_calls_this_run']} appels de cette exécution ; {result['cache_hits']} réponses réutilisées du cache. Coût de cette exécution mesuré ou réservé : {result['cost_measured_or_reserved_usd']:.4f} USD. Les coûts des essais préalables sont indiqués dans le journal de campagne.</p><p><a href="review.html">Ouvrir les 16 cas à annoter</a> · <a href="benchmark.json">Données détaillées JSON</a></p><h2>Évaluation sur les textes réservés au test</h2><p>Un succès conjoint exige l’attribut atteint, tous les faits conservés, aucun ajout et une similarité jugée d’au moins 0,85. Les échecs API restent dans le dénominateur du succès conjoint.</p><table><tr><th>Objectif</th><th>Méthode</th><th>Évalués</th><th>Attribut atteint</th><th>Succès conjoint estimé</th><th>Dérive estimée*</th><th>Écart moyen cible</th></tr>'''
    body=''
    for g in s['groups']:
        if g['split']!='test':continue
        gap='—' if g['target_gap_mean'] is None else str(round(g['target_gap_mean'],2))
        body+=f"<tr><td>{e(g['attribute'])}</td><td>{e(g['method'])}</td><td>{g['n_evaluated']}/{g['n']}</td><td>{g['attribute_success']}/{g['n']}</td><td>{g['joint_success_estimate']}/{g['n']}</td><td>{g['factual_drift_estimated']}/{g['factual_drift_denominator']}</td><td>{gap}</td></tr>"
    body+='</table><p class="tag">* Dérive = omission, contradiction, ajout factuel ou variation des nombres. Dénominateur : réponses évaluées. Écart : ratio de mots pour longueur, points de Flesch pour lisibilité, points de l’échelle du juge pour registre/ton. Ces unités ne se comparent pas entre objectifs.</p><h2>Différence appariée entre méthodes</h2><p>Écart du taux conjoint estimé, consigne structurée moins consigne simple ; intervalle bootstrap par texte (2 000 rééchantillonnages). Il ne tient pas compte des erreurs possibles du juge.</p><ul>'
    for a,v in s['paired_bootstrap_test'].items():
        if v:body+=f"<li>{a} : {v['delta_pp']:+.1f} points, intervalle descriptif à 95 % [{v['ci95_pp'][0]:.1f} ; {v['ci95_pp'][1]:.1f}].</li>"
    body+='</ul><h2>Examiner chaque résultat</h2><p>Les cas défavorables sont conservés. Filtrer la page avec la recherche du navigateur.</p>'
    for r in sorted(result['records'],key=lambda r:(r.get('metrics',{}).get('joint_success_estimate',False),r['source_id'],r['method'],r['attribute'])):
        m=r.get('metrics',{});j=r.get('judgment',{});status='succès conjoint estimé' if m.get('joint_success_estimate') else 'objectif ou fidélité non validé'
        body+=f'''<details><summary>{r['source_id']} / {e(r['method'])} / {r['attribute']} / {status}</summary><div class="grid"><section><h3>Source</h3><p>{e(r['source'])}</p><h4>Faits de référence</h4><ul>{''.join('<li>'+e(f['id']+' : '+f['text'])+'</li>' for f in r['facts'])}</ul></section><section><h3>Réécriture réelle</h3><p>{e(r['text'] or 'Aucune sortie exploitable')}</p><p>{e(j.get('reason',r.get('error','')))}</p><p>Faits manquants : {e(str(j.get('missing_fact_ids','non évalué')))}. Contradiction : {e(str(j.get('contradiction','non évalué')))}. Ajout : {e(str(j.get('added_claims','non évalué')))}.</p></section></div><pre>{e(json.dumps(m,ensure_ascii=False,indent=2))}</pre></details>'''
    body+='''<h2>Limites et protocole</h2><ul><li>40 textes synthétiques assez proches par leur forme, huit domaines ; les résultats ne prouvent pas une performance sur des mails réels.</li><li>Une génération par méthode et texte, température zéro : pas une étude de variance entre répétitions.</li><li>La méthode structurée reçoit les faits de référence explicites : la comparaison mesure ce paquet de consignes, pas seulement la mise en page du prompt.</li><li>Les quatre variantes sont générées dans le même appel ; un effet de contexte entre variantes est possible.</li><li>Les références sont définies avant la génération mais préparées avec assistance IA. Aucune annotation humaine n’est revendiquée.</li><li>Flesch français est un indice de surface. Il ne mesure pas directement la compréhension d’un lecteur.</li><li>Le contrôle des nombres peut rejeter une écriture équivalente, par exemple « deux » au lieu de « 2 ».</li><li>Le juge voit les variantes dans un ordre mélangé sans le nom de leur méthode. Il reste faillible. La grille de revue humaine doit être complétée avant de présenter ces scores comme validés.</li></ul><p>Assistance ChatGPT/Codex déclarée. Aucun secret nécessaire pour consulter ce rapport enregistré.</p></main></html>'''
    Path(path).write_text(header+body,encoding='utf8');return s

def render_review(rows,path):
    # Les méthodes sont masquées dans l'interface d'annotation pour limiter le biais.
    public=[{**r,'display_id':f'Cas {i+1:02}'} for i,r in enumerate(rows)]
    payload=json.dumps(public,ensure_ascii=False).replace('<','\\u003c')
    template='''<!doctype html><html lang="fr"><meta charset="utf-8"><title>A6 — Revue humaine</title><style>CSS</style><main><h1>Vérifier le juge IA</h1><p>Lire la source, les faits et la réécriture. Noter le registre et le ton, puis indiquer si tous les faits sont préservés et si le sens reste proche. Ne pas consulter les verdicts du juge avant de terminer.</p><div class="notice">Les cases sont volontairement vides. Elles doivent être remplies par Cliphton ou Igor après lecture. Les réponses restent dans ce navigateur jusqu’à l’export CSV. Aucun nom de personne n’est demandé.</div><p>Registre : 1 très familier, 2 oral, 3 neutre professionnel, 4 formel, 5 très soutenu.<br>Chaleur : 1 hostile, 2 froid, 3 neutre/poli, 4 accueillant, 5 très chaleureux.<br>Fidélité : « oui » uniquement si aucun fait omis, modifié ou ajouté. Similarité : 0 (sans rapport) à 1 (même sens).</p><p><button id="export">Exporter mes annotations CSV</button> <span id="progress"></span></p><div id="cases"></div><p><a href="rapport.html">Retour au rapport</a></p></main><script>
const rows=PAYLOAD;let answers={};try{answers=JSON.parse(localStorage.getItem('a6-review-v1')||'{}')}catch(e){}
const esc=s=>String(s).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const fields=['human_formality','human_warmth','human_meaning_preserved','human_similarity','human_comment'];
function progress(){document.getElementById('progress').textContent=rows.filter(r=>fields.slice(0,4).every(k=>String((answers[r.id]||{})[k]||'')!=='')).length+' / '+rows.length+' cas complets'}
document.getElementById('cases').innerHTML=rows.map(r=>`<details open><summary>${r.display_id} / objectif ${esc(r.attribute)}</summary><div class="grid"><section><h3>Source</h3><p>${esc(r.source)}</p><h4>Faits</h4><p>${esc(r.facts)}</p></section><section><h3>Réécriture</h3><p>${esc(r.rewrite)}</p></section></div>${fields.map(k=>`<label>${esc(({human_formality:'Registre (1 à 5)',human_warmth:'Chaleur (1 à 5)',human_meaning_preserved:'Tous les faits préservés ? oui / non',human_similarity:'Similarité du sens (0 à 1)',human_comment:'Commentaire facultatif'})[k])}<input data-id="${esc(r.id)}" data-key="${k}" value="${esc((answers[r.id]||{})[k]||'')}"></label>`).join('')}</details>`).join('');
document.addEventListener('input',e=>{if(!e.target.dataset.id)return;const {id,key}=e.target.dataset;answers[id]={...(answers[id]||{}),[key]:e.target.value};localStorage.setItem('a6-review-v1',JSON.stringify(answers));progress()});
document.getElementById('export').onclick=()=>{const cols=['id',...fields];const csv='\\ufeff'+[cols,...rows.map(r=>[r.id,...fields.map(k=>(answers[r.id]||{})[k]||'')])].map(row=>row.map(v=>'"'+String(v).replace(/"/g,'""')+'"').join(',')).join('\\r\\n');const a=document.createElement('a');a.href=URL.createObjectURL(new Blob([csv],{type:'text/csv;charset=utf-8'}));a.download='annotations_humaines.csv';a.click();URL.revokeObjectURL(a.href)};progress();
</script></html>'''
    Path(path).write_text(template.replace('CSS',CSS).replace('PAYLOAD',payload),encoding='utf8')

def validate_humans(result,csv_path):
    byid={r['source_id']+'-'+r['method']+'-'+r['attribute']:r for r in result['records']}
    ratings=list(csv.DictReader(Path(csv_path).open(encoding='utf-8-sig')));seen=set();scored=[]
    for row in ratings:
        if row['id'] not in byid or row['id'] in seen:raise ValueError('Identifiant inconnu ou dupliqué')
        seen.add(row['id']);r=byid[row['id']];j=r.get('judgment',{})
        try:
            form=int(row['human_formality']);warm=int(row['human_warmth']);sim=float(row['human_similarity']);faith=row['human_meaning_preserved'].strip().lower()
        except (ValueError,KeyError):raise ValueError('Annotations incomplètes ; aucun score humain inventé.')
        if not 1<=form<=5 or not 1<=warm<=5 or not 0<=sim<=1 or faith not in ('oui','non'):raise ValueError('Valeur hors échelle')
        scored.append({'id':row['id'],'formality_absolute_error':abs(form-j['formality']),'warmth_absolute_error':abs(warm-j['warmth']),
            'similarity_absolute_error':abs(sim-j['semantic_similarity']),'fidelity_agreement':(faith=='oui')==r['metrics']['meaning_preserved']})
    if len(scored)<16:raise ValueError('16 annotations complètes sont requises pour cette revue prévue.')
    return dict(n=len(scored),formality_mae=statistics.mean(r['formality_absolute_error'] for r in scored),
        warmth_mae=statistics.mean(r['warmth_absolute_error'] for r in scored),
        similarity_mae=statistics.mean(r['similarity_absolute_error'] for r in scored),
        fidelity_agreement=statistics.mean(r['fidelity_agreement'] for r in scored),details=scored,
        interpretation='Échantillon limité : examiner les désaccords ; aucun certificat automatique de validité.')
