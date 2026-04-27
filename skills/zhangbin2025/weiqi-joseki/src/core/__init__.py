#!/usr/bin/env python3
"""核心模块 - 数据模型和坐标系统"""

from .coords import (
    CoordinateSystem,
    COORDINATE_SYSTEMS,
    detect_corner,
    convert_to_top_right,
)

__all__ = [
    'CoordinateSystem',
    'COORDINATE_SYSTEMS',
    'detect_corner',
    'convert_to_top_right',
]
