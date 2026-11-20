# DRL for Task Offloading in IoT-Fog-Edge-Cloud: Multi-Objective Rewards, Weight Selection, Simulators, Baselines and Statistical Rigor

Research notes (English). Compiled 2026-11-20. Budget limits applied: about 20 tool calls. Many publisher pages (ACM DL, MDPI, ScienceDirect, Springer) returned 403 or login redirects, so some details come from search snippets or arXiv versions. That is noted wherever it applies. Q1 status is **not verified for any venue** in these notes. The report writer should check SJR/JCR before calling anything Q1.

Important exclusion: one search hit was the user's own repository (github.com/Yorskies/IFogsim2-ERWOPPO). It is the paper under development, not independent literature, and must not be cited as prior work.

## Q1. Which papers (2019-2026) use DRL for fog/edge offloading or scheduling with multi-objective weighted rewards, and how are the weights justified?

### Takeaway
A weighted-sum scalarized reward (latency + energy, sometimes + load balance or deadline/failure penalties) is the dominant formulation. In the papers checked in full text (the Buyya group's TMC 2023 and DRLIS papers), the weights are **fixed by hand to equal values (0.5/0.5)**, justified only as "equal importance" and "users can adjust." A smaller, newer line of work (2021-2026) argues that fixed weights are unknowable in advance and uses preference-conditioned or Pareto MORL instead. I found no fog/edge DRL paper that tunes reward weights with NSGA-II or any other metaheuristic. That is a gap the target paper can occupy, and a negative result there is new.

### Cited Findings
**Fixed, equal weights (checked in full text)**
- Goudarzi, Palaniswami, Buyya, "A Distributed Deep Reinforcement Learning Technique for Application Placement in Edge and Fog Computing Environments," *IEEE Transactions on Mobile Computing* 22(5):2491-2505, 2023 (arXiv 2110.12415). Method: X-DDRL, an IMPALA-based distributed actor-critic. Weighted cost per task ϕ = w1·ψ (execution time) + w2·ω (IoT device energy), with constraint w1 + w2 = 1. Quote: "both w1 and w2 are set to 0.5, meaning that the importance of execution time and the energy consumption is equal in the results." The paper adds that the weights "can be adjusted based on the users' requirements and network conditions." It reports up to 30% execution-cost improvement. — [ar5iv full text](https://ar5iv.labs.arxiv.org/html/2110.12415); [dblp TMC record](https://dblp.dagstuhl.de/rec/journals/tmc/GoudarziPB23.html); [arXiv](https://arxiv.org/abs/2110.12415v1)
- Wang, Goudarzi, Gong, Buyya, "Deep Reinforcement Learning-based Scheduling for Optimizing System Load and Response Time in Edge and Fog Computing Environments" (DRLIS), arXiv 2309.07407 (v2 Oct 2023). Method: PPO (clipped). Reward on success = w1·Norm(r_lb) + w2·Norm(r_rt), with a large negative penalty on failure. Load balance = a1·Var(CPU) + a2·Var(RAM). Quote: "both w1 and w2 are set to 0.5 in Eq. 19, meaning that the importance of load balancing and response time are equal." a1 = a2 = 0.5 "to show the equal importance of CPU and RAM." Reported reductions: up to 55% (load balancing), 37% (response time), 50% (weighted cost). — [ar5iv full text](https://ar5iv.labs.arxiv.org/html/2309.07407); [arXiv abs](https://arxiv.org/abs/2309.07407). Journal venue is unverified: the arXiv page lists none. My recollection is that it was published in *Future Generation Computer Systems* (2024), but I could not confirm that.
- The same group's TF-DDRL extends the weighted cost to response time + energy + monetary cost (weighting details not checked). — [arXiv 2410.14348](https://arxiv.org/html/2410.14348v2)

**Weighted sum as the field default (survey and snippet level)**
- The ACM systematic review "Reinforcement Learning Methods for Computation Offloading: A Systematic Review" (ACM Computing Surveys, DOI 10.1145/3603703) states that when the goal is to jointly reduce delay and energy, "the reward function is expressed as the weighted sum of these two parameters," and that designing an appropriate reward "is a subtle task." This comes from a search snippet; the full text returned 403. — [ACM DL](https://dl.acm.org/doi/10.1145/3603703)
- Mashal et al., "Multiobjective Offloading Optimization in Fog Computing Using Deep Reinforcement Learning," *Journal of Computer Networks and Communications* (Wiley/Hindawi), 2024. It uses a DQN with a reward that is a weighted combination of delay and energy (snippet level). — [Wiley](https://onlinelibrary.wiley.com/doi/full/10.1155/2024/6255511)
- A multi-agent TD3 paper for delay-sensitive fog offloading (*Electronics* 14(11):2169, MDPI, 2025) runs a **weight-coefficient ablation**. Prioritizing latency "significantly reduces average latency while energy consumption increases, but maintains an acceptable range." This is an example of the "sensitivity sweep" practice (snippet level). — [MDPI DOI](https://doi.org/10.3390/electronics14112169)
- A hybrid DQN/actor-critic paper for Fog-IoT (JESA, IIETA, 2025; low-tier venue, not Q1) uses three weights (α, β, γ) over latency, energy and deadline-miss penalty. — [IIETA](https://iieta.org/journals/jesa/paper/10.18280/jesa.581016)
- Huang, Bi, Zhang, DROO (arXiv 1808.01977) maximizes the **weighted sum of computation rates** across wireless devices, with the weights treated as given system parameters. It reports over 99.5% of the near-optimal benchmark's computation rate. Venue: my recollection is *IEEE TMC* 2020, but that is **unverified** here. — [arXiv](https://arxiv.org/pdf/1808.01977)
- Tang & Wong, "Deep Reinforcement Learning for Task Offloading in Mobile Edge Computing Systems," *IEEE TMC* (author PDF labelled TW-TMC-2020; arXiv 2005.02459). It uses distributed deep Q-learning (with LSTM and dueling/double extensions, per my recollection) for tasks with deadlines that may be dropped. The cost combines delay and dropped tasks. The exact weighting was not checked. — [author PDF](https://people.ece.ubc.ca/vincentw/J/TW-TMC-2020.pdf); [arXiv](https://arxiv.org/pdf/2005.02459)

**Preference-conditioned / Pareto MORL (the alternative to fixed weights)**
- "Offloading dependent tasks in multi-access edge computing: A multi-objective reinforcement learning approach," *Future Generation Computer Systems* (ScienceDirect pii S0167739X21004039, so FGCS, about 2021/2022). MORL-DWS learns weight-dependent vector Q-values and uses tournament selection over preferences. It claims to be "the first work to apply MORL to the computation offloading problem." Authors (Song, Xing et al., per my recollection) and volume are **unverified**, because the page returned 403. — [ScienceDirect](https://www.sciencedirect.com/science/article/abs/pii/S0167739X21004039)
- Yang, Wen, Zhang, Tang, "Multi-objective Deep Reinforcement Learning for Mobile Edge Computing," arXiv 2307.14346 (2023). The arXiv comment reads "Received by IEEE WiOpt 2023" (conference; final publication not confirmed). It is PPO-based MORL for energy and delay under **unknown preferences**. It argues preferences are "often unknown or challenging to specify in advance" and reports up to 233.1% higher Pareto-front hypervolume than benchmarks. — [arXiv](https://arxiv.org/abs/2307.14346)
- Follow-up: "Generalizable Pareto-Optimal Offloading with Reinforcement Learning in Mobile Edge Computing," arXiv 2509.10474 (2025). It targets generalization to unseen preferences. Venue is unverified. — [arXiv](https://arxiv.org/abs/2509.10474)
- PGN-MO-DDQN, a preference-generation network with Chebyshev scalarization for edge video-analytics offloading, evaluated on **EdgeSimPy**. It appears in an Elsevier journal (pii S1570870525003488, the ISSN of *Ad Hoc Networks*; this journal identification is my inference), 2025. — [ScienceDirect](https://www.sciencedirect.com/science/article/abs/pii/S1570870525003488)
- Zou et al., "Task Offloading Algorithm Based on Preference Weight Adaptive Multi-objective Reinforcement Learning for Cloud-Assisted MEC in IoV," *Automotive Innovation*, 2026. It combines Dueling Double DQN with preference-conditioned MORL. — [BIT Pure](https://pure.bit.edu.cn/en/publications/task-offloading-algorithm-based-on-preference-weight-adaptive-mul/)
- In adaptive distributed MARL for vehicles, objective weights are sampled periodically to simulate changing preferences. — [arXiv 2403.08879](https://arxiv.org/html/2403.08879v1)

**Metaheuristic tuning of weights: closest analogues (not fog DRL)**
- One search for NSGA-II tuning DRL reward weights found no such fog/edge paper. The nearest analogue is a robot/job-shop scheduling scheme in which an upper-layer NSGA-II "adaptively tunes cost-function weights" for a lower-layer min-cost-max-flow solver, which is not a DRL agent. Other hybrids go the other way: RL guides NSGA-II's operator selection (e.g., QNSGA-II; DRL-enhanced NSGA-II in *Systems* 13(8):659, 2025). — [MDPI Systems](https://doi.org/10.3390/systems13080659); [ScienceDirect QNSGA-II](https://www.sciencedirect.com/science/article/abs/pii/S2210650224001962); [Sci Rep 2026 NSGA-II+RL multi-cloud](https://www.nature.com/articles/s41598-026-51105-w)

### Inferences
- The weighting practices seen are: (a) fixed equal weights (most common in the strong-venue papers checked: Goudarzi TMC 2023, DRLIS); (b) hand-fixed unequal weights with a one-factor sensitivity sweep (the MDPI TD3 paper); (c) preference-conditioned or Pareto MORL (FGCS MORL-DWS, Yang et al. 2023, PGN-MO-DDQN, Zou 2026). Category (d), outer-loop metaheuristic search over reward weights for an offloading DRL agent, appears essentially absent. The target paper's finding that NSGA-II did not beat equal weights is therefore new, and it also supports the community's equal-weight default empirically.
- Equal weights are usually justified by assertion ("equal importance"), not by evidence. The target paper's result gives the first compute-controlled evidence that this default is hard to beat.

### Gaps
- Exact reward weights for Tang & Wong (TMC) and Mashal 2024 were not verified in full text.
- Journal venues for DRLIS (FGCS 2024?) and DROO (IEEE TMC 2020?) are unverified. MORL-DWS authors and volume are unverified.
- I did not find a quantitative census of how often weights are equal vs. tuned. No survey reports such a count.

## Q2. Which papers compare PPO against DQN, DDPG, A2C or Q-learning for offloading, and what did they find? Are the comparisons budget-matched and multi-seed?

### Takeaway
Many papers compare PPO with DQN, A2C or DDPG, and PPO usually "wins." Rankings are inconsistent across papers, though: a 2025 fog survey places TD3 first and PPO mid-pack, and one cloud-edge study found DQN best. None of the comparisons I could inspect stated that training budgets were matched or reported multiple seeds or significance tests.

### Cited Findings
- DRLIS (Wang, Goudarzi, Gong, Buyya, arXiv 2309.07407): PPO vs **DQN, Q-Learning, NSGA2 and NSGA3** (pymoo) on a FogBus2 physical testbed (Nectar, AWS, Raspberry Pi, MacBook, Linux VM). PPO is best on load balance, response time and weighted cost. The number of runs, seeds and significance tests was not reported in the text read (100k of about 122k characters read). — [ar5iv](https://ar5iv.labs.arxiv.org/html/2309.07407)
- Goudarzi et al. TMC 2023: X-DDRL vs PPO-RNN, PPO-No-RNN, Double-DQN (Ray) and Greedy, in a custom Python/OpenAI-Gym event-driven simulator plus a Raspberry Pi/Jetson/cloud testbed. Datasets: 100 DAGs per set, 25 topologies per task count. **No number of independent runs or seeds is stated, and no hypothesis tests.** Testbed results (Fig. 7) carry 95% CIs. — [ar5iv](https://ar5iv.labs.arxiv.org/html/2110.12415)
- "Proximal Policy Optimization for Efficient D2D-Assisted Computation Offloading and Resource Allocation in Multi-Access Edge Computing," *Future Internet* 16(1):19, MDPI, 2024. PPO "emerged as the superior performer in comparison to the DQN and A2C models, particularly in terms of optimizing the trade-off between the delay and energy consumption." DQN was steadier in some training phases (snippet level; the full text returned 403). — [MDPI DOI](https://doi.org/10.3390/fi16010019)
- Ali, Abawajy, Lemma, Baho, "Analysis of Deep Reinforcement Learning Algorithms for Task Offloading and Resource Allocation in Fog Computing Environments," *Sensors* 25(17):5286, 2025. This is a survey-style synthesis comparing TD3, A3C, DDPG, SAC, PPO and DQN. It reports TD3 best across latency, energy, task success and decision time. PPO slightly beats SAC on energy and success but has high decision time. DQN, despite being "the most widely used algorithm," has the highest latency and decision time. Its comparisons are summaries of prior figures, not new controlled experiments. — [PMC](https://pmc.ncbi.nlm.nih.gov/articles/PMC12431013/)
- "Research on Edge Computing and Cloud Collaborative Resource Scheduling" (arXiv 2502.18773; venue unverified). In a small preliminary experiment (100 tasks, 5 edge + 2 cloud nodes), DQN led PPO, A3C and DDPG in convergence speed and stability. — [arXiv](https://arxiv.org/pdf/2502.18773)
- Satellite-terrestrial offloading (arXiv 2306.17183): PPO converged faster and to higher reward than DQN, A2C and TRPO. — [arXiv](https://arxiv.org/pdf/2306.17183)
- A benchmarking paper on dynamic SLO compliance in the computing continuum (Sedlak et al., EDGE 2025) reports PPO and A2C performing well, while DQN "suffers from instability and sample inefficiency." — [TU Wien PDF](https://dsg.tuwien.ac.at/team/sd/papers/EDGE_2025_B_Sedlak_Benchmarking.pdf)
- Vehicular task scheduling (UVa repository, venue unverified): PPO outperformed DQN on waiting time and load balance. — [UVaDOC](https://uvadoc.uva.es/bitstream/handle/10324/78725/Deep%20Reinforcement%20Learning-based%20Task%20Scheduling.pdf?sequence=1&isAllowed=y)
- An iFogSim2 + Python-PPO multi-cloud scheduling study (NCI MSc thesis, not peer-reviewed) compares PPO against RR, FCFS, DQN and A2C on the same workloads. — [NORMA NCIRL](https://norma.ncirl.ie/9266/1/priyashanmugam.pdf)

### Inferences
- The "PPO beats DQN" narrative is common but rests on single-run, non-budget-matched comparisons, and some studies contradict it (DQN best in arXiv 2502.18773; TD3 best in the Sensors 2025 synthesis). That variability is itself a symptom of the evaluation-rigor problem: rankings likely depend on tuning effort, budget and seed.
- Comparing DRL against NSGA-II/NSGA-III as *direct schedulers* (DRLIS) differs from the target paper's design, where NSGA-II searches reward weights. No paper found compares "longer training at equal weights" against "weight search" at matched total compute.

### Gaps
- I could not verify full-text budget or seed details for the MDPI *Future Internet* 2024 paper (403).
- No paper found explicitly states equal environment-step budgets across PPO, DQN and DDPG baselines.

## Q3. How common is reporting of multiple seeds, CIs or hypothesis tests? Do any surveys criticize evaluation rigor in DRL-for-edge papers?

### Takeaway
In the offloading papers inspected, multi-seed reporting and hypothesis tests are rare to absent. Even the TMC 2023 paper reports no seed count and gives CIs only for testbed results. Rigor criticism exists in general DRL methodology papers (Henderson et al. AAAI 2018; Agarwal et al. NeurIPS 2021). Domain surveys raise weaker versions of it, such as missing baselines, insufficient benchmarking and suspiciously uniform convergence. I found no edge/fog survey that systematically counts seeds or significance tests.

### Cited Findings
- Henderson et al., "Deep Reinforcement Learning that Matters," AAAI 2018 (arXiv 1709.06560). It shows reported results vary greatly with seeds and implementations, and recommends significance testing, confidence intervals and power analysis. — [arXiv](https://arxiv.org/pdf/1709.06560)
- Agarwal et al., "Deep Reinforcement Learning at the Edge of the Statistical Precipice," NeurIPS 2021. Point estimates from few runs ignore statistical uncertainty. It proposes interval estimates (stratified bootstrap CIs, IQM, performance profiles) and the `rliable` library, and shows conclusions on Atari 100k change under proper analysis. — [arXiv](https://arxiv.org/abs/2108.13264); [ACM DL](https://dl.acm.org/doi/10.5555/3540261.3542505)
- AdaStop: adaptive sequential statistical testing for comparing deep RL agents (arXiv 2306.10882). — [arXiv](https://arxiv.org/pdf/2306.10882)
- Goudarzi et al. TMC 2023 reports no run or seed counts or hypothesis tests. It shows 95% CIs only for the testbed figure. — [ar5iv](https://ar5iv.labs.arxiv.org/html/2110.12415)
- DRLIS: no seeds, variance or tests visible in the text read. — [ar5iv](https://ar5iv.labs.arxiv.org/html/2309.07407)
- Uddin, Zhang, Sakr, "Intelligent Offloading in Vehicular Edge Computing: A Comprehensive Review of DRL Approaches and Architectures," *Vehicular Communications* (arXiv 2502.06963v2, June 2025). It criticizes reviewed works for "uniform convergence during training" (raising concerns about deterministic behaviour), "fixed network parameters (e.g., static exploration rates)," and a lack of "comparative evaluation against baseline DRL algorithms." It concludes "without thorough benchmarking, it becomes difficult to assess real-world applicability." — [arXiv HTML](https://arxiv.org/html/2502.06963v2)
- A 2026 arXiv DRL textbook (arXiv 2608.00133, venue and authors unverified) says small numbers of seeds, weak baselines, inconsistent tuning and cherry-picked curves produce non-replicable conclusions in applied networking areas (SD-WAN, UAV communication). This is indirect evidence for edge computing. — [arXiv](https://arxiv.org/pdf/2608.00133)

### Inferences
- The target paper can present itself as one of few offloading DRL studies with registered protocol, multiple seeds, CIs/tests and compute-matched baselines. It can cite Henderson 2018 and Agarwal 2021 as the methodological standard that the domain largely does not meet.
- The claim that "longer equal-weight training beats search at equal compute" ties directly to Henderson's point that comparisons without matched budgets and tuning effort are unreliable.

### Gaps
- I found no quantitative audit (e.g., "X% of offloading papers report ≥5 seeds"). The share of papers reporting seeds remains unmeasured. Building a small audit table of 20-30 papers would strengthen this claim but was out of budget.

## Q4. Surveys on DRL for computation offloading that note open problems in reward design or weight selection

### Takeaway
Several surveys flag reward design as an open problem: miscalibrated penalties, multi-objective trade-offs handled only post hoc, and multi-agent reward coupling. None that I found treats weight selection for weighted-sum rewards as a dedicated research problem, or proposes or evaluates metaheuristic weight tuning.

### Cited Findings
- Uddin, Zhang, Sakr (*Vehicular Communications*, 2025): the survey aims to "assess the variability and limitations of reward function design," especially multi-objective, an "aspect often neglected or improperly balanced in existing studies." Its open problems include "reward function design and scaling" and "multi-objective synchronous learning." Snippet: reward design "remains problematic, especially when penalization is miscalibrated or fails to reflect task priorities." Several studies "infer multi-objective performance primarily from evaluation metrics reported after training, rather than explicitly incorporating trade-offs within the reward formulation." — [arXiv HTML](https://arxiv.org/html/2502.06963v2); [arXiv PDF](https://arxiv.org/pdf/2502.06963)
- "Reinforcement Learning Methods for Computation Offloading: A Systematic Review," *ACM Computing Surveys* (DOI 10.1145/3603703, about 2023). It says the weighted sum is the standard delay+energy reward and that reward design "is a subtle task." It names multi-agent reward dependence as an open issue (snippet level). — [ACM DL](https://dl.acm.org/doi/10.1145/3603703)
- Peng et al., "A survey on computation offloading in edge systems: From the perspective of deep reinforcement learning approaches," *Computer Science Review*, 2024 (pii S1574013724000406; co-author Keqin Li per the hosting site). It states that "the great complexity in DRL-based algorithm design turns out to be an obstacle" and lists open challenges in algorithm design and realistic requirements. Reward-weight specifics were not verified. — [ScienceDirect](https://www.sciencedirect.com/science/article/abs/pii/S1574013724000406); [author PDF](http://cs.newpaltz.edu/~lik/publications/Peng-Peng-CSR-2024)
- Ali et al., *Sensors* 2025: frames offloading as multi-objective (latency, energy, cost), "which makes reward design more complex." It notes that continuous updating may favour immediate over long-run performance. — [PMC](https://pmc.ncbi.nlm.nih.gov/articles/PMC12431013/)
- A comprehensive survey on RL-based offloading is hosted at UVa (venue unverified). — [UVaDOC](https://uvadoc.uva.es/bitstream/handle/10324/62165/dhortelano_A_comprehensive_survey_on_reinforcement-learning.pdf?sequence=1&isAllowed=y)

### Inferences
- The surveys support the paper's motivation that reward design is open. They leave room for its specific contribution: empirical evidence on whether *searching* weights is worth the compute.

### Gaps
- I did not verify IEEE Communications Surveys & Tutorials, JNCA or FGCS DRL-offloading surveys in this session. Searches surfaced none directly, and they would need a follow-up.
- The full text of the ACM CSUR review and the CSR 2024 survey was inaccessible (403).

## Q5. Which papers use iFogSim/iFogSim2 with DRL? Which simulators dominate?

### Takeaway
Peer-reviewed DRL work on iFogSim2 specifically is scarce. Most strong-venue DRL offloading papers use custom Python/Gym simulators or real testbeds (FogBus2), not iFogSim. iFogSim appears more with heuristic or ML methods and in lower-tier venues, and iFogSim2 + PPO appears mainly in non-peer-reviewed theses. This suggests that an iFogSim2-based DRL study with rigorous statistics is relatively uncommon.

### Cited Findings
- iFogSim2 itself: Mahmud, Pallewatta, Goudarzi, Buyya, "iFogSim2: An extended iFogSim simulator for mobility, clustering, and microservice management in edge and fog computing environments" (*Journal of Systems and Software*, 2022, per my recollection; the venue was not verified this session). — [ResearchGate](https://www.researchgate.net/publication/360389219_iFogSim2_An_extended_iFogSim_simulator_for_mobility_clustering_and_microservice_management_in_edge_and_fog_computing_environments)
- "An efficient deep reinforcement learning based task scheduler in cloud-fog environment," *Cluster Computing* (Springer), 2024 (DOI 10.1007/s10586-024-04712-z). The snippet says Deep Q-learning and double Q-learning "were implemented on iFogSim." Authors and full details are unverified (login redirect). — [Springer](https://link.springer.com/article/10.1007/s10586-024-04712-z)
- Heliyon (Dec 2023): learning automata + LSTM-A3C with fuzzy logic for MEC offloading, "confirmed through extensive experiments using the iFogSim simulator" (snippet; title and authors not captured). — [PMC](https://pmc.ncbi.nlm.nih.gov/articles/PMC10772128)
- A multi-classifier (non-DRL) energy-efficient offloading method evaluated on iFogSim against edge-ward and cloud-only placement. — [PMC10458720](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC10458720/)
- An iFogSim2 (Java) + Python PPO over a socket, compared with RR, FCFS, DQN and A2C. This is an NCI MSc thesis, not peer-reviewed. — [NORMA NCIRL](https://norma.ncirl.ie/9266/1/priyashanmugam.pdf)
- A Pareto-DQN fog load balancing work optimizing latency and energy (NCI thesis; simulator unconfirmed). — [NORMA NCIRL](https://norma.ncirl.ie/9228/1/myungjeekoh.pdf)
- A source-code analysis of iFogSim covering simulation coverage and limitations (arXiv 2604.23122, 2026; venue unverified). Useful for discussing simulator validity. — [arXiv](https://arxiv.org/pdf/2604.23122)
- Non-iFogSim simulators in strong papers: Goudarzi TMC 2023 used a custom Python/OpenAI-Gym event-driven simulator plus a testbed — [ar5iv](https://ar5iv.labs.arxiv.org/html/2110.12415). DRLIS used the FogBus2 real testbed — [ar5iv](https://ar5iv.labs.arxiv.org/html/2309.07407). PGN-MO-DDQN used EdgeSimPy — [ScienceDirect](https://www.sciencedirect.com/science/article/abs/pii/S1570870525003488).

### Inferences
- Custom Python/Gym environments dominate DRL offloading work because they integrate easily with RL libraries. iFogSim/iFogSim2 (Java) needs a bridge (socket or Py4J), which may explain why few DRL papers use it. The target paper's iFogSim2 integration is a differentiator, but reviewers may ask how sim-to-learner coupling and simulation fidelity were handled.

### Gaps
- I could not confirm any Q1-journal paper that couples PPO with iFogSim2. Absence of evidence here is search-limited, not exhaustive. A direct Scopus/IEEE Xplore query for "iFogSim2" AND "reinforcement learning" is recommended.
- EdgeCloudSim and CloudSim-based DRL offloading papers were not specifically searched in this session.
