import pickle

import annif.analyzer
import pytest

from annif_zh.analyzer import JiebaAnalyzer
from annif_zh.userdict import build

TEXT = "南海夏季风爆发前后大气环流的演变。本文利用1958-1997年的NCEP资料，分析了季风爆发！"


@pytest.fixture
def vocab_dir(tmp_path):
    vocab = tmp_path / "vocab.csv"
    vocab.write_text("uri,label_zh\nu:1,南海夏季风\nu:2,大气环流\nu:3,分析\nu:4,1-甲基环丙烯\n",
                     encoding="utf-8")
    stop = tmp_path / "stop.txt"
    stop.write_text("# 注释\n的\n了\n分析\n本文\n", encoding="utf-8")
    build(vocab, tmp_path / "out", stop)
    return tmp_path / "out"


def test_registered_in_annif():
    analyzer = annif.analyzer.get_analyzer("jieba")
    assert isinstance(analyzer, JiebaAnalyzer)
    assert analyzer.token_min_length == 1


def test_default_dictionary_splits_chinese():
    tokens = JiebaAnalyzer(None).tokenize_words("大气环流的演变")
    assert "大气" in tokens and "环流" in tokens and "的" in tokens


def test_userdict_and_stopwords(vocab_dir):
    spec = f"jieba(userdict={vocab_dir}/userdict.txt,stopwords={vocab_dir}/stopwords.txt)"
    tokens = annif.analyzer.get_analyzer(spec).tokenize_words(TEXT)
    assert "南海夏季风" in tokens and "大气环流" in tokens
    assert "的" not in tokens and "本文" not in tokens
    # 停用词表里的“分析”本身是标签，build() 已把它从停用词中去掉
    assert "分析" in tokens
    # 数字、英文保留，英文转小写
    assert "1958" in tokens and "ncep" in tokens


def test_userdict_entries(vocab_dir):
    entries = (vocab_dir / "userdict.txt").read_text(encoding="utf-8").split()
    assert "甲基环丙烯" in entries and "南海夏季风" in entries


def test_filter_false_keeps_stopwords(vocab_dir):
    analyzer = JiebaAnalyzer(None, stopwords=f"{vocab_dir}/stopwords.txt")
    assert "的" in analyzer.tokenize_words("大气环流的演变", filter=False)


def test_token_min_length():
    tokens = JiebaAnalyzer(None, token_min_length="2").tokenize_words("大气环流的演变")
    assert "的" not in tokens and "大气" in tokens


def test_sentences():
    assert JiebaAnalyzer(None).tokenize_sentences(TEXT) == [
        "南海夏季风爆发前后大气环流的演变",
        "本文利用1958-1997年的NCEP资料，分析了季风爆发",
    ]


def test_pickle_roundtrip(vocab_dir):
    analyzer = JiebaAnalyzer(None, userdict=f"{vocab_dir}/userdict.txt")
    before = analyzer.tokenize_words(TEXT)
    restored = pickle.loads(pickle.dumps(analyzer.tokenize_words.__self__))
    assert restored._tokenizer is None
    assert restored.tokenize_words(TEXT) == before
