# Evolutionary / metaheuristic search of DRL reward weights and hyperparameters, and MOEA comparisons in fog/edge/cloud

Scope note: about 25 search and fetch calls (WebSearch and WebFetch, Nov 2026). Paywalled full texts (ScienceDirect, Nature/Sci Rep, MDPI 403) were often not readable. Where a claim rests only on a search-engine snippet or summary and not on the primary text, it is marked **[snippet-level]**. Anything I could not confirm is marked **[unverified]** or left out.

## Q1. Which papers combine NSGA-II (or other MOEAs/GA/PSO) with DRL for edge/fog offloading or scheduling, and what does the EC part optimize?

### Takeaway
In edge/fog/cloud work, EC+DRL hybrids almost never use the EC loop to pick the DRL reward weights. The EC part usually (a) searches offloading/schedule decisions directly, (b) gets its operators or parameters tuned by RL, (c) trains the policy network weights in place of gradient descent, or (d) runs as a separate baseline. Reward weights in DRL offloading papers are nearly always hand-set constants such as 0.5/0.5 or a 0.1 penalty. I found no edge/fog paper where NSGA-II chooses PPO reward weights.

### Cited Findings
- **NSGA-II trains the policy, not the reward weights (cloud load balancing).** In "Reducing Idleness in Financial Cloud Services via Multi-objective Evolutionary Reinforcement Learning based Load Balancer" (arXiv 2305.03463; also in Science China Information Sciences, 2024), NSGA-II evolves the *policy's* parameters. Pareto dominance stands in for a weighted-sum reward, so the authors "do not need to set the aggregation weights manually". The PPO baseline uses fixed aggregation weights of 0.5/0.5 for the load-balancing and idle-time rewards — [arXiv 2305.03463](https://arxiv.org/pdf/2305.03463); [SCIS PDF](http://scis.scichina.com/en/2024/120102.pdf) [snippet-level for the quoted weights]
- **RL-modified NSGA-II, then weighting and ranking (dependent-task MEC offloading).** This FGCS paper (S0167739X21004039, 2021/2022; title "Offloading dependent tasks in multi-access edge computing: A multi-objective reinforcement learning approach") produces Pareto solutions with a reinforcement-learning-modified NSGA-II. A second stage uses a weighting method and ranking to pick a solution, and the reward is treated as a vector whose weights follow user preference. Here the EC searches the offloading decisions, not the RL reward weights — [ScienceDirect FGCS](https://www.sciencedirect.com/science/article/abs/pii/S0167739X21004039) [snippet-level; authors not verified]
- **NSGA-II inside a meta-RL offloading framework.** "Dynamic Task Offloading Scheme for Edge Computing via Meta-Reinforcement Learning" (Computers, Materials & Continua, 2025) folds NSGA-II into the framework to jointly optimize delay and energy — [ScienceDirect/CMC](https://www.sciencedirect.com/org/science/article/pii/S1546221825000712) [snippet-level; the exact role of NSGA-II is not verified]
- **NSGA-II + RL for federated multi-cloud scheduling.** Scientific Reports (2026), "Federated multi-cloud task scheduling with load balancing using multi-objective NSGA-II and reinforcement learning". The full text was paywalled or redirected, so I could not verify whether NSGA-II optimizes schedules, hyperparameters or reward weights — [Nature Sci Rep](https://www.nature.com/articles/s41598-026-51105-w) [unverified details]
- **Hybrid RL + metaheuristic fog scheduling.** "A novel hybrid task scheduling method in fog computing using reinforcement learning and metaheuristic algorithms" (Cluster Computing, Springer, 2026) uses NSGA-III for large "heavy" clusters and swaps crowding distance for reference points. The EC searches schedules directly — [Springer Cluster Computing](https://link.springer.com/article/10.1007/s10586-026-06038-4) [snippet-level]
- **MOEA/D and NSGA-II in a multi-objective DRL fog scheduler.** "An Intelligent Scheduling Strategy in Fog Computing System Based on Multi-Objective Deep Reinforcement Learning Algorithm" (2023) reports that both algorithms optimized the objectives effectively — [ResearchGate 376784011](https://www.researchgate.net/publication/376784011_An_Intelligent_Scheduling_Strategy_in_Fog_Computing_System_Based_on_Multi-Objective_Deep_Reinforcement_Learning_Algorithm) [snippet-level; venue not verified]
- **NSGA-II + PPO for spectrum allocation (preprint).** The hybrid is reported to beat Random, Greedy and standalone PPO. This is an unreviewed preprint — [Preprints.org](https://www.preprints.org/frontend/manuscript/aeade0a4b1cf60a1276154bf27aa0fa8/download_pub) [snippet-level]
- **GA/PSO + DQN hybrids for offloading (review-level).** A review lists PSO-DQN and GA-DRL hybrids, where the EC is used to explore the decision space and avoid local optima. It also mentions a "DDRL-based Genetic Optimization Algorithm" for vehicular joint offloading, whose primary source I did not find — [Genetics & Mol. Research-hosted review](https://geneticsmr.com/index.php/gmr/article/download/1673/1014/4960) [low-quality venue; snippet-level]
- **Whale + GA with RL in edge-fog-cloud offloading.** The Computer Journal (OUP), 2025, vol. 68(9), p. 1225: WOA+GA handles device selection, combined with RL — [Computer Journal](https://academic.oup.com/comjnl/article/68/9/1225/8110711) [snippet-level]
- **EC as a competing baseline, not combined.** DRLIS (PPO-based fog scheduler, arXiv 2309.07407; Wang, Goudarzi, Buyya et al.) compares against a weighted-cost GA baseline — [arXiv 2309.07407](https://arxiv.org/html/2309.07407v2) [snippet-level]
- **Opposite direction: DQN seeds the GA population.** A review describes DQN used to generate the GA's initial population to speed convergence — [arXiv 2408.02938, RL workflow scheduling review](https://arxiv.org/pdf/2408.02938) [snippet-level]
- **Hand-chosen reward weights are the norm.** For example, a multi-agent DRL offloading paper for LEO satellite edge sets its deadline-penalty weight to 0.1 by hand — [MDPI Electronics 14(20):4063, 2025](https://www.mdpi.com/2079-9292/14/20/4063). A DDPG cloud-fog workflow scheduler notes that the "balance between all weights related to scheduling goals is necessary" but does not say how the weights were chosen — [Applied AI (T&F), 2026](https://www.tandfonline.com/doi/pdf/10.1080/08839514.2026.2700911) [snippet-level]
- **Evolving reward components for behavior diversity (non-edge).** EMOGI (arXiv 2202.12028) builds a multi-objective reward from one performance objective plus several behavior objectives, then uses NSGA-II to evolve a set of trade-off policies — [arXiv 2202.12028](https://arxiv.org/pdf/2202.12028) [snippet-level]
- **Surveys.** "Bridging Evolutionary Algorithms and Reinforcement Learning: A Comprehensive Survey on Hybrid Algorithms" (arXiv 2401.11963; published in IEEE TEVC per arXiv listing [unverified]) — [arXiv](https://arxiv.org/html/2401.11963v3). "Evolutionary Reinforcement Learning: A Survey" (Intelligent Computing, 2023) treats hyperparameter optimization, reward shaping and MORL as separate categories and notes that MORL "has mainly used NSGA-II and the HV metric" — [Intelligent Computing](https://spj.science.org/doi/10.34133/icomputing.0025). "Evolutionary Reinforcement Learning: A Systematic Review and Future Directions" (arXiv 2402.13296) — [arXiv](https://arxiv.org/pdf/2402.13296)

### Inferences
- The EC+DRL design space in edge/fog splits as follows. Most common: EC searches decisions directly, or EC is a baseline. Less common: EC trains policy weights. Rare or absent: EC searches reward weights or hyperparameters for an RL offloading agent. A paper on "MOEA-selected reward weights for PPO in fog" therefore occupies an almost empty niche.
- Because many hybrids report gains against weak baselines (Random, Greedy, a fixed-weight PPO) without compute matching, a negative or neutral result under compute-matched controls would be a real methodological contribution.

### Gaps
- I could not read the full texts of the Sci Rep 2026, CMC 2025 and FGCS dependent-task papers, so I cannot confirm what their EC layer encodes.
- I found no edge/fog paper that tunes DRL hyperparameters with a GA. A review mentions a "GA for DDRL" vehicular paper, but I could not locate the primary source.

## Q2. Which papers do evolutionary or automated reward-weight / reward-shaping search for RL, and do they report compute cost or compare against random search or longer training?

### Takeaway
The main evolutionary reward-search papers are Faust et al. 2019, Chiang et al. 2019 RA-L, PBT and its Capture-the-Flag use, and Dierkes et al. 2024. They report large compute (for example 1,000 agents, 12 days) and compare against hand-tuned rewards or hyperparameter-only tuning. None uses a pure random-search baseline at equal budget or a "train one agent longer" baseline. Their outer loops do begin with a random-sampling phase, but that phase is never reported as a separate baseline.

### Cited Findings
- **Faust, Francis & Mehta (2019), "Evolving Rewards to Automate Reinforcement Learning", 6th ICML Workshop on AutoML (arXiv 1905.07628).**
  - Method: AutoRL is an evolutionary layer that treats reward tuning as hyperparameter optimization. The proxy reward is a re-weighting of the standard Gym reward components (achievement such as velocity or height, control cost, impact cost, alive bonus).
  - Outer loop: Gaussian Process Bandits via Google Vizier. Up to n_g = 1000 agents with 100 parallel workers, and the first 100 reward parameterizations are sampled randomly. Each agent is evaluated over 50 trajectories.
  - Cost: wall-clock is about n_g/n_mc (≈10x) a single RL run, on 100x the processors. SAC uses 2M steps per agent; PPO uses about 19.8M (Ant, Walker) to 158.4M (Humanoid, Standup) steps per agent.
  - Baselines: hand-tuned reward with default hyperparameters (HT) and Vizier-tuned learning hyperparameters (HP). **No random-search baseline and no equal-compute longer-training baseline.**
  - Results: beats HP on all SAC tasks and on Walker/Humanoid with PPO, with a 489% gain on SAC Humanoid's single-task objective. Gains are small on simpler tasks.
  - Sources: [arXiv](https://arxiv.org/abs/1905.07628); [ar5iv full text](https://ar5iv.arxiv.org/html/1905.07628); [Google Research](https://research.google/pubs/evolving-rewards-to-automate-reinforcement-learning/)
- **Chiang, Faust, Fiser & Francis (2019), "Learning Navigation Behaviors End-to-End with AutoRL", IEEE RA-L 4(2):2007–2014, DOI 10.1109/LRA.2019.2899918.**
  - AutoRL first searches reward weights to maximize task completion, then searches network architecture to maximize cumulative found reward. The first n_mc trials choose reward weights randomly, and later trials use a gradient-free optimizer.
  - Reports 23% and 26% higher success than comparison methods (path following and point-to-point).
  - The authors state that AutoRL "is not sample efficient: it took 12 days to train 1000 agents."
  - Sources: [arXiv 1809.10124](https://arxiv.org/abs/1809.10124); [ar5iv](https://ar5iv.arxiv.org/html/1809.10124)
- **Jaderberg et al. (2017), "Population Based Training of Neural Networks", arXiv 1711.09846.** PBT is an asynchronous method that "effectively utilises a fixed computational budget to jointly optimise a population of models and their hyperparameters" through exploit (copy a better model) and explore (perturb its hyperparameters) — [arXiv](https://arxiv.org/abs/1711.09846v2)
- **Jaderberg et al. (2019), Science 364:859–865, Quake III Capture the Flag (arXiv 1807.01281).** A population of 30 agents is used to evolve each agent's *internal reward* (dense shaping on top of sparse win/loss) and its hyperparameters. This is PBT-based evolutionary reward shaping at scale — [Science PDF](https://people.eecs.berkeley.edu/~russell/classes/cs294/f21/papers/Jaderberg-etal-2019-Science-Capture-The-Flag.pdf); [arXiv 1807.01281](https://ar5iv.arxiv.org/html/1807.01281)
- **Dierkes, Cramer, Hoos & Trimpe (2024), "Combining Automated Optimisation of Hyperparameters and Reward Shape", Reinforcement Learning Journal (RLC 2024), arXiv 2406.18293.**
  - Jointly optimizes PPO/SAC hyperparameters and reward weights on LunarLander, Ant, Humanoid and Wipe, adding a variance penalty as an objective.
  - Finds hyperparameters and reward weights mutually dependent. Combined optimisation "significantly improves over baseline in half of the environments and is competitive in the others", with only a minor added compute cost.
  - The abstract does not say whether a random-search baseline was used or which optimizer was used (I could not verify the full text).
  - Source: [arXiv](https://arxiv.org/abs/2406.18293)
- **Evolutionary bilevel reward shaping (arXiv 2606.16236, 2026).** Optimizes reward parameters with CMA-ES (bounded to [-5, 5]) for generalization across physical-parameter variations — [arXiv](https://arxiv.org/html/2606.16236v1) [snippet-level; authors and venue unverified]
- **Contrast, LLM reward design: Ma et al. (2024), "Eureka: Human-Level Reward Design via Coding Large Language Models", ICLR 2024 (arXiv 2310.12931).** GPT-4 writes reward code inside an evolutionary-style loop of generate, train and reflect. It beats expert human rewards on most of 29 tasks across 10 robot morphologies, with a 52% average normalized improvement. This is also a compute-heavy outer loop (many RL trainings per iteration) compared mainly against human rewards — [arXiv](https://arxiv.org/abs/2310.12931); [ICLR](https://iclr.cc/virtual/2024/poster/18971)
- **Survey: Parker-Holder, Rajan, Song, Biedenkapp, Miao, Eimer, Zhang, Nguyen, Calandra, Faust, Hutter & Lindauer (2022), "Automated Reinforcement Learning (AutoRL): A Survey and Open Problems", JAIR 74:517–568, DOI 10.1613/jair.1.13596.** Covers reward design and environment design as part of the AutoRL pipeline, and notes that grid and random search keep hyperparameters fixed within a run — [JAIR](https://www.jair.org/index.php/jair/article/view/13596); [arXiv 2201.03916](https://arxiv.org/abs/2201.03916); [AutoML.org overview](https://www.automl.org/autorl-survey/) (full author list from memory of the arXiv page [partly unverified])
- **Felten, Gareev, Talbi & Danoy (2023), "Hyperparameter Optimization for Multi-Objective Reinforcement Learning", MoDeM workshop, Kraków (arXiv 2310.16487).** Formalizes HPO for MORL and reports preliminary gains for a state-of-the-art MORL algorithm. Peer-review status conflicts between ORBilu ("peer reviewed") and SciCast ("preprint") — [arXiv](https://arxiv.org/abs/2310.16487); [ORBilu](https://orbilu.uni.lu/handle/10993/58788)

### Inferences
- In the canonical evolutionary reward-search papers, the reported gains are measured against hand-tuned or HP-only baselines, at 10–1000x the compute of a single training run. None isolates "smart search vs random search at equal budget" or "search vs spending the same budget on one longer run". This is exactly the control the user's paper adds.
- Faust 2019 itself observes that gains are small on simpler tasks and largest on Humanoid. This supports the view that reward-weight search pays off mainly when the default reward is badly mis-specified. That may not hold for a sensibly normalized equal-weight offloading reward (inference).

### Gaps
- I could not confirm whether Dierkes et al. 2024 includes a random-search or equal-compute baseline; the full text needs checking.
- I found no paper that compares evolutionary reward-weight search against "train the default-reward agent for N times longer" at matched environment steps.

## Q3. Which papers compare NSGA-II, NSGA-III, MOEA/D and SPEA2 in fog/edge/cloud scheduling, offloading or placement, and what were the outcomes?

### Takeaway
Head-to-head MOEA comparisons in fog/edge/cloud are few, usually cover only 2–3 algorithms, and are often run by authors promoting their own variant. The most cited neutral study, Guerrero, Lera & Juiz (FGCS 2019), found that NSGA-II gave the best objective values and diversity while MOEA/D was fastest. I found no single controlled study of all four (NSGA-II, NSGA-III, MOEA/D, SPEA2) on one fog benchmark. Outcomes vary with the problem.

### Cited Findings
- **Guerrero, Lera & Juiz (2019), "Evaluation and efficiency comparison of evolutionary algorithms for service placement optimization in fog architectures", Future Generation Computer Systems 97:131–144, DOI 10.1016/j.future.2019.02.056 (arXiv 2501.09958).**
  - Compares a weighted-sum GA (WSGA), NSGA-II and MOEA/D on fog service placement. Objectives are latency, service spread and resource use, on a Barabási–Albert topology of 100 devices with 100 and 200 services.
  - NSGA-II "obtained the highest optimizations of the objectives and the highest diversity of the solution space"; MOEA/D "was better to reduce the execution times"; WSGA "did not show any benefit" over the other two.
  - Sources: [arXiv 2501.09958](https://arxiv.org/html/2501.09958v1); [UIB repository](https://dspace.uib.es/xmlui/handle/11201/167131?show=full)
- **Hybrid MOEAs for service placement in the computing continuum.** "Hybrid multi-objective evolutionary algorithms for service placement in the computing continuum: a comparative study with genetic traceability" (arXiv 2607.13200, 2026) is a recent comparative placement study — [arXiv](https://arxiv.org/pdf/2607.13200) [found in search only; contents unverified]
- **I-NSGA-III for many-objective QoS in fog–cloud (MDPI IoT, 2026, 7(4):97).** Reports that NSGA-III generally beat NSGA-II on latency, with more variable cost. It also restates the Guerrero et al. finding (NSGA-II best optimization and diversity, MOEA/D faster) — [MDPI IoT](https://www.mdpi.com/2624-831X/7/4/97) [snippet-level; page returned 403]
- **M-E-AWA (Processes 2023, 11(4):1053, DOI 10.3390/pr11041053).** A MOEA/D variant with adaptive weight vectors for fog task scheduling. It compares MOEA/D, NSGA-II and NSGA-III but on DTLZ test functions; NSGA-II was much worse than MOEA/D there — [DOI](https://doi.org/10.3390/pr11041053) [snippet-level]
- **IEEE TCC 2020/2022, "An Automated Task Scheduling Model using Non-Dominated Sorting Genetic Algorithm II for Fog-Cloud Systems" (DOI 10.1109/TCC.2020.3032386; Choo is a co-author per the hosting UTSA page; full author list not verified).** A search summary reports that its DNSGA-II cut average makespan by about 37–42% against SPEA-II, MOPSO, PESA-II and MOEA/D. These are the authors' own-method claims — [UTSA PDF](https://cspecc.utsa.edu/publications/files/Refereed_Papers/2020_Choo_Automated_Task_Scheduling.pdf) [numbers snippet-level, not verified in full text]
- **Latency-aware multi-objective fog scheduling (LAMOMRank).** Benchmarks NSGA-II and SPEA2 against the proposed method and MOHEFT; NSGA-II and SPEA2 are credited with strong results — [ResearchGate 380280421](https://www.researchgate.net/publication/380280421_Latency-Aware_Multi-Objective_Fog_Scheduling_Addressing_Real-Time_Constraints_in_Distributed_Environments) [snippet-level; venue unverified]
- **RIOT (arXiv 1708.08127, cloud workflow scheduling; Chen & Menzies, published in a later venue [unverified]).** Uses EMSC with NSGA-II, SPEA2 and MOEA/D as the inner MOEA. The three variants performed close to one another and were all much slower than RIOT. The paper frames them as differing mainly in how they select the frontier from the population — [arXiv](https://arxiv.org/pdf/1708.08127)
- **MEC offloading with multi-objective whale optimization (Sensors 2021, 21(8):2628, DOI 10.3390/s21082628).** Benchmarks include MOEA/D-DE, MOEA/D-DRA and NSGA-III with hypervolume; MOEA/D-DE beat NSGA-III on several metrics — [DOI](https://doi.org/10.3390/s21082628) [snippet-level]
- **IoV offloading (Wireless Personal Communications, Springer, 2024, DOI 10.1007/s11277-024-11499-0).** A MOEA/D-based scheme for delay, energy and load balance, compared against NSGA-II, NSGA-III, PESA-II and SPEA2; numbers were not seen — [Springer](https://link.springer.com/article/10.1007/s11277-024-11499-0) [snippet-level]
- **Multi-user VR MEC (arXiv 2510.14243).** Normalized HV: NSGA-II 0.6615 vs MOEA/D 0.6572, essentially tied — [arXiv](https://arxiv.org/pdf/2510.14243) [snippet-level]
- **IIoT constrained offloading (decomposition multitasking).** Compared against NSGA-II, MOEA/D, NSGA-III, RVEA, SMS-EMOA and SPEA2 on HV/IGD, with the proposed constrained decomposition method best. I could not confirm the ranking among the baseline MOEAs — [ResearchGate 412799548](https://www.researchgate.net/publication/412799548_Exploiting_Base-Station_Separability_in_Constrained_Multiobjective_Task_Offloading_for_the_Industrial_Internet_of_Things_A_Decomposition_Multitasking_Method_with_Exact_Pareto-Front_Synthesis) [snippet-level]
- **Survey context.** "Genetic-based optimization in fog computing: current trends and research opportunities" (arXiv 2112.01958) — [arXiv](https://arxiv.org/pdf/2112.01958)

### Inferences
- The fog literature broadly shows NSGA-II as strong on quality and diversity for 2–3 objectives, MOEA/D as fastest, and NSGA-III mattering mainly at 4+ objectives. A "no clear winner" result among MOEAs on a 2–3-objective reward-weight problem would match this literature.
- Most comparisons pit a proposed variant against untuned baselines, so differences between NSGA-II, MOEA/D and SPEA2 as baselines are often within noise (for example RIOT, VR-MEC HV 0.6615 vs 0.6572).

### Gaps
- No neutral four-way (NSGA-II / NSGA-III / MOEA/D / SPEA2) benchmark on a fog or iFogSim workload was found.
- Several outcome numbers above are snippet-level and need checking in the full texts.

## Q4. Is there evidence that random search is competitive in AutoRL/HPO, or that search gains vanish under compute-matched comparison?

### Takeaway
Yes, with caveats. Several strong sources show random search to be a competitive baseline in RL and in NAS/HPO. RL results are dominated by seed variance, and tuning on the evaluation seeds inflates gains. Eimer et al. (ICML 2023), however, find that random search scales worse than better HPO methods at larger budgets. I found no study that directly shows reward-search gains vanishing against "train longer at equal compute".

### Cited Findings
- **Mania, Guy & Recht (2018), "Simple random search of static linear policies is competitive for reinforcement learning", NeurIPS 2018 (arXiv 1803.07055).** Random search (ARS) matches or exceeds state-of-the-art sample efficiency on MuJoCo and is at least 15x more computationally efficient than ES. The authors show high sensitivity to hyperparameters and seeds, warning that tuning can "artificially improve the perceived sample efficiency" — [NeurIPS PDF](https://papers.nips.cc/paper/2018/file/7634ea65a4e6d9041cfd3f7de18e334a-Paper.pdf); [arXiv](https://arxiv.org/abs/1803.07055)
- **Li & Talwalkar (2019), "Random Search and Reproducibility for Neural Architecture Search", UAI 2019 (arXiv 1902.07638).** Random search is a competitive baseline. The paper proposes the "multiple of random search" metric, meaning how much more compute random search needs to match a method — a direct template for compute-matched reporting — [arXiv](https://arxiv.org/pdf/1902.07638)
- **Eimer, Lindauer & Raileanu (2023), "Hyperparameters in Reinforcement Learning and How To Tune Them", ICML 2023, PMLR 202:9104–9149.**
  - The hyperparameter landscape "can strongly depend on the tuning seed, which may lead to overfitting", so tuning and test seeds should be kept separate.
  - Grid sweeps are "suboptimal and costly compared to even simple HPO baselines like random search".
  - Random search is "not a bad choice on smaller budgets" but does not scale as well as better HPO methods.
  - HPO tools beat hand-tuning using fewer resources.
  - Sources: [PMLR](https://proceedings.mlr.press/v202/eimer23a); [arXiv 2306.01324](https://arxiv.org/html/2306.01324v1)
- **Franke, Köhler, Biedenkapp & Hutter (2021), "Sample-Efficient Automated Deep Reinforcement Learning" (SEARL), ICLR 2021 (arXiv 2009.01555).** The random-search baseline (20 TD3 configs × 1M frames) and modified PBT need about an order of magnitude more environment steps than SEARL to reach the same reward. The comparison is at matched reward, not matched compute — [arXiv](https://arxiv.org/pdf/2009.01555)
- **PB2 / population-based AutoRL (Parker-Holder et al.; arXiv 2106.15883 is the mixed-input follow-up, "Tuning Mixed Input Hyperparameters on the Fly for Efficient Population Based AutoRL", NeurIPS 2021).** Random search shows linear regret, while PBT-style methods give incremental improvements — [arXiv 2106.15883](https://arxiv.org/html/2106.15883v1) [snippet-level]
- **Reijnen, Zhang, Lau & Bukhsh (2022), "Learning Adaptive Evolutionary Computation for Solving Multi-Objective Optimization Problems" (arXiv 2211.09719; authors from memory [unverified]).** A DRL controller for NSGA-III parameters reached HV 0.92, against 0.91 for the *untrained/random* DRL controller and 0.89 for tuned NSGA-III. The learned method's margin over a random variant is small — [arXiv](https://arxiv.org/html/2211.09719)
- Classic background (not re-fetched): Bergstra & Bengio (2012), "Random Search for Hyper-Parameter Optimization", JMLR 13:281–305; Henderson et al. (2018), "Deep Reinforcement Learning that Matters", AAAI 2018, on seed variance and reporting. Both are well known; no URL was fetched in this session.

### Inferences
- The user's finding (NSGA-II ≈ random search; longer training at equal compute beats search) fits Mania et al. (seed and hyperparameter sensitivity), Li & Talwalkar (random search as a strong baseline, so report a multiple-of-random-search) and Eimer et al. (random search is fine at small budgets; tuning-seed overfitting). With small search budgets, typical for expensive DRL inner loops, little separation between NSGA-II and random search is expected.
- The "train longer" control is under-used in the AutoRL literature. Faust 2019 and Chiang 2019 report 10x–1000x compute without one. This is a defensible novelty claim if phrased carefully.

### Gaps
- I found no paper that explicitly shows reward-weight search gains disappearing against a compute-matched longer single run. This should be stated as absent from the literature found, not as proven absent.

## Q5. Is there any prior benchmark of several MOEAs for reward-weight tuning of DRL (any domain)?

### Takeaway
None found. After targeted searches I found no study that benchmarks several MOEAs (NSGA-II, NSGA-III, MOEA/D, SPEA2, or with CMA-ES or random search) as outer-loop optimizers of DRL reward weights, in any domain. Nearby work either uses a single optimizer for reward search (GP-bandit/Vizier, PBT, CMA-ES, an LLM loop), compares MOEAs on decision problems without RL, or uses MOEAs to train policies or produce Pareto sets of policies (EMOGI, MOEA-based MORL).

### Cited Findings
Queries tried (WebSearch, standard and extended modes):
1. "NSGA-II reward weights deep reinforcement learning task offloading edge computing"
2. "multi-objective evolutionary algorithm optimize reward function weights reinforcement learning NSGA-II PPO"
3. "evolutionary search reward weights DRL 'compared with random search' reward shaping hyperparameters benchmark multiple MOEAs"
4. "multi-objective evolutionary optimization of reward weights for deep reinforcement learning agent comparison NSGA-II MOEA/D CMA-ES random search"
5. "genetic algorithm optimizes reward function weights deep reinforcement learning scheduling cloud fog DQN PPO weight coefficients"
6. "genetic algorithm hyperparameter optimization DRL task offloading edge computing PSO DQN hybrid"

Closest items found, none of which is a multi-MOEA reward-weight benchmark:
- Faust et al. 2019 and Chiang et al. 2019: single outer optimizer (GP bandits/Vizier) over reward weights — [arXiv 1905.07628](https://arxiv.org/abs/1905.07628); [arXiv 1809.10124](https://arxiv.org/abs/1809.10124)
- Dierkes et al. 2024: joint HPO plus reward-weight optimization, with one optimizer family — [arXiv 2406.18293](https://arxiv.org/abs/2406.18293)
- EMOGI: NSGA-II over policies, with reward components as objectives — [arXiv 2202.12028](https://arxiv.org/pdf/2202.12028)
- An RL paper uses NSGA-II and MOEA/D as "two of the most popular" MOEAs, but as baselines against an MORL method, not as reward tuners — [arXiv 2311.12495, MORL/D taxonomy](https://arxiv.org/pdf/2311.12495) [snippet-level]
- MOEA comparisons in neighbouring settings without RL: NSGA-II approximated the front better than MOEA/D in neurotrajectory prediction, with MOEA/D suggested for preference-biased search — [arXiv 2308.02710](https://arxiv.org/pdf/2308.02710) [snippet-level]

### Inferences
- A controlled benchmark of NSGA-II vs other MOEAs vs random search as outer loops for PPO reward weights, with a compute-matched longer-training control, appears to be **novel** going by these searches. The claim should be worded as "to our knowledge, no prior study…", listing the databases and queries used.
- The literature in Q3 and Q4 suggests a multi-MOEA extension would likely show small, noisy differences between MOEAs at low evaluation budgets, which would strengthen rather than overturn the user's negative result (inference).

### Gaps
- Google Scholar, IEEE Xplore and Scopus were not queried directly (web search only). A final check there with queries such as "reward weight" AND (NSGA-II OR MOEA/D OR SPEA2) AND "reinforcement learning" is recommended before claiming novelty in the paper.
