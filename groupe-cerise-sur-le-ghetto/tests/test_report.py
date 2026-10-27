import csv,json,pytest
from a6.report import summarize,paired_interval,render_report,render_review,validate_humans
from a6.corpus import build
from a6.metrics import measures
from a6.pipeline import export_review

def test_bootstrap_pair_not_outputs():
    rows=[]
    for i in range(4):
        for m in ('baseline','structuree'):rows.append(dict(source_id=str(i),attribute='ton',method=m,metrics={'joint_success_estimate':m=='structuree'}))
    b=paired_interval(rows,'ton');assert b['n_pairs']==4 and b['delta_pp']==100 and b['ci95_pp']==[100,100]

def test_unannotated_human_csv_refused(tmp_path):
    p=tmp_path/'empty.csv';p.write_text('id,human_formality\n')
    with pytest.raises(ValueError):validate_humans({'records':[]},p)

def test_review_has_no_default_human_labels(tmp_path):
    rows=[dict(id='T01-baseline-ton',source='source',rewrite='sortie',attribute='ton',facts='Fait')]
    p=tmp_path/'review.html';render_review(rows,p);s=p.read_text();assert 'Les cases sont volontairement vides' in s and 'human_meaning_preserved' in s

def test_report_escapes_untrusted_text(tmp_path):
    row=dict(source_id='T01',domain='test',split='test',method='baseline',attribute='ton',source='<script>danger</script>',facts=[{'id':'F1','text':'texte'}],text='<script>danger</script>',status='generation_error',error='test')
    result=dict(records=[row],corpus_size=1,generator='test',judge='test',live_calls_this_run=0,cache_hits=0,cost_measured_or_reserved_usd=0)
    p=tmp_path/'report.html';render_report(result,p);assert '<script>danger</script>' not in p.read_text() and '&lt;script&gt;' in p.read_text()
