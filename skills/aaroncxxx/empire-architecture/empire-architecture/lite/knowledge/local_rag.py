"""
RAG 自建知识库 (Local RAG)
抓取公开知识 → 分块 → 向量化 → 本地检索

零外部依赖，纯 Python 实现（轻量 TF-IDF 向量检索）。
支持：
  - 网页抓取
  - 本地文件（txt/md/json）
  - 目录批量导入
"""

import json
import os
import re
import math
import hashlib
import urllib.request
import urllib.error
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path
from .base import KnowledgeProvider, KnowledgeResult


# ============================================================
# 文本分块
# ============================================================

def chunk_text(text: str, chunk_size: int = 500, overlap: int = 100) -> list[str]:
    """按字符数分块，支持重叠"""
    text = text.strip()
    if not text:
        return []

    # 先按段落分割
    paragraphs = re.split(r'\n{2,}', text)
    chunks = []
    current = ""

    for para in paragraphs:
        para = para.strip()
        if not para:
            continue

        if len(current) + len(para) < chunk_size:
            current += ("\n\n" if current else "") + para
        else:
            if current:
                chunks.append(current)
            # 长段落单独切
            if len(para) > chunk_size:
                for i in range(0, len(para), chunk_size - overlap):
                    chunk = para[i:i + chunk_size]
                    if chunk.strip():
                        chunks.append(chunk.strip())
            else:
                current = para

    if current.strip():
        chunks.append(current.strip())

    return chunks


# ============================================================
# TF-IDF 向量器（纯 Python，零依赖）
# ============================================================

class TFIDFVectorizer:
    """轻量 TF-IDF 向量化，纯 Python 实现"""

    def __init__(self):
        self.vocab: dict[str, int] = {}
        self.idf: dict[str, float] = {}
        self.doc_count = 0

    def _tokenize(self, text: str) -> list[str]:
        """中英文混合分词"""
        text = text.lower()
        # 英文单词
        words = re.findall(r'[a-z0-9]+', text)
        # 中文字符（bigram）
        cn_chars = re.findall(r'[\u4e00-\u9fff]', text)
        cn_bigrams = [cn_chars[i] + cn_chars[i + 1]
                      for i in range(len(cn_chars) - 1)]
        # 中文单字也保留
        return words + cn_bigrams + cn_chars

    def fit(self, documents: list[str]):
        """构建词汇表和 IDF"""
        self.doc_count = len(documents)
        doc_freq = Counter()

        for doc in documents:
            tokens = set(self._tokenize(doc))
            for token in tokens:
                doc_freq[token] += 1

        # 建词汇表
        self.vocab = {word: idx for idx, word in enumerate(doc_freq.keys())}

        # 计算 IDF
        self.idf = {}
        for word, df in doc_freq.items():
            self.idf[word] = math.log((self.doc_count + 1) / (df + 1)) + 1

    def transform(self, text: str) -> dict[int, float]:
        """将文本转为稀疏向量 {idx: tfidf_score}"""
        tokens = self._tokenize(text)
        if not tokens:
            return {}

        tf = Counter(tokens)
        total = len(tokens)
        vector = {}

        for word, count in tf.items():
            if word in self.vocab:
                idx = self.vocab[word]
                tfidf = (count / total) * self.idf.get(word, 1.0)
                vector[idx] = tfidf

        return vector

    @staticmethod
    def cosine_sim(a: dict[int, float], b: dict[int, float]) -> float:
        """余弦相似度（稀疏向量）"""
        common = set(a.keys()) & set(b.keys())
        if not common:
            return 0.0
        dot = sum(a[i] * b[i] for i in common)
        norm_a = math.sqrt(sum(v * v for v in a.values()))
        norm_b = math.sqrt(sum(v * v for v in b.values()))
        if norm_a == 0 or norm_b == 0:
            return 0.0
        return dot / (norm_a * norm_b)


# ============================================================
# 本地向量库
# ============================================================

@dataclass
class Document:
    """文档记录"""
    doc_id: str
    title: str
    chunks: list[str] = field(default_factory=list)
    vectors: list[dict[int, float]] = field(default_factory=list)
    metadata: dict = field(default_factory=dict)


