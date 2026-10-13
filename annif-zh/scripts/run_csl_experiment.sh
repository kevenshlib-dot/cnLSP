#!/usr/bin/env bash
# CSL 关键词集成实验：TF-IDF / Omikuji / fastText，再做 ensemble、PAV、nn_ensemble。
# 用法：scripts/run_csl_experiment.sh            # 全部步骤
#       STEPS="eval" scripts/run_csl_experiment.sh   # 只跑部分步骤
#       DATA=annif-csl-jieba-server NAME=csl-keywords-jieba-ensemble scripts/run_csl_experiment.sh
set -euo pipefail

ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
DATA="${DATA:-annif-csl-server}"            # data/teaching/ 下的数据集目录
NAME="${NAME:-csl-keywords-ensemble}"        # models/ 下的输出目录
IN="${ROOT}/data/teaching/${DATA}/prepared-keywords"
OUT="${ROOT}/models/${NAME}"
IMAGE="${IMAGE:-annif-zh:1.4.2}"
JOBS="${JOBS:-12}"
STEPS="${STEPS:-vocab base hyperopt fusion eval}"
# PAV 要为 2 万多个主题逐一拟合，单线程一个来源就超过 1.5 小时，默认不跑
FUSION="${FUSION:-csl-nn}"
# nn_ensemble 让每个来源对每篇文档给全部 2 万多个主题打分，又慢又占内存；
# Annif 建议 1k–10k 篇训练文档，这里取 dev 前 1 万篇、8 个进程
FUSION_DOCS="${FUSION_DOCS:-10000}"
FUSION_JOBS="${FUSION_JOBS:-8}"
# 评测：EVAL_DOCS>0 时只用 test 前 N 篇（两个数据集的 test 顺序一致，可直接对比）
EVAL_DOCS="${EVAL_DOCS:-0}"
EVAL_JOBS="${EVAL_JOBS:-$JOBS}"
NN_EVAL_JOBS="${NN_EVAL_JOBS:-6}"            # 12 个进程会让 nn_ensemble 评测内存溢出卡死
METRICS_PREFIX="${METRICS_PREFIX:-test}"
EVAL="${EVAL:-csl-tfidf csl-omikuji csl-fasttext csl-ensemble csl-nn}"

mkdir -p "$OUT"
# 配置只在首次运行时复制，以免覆盖 hyperopt 调好的集成权重
[[ -f "${OUT}/projects.cfg" ]] || cp "${ROOT}/configs/csl-keywords-ensemble.cfg" "${OUT}/projects.cfg"
cd -- "$OUT"

run() {
    docker run --rm --memory 18g \
        -v "${IN}:/in:ro" -v "${OUT}:/annif-projects" -w /annif-projects \
        "$IMAGE" "$@"
}
step() { printf '\n=== %s  %s\n' "$(date '+%H:%M:%S')" "$*"; }

if [[ " $STEPS " == *" vocab "* ]]; then
    step "load-vocab"
    run annif load-vocab csl-keywords /in/vocab.csv --projects projects.cfg
fi
if [[ " $STEPS " == *" base "* ]]; then
    for p in csl-tfidf csl-omikuji csl-fasttext; do
        step "train $p"
        time run annif train "$p" /in/train.jsonl --projects projects.cfg --jobs "$JOBS"
    done
fi
if [[ " $STEPS " == *" hyperopt "* ]]; then
    step "hyperopt csl-ensemble (dev)"
    time run annif hyperopt csl-ensemble /in/dev.jsonl --projects projects.cfg \
        --trials 30 --jobs "$JOBS" --metric NDCG --results-file ensemble-hyperopt.tsv \
        | tee ensemble-hyperopt.out
    best="$(grep -E '^sources=' ensemble-hyperopt.out | tail -1)"
    [[ -n "$best" ]] || { echo "hyperopt 没有输出 sources= 行" >&2; exit 1; }
    # 把最优权重写回 [csl-ensemble] 一节
    python3 - "${OUT}/projects.cfg" "$best" <<'PY'
import re, sys
path, best = sys.argv[1], sys.argv[2]
cfg = open(path, encoding="utf-8").read()
head, sep, rest = cfg.partition("[csl-ensemble]")
rest = re.sub(r"^sources=.*$", best, rest, count=1, flags=re.M)
open(path, "w", encoding="utf-8").write(head + sep + rest)
PY
    grep -A6 '^\[csl-ensemble\]' "${OUT}/projects.cfg"
fi
if [[ " $STEPS " == *" fusion "* ]]; then
    for p in $FUSION; do
        step "train $p (dev)"
        time run annif train "$p" /in/dev.jsonl --projects projects.cfg \
            --jobs "$FUSION_JOBS" --docs-limit "$FUSION_DOCS"
    done
fi
if [[ " $STEPS " == *" eval "* ]]; then
    for p in $EVAL; do
        jobs="$EVAL_JOBS"; [[ "$p" == csl-nn ]] && jobs="$NN_EVAL_JOBS"
        extra=(); (( EVAL_DOCS > 0 )) && extra=(--docs-limit "$EVAL_DOCS")
        step "eval $p (test, docs=${EVAL_DOCS:-all}, jobs=$jobs)"
        time run annif eval "$p" /in/test.jsonl --projects projects.cfg \
            --limit 5 --jobs "$jobs" ${extra[@]+"${extra[@]}"} --metrics-file "${METRICS_PREFIX}-${p}.json"
    done
fi
step "done"
