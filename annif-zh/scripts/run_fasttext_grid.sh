#!/usr/bin/env bash
# fastText 网格搜索：train 上训练，dev 前 5000 篇比较 F1@5 / nDCG@10
# 用法：DATA=annif-csl-server scripts/run_fasttext_grid.sh
set -euo pipefail
ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
DATA="${DATA:-annif-csl-server}"
IN="${ROOT}/data/teaching/${DATA}/prepared-keywords"
OUT="${ROOT}/models/fasttext-grid-${DATA}"
IMAGE="${IMAGE:-annif-zh:1.4.2}"
JOBS="${JOBS:-12}"
GRID="${GRID:-ft-a ft-b ft-c ft-d ft-e}"

mkdir -p "$OUT"
cp "${ROOT}/configs/csl-fasttext-grid.cfg" "${OUT}/projects.cfg"
cd -- "$OUT"
run() {
    docker run --rm --memory 18g -v "${IN}:/in:ro" -v "${OUT}:/annif-projects" -w /annif-projects \
        "$IMAGE" "$@"
}
step() { printf '\n=== %s  %s\n' "$(date '+%H:%M:%S')" "$*"; }

step "load-vocab"
run annif load-vocab csl-keywords /in/vocab.csv --projects projects.cfg
for p in $GRID; do
    step "train $p"
    time run annif train "$p" /in/train.jsonl --projects projects.cfg --jobs "$JOBS"
    step "eval $p (dev 5000)"
    run annif eval "$p" /in/dev.jsonl --projects projects.cfg --limit 5 --jobs "$JOBS" \
        --docs-limit 5000 --metrics-file "dev5k-${p}.json"
    # 模型较大，比完即删，只留指标
    rm -rf "data/projects/${p}"
done
step "done"