class LocalVectorStore:
    """本地向量存储"""

    def __init__(self, persist_dir: str = ""):
        self.documents: dict[str, Document] = {}
        self.vectorizer = TFIDFVectorizer()
        self.persist_dir = persist_dir
        self._dirty = True

    def add_document(self, title: str, content: str,
                     chunk_size: int = 500, metadata: dict = None) -> str:
        """添加文档并分块向量化"""
        doc_id = hashlib.md5(title.encode()).hexdigest()[:12]
        chunks = chunk_text(content, chunk_size)

        doc = Document(
            doc_id=doc_id,
            title=title,
            chunks=chunks,
            metadata=metadata or {},
        )
        self.documents[doc_id] = doc
        self._dirty = True
        self._rebuild_index()
        return doc_id

    def _rebuild_index(self):
        """重建 TF-IDF 索引"""
        all_chunks = []
        for doc in self.documents.values():
            all_chunks.extend(doc.chunks)

        if not all_chunks:
            return

        self.vectorizer.fit(all_chunks)
        idx = 0
        for doc in self.documents.values():
            doc.vectors = []
            for chunk in doc.chunks:
                vec = self.vectorizer.transform(chunk)
                doc.vectors.append(vec)
                idx += 1
        self._dirty = False

    def search(self, query: str, top_k: int = 3) -> list[KnowledgeResult]:
        """检索最相关的文档块"""
        if not self.documents:
            return []

        if self._dirty:
            self._rebuild_index()

        query_vec = self.vectorizer.transform(query)
        scored = []

        for doc in self.documents.values():
            for i, vec in enumerate(doc.vectors):
                score = self.vectorizer.cosine_sim(query_vec, vec)
                if score > 0.01:
                    scored.append((score, doc, i))

        scored.sort(key=lambda x: x[0], reverse=True)

        results = []
        seen = set()
        for score, doc, chunk_idx in scored[:top_k * 2]:
            chunk_key = f"{doc.doc_id}:{chunk_idx}"
            if chunk_key in seen:
                continue
            seen.add(chunk_key)

            # 上下文拼接：当前块 + 前后各一块
            context_chunks = []
            for j in range(max(0, chunk_idx - 1),
                           min(len(doc.chunks), chunk_idx + 2)):
                context_chunks.append(doc.chunks[j])
            context = "\n\n".join(context_chunks)

            results.append(KnowledgeResult(
                title=doc.title,
                content=context[:800],
                source="local_rag",
                score=round(score, 4),
                metadata={
                    "doc_id": doc.doc_id,
                    "chunk_index": chunk_idx,
                    **doc.metadata,
                },
            ))
            if len(results) >= top_k:
                break

        return results

    def save(self, path: str = ""):
        """持久化到 JSON"""
        path = path or os.path.join(self.persist_dir, "vectorstore.json")
        data = {}
        for doc_id, doc in self.documents.items():
            data[doc_id] = {
                "title": doc.title,
                "chunks": doc.chunks,
                "metadata": doc.metadata,
            }
        os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def load(self, path: str = ""):
        """从 JSON 加载"""
        path = path or os.path.join(self.persist_dir, "vectorstore.json")
        if not os.path.exists(path):
            return
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        for doc_id, info in data.items():
            doc = Document(
                doc_id=doc_id,
                title=info["title"],
                chunks=info["chunks"],
                metadata=info.get("metadata", {}),
            )
            self.documents[doc_id] = doc
        self._dirty = True
        self._rebuild_index()

    def stats(self) -> dict:
        return {
            "documents": len(self.documents),
            "total_chunks": sum(len(d.chunks) for d in self.documents.values()),
            "vocab_size": len(self.vectorizer.vocab),
        }


# ============================================================
# RAG 知识提供者
# ============================================================

class LocalRAGKnowledge(KnowledgeProvider):
    """RAG 自建知识库 - KnowledgeProvider 接口"""

    name = "local_rag"

    def __init__(self, persist_dir: str = "./data/knowledge"):
        self.persist_dir = persist_dir
        self.store = LocalVectorStore(persist_dir)
        # 尝试加载已有数据
        try:
            self.store.load()
        except Exception:
            pass

    def ingest_url(self, url: str) -> str:
        """抓取网页并入库"""
        req = urllib.request.Request(url, headers={
            "User-Agent": "Mozilla/5.0 (compatible; EmpireBot/1.0)"
        })
        with urllib.request.urlopen(req, timeout=15) as resp:
            html = resp.read().decode("utf-8", errors="ignore")

        # 粗略去 HTML 标签
        text = re.sub(r'<script[^>]*>.*?</script>', '', html, flags=re.DOTALL)
        text = re.sub(r'<style[^>]*>.*?</style>', '', text, flags=re.DOTALL)
        text = re.sub(r'<[^>]+>', ' ', text)
        text = re.sub(r'\s+', ' ', text).strip()

        title_match = re.search(r'<title>(.*?)</title>', html, re.DOTALL)
        title = title_match.group(1).strip() if title_match else url

        doc_id = self.store.add_document(
            title=title, content=text,
            metadata={"source_url": url, "type": "web"},
        )
        self.store.save()
        return doc_id

    def ingest_file(self, file_path: str) -> str:
        """导入本地文件"""
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"文件不存在: {file_path}")

        content = path.read_text(encoding="utf-8", errors="ignore")
        doc_id = self.store.add_document(
            title=path.name, content=content,
            metadata={"source_path": str(path), "type": "file"},
        )
        self.store.save()
        return doc_id

    def ingest_directory(self, dir_path: str,
                         extensions: list[str] = None) -> list[str]:
        """批量导入目录"""
        extensions = extensions or [".txt", ".md", ".json", ".py", ".jsonl"]
        path = Path(dir_path)
        doc_ids = []
        for f in path.rglob("*"):
            if f.suffix.lower() in extensions and f.is_file():
                try:
                    doc_id = self.ingest_file(str(f))
                    doc_ids.append(doc_id)
                except Exception:
                    continue
        return doc_ids

    def ingest_text(self, title: str, content: str) -> str:
        """直接导入文本"""
        doc_id = self.store.add_document(
            title=title, content=content,
            metadata={"type": "text"},
        )
        self.store.save()
        return doc_id

    async def search(self, query: str, top_k: int = 3) -> list[KnowledgeResult]:
        return self.store.search(query, top_k)

    async def health_check(self) -> bool:
        return True  # 本地库永远可用

    def stats(self) -> dict:
        return self.store.stats()
