#!/usr/bin/env bash
# 用官方 Annif 1.4.2 镜像跑 CSL 关键词 TF-IDF 基线。
# 输入（只读挂载）：annif-zh/data/teaching/annif-csl-server/prepared-keywords
# 输出：annif-zh/models/csl-keywords-baseline（模型、指标、日志）
set -euo pipefail

ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
IN="${ROOT}/data/teaching/annif-csl-server/prepared-keywords"
OUT="${ROOT}/models/csl-keywords-baseline"
IMAGE="quay.io/natlibfi/annif:1.4.2"
JOBS="${JOBS:-8}"

mkdir -p "$OUT"
cp "${IN}/projects.cfg" "${OUT}/projects.cfg"

run() {
    docker run --rm --platform linux/amd64 --memory 16g \
        -v "${IN}:/in:ro" -v "${IN}/..:/src:ro" -v "${OUT}:/annif-projects" -w /annif-projects \
        "$IMAGE" "$@"
}

time run annif load-vocab csl-keywords /in/vocab.csv --projects projects.cfg
time run annif train csl-keywords-zh /in/train.jsonl --projects projects.cfg --jobs "$JOBS"
for split in dev test; do
    time run annif eval csl-keywords-zh "/in/${split}.jsonl" --projects projects.cfg \
        --limit 5 --jobs "$JOBS" --metrics-file "${split}-metrics.json"
done
# 推荐前要做与训练相同的双字切分，所以经由原作者的 csl_annif.py 调用
run python /src/csl_annif.py suggest --input /in/example.txt --projects projects.cfg --limit 5
