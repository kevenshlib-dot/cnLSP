"""jieba 中文分析器：让 Annif 直接处理未分词的中文文本。

配置写法（路径相对于 Annif 的工作目录，路径中不能有逗号）：

    analyzer=jieba
    analyzer=jieba(userdict=vocab/userdict.txt,stopwords=vocab/stopwords.txt)
    analyzer=jieba(userdict=vocab/userdict.txt,hmm=0,token_min_length=2)

切分规则与 scripts/prepare_csl_jieba_userdict.py 完全一致：NFKC 规范化 → jieba
精确模式 → 每个词再拆成连续的汉字段或字母数字段 → 小写 → 去停用词。数字串会保留，
因为年份、型号常常有区分度。
"""

from __future__ import annotations

import logging
import re
import unicodedata

import annif.util
from annif.analyzer import analyzer

_CJK = r"㐀-䶿一-鿿"
TOKEN_PARTS = re.compile(rf"[{_CJK}]+|[A-Za-z0-9]+")
SENTENCE_END = re.compile(r"[。！？!?；;\n]+")


def load_wordlist(path: str | None) -> frozenset[str]:
    """读一行一词的词表；空行和 # 开头的行忽略。"""
    if not path:
        return frozenset()
    with open(path, encoding="utf-8") as f:
        return frozenset(
            line.strip().lower() for line in f if line.strip() and not line.startswith("#")
        )


class JiebaAnalyzer(analyzer.Analyzer):
    name = "jieba"
    # 中文主题词以双字词为主，默认的 3 会丢掉大部分词
    token_min_length = 1

    @staticmethod
    def is_available() -> bool:
        import importlib.util

        return importlib.util.find_spec("jieba") is not None

    def __init__(self, param: str | None, **kwargs) -> None:
        self.param = param
        # 唯一的位置参数视为 userdict：analyzer=jieba(vocab/userdict.txt)
        self.userdict = kwargs.pop("userdict", None) or param
        self.stopwords_path = kwargs.pop("stopwords", None)
        self.hmm = annif.util.boolean(kwargs.pop("hmm", True))
        self.stopwords = load_wordlist(self.stopwords_path)
        self._tokenizer = None
        super().__init__(**kwargs)

    def __str__(self) -> str:
        return (f"jieba(userdict={self.userdict}, stopwords={self.stopwords_path}, "
                f"hmm={self.hmm}, token_min_length={self.token_min_length})")

    # Omikuji 会把 tokenize_words 连同分析器一起 pickle；jieba 分词器带线程锁，
    # 不能序列化，所以只保存配置，加载后按需重建。
    def __getstate__(self) -> dict:
        state = self.__dict__.copy()
        state["_tokenizer"] = None
        return state

    @property
    def tokenizer(self):
        if self._tokenizer is None:
            import jieba

            jieba.setLogLevel(logging.WARNING)
            tokenizer = jieba.Tokenizer()
            tokenizer.initialize()
            if self.userdict:
                tokenizer.load_userdict(self.userdict)
            self._tokenizer = tokenizer
        return self._tokenizer

    def tokenize_sentences(self, text: str) -> list[str]:
        return [s for s in (p.strip() for p in SENTENCE_END.split(text)) if s]

    def tokenize_words(self, text: str, filter: bool = True) -> list[str]:
        text = unicodedata.normalize("NFKC", text)
        tokens = []
        for word in self.tokenizer.cut(text, cut_all=False, HMM=self.hmm):
            for part in TOKEN_PARTS.findall(word):
                part = part.lower()
                if filter and (len(part) < self.token_min_length or part in self.stopwords):
                    continue
                tokens.append(part)
        return tokens
