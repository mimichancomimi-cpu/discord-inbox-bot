# -*- coding: utf-8 -*-
"""
投稿スケジュールパッケージ
"""

import sys
from pathlib import Path

# このパッケージのディレクトリをパスに追加
package_dir = Path(__file__).parent
if str(package_dir) not in sys.path:
    sys.path.insert(0, str(package_dir))

# モジュールをインポート（ファイル名が日本語なので動的にインポート）
import importlib.util
module_file = package_dir / "投稿スケジュール.py"
spec = importlib.util.spec_from_file_location("投稿スケジュール", module_file)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

# 関数をエクスポート
schedule_posts_to_spreadsheet = module.schedule_posts_to_spreadsheet

__all__ = ['schedule_posts_to_spreadsheet']
