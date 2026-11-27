import argparse,json
from .pipeline import ROOT,run,export_review,load_corpus
from .report import render_report,render_review,validate_humans

def main():
    p=argparse.ArgumentParser(description='A6 : réécriture contrôlée et évaluation')
    sub=p.add_subparsers(dest='command',required=True)
    r=sub.add_parser('benchmark');r.add_argument('--limit',type=int,default=40);r.add_argument('--workers',type=int,default=4);r.add_argument('--budget',type=float,default=3.);r.add_argument('--output',default='benchmark.json')
    r=sub.add_parser('report');r.add_argument('--input',default='benchmark.json')
    r=sub.add_parser('serve');r.add_argument('--port',type=int,default=8765)
    r=sub.add_parser('validate-human');r.add_argument('csv')
    args=p.parse_args()
    if args.command=='benchmark':
        if not 1<=args.limit<=40 or not 1<=args.workers<=8 or not 0<=args.budget<=8:p.error('limit 1..40, workers 1..8, budget 0..8 USD')
        run(args.limit,args.workers,args.budget,args.output)
    elif args.command=='report':
        result=json.loads((ROOT/'results'/args.input).read_text());render_report(result,ROOT/'results/rapport.html')
        rows=export_review(result,ROOT/'results/annotation_template.csv');render_review(rows,ROOT/'results/review.html');print('Rapport et revue humaine créés dans results/.')
    elif args.command=='validate-human':
        result=json.loads((ROOT/'results/benchmark.json').read_text());r=validate_humans(result,args.csv)
        (ROOT/'results/validation_humaine.json').write_text(json.dumps(r,ensure_ascii=False,indent=2));print(json.dumps(r,ensure_ascii=False,indent=2))
    else:
        from .server import serve
        serve(args.port)
if __name__=='__main__':main()
