#!/bin/bash
# 向量搜索工具库 v3.3.0
# 依赖 LM Studio embedding API

VECTOR_API="${VECTOR_API:-http://localhost:1234/v1/embeddings}"
VECTOR_MODEL="${VECTOR_MODEL:-text-embedding-bge-large-zh-v1.5}"
VECTOR_DIR=""

# 初始化：设置 VECTOR_DIR 并创建目录
vector_init() {
  local state_dir="${1:-}"
  if [ -z "$state_dir" ]; then
    if [ -n "$OPENCLAW_STATE_DIR" ]; then
      state_dir="$OPENCLAW_STATE_DIR"
    else
      state_dir="$HOME/.openclaw"
    fi
  fi
  VECTOR_DIR="$state_dir/.learnings/vectors"
  mkdir -p "$VECTOR_DIR"
}

# 检测 LM Studio embedding 是否可用
vector_check() {
  curl -s --max-time 3 "$VECTOR_API" \
    -H "Content-Type: application/json" \
    -d "{\"model\":\"$VECTOR_MODEL\",\"input\":\"health\"}" 2>/dev/null | grep -q '"embedding"'
}

# 降级搜索：关键词匹配（当向量搜索不可用时）
vector_fallback_search() {
  local query="$1" top_n="${2:-5}"
  [ -z "$VECTOR_DIR" ] && vector_init
  [ ! -f "$VECTOR_DIR/index.jsonl" ] && return 1
  
  # 预处理查询
  local query_processed
  query_processed=$(vector_preprocess "$query")
  
  # 用 python3 做关键词匹配：提取文本中的关键词，做简单包含匹配
  python3 -c "
import json, sys, re
query = ' '.join(sys.argv[1:])
top_n = int(sys.argv[$#])
results = []
with open('$VECTOR_DIR/index.jsonl') as f:
    for line in f:
        line = line.strip()
        if not line: continue
        entry = json.loads(line)
        text = entry.get('text', '').lower()
        # 简单关键词匹配：查询词在文本中出现的次数
        keywords = query.lower().split()
        matches = sum(1 for kw in keywords if kw in text)
        if matches > 0:
            score = min(matches / len(keywords), 1.0)
            results.append((score, entry.get('id',''), entry.get('text','')[:80], entry.get('area','')))
results.sort(reverse=True)
for score, eid, text, area in results[:top_n]:
    clean_text = text.replace(chr(10), ' ').replace(chr(13), '')
    print(f'{score:.3f}|{eid}|{area}|{clean_text}')
" $query_processed $top_n
}

# 预处理查询：增强纯数字/英文，检测否定语义，纠正拼写错误
vector_preprocess() {
  local query="$1"
  
  # 1. 拼写纠错（常见错误映射，避免wrong是right前缀的陷阱）
  # 注意：docke->docker会导致双重扩展，已删除
  eval "set -- phpfpm:php-fpm ngins:nginx apahce:apache reids:redis mencache:memcached"
  for pair in "$@"; do
    wrong="${pair%%:*}"
    right="${pair##*:}"
    if [[ "$query" == *"$wrong"* ]]; then
      query="${query//$wrong/$right}"
    fi
  done
  
  # 2. 纯数字增强（404/502等错误码）
  if [[ "$query" =~ ^[0-9]+$ ]]; then
    query="错误代码 $query"
  fi
  
  # 3. 纯英文/小写增强（给技术术语加更具体的上下文）
  if [[ "$query" =~ ^[a-zA-Z]+$ ]]; then
    query_lower=$(echo "$query" | tr '[:upper:]' '[:lower:]')
    # 常见技术术语自动加配置/服务器等上下文
    case "$query_lower" in
      nginx|apache|redis|memcached|mysql|php|docker|kubernetes|git)
        query="$query 配置"
        ;;
      *)
        query="$query 服务器"
        ;;
    esac
  fi
  
  # 4. 混合查询中含英文词时加中文补充（docker/nginx等英文软件名）
  if python3 -c "
import sys, locale
text = sys.stdin.read().strip()
has_cn = any('\u4e00' <= c <= '\u9fff' for c in text)
has_en = any('a' <= c <= 'z' or 'A' <= c <= 'Z' for c in text)
sys.exit(0 if (has_cn and has_en) else 1)
" 2>/dev/null; then
    query="$query 服务器"
  fi
  
  echo "$query"
}

