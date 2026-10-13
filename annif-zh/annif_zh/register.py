"""把 annif-zh 的扩展登记进已安装的 Annif。

Annif 1.4 的分析器和后端都没有插件入口，这里在两个注册文件末尾各追加一段登记代码：
  - annif/analyzer/__init__.py：jieba 分析器
  - annif/backend/__init__.py：llm_rerank 后端（与 Annif 自带后端一样按需导入）
重复运行不会重复追加。镜像构建时执行：python -m annif_zh.register
"""

from pathlib import Path

ANALYZER_MARKER = "# annif-zh: jieba analyzer"
ANALYZER_SNIPPET = f'''
{ANALYZER_MARKER}
try:
    from annif_zh.analyzer import JiebaAnalyzer

    register_analyzer(JiebaAnalyzer)
except ImportError:  # annif_zh 或 jieba 未安装
    pass
'''

BACKEND_MARKER = "# annif-zh: llm_rerank backend"
BACKEND_SNIPPET = f'''
{BACKEND_MARKER}
def _llm_rerank() -> Type[AnnifBackend]:
    try:
        from annif_zh.backend import llm_rerank

        return llm_rerank.LLMRerankBackend
    except ImportError:
        raise ValueError("annif_zh not available, cannot use llm_rerank backend")


_backend_fns["llm_rerank"] = _llm_rerank
'''


def _append(path: Path, marker: str, snippet: str) -> None:
    source = path.read_text(encoding="utf-8")
    if marker in source:
        print(f"already registered in {path}")
        return
    path.write_text(source + snippet, encoding="utf-8")
    print(f"registered in {path}")


def main() -> None:
    import annif.analyzer
    import annif.backend

    _append(Path(annif.analyzer.__file__), ANALYZER_MARKER, ANALYZER_SNIPPET)
    _append(Path(annif.backend.__file__), BACKEND_MARKER, BACKEND_SNIPPET)


if __name__ == "__main__":
    main()
