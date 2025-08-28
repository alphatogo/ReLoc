# ReLoc: Let's Revise Step-by-Step

Code for **"Let's Revise Step-by-Step: A Unified Local Search Framework for Code Generation with LLMs"** (NeurIPS 2025).

ReLoc reframes improvement-based LLM code generation as **local search**: starting from an initial draft, it iteratively generates neighboring code revisions, scores them, and updates the incumbent solution, enjoying the anytime property of local search. It is instantiated as two algorithms — **Hill Climbing (HC)** and **Genetic Algorithm (GA)** — and guided by a specialized **revision reward model** that ranks candidates by their *revision distance* (how many edits away they are from a correct solution), rather than relying on noisy pass-rate or LLM self-evaluation signals.

The trained revision reward model checkpoint is available at [ZHIYII/ReLoc_RRM](https://huggingface.co/ZHIYII/ReLoc_RRM) on Hugging Face.

## Repository structure

```
main.py                    # entry point: loads a benchmark, runs the search, saves results
runner.py                  # drives the local-search loop (seed -> expand -> select)
Node_selection.py          # search tree / node bookkeeping and candidate selection
model.py                   # LLM wrapper (vLLM / transformers / OpenAI-compatible backends)
parser.py                  # CLI arguments
config/                    # per-algorithm search hyperparameters (Hill_climbing.yaml, GEN_gen.yaml)
prompts/                   # prompt templates (drafting, revision, reflection, self-scoring, ...)
LLM_runner/                # low-level generation + text-extraction helpers
feedback/                  # test-case execution/scoring and the revision reward model wrapper
data/                      # LiveCodeBench / TACO loaders
Revision_reward_model/     # training script + configs for the revision reward model (uses TRL)
script/                    # example launch scripts
```

## Setup

```bash
pip install -r requirements.txt
```

The code generation backbone can be a local vLLM/Transformers model (e.g. `Qwen/Qwen2.5-32B-Instruct`) or an OpenAI-compatible API model (any `--model` containing `"gpt"`), configured via:

```bash
export OPENAI_API_KEY="..."
export OPENAI_BASE_URL="..."   # optional, for OpenAI-compatible endpoints
```

## Running local search

```bash
# Hill Climbing on LiveCodeBench
python main.py \
  --config_path Hill_climbing --method Hill_climbing \
  --dataset LCB --model Qwen/Qwen2.5-32B-Instruct \
  --rm ZHIYII/ReLoc_RRM --device cuda:0

# Genetic Algorithm on LiveCodeBench
python main.py \
  --config_path GEN_gen \
  --dataset LCB --model Qwen/Qwen2.5-32B-Instruct \
  --rm ZHIYII/ReLoc_RRM --device cuda:0
```

Or use the provided scripts (`script/Hill_climbing.sh`, `script/GA.sh`) after filling in `--rm` with the reward model path above. Set `--dataset TACO` to switch benchmarks. Search hyperparameters (budget, population size, selection weights, etc.) live in `config/*.yaml`.

Results are written to `output/<task>/<dataset>/<Code_source>/<method>/exp_<timestamp>_<config>/sampling_per_problem/<problem>.json`, containing the final committed solutions plus every explored node with its execution results and reward.

## Training the revision reward model

`Revision_reward_model/` contains a minimal setup on top of [TRL](https://github.com/huggingface/trl)'s reward-modeling trainer. Build a pairwise preference dataset from revision-distance comparisons (Section 3.2 of the paper), then run:

```bash
cd Revision_reward_model
pip install trl
bash RM.sh
```

adjusting `--dataset_name` to point to your constructed preference dataset. A ready-to-use checkpoint trained this way is published at [ZHIYII/ReLoc_RRM](https://huggingface.co/ZHIYII/ReLoc_RRM).

## Citation

```bibtex
@inproceedings{lyu2025reloc,
  title     = {Let's Revise Step-by-Step: A Unified Local Search Framework for Code Generation with LLMs},
  author    = {Lyu, Zhiyi and Huang, Jianguo and Deng, Yanchen and Hoi, Steven and An, Bo},
  booktitle = {Advances in Neural Information Processing Systems (NeurIPS)},
  year      = {2025}
}
```

## License

MIT (see [LICENSE](LICENSE)). `Revision_reward_model/` builds on [TRL](https://github.com/huggingface/trl), licensed under Apache 2.0.
