#!/usr/bin/env python3
"""
简化版CLI - 仅支持KataGo定式库
"""

import argparse
import sys
from pathlib import Path

from ..storage import JsonStorage, DEFAULT_DB_PATH
from ..builder import KatagoJosekiBuilder, convert_to_rudl
from ..discover import discover_joseki
from ..extraction import extract_moves_all_corners, convert_to_multigogm


def cmd_init(args):
    """初始化空数据库"""
    storage = JsonStorage(args.db)
    storage.clear()
    print(f"✅ 已初始化空数据库: {storage.db_path}")


def cmd_katago(args):
    """从KataGo棋谱构建定式库（支持日期范围）"""
    import signal
    from datetime import datetime, timedelta
    from ..extraction.katago_downloader import download_katago_games
    
    # 配置
    CACHE_DIR = Path.home() / ".weiqi-joseki/katago-cache"
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    
    # 解析日期
    try:
        start_date = datetime.strptime(args.start_date, "%Y-%m-%d")
        end_date = datetime.strptime(args.end_date, "%Y-%m-%d")
    except ValueError:
        print("❌ 错误: 日期格式应为 YYYY-MM-DD")
        sys.exit(1)
    
    if start_date > end_date:
        print("❌ 错误: 起始日期不能晚于结束日期")
        sys.exit(1)
    
    # 生成日期列表
    dates = []
    current = start_date
    while current <= end_date:
        dates.append(current.strftime("%Y-%m-%d"))
        current += timedelta(days=1)
    
    print(f"📅 日期范围: {args.start_date} 至 {args.end_date}（共{len(dates)}天）")
    print(f"💾 缓存目录: {CACHE_DIR}")
    print(f"🗄️  数据库: {args.db}")
    print()
    
    # 设置信号处理
    stop_flag = [False]
    
    def signal_handler(sig, frame):
        print("\n\n⚠️ 收到中断信号...")
        stop_flag[0] = True
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # 下载阶段
    print(f"📥 开始下载/检查缓存...")
    
    downloaded_files, missing_dates = download_katago_games(
        start_date=args.start_date,
        end_date=args.end_date,
        cache_dir=CACHE_DIR,
        max_retries=3,
        workers=3,
        keep_cache=True
    )
    
    print(f"✅ 文件准备完成: {len(downloaded_files)}/{len(dates)} 个")
    if missing_dates:
        print(f"⚠️  未找到: {len(missing_dates)} 个日期")
    print()
    
    if not downloaded_files:
        print("❌ 没有可处理的文件")
        return 1
    
    if stop_flag[0]:
        return 1
    
    # 构建定式库 - 统一处理所有文件
    print(f"⏳ 开始构建定式库（前{args.first_n}手）...")
    print(f"   参数: min-freq={args.min_freq}, top-k={args.top_k}")
    print()
    
    builder = KatagoJosekiBuilder(args.db)
    
    # Phase 1: 统计所有文件的定式频率
    print("📊 Phase 1: CMS统计前缀频率...")
    
    from ..utils import CountMinSketch
    import gzip
    import tempfile
    
    # 使用高精度CMS（4194304x4, ~64MB, 误差~0.024%）
    cms = CountMinSketch(width=4194304, depth=4)
    temp_file = tempfile.NamedTemporaryFile(mode='wb', suffix='.gz', delete=False)
    temp_path = Path(temp_file.name)
    
    from ..extraction.katago_downloader import iter_sgf_from_tar
    from ..extraction import get_move_sequence
    from ..core.coords import convert_to_top_right
    
    CORNERS = ['tl', 'tr', 'bl', 'br']
    min_moves = args.min_moves
    first_n = args.first_n
    distance_threshold = args.distance_threshold
    
    processed = 0
    joseki_count = 0
    prefix_count = 0
    
    with gzip.open(temp_path, 'wt', encoding='utf-8') as f_out:
        for tar_path in downloaded_files:
            if stop_flag[0]:
                break
            
            print(f"   处理: {tar_path.name}...")
            
            for sgf_data in iter_sgf_from_tar(tar_path):
                if stop_flag[0]:
                    break
                
                try:
                    corner_moves_dict = extract_moves_all_corners(
                        sgf_data, first_n=first_n, distance_threshold=distance_threshold
                    )
                    
                    seen_sequences = set()
                    
                    for corner in CORNERS:
                        moves = corner_moves_dict.get(corner)
                        if not moves or len(moves) < min_moves:
                            continue
                        
                        coords = get_move_sequence(moves)
                        if len(coords) < min_moves:
                            continue
                        
                        tr_coords = convert_to_top_right(coords, corner)
                        
                        # 生成两个方向
                        ruld = " ".join(tr_coords)
                        rudl_seq = " ".join(convert_to_rudl(tr_coords))
                        
                        for direction, seq in [('ruld', ruld), ('rudl', rudl_seq)]:
                            if seq in seen_sequences:
                                continue
                            seen_sequences.add(seq)
                            
                            f_out.write(f"{direction}|{seq}\n")
                            joseki_count += 1
                            
                            seq_parts = seq.split()
                            for end in range(min_moves, len(seq_parts) + 1):
                                prefix = " ".join(seq_parts[:end])
                                cms.update(prefix)
                                prefix_count += 1
                    
                    processed += 1
                    
                except Exception as e:
                    continue
            
            print(f"      累计: {processed}谱, {joseki_count}定式串, {prefix_count}前缀")
    
    print(f"\n✅ Phase 1完成: {processed}谱, {joseki_count}定式串, {prefix_count}前缀")
    print()
    
    if stop_flag[0]:
        temp_path.unlink()
        return 1
    
    # Phase 2 & 3: 逆向遍历 + 单链检测 + 去重
    print(f"🔄 Phase 2-3: 逆向遍历+单链检测+去重...")
    
    joseki_list = builder._process_temp_file(
        temp_path, cms, 
        min_freq=args.min_freq,
        top_k=args.top_k,
        min_moves=min_moves,
        max_moves=args.max_moves
    )
    
    # 清理临时文件
    temp_path.unlink()
    
    print(f"✅ 构建完成: {len(joseki_list)} 条定式")
    print()
    
    # Phase 4: 入库
    print("🔄 Phase 4: 保存到数据库...")
    builder.save_to_db(joseki_list, append=False)
    
    print()
    print("=" * 50)
    print(f"🎉 全部完成！共 {len(joseki_list)} 条定式")
    print("=" * 50)


