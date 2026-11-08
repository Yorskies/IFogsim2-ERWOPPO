"""P08 candidate evaluator and gated full search CLI. No training occurs on import."""
import argparse
from pathlib import Path
import time

from .config import load_config,read_json,require,sha256
from .learning import run_training,run_evaluation,write_json,file_hash,provenance
from .learning_report import rows
from .search import optimize,repeated_objectives,feasible


def require_gate(path):
    result=read_json(path/'result.json');verification=read_json(path/'fidelity_verification.json')
    protocol=read_json(path/'protocol.json')
    require(result['status']=='fidelity_pass' and result['selected_K'] in (5120,10240,20480),'Fidelity gate has not passed')
    require(verification['status']=='pass' and verification['selected_K']==result['selected_K'],'Missing or mismatched fidelity audit')
    require(verification['result_sha256']==file_hash(path/'result.json'),'Fidelity result changed after audit')
    require(protocol['config_sha256']==sha256(load_config()),'Search config differs from fidelity config')
    receipt=read_json(Path(__file__).resolve().parents[1]/'ifogsim/build/research_v2/build_receipt.json')
    require(receipt['artifact_sha256']==protocol['jar_sha256'],'Search JAR differs from fidelity JAR')
    for name in ('learning.py','search.py','gym_env.py','rpc_client.py','traces.py'):
        path=Path(__file__).resolve().parent/name
        require(file_hash(path)==protocol['source_hashes']['research_v2/'+name],f'Source changed after fidelity: {name}')
    return result['selected_K']


class CandidateEvaluator:
    """Two fresh models per charged slot. Names/weights never enter RNG seed namespaces."""
    def __init__(self,directory,outer,budget,jdk_home=None,learner_version='0.2'):
        require(type(outer) is int and 0<=outer<20,'Main search outer must be 0..19')
        self.directory=Path(directory);self.outer=outer;self.budget=budget;self.jdk_home=jdk_home
        self.learner_version=learner_version
        self.training_decisions=0;self.validation_decisions=0;self.slots=[]

    def __call__(self,weights,slot):
        weights=feasible(weights).tolist();base=self.directory/f'slot_{slot:03d}';base.mkdir(parents=True,exist_ok=False)
        vectors=[];models=[];started=time.monotonic()
        for repeat in (0,1):
            path=base/f'model_{repeat}'
            run_training(path,self.outer,repeat,self.budget,weights,self.jdk_home,
                         training_split='train_candidate',phase='P08' if self.learner_version=='0.2' else 'P11',
                         checkpoint_at=[self.budget],fast_rpc=True,learner_version=self.learner_version)
            checkpoint=path/f'checkpoint_{self.budget:08d}'
            validation=base/f'validation_{repeat}'
            run_evaluation(checkpoint,validation,self.jdk_home,split='validation',fast_rpc=True)
            summary=read_json(validation/'summary.json');episodes=rows(validation/'episodes.jsonl')
            count=sum(r['decisions'] for r in episodes)
            self.training_decisions+=self.budget;self.validation_decisions+=count
            vectors.append(summary['macro_costs'])
            models.append({'repeat':repeat,'model_seed':200000+2*self.outer+repeat,
                           'checkpoint_sha256':file_hash(checkpoint/'model.zip'),'validation_decisions':count,
                           'macro_costs':summary['macro_costs'],
                           'validation_payloads':[r['trace_sha256'] for r in episodes]})
        result=repeated_objectives(vectors)
        record={'status':'complete','slot':slot,'weights':weights,**result,'models':models,'learner_version':self.learner_version,
                'training_decisions':2*self.budget,'validation_decisions':sum(m['validation_decisions'] for m in models),
                'wall_s':time.monotonic()-started}
        write_json(base/'candidate.json',record);self.slots.append(record)
        return result['costs']


def run(method,outer,root,fidelity,jdk_home=None):
    budget=require_gate(fidelity);root.mkdir(parents=True,exist_ok=False)
    config=load_config();write_json(root/'protocol.json',{'phase':'P08','method':method,'outer':outer,'K':budget,
        'candidate_slots':80,'model_repeats':2,'worker_count':1,'rpc_schema_validation':False,
        'fidelity_evidence':str(fidelity.resolve()),'provenance':provenance(config),
        'not_included':'No final policy training, test evaluation, or confirmatory batch.'})
    evaluator=CandidateEvaluator(root/'candidates',outer,budget,jdk_home)
    result=optimize(method,outer,evaluator,config)
    result.update(status='complete',K=budget,training_decisions=evaluator.training_decisions,
                  validation_decisions=evaluator.validation_decisions,test_accessed=False,
                  final_policy_trained=False,search_cost=evaluator.training_decisions+evaluator.validation_decisions)
    write_json(root/'result.json',result)


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--method',choices=('nsga2','random'),required=True)
    p.add_argument('--outer',type=int,required=True);p.add_argument('--output-dir',type=Path,required=True)
    p.add_argument('--fidelity-evidence',type=Path,required=True);p.add_argument('--jdk-home',type=Path)
    args=p.parse_args();run(args.method,args.outer,args.output_dir,args.fidelity_evidence,args.jdk_home)


if __name__=='__main__':main()
