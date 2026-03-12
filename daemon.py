#!/usr/bin/env python3
"""
守护进程：监控股票分析脚本
每10秒检查一次，如果进程挂了则自动重启
使用PID文件避免重复启动
"""

import os
import time
import subprocess
from datetime import datetime

SCRIPT = '/home/seekey/dev/workspace/openclaw/stock/step2_analyze.py'
LOG_FILE = '/home/seekey/dev/workspace/openclaw/stock/analyze.log'
PID_FILE = '/home/seekey/dev/workspace/openclaw/stock/daemon.pid'
CHECK_INTERVAL = 10  # 10秒检查一次

def is_running():
    """检查进程是否在运行（通过PID文件）"""
    if not os.path.exists(PID_FILE):
        return False
    
    try:
        with open(PID_FILE, 'r') as f:
            pid = int(f.read().strip())
        
        # 检查进程是否存在
        os.kill(pid, 0)
        return True
    except:
        return False

def restart():
    """重启分析脚本"""
    print(f"[{datetime.now().strftime('%H:%M:%S')}] 进程已停止，正在重启...")
    # 启动新进程
    proc = subprocess.Popen(
        ['python3', SCRIPT],
        stdout=open(LOG_FILE, 'a'),
        stderr=subprocess.STDOUT,
        cwd='/home/seekey/dev/workspace/openclaw/stock'
    )
    # 保存PID
    with open(PID_FILE, 'w') as f:
        f.write(str(proc.pid))

def main():
    print("=" * 50)
    print("  守护进程已启动")
    print(f"  检查间隔: {CHECK_INTERVAL}秒")
    print(f"  PID文件: {PID_FILE}")
    print("=" * 50)
    
    while True:
        if not is_running():
            print(f"[{datetime.now().strftime('%H:%M:%S')}] 进程已停止")
            restart()
        else:
            try:
                status_file = '/home/seekey/dev/workspace/openclaw/stock/tmp/analyze_status.csv'
                if os.path.exists(status_file):
                    import pandas as pd
                    df = pd.read_csv(status_file)
                    done = len(df[df['analyzed'] == '是'])
                    print(f"[{datetime.now().strftime('%H:%M:%S')}] 运行中... 进度: {done}/4586 ({done/4586*100:.1f}%)")
            except:
                print(f"[{datetime.now().strftime('%H:%M:%S')}] 运行中...")
        
        time.sleep(CHECK_INTERVAL)

if __name__ == "__main__":
    main()