# 调用 API 生成 embedding，输出向量 JSON 数组到 stdout
vector_embed() {
  local text="$1"
  [ -z "$text" ] && return 1
  
  # 用 python3 解析 JSON（macOS/Linux 都有），带异常处理
  # 使用 python3 json.dumps 避免 shell 注入
  local json_payload=$(python3 -c 'import json,sys; print(json.dumps(sys.stdin.read().strip()))' <<< "$text")
  curl -s --max-time 10 "$VECTOR_API" \
    -H "Content-Type: application/json" \
    -d "{\"model\":\"$VECTOR_MODEL\",\"input\":$json_payload}" \
    2>/dev/null | python3 -c '
import json, sys
try:
    d = json.load(sys.stdin)
    print(json.dumps(d["data"][0]["embedding"]))
except (json.JSONDecodeError, KeyError, IndexError):
    sys.exit(1)
'
}

# 计算两个向量的余弦相似度（python3 实现）
vector_cosine() {
  python3 -c "
import json, sys
a = json.loads(sys.argv[1])
b = json.loads(sys.argv[2])
dot = sum(x*y for x,y in zip(a,b))
na = sum(x*x for x in a)**0.5
nb = sum(x*x for x in b)**0.5
print(dot/(na*nb) if na*nb > 0 else 0)
" "$1" "$2"
}