def cmd_list(args):
    """列出定式"""
    storage = JsonStorage(args.db)
    joseki_list = storage.get_all()
    
    if not joseki_list:
        print("数据库为空")
        return
    
    # 排序
    reverse = (args.order == "desc")
    if args.sort == "freq":
        joseki_list.sort(key=lambda x: x.get("frequency", 0), reverse=reverse)
    elif args.sort == "length":
        joseki_list.sort(key=lambda x: len(x.get("moves", [])), reverse=reverse)
    else:  # id
        joseki_list.sort(key=lambda x: x.get("id", ""), reverse=reverse)
    
    # 限制数量
    if args.limit:
        joseki_list = joseki_list[:args.limit]
    
    print(f"共 {len(storage.get_all())} 条定式")
    print()
    print(f"{'ID':<12} {'手数':>4} {'频率':>8} {'着法串'}")
    print("-" * 60)
    
    for j in joseki_list:
        jid = j.get("id", "-")
        moves = j.get("moves", [])
        freq = j.get("frequency", 0)
        moves_str = " ".join(moves[:8])
        if len(moves) > 8:
            moves_str += "..."
        print(f"{jid:<12} {len(moves):>4} {freq:>8} {moves_str}")


def cmd_stats(args):
    """统计信息"""
    storage = JsonStorage(args.db)
    joseki_list = storage.get_all()
    
    if not joseki_list:
        print("数据库为空")
        return
    
    total = len(joseki_list)
    frequencies = [j.get("frequency", 0) for j in joseki_list]
    lengths = [len(j.get("moves", [])) for j in joseki_list]
    
    # 频率统计
    freq_sorted = sorted(frequencies, reverse=True)
    total_freq = sum(frequencies)
    
    # 中位数
    def median(lst):
        lst_sorted = sorted(lst)
        n = len(lst_sorted)
        if n == 0:
            return 0
        if n % 2 == 1:
            return lst_sorted[n // 2]
        return (lst_sorted[n // 2 - 1] + lst_sorted[n // 2]) // 2
    
    # 找出频率最高的定式
    max_freq_joseki = max(joseki_list, key=lambda x: x.get("frequency", 0))
    
    print("=" * 50)
    print("定式库统计")
    print("=" * 50)
    print(f"总定式数:     {total}")
    print(f"总出现次数:   {total_freq}")
    print()
    print("【频率统计】")
    print(f"  最高:       {max(frequencies)}")
    print(f"  最低:       {min(frequencies)}")
    print(f"  平均:       {total_freq / total:.1f}")
    print(f"  中位数:     {median(frequencies)}")
    print(f"  Top 10%平均: {sum(freq_sorted[:total//10]) / (total//10 or 1):.1f}")
    print()
    print("【着法长度统计】")
    print(f"  最长:       {max(lengths)} 手")
    print(f"  最短:       {min(lengths)} 手")
    print(f"  平均:       {sum(lengths) / total:.1f} 手")
    print(f"  中位数:     {median(lengths)} 手")
    print()
    print("【出现最多定式】")
    print(f"  ID:         {max_freq_joseki.get('id')}")
    print(f"  频率:       {max_freq_joseki.get('frequency', 0)}")
    print(f"  着法:       {' '.join(max_freq_joseki.get('moves', []))}")


def cmd_extract(args):
    """从SGF提取四角着法"""
    if not Path(args.input).exists():
        print(f"❌ 文件不存在: {args.input}")
        return 1
    
    sgf_data = Path(args.input).read_text(encoding='utf-8')
    
    result = extract_moves_all_corners(
        sgf_data,
        first_n=args.first_n,
        distance_threshold=args.distance_threshold
    )
    
    if not result:
        print("未提取到着法")
        return
    
    print(f"提取结果（前{args.first_n}手，距离阈值{args.distance_threshold}）:")
    print()
    
    corner_names = {'tl': '左上', 'tr': '右上', 'bl': '左下', 'br': '右下'}
    
    for corner in ['tl', 'tr', 'bl', 'br']:
        if corner not in result:
            continue
        
        moves = result[corner]
        coords = [c for _, c in moves]
        
        print(f"【{corner_names.get(corner, corner)}】{len(coords)}手")
        
        if args.verbose:
            for i, (color, coord) in enumerate(moves):
                coord_display = coord if coord != 'tt' else 'tt(脱先)'
                print(f"  {i+1:2d}. {color}[{coord_display}]")
        else:
            moves_str = " ".join(coords[:10])
            if len(coords) > 10:
                moves_str += f"... ({len(coords)}手)"
            print(f"  {moves_str}")
        print()
    
    # 可选保存MULTIGOGM
    if args.output:
        multigogm = convert_to_multigogm(result)
        Path(args.output).write_text(multigogm, encoding='utf-8')
        print(f"已保存MULTIGOGM: {args.output}")


def cmd_discover(args):
    """从SGF发现定式（支持批量目录和JSON输出）"""
    import json
    
    storage = JsonStorage(args.db)
    joseki_list = storage.get_all()
    
    if not joseki_list:
        print("❌ 数据库为空，请先使用katago命令构建定式库")
        return 1
    
    # 收集所有SGF文件
    sgf_files = []
    for path_str in args.paths:
        path = Path(path_str)
        if not path.exists():
            print(f"⚠️  路径不存在: {path_str}")
            continue
        
        if path.is_file() and path.suffix == '.sgf':
            sgf_files.append(path)
        elif path.is_dir():
            sgf_files.extend(path.glob("*.sgf"))
    
    if not sgf_files:
        print("❌ 未找到SGF文件")
        return 1
    
    # 批量处理 - 收集所有匹配结果
    all_matches = []
    for sgf_file in sgf_files:
        try:
            sgf_data = sgf_file.read_text(encoding='utf-8')
            
            # 解析SGF元数据
            from ..extraction.sgf_parser import parse_sgf
            sgf_result = parse_sgf(sgf_data)
            sgf_game_info = sgf_result.get("game_info", {})
            
            # 优先取EV，没有则取GN
            event = sgf_game_info.get("event", "")
            if not event:
                # 从原始properties获取GN
                tree = sgf_result.get("tree", {})
                props = tree.get("properties", {})
                event = props.get("GN", "")
            
            game_info = {
                "black": sgf_game_info.get("black", "未知"),
                "white": sgf_game_info.get("white", "未知"),
                "result": sgf_game_info.get("result", ""),
                "event": event,
                "date": sgf_game_info.get("date", "")
            }
            
            # 提取四角着法（用于输出）
            from ..extraction import extract_moves_all_corners, get_move_sequence
            from ..core.coords import convert_to_top_right
            from ..builder import convert_to_rudl
            corner_moves_dict = extract_moves_all_corners(
                sgf_data, first_n=args.first_n, distance_threshold=args.distance_threshold
            )
            # 准备着法串（用于输出）
            extracted_moves = {}
            for corner, moves in corner_moves_dict.items():
                coords = get_move_sequence(moves)
                tr_coords = convert_to_top_right(coords, corner)
                extracted_moves[corner] = " ".join(tr_coords)
            
            results = discover_joseki(
                sgf_data,
                joseki_list,
                first_n=args.first_n,
                distance_threshold=args.distance_threshold
            )
            
            # 每条定式一条记录
            for corner, m in results.items():
                joseki = storage.get(m.joseki_id)
                all_matches.append({
                    "file": str(sgf_file),
                    "game_info": game_info,
                    "source_corner": m.source_corner,
                    "extracted_moves": m.moves,
                    "joseki_id": m.joseki_id,
                    "prefix": m.prefix,
                    "prefix_len": m.prefix_len,
                    "total_moves": m.total_moves,
                    "frequency": joseki.get("frequency", 0) if joseki else 0,
                    "probability": joseki.get("probability", 0.0) if joseki else 0.0
                })
        except Exception as e:
            print(f"⚠️  处理失败 {sgf_file}: {e}")
            continue
    
    if not all_matches:
        print("未发现定式")
        return
    
    # 按匹配长度从长到短排序
    all_matches.sort(key=lambda x: -x["prefix_len"])
    
    # JSON输出
    if args.json:
        output = json.dumps(all_matches, ensure_ascii=False, indent=2)
        if args.output:
            Path(args.output).write_text(output, encoding='utf-8')
            print(f"✅ 已保存到: {args.output}")
        else:
            print(output)
    else:
        # 文本输出
        corner_names = {'tl': '左上', 'tr': '右上', 'bl': '左下', 'br': '右下'}
        print(f"\n发现 {len(all_matches)} 个定式匹配（按匹配长度排序）：\n")
        for m in all_matches:
            print(f"📄 {m['file']}")
            print(f"  来源角: {corner_names.get(m['source_corner'], m['source_corner'])}")
            print(f"  定式ID: {m['joseki_id']}")
            print(f"  匹配: {m['prefix_len']}/{m['total_moves']}手")
            print(f"  前缀: {m['prefix']}")
            print(f"  频率: {m['frequency']}  概率: {m['probability']:.4%}")
            print()


def cmd_export(args):
    """导出定式"""
    storage = JsonStorage(args.db)
    joseki_list = storage.get_all()
    
    if not joseki_list:
        print("数据库为空")
        return
    
    if args.format == "json":
        import json
        output = json.dumps(joseki_list, ensure_ascii=False, indent=2)
    elif args.format == "sgf":
        # 简单SGF格式
        lines = ["(;CA[utf-8]FF[4]AP[JosekiExport]SZ[19]GM[1]"]
        for j in joseki_list[:args.limit or 100]:
            moves = j.get("moves", [])
            if moves:
                lines.append(f"(;C[{j.get('id')} freq={j.get('frequency',0)}]")
                color = 'B'
                for m in moves:
                    lines.append(f";{color}[{m}]")
                    color = 'W' if color == 'B' else 'B'
                lines.append(")")
        lines.append(")")
        output = "".join(lines)
    else:
        print(f"❌ 不支持的格式: {args.format}")
        return 1
    
    if args.output:
        Path(args.output).write_text(output, encoding='utf-8')
        print(f"✅ 已导出到: {args.output}")
    else:
        print(output)


def main():
    parser = argparse.ArgumentParser(
        prog="weiqi-joseki",
        description="围棋定式数据库 - KataGo版"
    )
    parser.add_argument("--db", help="数据库路径", default=str(DEFAULT_DB_PATH))
    
    subparsers = parser.add_subparsers(dest="command", help="命令")
    
    # init
    p_init = subparsers.add_parser("init", help="初始化空数据库")
    
    # katago
    p_katago = subparsers.add_parser("katago", help="从KataGo棋谱构建定式库")
    p_katago.add_argument("--start-date", required=True, help="起始日期 (YYYY-MM-DD)")
    p_katago.add_argument("--end-date", required=True, help="结束日期 (YYYY-MM-DD)")
    p_katago.add_argument("--min-freq", type=int, default=10, help="最小频率")
    p_katago.add_argument("--top-k", type=int, default=100000, help="入库数量上限")
    p_katago.add_argument("--first-n", type=int, default=80, help="提取前N手")
    p_katago.add_argument("--distance-threshold", type=int, default=4, help="连通块距离阈值")
    p_katago.add_argument("--min-moves", type=int, default=4, help="最少手数")
    p_katago.add_argument("--max-moves", type=int, default=50, help="最多手数")
    
    # list
    p_list = subparsers.add_parser("list", help="列出定式")
    p_list.add_argument("--limit", type=int, help="限制数量")
    p_list.add_argument("--sort", choices=["id", "freq", "length"], default="id", help="排序方式")
    p_list.add_argument("--order", choices=["asc", "desc"], default="asc", help="排序方向")
    
    # stats
    p_stats = subparsers.add_parser("stats", help="统计信息")
    
    # extract
    p_extract = subparsers.add_parser("extract", help="从SGF提取四角着法")
    p_extract.add_argument("input", help="SGF文件路径")
    p_extract.add_argument("--first-n", type=int, default=80, help="提取前N手")
    p_extract.add_argument("--distance-threshold", type=int, default=4, help="连通块距离阈值")
    p_extract.add_argument("--output", "-o", help="输出MULTIGOGM文件")
    p_extract.add_argument("--verbose", "-v", action="store_true", help="详细输出")
    
    # discover
    p_discover = subparsers.add_parser("discover", help="从SGF发现定式")
    p_discover.add_argument("paths", nargs="+", help="SGF文件或目录路径")
    p_discover.add_argument("--first-n", type=int, default=80, help="提取前N手")
    p_discover.add_argument("--distance-threshold", type=int, default=4, help="连通块距离阈值")
    p_discover.add_argument("--json", action="store_true", help="JSON格式输出")
    p_discover.add_argument("--output", "-o", help="输出文件")
    p_discover.add_argument("--verbose", "-v", action="store_true", help="详细输出")
    
    # export
    p_export = subparsers.add_parser("export", help="导出定式")
    p_export.add_argument("--format", choices=["json", "sgf"], default="json", help="导出格式")
    p_export.add_argument("--output", "-o", help="输出文件")
    p_export.add_argument("--limit", type=int, help="限制导出数量")
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return 1
    
    commands = {
        "init": cmd_init,
        "katago": cmd_katago,
        "list": cmd_list,
        "stats": cmd_stats,
        "extract": cmd_extract,
        "discover": cmd_discover,
        "export": cmd_export,
    }
    
    func = commands.get(args.command)
    if func:
        return func(args) or 0
    else:
        parser.print_help()
        return 1


if __name__ == "__main__":
    sys.exit(main())
