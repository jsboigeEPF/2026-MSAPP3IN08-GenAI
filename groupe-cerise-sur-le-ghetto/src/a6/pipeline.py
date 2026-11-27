import concurrent.futures as cf,csv,json,os,random,time
from pathlib import Path
from .engine import Client,APIError,load_env
from .corpus import build,write
from .metrics import ATTRIBUTES,measures,cosine
from .prompts import GEN_SCHEMA,JUDGE_SCHEMA,generation_messages,judge_messages,validate_generation,validate_judgments

ROOT=Path(__file__).resolve().parents[2]
def load_corpus():return [json.loads(l) for l in (ROOT/'data/corpus.jsonl').read_text().splitlines() if l]

def run_source(item,client,generator,judge):
    records=[];refs={};batches=[]
    for method in ('baseline','structuree'):
        try:
            result=client.call(generator,generation_messages(item,method),GEN_SCHEMA,2400)
            variants=validate_generation(result['data'])
            for attribute in ATTRIBUTES:
                rec=dict(source_id=item['id'],domain=item['domain'],split=item['split'],method=method,attribute=attribute,
                    source=item['source'],facts=item['facts'],text=variants[attribute],generation={k:v for k,v in result.items() if k!='data'},status='generated')
                records.append(rec)
        except (APIError,ValueError) as e:
            for attribute in ATTRIBUTES:records.append(dict(source_id=item['id'],domain=item['domain'],split=item['split'],method=method,attribute=attribute,source=item['source'],facts=item['facts'],text='',status='generation_error',error=str(e)))
    valid=[r for r in records if r['text']]
    # Ordre déterministe mélangé ; aucun nom de méthode ni objectif n'est envoyé au juge.
    random.Random(item['id']).shuffle(valid)
    for i,r in enumerate(valid):refs[f'V{i+1}']=r;batches.append({'id':f'V{i+1}','text':r['text']})
    if valid:
        try:
            evaluated=client.call(judge,judge_messages(item,batches),JUDGE_SCHEMA,3200)
            verdicts=validate_judgments(evaluated['data'],refs,item['facts'])
            for rid,r in refs.items():
                r['judgment']=verdicts[rid];r['evaluation']={k:v for k,v in evaluated.items() if k!='data'}
                r['metrics']=measures(r['source'],r['text'],r['attribute'],r['judgment']);r['status']='evaluated'
        except (APIError,ValueError) as e:
            for r in valid:r.update(status='evaluation_error',error=str(e),metrics=measures(r['source'],r['text'],r['attribute'],{}))
    return records

def run(limit=40,workers=4,budget=3.,output='benchmark.json',embeddings=False):
    load_env(ROOT/'.env')
    generator=os.getenv('GENERATOR_MODEL','qwen/qwen3.8-flash');judge=os.getenv('JUDGE_MODEL') or 'deepseek/deepseek-v4.1-flash'
    client=Client(ROOT/'.cache',budget=budget)
    corpus=load_corpus()[:limit];records=[];errors=[]
    started=time.monotonic()
    with cf.ThreadPoolExecutor(max_workers=workers) as pool:
        futures={pool.submit(run_source,item,client,generator,judge):item for item in corpus}
        for fut in cf.as_completed(futures):
            item=futures[fut]
            try:records.extend(fut.result())
            except Exception as e:errors.append({'source_id':item['id'],'error':type(e).__name__})
            print(f"{len(records)//8}/{len(corpus)} textes traités ; coût mesuré/réservé {client.cost:.4f} USD",flush=True)
            # Checkpoint à chaque source ; ne disparaît pas si un autre appel échoue.
            (ROOT/'results'/output).write_text(json.dumps({'records':records,'errors':errors,'partial':True},ensure_ascii=False,indent=2))
    semantic_backend='llm_judge_estimate_not_embeddings';embedding_error=None
    if embeddings and records:
        texts=list(dict.fromkeys([r['source'] for r in records]+[r['text'] for r in records if r['text']]))
        try:
            e=client.embeddings(texts,os.getenv('EMBEDDING_MODEL','openai/text-embedding-3-small'));vecs=dict(zip(texts,e['vectors']))
            for r in records:
                if r['text']:r['metrics']=measures(r['source'],r['text'],r['attribute'],r.get('judgment'),cosine(vecs[r['source']],vecs[r['text']]))
            semantic_backend='embedding_cosine:'+e['model']
        except APIError as e:embedding_error=str(e)
    records.sort(key=lambda r:(r['source_id'],r['method'],r['attribute']))
    result={'protocol_version':'1.0','created_utc':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),
        'corpus_size':len(corpus),'planned_outputs':len(corpus)*8,'generator':generator,'judge':judge,
        'same_model_judge':generator==judge,'semantic_backend':semantic_backend,'embedding_error':embedding_error,
        'human_validation':'pending','live_calls_this_run':client.calls,'cache_hits':client.hits,
        'cost_measured_or_reserved_usd':round(client.cost,6),'wall_time_s':round(time.monotonic()-started,2),
        'partial':False,'errors':errors,'records':records}
    (ROOT/'results'/output).write_text(json.dumps(result,ensure_ascii=False,indent=2));return result

def export_review(result,path):
    # 2 sorties par attribut et méthode, tirage fixe sans filtrer sur la réussite.
    rows=[]
    for attr in ATTRIBUTES:
        for method in ('baseline','structuree'):
            candidates=[r for r in result['records'] if r['attribute']==attr and r['method']==method and r['text']]
            random.Random(attr+method).shuffle(candidates)
            for r in candidates[:2]:
                rows.append(dict(id=r['source_id']+'-'+method+'-'+attr,source=r['source'],rewrite=r['text'],attribute=attr,
                    facts=' / '.join(f['text'] for f in r['facts']),human_formality='',human_warmth='',
                    human_meaning_preserved='',human_similarity='',human_comment=''))
    with Path(path).open('w',newline='',encoding='utf-8-sig') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]) if rows else ['id']);w.writeheader();w.writerows(rows)
    return rows