# 追加一条记录到 index.jsonl（使用 base64 避免单引号注入）
vector_index_add() {
  local id="$1" text="$2" area="$3" namespace="$4" tags="$5"
  [ -z "$VECTOR_DIR" ] && vector_init
  local vec
  vec=$(vector_embed "$text") || return 1
  
  # 用 base64 编码传递含特殊字符的文本，避免 shell 注入
  local id_b64=$(echo -n "$id" | base64)
  local text_b64=$(echo -n "$text" | base64)
  local vec_b64=$(echo -n "$vec" | base64)
  local area_b64=$(echo -n "$area" | base64)
  local ns_b64=$(echo -n "$namespace" | base64)
  local tags_b64=$(echo -n "$tags" | base64)
  
  local entry=$(python3 -c "
import json, sys, base64
d = {
  'id': base64.b64decode('$id_b64').decode('utf-8'),
  'text': base64.b64decode('$text_b64').decode('utf-8'),
  'vector': json.loads(base64.b64decode('$vec_b64').decode('utf-8')),
  'area': base64.b64decode('$area_b64').decode('utf-8'),
  'namespace': base64.b64decode('$ns_b64').decode('utf-8'),
  'tags': base64.b64decode('$tags_b64').decode('utf-8')
}
print(json.dumps(d, ensure_ascii=False))
")
  # N2 fix: 向量大小校验，拒绝超过100KB的条目防止磁盘耗尽
  local entry_len=${#entry}
  if [ "$entry_len" -gt 102400 ]; then
    echo "⚠️  向量条目过大（${entry_len}字节>100KB），拒绝写入" >&2
    return 1
  fi
  
  # 原子写入：用 flock 保护（macOS 无 flock，用 mkdir 锁目录更兼容）
  # P5 fix: 加最大重试次数（100次=5秒），避免崩溃残留锁目录导致死循环
  local lock_dir="$VECTOR_DIR/.write_lock"
  local max_retry=100
  local retry=0
  while ! mkdir "$lock_dir" 2>/dev/null; do
    sleep 0.05
    retry=$((retry+1))
    if [ $retry -ge $max_retry ]; then
      echo "⚠️  向量索引写入超时（锁竞争超过5秒），跳过本次写入" >&2
      return 1
    fi
  done
  echo "$entry" >> "$VECTOR_DIR/index.jsonl"
  rmdir "$lock_dir"
}

# 搜索：输入文本 → 生成向量 → 遍历 index.jsonl 计算 cosine → 返回 topN
# 输出格式: score|id|area|text
# 如果向量生成失败，自动降级到关键词搜索
vector_search() {
  local query="$1" top_n="${2:-5}" threshold="${3:-0.6}"
  [ -z "$VECTOR_DIR" ] && vector_init
  
  # 预处理：增强数字/英文，纠错
  local query_processed
  query_processed=$(vector_preprocess "$query")
  
  # 尝试向量搜索，失败则降级到关键词搜索
  local query_vec
  if query_vec=$(vector_embed "$query_processed") 2>/dev/null; then
    # 向量搜索正常
    _vector_search_vec "$query_vec" "$threshold" "$top_n"
  else
    # 降级到关键词搜索
    echo "⚠️  向量搜索不可用，降级到关键词搜索" >&2
    vector_fallback_search "$query_processed" "$top_n"
  fi
}

# 向量搜索核心实现
_vector_search_vec() {
  local query_vec="$1" threshold="$2" top_n="$3"
  [ ! -f "$VECTOR_DIR/index.jsonl" ] && return 1
  
  # python3 一次性处理：遍历所有条目，计算余弦相似度，输出 topN
  python3 -c "
import json, sys
query_vec = json.loads(sys.argv[1])
threshold = float(sys.argv[2])
top_n = int(sys.argv[3])
results = []
with open(sys.argv[4]) as f:
  for line in f:
    line = line.strip()
    if not line: continue
    entry = json.loads(line)
    doc_vec = entry['vector']
    dot = sum(a*b for a,b in zip(query_vec, doc_vec))
    na = sum(x*x for x in query_vec)**0.5
    nb = sum(x*x for x in doc_vec)**0.5
    score = dot/(na*nb) if na*nb > 0 else 0
    if score >= threshold:
      results.append((score, entry['id'], entry.get('text',''), entry.get('area','')))
results.sort(reverse=True)
for score, eid, text, area in results[:top_n]:
  # 替换 text 中的换行为空格，避免破坏 | 分隔格式
  clean_text = text[:80].replace('\n', ' ').replace('\r', '')
  print(f'{score:.3f}|{eid}|{area}|{clean_text}')
" "$query_vec" "$threshold" "$top_n" "$VECTOR_DIR/index.jsonl"
}

# 从 experiences.md 重建全部索引（python3 直接处理，避免 bash regex 兼容性问题）
# P2 fix: 通过 sys.argv[1:4] 传递参数，避开 heredoc 注入风险
vector_reindex_all() {
  local errors_file="${1:-$HOME/.openclaw/.learnings/experiences.md}"
  # 安全: 验证路径不包含 .. 穿越
  if [[ "$errors_file" == *../* ]]; then
    echo "❌ 路径不允许 ../ 穿越" >&2
    return 1
  fi
  [ -z "$VECTOR_DIR" ] && vector_init
  [ ! -f "$errors_file" ] && return 1

  python3 -c "
import re, json, sys, os, urllib.request, urllib.error

errors_file = sys.argv[1]
vector_dir = sys.argv[2]
api_url = sys.argv[3]
model = sys.argv[4]

with open(errors_file, 'r', encoding='utf-8') as f:
    content = f.read()

pattern = r'## \[EXP-([^\]]+)\]\s*(.*?)(?=\n## \[EXP-|\$)'
entries = re.findall(pattern, content, re.DOTALL)

if not entries:
    print('WARNING: No entries found')
    sys.exit(0)

os.makedirs(vector_dir, exist_ok=True)
index_path = os.path.join(vector_dir, 'index.jsonl')

def get_embedding(text):
    payload = json.dumps({'model': model, 'input': text}).encode('utf-8')
    req = urllib.request.Request(api_url, data=payload, headers={'Content-Type': 'application/json'}, method='POST')
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = json.loads(resp.read().decode('utf-8'))
            return data['data'][0]['embedding']
    except Exception as e:
        print('WARNING: embedding failed: ' + str(e), file=sys.stderr)
        return None

count = 0
with open(index_path, 'w', encoding='utf-8') as idx:
    for entry_id, body in entries:
        entry_id = entry_id.strip()

        area_match = re.search(r'\*\*Area\*\*:\s*(.+)', body)
        area = area_match.group(1).strip() if area_match else ''

        tags_match = re.search(r'\*\*Tags\*\*:\s*(.+)', body)
        tags = tags_match.group(1).strip() if tags_match else ''

        ns_match = re.search(r'\*\*Namespace\*\*:\s*(.+)', body)
        namespace = ns_match.group(1).strip() if ns_match else 'global'

        problem_lines = [l.strip() for l in body.split('\n') if l.strip() and not l.strip().startswith('**') and not l.strip().startswith('###')]
        problem = problem_lines[0] if problem_lines else ''

        solution_match = re.search(r'### 正确方案\n(.+)', body, re.DOTALL)
        solution = solution_match.group(1).strip() if solution_match else ''

        text = problem + '\u3002' + solution + '\u3002'
        if tags:
            text += ' Tags: ' + tags

        emb = get_embedding(text)
        if emb is None:
            continue

        record = {'id': 'EXP-' + entry_id, 'text': text, 'vector': emb, 'area': area, 'namespace': namespace, 'tags': tags}
        idx.write(json.dumps(record, ensure_ascii=False) + '\n')
        count += 1
        print('  Indexing: ' + str(count), flush=True)

print('DONE: Indexed ' + str(count) + ' entries')
" "$errors_file" "$VECTOR_DIR" "$VECTOR_API" "$VECTOR_MODEL"
}
