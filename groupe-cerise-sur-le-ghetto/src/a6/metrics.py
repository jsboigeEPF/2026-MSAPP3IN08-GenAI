"""Mesures : les proxys lexicaux ne sont jamais appelés similarité sémantique."""
import re,math
import textstat
textstat.set_lang('fr')
ATTRIBUTES=('longueur','lisibilite','registre','ton')

def words(text):return re.findall(r"\b[\w]+(?:[’'-][\w]+)*\b",text,flags=re.UNICODE)
def readability(text):return float(textstat.flesch_reading_ease(text))
def cosine(a,b):
    na=math.sqrt(sum(x*x for x in a));nb=math.sqrt(sum(x*x for x in b))
    if not na or not nb:raise ValueError('Vecteur nul')
    if len(a)!=len(b):raise ValueError('Dimensions différentes')
    return sum(x*y for x,y in zip(a,b))/(na*nb)
def numbers(text):return sorted(re.findall(r'\d+(?:[,.]\d+)?',text))
def targets(source):
    return {'longueur':{'ratio':.65,'tolerance':.15},'lisibilite':{'score_min':round(readability(source)+10,2)},
            'registre':{'score_min':4,'gain_min':1},'ton':{'score_min':4,'gain_min':1}}

def measures(source,rewritten,attribute,judgment,semantic_cosine=None):
    if attribute not in ATTRIBUTES:raise ValueError('Attribut inconnu')
    if not source.strip() or not rewritten.strip():raise ValueError('Texte vide')
    target=targets(source)[attribute];nw=len(words(rewritten));sw=len(words(source))
    j=judgment or {};metrics={'source_words':sw,'output_words':nw,'word_ratio':nw/sw,
        'source_readability':round(readability(source),2),'output_readability':round(readability(rewritten),2),
        'numbers_equal':numbers(source)==numbers(rewritten),'semantic_cosine':semantic_cosine,
        'judge_semantic_similarity':j.get('semantic_similarity')}
    if attribute=='longueur':
        observed=nw/sw;gap=abs(observed-target['ratio']);ok=gap<=target['tolerance']
    elif attribute=='lisibilite':
        observed=metrics['output_readability'];gap=max(0,target['score_min']-observed);ok=observed>=target['score_min']
    else:
        field='formality' if attribute=='registre' else 'warmth'
        observed=j.get(field);initial=j.get('source_'+field)
        gap=None if observed is None or initial is None else max(0,target['score_min']-observed,target['gain_min']-(observed-initial))
        ok=gap==0 if gap is not None else None
    judged=bool(j.get('evaluation_complete'))
    preserved=judged and not j.get('missing_fact_ids') and not j.get('contradiction') and not j.get('added_claims')
    # Un nombre perdu/modifié entraîne aussi un échec, même si le juge ne le remarque pas.
    preserved=preserved and metrics['numbers_equal']
    semantic_ok=(semantic_cosine>=.80) if semantic_cosine is not None else (j.get('semantic_similarity',-1)>=.85 if judged else False)
    metrics.update(target=target,attribute_observed=observed,target_gap=gap,attribute_success=ok,
        meaning_preserved=preserved,semantic_success=semantic_ok,
        joint_success_estimate=bool(ok and preserved and semantic_ok),
        validation_status='provisoire_jugement_non_valide_humain',
        factual_drift_estimate=not preserved if judged else None)
    return metrics
