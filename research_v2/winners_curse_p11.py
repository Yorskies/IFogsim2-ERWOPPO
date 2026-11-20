"""Winner's-curse estimate from the P11 searches (descriptive, development data only: the search-validation split).

Every P11 candidate was scored by two PPO models with the same weights (model_0, model_1: different seed and training stream,
same 20 validation traces). Their disagreement measures training noise directly. From the 40 searches x 80 candidates:
per-model noise, the noise of the 2-model candidate score, the within-search spread of scores, the implied weight signal,
and the shrinkage-predicted true D of each selected candidate, compared with the observed final-model test D (P11 report).

    PYTHONPATH=. venv/bin/python -m research_v2.winners_curse_p11
writes results/research_v2/v0.4/p11/winners_curse_estimate.json
"""
import glob
import json
from pathlib import Path

import numpy as np

from .config import ROOT

BASE = ROOT / 'results/research_v2/v0.4/p11'


def search_dir(method, outer):
    return Path(sorted(glob.glob(str(BASE / f'shard_*/jobs/r{outer:02d}_{method}_search/attempt_*/data')))[-1])


def main():
    from . import p12
    from .analysis.stats import aggregate
    table = p12.table_from(BASE / 'test_evaluation/episodes', ('nsga2', 'random'), list(range(20)), 'test')
    test_D = aggregate(table)['D']
    searches = []
    for mi, method in enumerate(('nsga2', 'random')):
        for outer in range(20):
            base = search_dir(method, outer)
            result = json.loads((base / 'result.json').read_text())
            d0, d1, score = [], [], []
            for record in result['records']:
                slot = base / 'candidates' / f'slot_{record["slot"]:03d}'
                d0.append(json.loads((slot / 'validation_0/summary.json').read_text())['D_macro'])
                d1.append(json.loads((slot / 'validation_1/summary.json').read_text())['D_macro'])
                score.append(record['D'])
            searches.append({'method': method, 'outer': outer, 'd0': np.array(d0), 'd1': np.array(d1), 'score': np.array(score),
                             'selected': result['selected']['slot'], 'test_D': float(test_D[mi][outer])})
    d0 = np.concatenate([s['d0'] for s in searches])
    d1 = np.concatenate([s['d1'] for s in searches])
    noise_model = float(np.var(d0 - d1, ddof=1) / 2)          # variance of one model's D around its weight's expectation
    noise_score = noise_model / 2                             # the candidate score averages two models
    spread = float(np.mean([np.var(s['score'], ddof=1) for s in searches]))
    signal = max(spread - noise_score, 0.0)
    reliability = signal / spread if spread > 0 else 0.0
    within_corr = float(np.mean([np.corrcoef(s['d0'], s['d1'])[0, 1] for s in searches]))
    rows = []
    for s in searches:
        mean = float(s['score'].mean())
        chosen = float(s['score'][s['selected']])
        rows.append({'method': s['method'], 'outer': s['outer'], 'selected_score': chosen, 'candidate_mean': mean,
                     'predicted_true': mean + reliability * (chosen - mean), 'final_test_D': s['test_D']})
    summary = {
        'per_model_noise_sd': noise_model ** 0.5, 'candidate_score_noise_sd': noise_score ** 0.5,
        'within_search_score_sd': spread ** 0.5, 'implied_weight_signal_sd': signal ** 0.5, 'score_reliability': reliability,
        'within_search_corr_model0_model1': within_corr,
        'spearman_brown_2model_reliability_from_corr': 2 * within_corr / (1 + within_corr),
        'mean_selected_score': float(np.mean([r['selected_score'] for r in rows])),
        'mean_candidate_score': float(np.mean([r['candidate_mean'] for r in rows])),
        'mean_predicted_true': float(np.mean([r['predicted_true'] for r in rows])),
        'mean_final_test_D': float(np.mean([r['final_test_D'] for r in rows])),
        'searches': len(searches), 'candidates': int(d0.size),
        'note': 'model_0/model_1 share the 20 validation traces, so weight x trace interaction counts as signal here; the true '
                'reliability is at most this estimate. Final test D uses a fresh train_final model and the test traces.'}
    out = BASE / 'winners_curse_estimate.json'
    out.write_text(json.dumps({'summary': summary, 'per_search': rows}, indent=2) + '\n')
    print(json.dumps(summary, indent=2))


if __name__ == '__main__':
    main()
