"""Appels API compatibles OpenAI, cache, limites de budget et provenance."""
import hashlib,json,os,time,threading,urllib.request,urllib.error
from pathlib import Path

class APIError(RuntimeError): pass
class BudgetError(APIError): pass

def load_env(path):
    if Path(path).exists():
        for line in Path(path).read_text().splitlines():
            if '=' in line and not line.lstrip().startswith('#'):
                k,v=line.split('=',1)
                value=v.strip().strip('"').strip("'")
                if value:os.environ.setdefault(k.strip(),value)

def strict_schema(properties):
    return dict(type='object',properties=properties,required=list(properties),additionalProperties=False)

def array_schema(properties):
    return {'type':'array','items':strict_schema(properties)}

def sha(value):
    return hashlib.sha256(json.dumps(value,ensure_ascii=False,sort_keys=True).encode()).hexdigest()

class Client:
    def __init__(self,cache_dir,budget=3.,timeout=90):
        self.base=(os.getenv('MODEL_BASE_URL') or 'https://openrouter.ai/api/v1').rstrip('/')
        self.key=os.getenv('MODEL_API_KEY') or os.getenv('OPENROUTER_API_KEY') or os.getenv('OPENAI_API_KEY')
        if not self.key:raise APIError('Clé API absente : renseigner MODEL_API_KEY dans .env.')
        if not self.base.startswith('https://'):raise APIError('Le fournisseur doit utiliser HTTPS.')
        self.cache=Path(cache_dir);self.cache.mkdir(parents=True,exist_ok=True)
        self.budget=budget;self.timeout=timeout;self.lock=threading.Lock();self.cost=0.;self.calls=0;self.hits=0
        self.entries=[]
    def call(self,model,messages,schema,max_tokens=2400):
        payload=dict(model=model,messages=messages,temperature=0,max_tokens=max_tokens,
            response_format={'type':'json_schema','json_schema':{'name':'evaluation_a6','strict':True,'schema':schema}})
        if 'openrouter.ai' in self.base:payload['reasoning']={'effort':'low' if 'glm' in model else 'none'}
        cache_key=sha({'base':self.base,'payload':payload});path=self.cache/(cache_key+'.json')
        if path.exists():
            cached=json.loads(path.read_text());
            with self.lock:self.hits+=1
            return cached
        # Réserve conservative par appel, coût réel mesuré si le fournisseur le retourne.
        reserve=.05
        with self.lock:
            if self.cost+reserve>self.budget:raise BudgetError('Budget local atteint : arrêt sans nouvel appel.')
            self.cost+=reserve;self.calls+=1
        started=time.monotonic()
        req=urllib.request.Request(self.base+'/chat/completions',data=json.dumps(payload).encode(),
            headers={'Authorization':'Bearer '+self.key,'Content-Type':'application/json'})
        try:
            with urllib.request.urlopen(req,timeout=self.timeout) as response:r=json.load(response)
            if 'error' in r:raise APIError('Le fournisseur a renvoyé une erreur ; aucun résultat substitué.')
            choice=r['choices'][0]
            usage=r.get('usage',{});cost=usage.get('cost')
            with self.lock:
                if isinstance(cost,(int,float)) and cost>=0:self.cost+=cost-reserve
            if choice.get('finish_reason')=='length':raise APIError('Réponse tronquée : échec conservé.')
            data=json.loads(choice['message']['content'])
            usage=r.get('usage',{});cost=usage.get('cost')
            item=dict(data=data,model=r.get('model',model),requested_model=model,request_hash=cache_key,
                response_id=r.get('id'),usage=usage,cost_usd=cost,latency_s=round(time.monotonic()-started,3),
                created_utc=time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),provenance='live_api')
            with self.lock:
                self.entries.append({k:item[k] for k in ['request_hash','model','cost_usd','latency_s','created_utc']})
            tmp=path.with_suffix('.tmp');tmp.write_text(json.dumps(item,ensure_ascii=False));tmp.replace(path)
            return item
        except urllib.error.HTTPError as e:
            # Ne pas renvoyer le corps d'erreur distant, qui peut contenir des informations sensibles.
            raise APIError(f'API HTTP {e.code} ; vérifier modèle autorisé, clé ou quota.') from None
        except (KeyError,ValueError,TimeoutError,OSError) as e:
            raise APIError('Réponse API inexploitable ou réseau indisponible ('+type(e).__name__+').') from None
    def embeddings(self,texts,model='openai/text-embedding-3-small'):
        key=sha({'base':self.base,'model':model,'texts':texts});p=self.cache/(key+'.embeddings.json')
        if p.exists():return json.loads(p.read_text())
        with self.lock:
            if self.cost+.05>self.budget:raise BudgetError('Budget atteint.')
            self.cost+=.05;self.calls+=1
        req=urllib.request.Request(self.base+'/embeddings',data=json.dumps(dict(model=model,input=texts)).encode(),
            headers={'Authorization':'Bearer '+self.key,'Content-Type':'application/json'})
        try:
            r=json.load(urllib.request.urlopen(req,timeout=self.timeout));data=sorted(r['data'],key=lambda x:x['index'])
            if len(data)!=len(texts):raise APIError('Nombre de vecteurs incorrect.')
            result=dict(vectors=[d['embedding'] for d in data],model=model,usage=r.get('usage',{}),provenance='live_api')
            c=r.get('usage',{}).get('cost')
            with self.lock:
                if isinstance(c,(float,int)) and c>=0:self.cost+=c-.05
            p.write_text(json.dumps(result));return result
        except urllib.error.HTTPError as e:raise APIError(f'Embeddings indisponibles (HTTP {e.code}).') from None
        except (KeyError,ValueError,TimeoutError,OSError) as e:raise APIError('Embeddings indisponibles ('+type(e).__name__+').') from None
