"""把 jieba 分析器登记进已安装的 Annif。

Annif 1.4 没有分析器插件入口，这里在 annif/analyzer/__init__.py 末尾追加一段登记代码。
重复运行不会重复追加。镜像构建时执行：python -m annif_zh.register
"""

from pathlib import Path

MARKER = "# annif-zh: jieba analyzer"
SNIPPET = f'''
{MARKER}
try:
    from annif_zh.analyzer import JiebaAnalyzer

    register_analyzer(JiebaAnalyzer)
except ImportError:  # annif_zh 或 jieba 未安装
    pass
'''


def main() -> None:
    import annif.analyzer

    path = Path(annif.analyzer.__file__)
    source = path.read_text(encoding="utf-8")
    if MARKER in source:
        print(f"already registered in {path}")
        return
    path.write_text(source + SNIPPET, encoding="utf-8")
    print(f"registered jieba analyzer in {path}")


if __name__ == "__main__":
    main()
