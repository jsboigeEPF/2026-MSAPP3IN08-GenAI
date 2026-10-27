import copy,json,pytest
from a6.corpus import build
from a6.engine import Client,BudgetError,APIError
from a6.metrics import measures,cosine,numbers,targets
from a6.prompts import validate_generation,validate_judgments,GEN_SCHEMA,generation_messages

SOURCE='Le lot comprend 24 capteurs. La livraison est prévue le 14 novembre. L’installation n’est pas comprise.'
J={'evaluation_complete':True,'formality':4,'source_formality':3,'warmth':4,'source_warmth':3,
   'missing_fact_ids':[],'contradiction':False,'added_claims':False,'semantic_similarity':.95}

def test_corpus():
    c=build();assert len(c)==40 and len({r['id'] for r in c})==40
    assert sum(r['split']=='dev' for r in c)==8
    assert len({r['domain'] for r in c})==8
    assert all(len(r['facts'])==3 and len({f['id'] for f in r['facts']})==3 for r in c)

def test_joint_rejects_omission_despite_attribute():
    j={**J,'missing_fact_ids':['F3']}
    r=measures(SOURCE,SOURCE,'registre',j,.99)
    assert r['attribute_success'] and not r['joint_success_estimate']

def test_joint_rejects_negation_changed():
    out=SOURCE.replace('n’est pas comprise','est comprise')
    r=measures(SOURCE,out,'ton',{**J,'contradiction':True},.99)
    assert r['numbers_equal'] and not r['joint_success_estimate']

def test_joint_rejects_changed_number():
    r=measures(SOURCE,SOURCE.replace('24','25'),'registre',J,.99)
    assert not r['numbers_equal'] and not r['joint_success_estimate']

def test_joint_unknown_judge_not_success():
    r=measures(SOURCE,SOURCE,'registre',{})
    assert r['attribute_success'] is None and not r['joint_success_estimate']

def test_formality_requires_increase():
    r=measures(SOURCE,SOURCE,'registre',{**J,'source_formality':4})
    assert not r['attribute_success']

def test_success_and_no_expected_missing():
    r=measures(SOURCE,SOURCE,'registre',J,.95)
    assert r['joint_success_estimate'] and r['factual_drift_estimate'] is False

def test_cosine():
    assert cosine([1,0],[1,0])==1 and cosine([1,0],[0,1])==0
    with pytest.raises(ValueError):cosine([0,0],[1,0])
    with pytest.raises(ValueError):cosine([1],[1,2])

def test_empty_text_rejected():
    with pytest.raises(ValueError):measures('',SOURCE,'ton',J)

def test_duplicate_attribute_rejected():
    bad={'rewrites':[{'attribute':'ton','text':'Texte'}]*4}
    with pytest.raises(ValueError):validate_generation(bad)

def test_judge_schema_rejects_missing_and_invalid():
    with pytest.raises(ValueError):validate_judgments({'evaluations':[]},['V1'],[{'id':'F1'}])
    with pytest.raises(ValueError):validate_judgments({'evaluations':[{'id':'V1','formality':10}]},['V1'],[{'id':'F1'}])

def test_budget_zero_no_network(tmp_path,monkeypatch):
    monkeypatch.setenv('MODEL_API_KEY','test-not-a-real-key')
    c=Client(tmp_path,budget=0)
    with pytest.raises(BudgetError):c.call('model',[],GEN_SCHEMA)
    assert c.calls==0

def test_cache_no_network(tmp_path,monkeypatch):
    from a6.engine import sha
    monkeypatch.setenv('MODEL_API_KEY','test-not-a-real-key')
    c=Client(tmp_path,budget=0)
    payload=dict(model='model',messages=[],temperature=0,max_tokens=2400,response_format={'type':'json_schema','json_schema':{'name':'evaluation_a6','strict':True,'schema':GEN_SCHEMA}})
    if 'openrouter.ai' in c.base:payload['reasoning']={'effort':'none'}
    key=sha({'base':c.base,'payload':payload});(tmp_path/(key+'.json')).write_text(json.dumps({'data':{'cached':True}}))
    assert c.call('model',[],GEN_SCHEMA)['data']['cached'] and c.calls==0 and c.hits==1

def test_missing_key(monkeypatch,tmp_path):
    for k in ('MODEL_API_KEY','OPENROUTER_API_KEY','OPENAI_API_KEY'):monkeypatch.delenv(k,raising=False)
    with pytest.raises(APIError):Client(tmp_path)

def test_prompt_methods_same_source():
    row=build()[0]
    for m in ('baseline','structuree'):assert row['source'] in generation_messages(row,m)[1]['content']
    assert 'FAITS A PRESERVER' not in generation_messages(row,'baseline')[1]['content']
    assert 'FAITS A PRESERVER' in generation_messages(row,'structuree')[1]['content']


def test_env_blank_uses_defaults(tmp_path,monkeypatch):
    from a6.engine import load_env
    monkeypatch.delenv('MODEL_BASE_URL',raising=False)
    p=tmp_path/'.env';p.write_text('MODEL_BASE_URL=\n# Commentaire\n')
    load_env(p)
    monkeypatch.setenv('MODEL_API_KEY','test-not-a-real-key')
    assert Client(tmp_path/'cache').base=='https://openrouter.ai/api/v1'
