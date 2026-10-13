# annif-zh 训练/服务镜像：Annif 1.4.2 + Omikuji + fastText + nn_ensemble，原生多架构（含 arm64）
FROM python:3.12-slim

RUN apt-get update \
    && apt-get install -y --no-install-recommends build-essential curl \
    && rm -rf /var/lib/apt/lists/*

# 部分可选依赖在 aarch64 上没有现成 wheel 时需要从源码编译（omikuji 需要 Rust）
RUN curl -sSf https://sh.rustup.rs | sh -s -- -y --profile minimal
ENV PATH="/root/.cargo/bin:${PATH}"

# nn 附加项指定的 tensorflow-cpu 没有 linux/aarch64 wheel，改为单独安装同版本的 tensorflow
RUN pip install --no-cache-dir "annif[omikuji,fasttext]==1.4.2" "tensorflow~=2.20.0" "lmdb~=1.7.3" \
        "jieba==0.42.1" opencc-python-reimplemented \
    && python -m nltk.downloader -d /usr/local/share/nltk_data punkt_tab

# annif-zh 扩展：jieba 分析器，并登记进 Annif
COPY pyproject.toml /opt/annif-zh/
COPY annif_zh /opt/annif-zh/annif_zh
RUN pip install --no-cache-dir --no-deps /opt/annif-zh && python -m annif_zh.register

WORKDIR /annif-projects
CMD ["annif", "--help"]
