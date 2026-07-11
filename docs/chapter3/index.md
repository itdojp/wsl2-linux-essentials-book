---
title: "第3章: プロセスとサービス管理"
chapter: chapter3
layout: book
---

# 第3章: プロセスとサービス管理

## 前提（検証環境）
- WSL2 上の Ubuntu（例: 22.04/24.04）
- 本章の `systemctl` 例は systemd 有効を前提（無効の場合は章内「systemd無効時の代替手段」を参照）
- 設定変更やサービス操作は `sudo` が必要

## この章の目標
- プロセスとサービスの違いを説明できる
- systemd によるサービス管理（起動・停止・状態確認）の基本を理解する
- システムリソースの状況を確認できる

## できるようになること
- 不要なプロセスを終了できる
- Web サーバーなどのサービスを起動・停止できる
- システムの状態を把握し、一次切り分けができる

## はじめに：プロセスとサービスを理解する

コンピュータで動いているプログラムには、大きく分けて2種類あります。

### プロセス（実行中のプログラム）
- **例**: ls コマンド、電卓、メモ帳
- **特徴**: 実行して終了する
- **寿命**: 数秒〜数時間（処理内容による）

### サービス（常駐プロセス）
- **例**: Web サーバー、データベース、SSH サーバー
- **特徴**: 停止するまで常駐して動作する
- **寿命**: 停止するまで継続する

## 3.1 WSL2 での systemd 有効化

### systemdとは何か？

systemd は、Linux のサービスを管理するマネージャーです。Windows の「サービス」管理ツールに相当します。

### なぜsystemdが必要なのか？

- サービスの自動起動を管理
- サービスの状態を監視
- ログを統一管理

現在の `wsl --install` で導入される Ubuntu では systemd が既定です。既存環境や他のディストリビューションでは無効の場合があるため、設定変更の前に PID 1 を確認します。

### 有効化手順

```bash
# 1. 現在の init を確認（systemd なら以降の変更は不要）
ps -p 1 -o comm=

# 2. systemd でない場合だけ設定ファイルを編集
sudo vi /etc/wsl.conf
```

`/etc/wsl.conf` へ次を記入します。

```ini
[boot]
systemd=true
```

保存後、PowerShell で対象ディストリビューションを停止して再開します。`Ubuntu` は `wsl --list --verbose` に表示された名前へ読み替えてください。

```powershell
$distro = "Ubuntu"
wsl --terminate $distro
wsl -d $distro
```

再開した Ubuntu で確認します。

```bash
systemctl status
```

`wsl --terminate` は指定したディストリビューションだけを停止します。`wsl --shutdown` は実行中の全ディストリビューションと WSL 2 の軽量 VM を停止するため、他の作業がないことを確認して使います。`wsl --version` が利用できない場合や古い場合は、先に PowerShell で `wsl --update` を実行します。

### systemd無効時の代替手段

```bash
# systemd無効環境での手動サービス起動
sudo service nginx start
sudo service mysql start
```

これは現在のセッションでの手動起動です。`.bashrc` に `sudo service ... start` を追加すると、シェルを開くたびに権限昇格とサービス起動を試みるため、本書では自動起動の代替として使用しません。自動起動が必要なら systemd を有効にし、対象サービスの unit と公開範囲を確認します。

## 3.2 プロセスの概念と管理

### プロセスとは

プロセスは実行中のプログラムのインスタンスです。各プロセスは固有のPID（Process ID）を持ちます。

![プロセス・サービス関係図]({{ site.baseurl }}/assets/images/process-service-diagram.svg)

```bash
# 現在のシェルのPID確認
echo $$
# 出力例: 1234

# 親プロセスのPID確認
echo $PPID
# 出力例: 1000
```

上の図は、プロセスとサービスの関係性、そして親子プロセスの階層構造を示しています。systemdがすべてのプロセスの最上位に位置し、その下に様々なサービスやユーザープロセスが配置される構造が理解できます。

### ps - プロセス表示

```bash
# 基本表示
ps

# 全プロセス表示（BSD形式）
ps aux

# 全プロセス表示（UNIX(System V)形式）
ps -ef

# ツリー表示
ps auxf
```

ps auxの出力解説は次のとおりです。
```text
USER  PID %CPU %MEM    VSZ   RSS TTY STAT START TIME COMMAND
root    1  0.0  0.1 169432 11204 ?   Ss   09:00 0:01 /sbin/init
│       │    │    │      │     │   │    │     │    │    └─ 実行コマンド
│       │    │    │      │     │   │    │     │    └─ CPU 使用時間
│       │    │    │      │     │   │    │     └─ 開始時刻
│       │    │    │      │     │   │    └─ プロセス状態
│       │    │    │      │     │   └─ 制御端末
│       │    │    │      │     └─ 物理メモリ（KB）
│       │    │    │      └─ 仮想メモリ（KB）
│       │    │    └─ メモリ使用率
│       │    └─ CPU 使用率
│       └─ プロセスID
└─ 実行ユーザー
```

プロセス状態（STAT）の意味は次のとおりです。
- R: 実行中（Running）
- S: スリープ（Sleeping）
- D: ディスクI/O待ち
- Z: ゾンビ
- T: 停止
- <: 高優先度
- N: 低優先度

### top/htop - リアルタイム監視

```bash
# top起動
top

# 操作キー：
# q: 終了
# k: プロセスkill
# r: nice値変更
# M: メモリ使用順ソート
# P: CPU 使用順ソート
# 1: CPU 別表示
```

htopの導入と使用は次のとおりです。
```bash
# インストール
sudo apt update
sudo apt install htop -y

# 起動
htop

# 利点：
# - カラー表示
# - マウス操作対応
# - プロセスツリー表示
# - より直感的な UI
```

### プロセスの制御

```bash
# バックグラウンド実行
command &
sleep 100 &

# ジョブ確認
jobs
# 出力: [1]+ Running sleep 100 &

# フォアグラウンドへ
fg %1

# バックグラウンドへ
# Ctrl+Z で一時停止後
bg %1

# プロセス終了
kill PID        # 通常終了（SIGTERM）
kill -9 PID     # 強制終了（SIGKILL）
killall command # 名前指定で終了
```

シグナル一覧は次のとおりです。
```bash
# 主要シグナル
kill -l
# 1) SIGHUP     # 再読み込み
# 2) SIGINT     # 割り込み（Ctrl+C）
# 9) SIGKILL    # 強制終了
# 15) SIGTERM   # 終了要求（デフォルト）
# 19) SIGSTOP   # 一時停止
# 18) SIGCONT   # 再開
```

### 実践: ゾンビプロセスの理解と対処

```bash
# ゾンビプロセス生成例
cat << 'SCRIPT' > zombie_test.sh
#!/bin/bash
# 親プロセス
echo "Parent PID: $$"
# 子プロセス生成
(sleep 2; echo "Child finished") &
CHILD_PID=$!
echo "Child PID: $CHILD_PID"
# 親は子の終了を待たない
sleep 10
SCRIPT

chmod +x zombie_test.sh
./zombie_test.sh &

# 別ターミナルで確認
ps aux | grep defunct
# ゾンビプロセスが表示される

# 対処: 親プロセスを終了
kill $(ps aux | grep zombie_test | grep -v grep | awk '{print $2}')
```

## 3.3 systemdによるサービス管理

### systemctlコマンド基本

```bash
# サービス状態確認
systemctl status nginx

# サービス操作
sudo systemctl start nginx    # 起動
sudo systemctl stop nginx     # 停止
sudo systemctl restart nginx  # 再起動
sudo systemctl reload nginx   # 設定再読み込み

# 自動起動設定
sudo systemctl enable nginx   # 有効化
sudo systemctl disable nginx  # 無効化

# 全サービス一覧
systemctl list-units --type=service
systemctl list-units --type=service --state=running
```

### サービスユニットファイルの理解

```bash
# ユニットファイルの場所
ls /lib/systemd/system/*.service
ls /etc/systemd/system/*.service

# ユニットファイルの内容確認
cat /lib/systemd/system/nginx.service
```

基本的なユニットファイル構造は次のとおりです。
```ini
[Unit]
Description=Nginx Web Server
After=network.target

[Service]
Type=forking
PIDFile=/run/nginx.pid
ExecStartPre=/usr/sbin/nginx -t
ExecStart=/usr/sbin/nginx
ExecReload=/bin/kill -s HUP $MAINPID
ExecStop=/bin/kill -s QUIT $MAINPID
Restart=on-failure

[Install]
WantedBy=multi-user.target
```

### カスタムサービスの作成

```bash
# 1. アプリケーションスクリプト作成
sudo nano /usr/local/bin/myapp.sh
```

```bash
#!/bin/bash
# myapp.sh - サンプルアプリケーション
while true; do
    echo "$(date): MyApp is running"
    sleep 10
done
```

```bash
# 2. 実行権限付与
sudo chmod +x /usr/local/bin/myapp.sh

# 3. ユニットファイル作成
sudo nano /etc/systemd/system/myapp.service
```

```ini
[Unit]
Description=My Custom Application
After=network.target

[Service]
Type=simple
User=nobody
Group=nogroup
ExecStart=/usr/local/bin/myapp.sh
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

```bash
# 4. サービス登録と起動
sudo systemctl daemon-reload
sudo systemctl start myapp
sudo systemctl status myapp
sudo systemctl enable myapp

# 5. ログ確認
sudo journalctl -u myapp -f
```

### journalctl - ログ管理

```bash
# 全ログ表示
journalctl

# 特定サービスのログ
journalctl -u nginx

# 最新ログのみ
journalctl -u nginx -n 50

# リアルタイム追跡
journalctl -u nginx -f

# 時間範囲指定
journalctl --since "2025-01-15 10:00:00"
journalctl --since "1 hour ago"
journalctl --since yesterday --until today

# エラーレベル以上のみ
journalctl -p err

# ブート単位で表示
journalctl -b  # 現在のブート
journalctl -b -1  # 前回のブート
```

## 3.4 実践: Web サーバーの導入と管理

### Nginx導入

```bash
# 1. パッケージ更新とインストール
sudo apt update
sudo apt install nginx -y

# 2. 状態確認
systemctl status nginx

# 3. 設定ファイル構造
ls -la /etc/nginx/
# nginx.conf         - メイン設定
# sites-available/   - 利用可能サイト設定
# sites-enabled/     - 有効化されたサイト

# 4. デフォルトページ確認
curl http://localhost
```

### 仮想ホスト設定

```bash
# 1. サイト用ディレクトリ作成
sudo mkdir -p /var/www/mysite
sudo chown -R $USER:$USER /var/www/mysite

# 2. テストページ作成
cat << 'HTML' > /var/www/mysite/index.html
<!DOCTYPE html>
<html>
<head><title>My Site</title></head>
<body>
    <h1>Welcome to My Site on WSL2!</h1>
    <p>Served by Nginx</p>
</body>
</html>
HTML

# 3. サイト設定作成
sudo nano /etc/nginx/sites-available/mysite
```

```nginx
server {
    listen 80;
    listen [::]:80;
    
    server_name mysite.local;
    root /var/www/mysite;
    index index.html;
    
    location / {
        try_files $uri $uri/ =404;
    }
    
    access_log /var/log/nginx/mysite_access.log;
    error_log /var/log/nginx/mysite_error.log;
}
```

```bash
# 4. サイト有効化
sudo ln -s /etc/nginx/sites-available/mysite /etc/nginx/sites-enabled/

# 5. 設定テスト
sudo nginx -t

# 6. Nginx再起動
sudo systemctl reload nginx

# 7. hosts編集（Windows 側）
# C:\Windows\System32\drivers\etc\hosts に追加
# 127.0.0.1 mysite.local
```

### パフォーマンス監視

```bash
# Nginxステータスモジュール有効化
sudo nano /etc/nginx/sites-available/default

# server ブロック内に追加：
location /nginx_status {
    stub_status;
    allow 127.0.0.1;
    deny all;
}

# 再読み込み
sudo systemctl reload nginx

# ステータス確認
curl http://localhost/nginx_status
```

## 3.5 プロセス優先度とリソース制限

### nice/renice - 優先度管理

```bash
# nice値確認（-20～19、小さいほど高優先度）
ps -eo pid,nice,cmd

# 低優先度で実行
nice -n 10 command

# 高優先度で実行（要root）
sudo nice -n -5 command

# 実行中プロセスの優先度変更
renice -n 5 -p PID
sudo renice -n -5 -p PID
```

### ulimit - リソース制限

```bash
# 現在の制限確認
ulimit -a

# ファイルディスクリプタ数
ulimit -n        # 確認
ulimit -n 4096   # 設定

# プロセス数制限
ulimit -u        # 確認
ulimit -u 1024   # 設定

# コアダンプサイズ
ulimit -c unlimited  # 無制限に設定
```

### cgroups - リソース制御

```bash
# CPU 使用率制限例
# 1. cgroupsインストール（必要な場合）
sudo apt install cgroup-tools -y

# 2. グループ作成
sudo cgcreate -g cpu:/mygroup

# 3. CPU 使用率50%に制限
sudo cgset -r cpu.cfs_quota_us=50000 mygroup

# 4. プロセス実行
sudo cgexec -g cpu:mygroup stress --cpu 1
```

## 3.6 演習問題

### 演習1: プロセス監視スクリプト

```bash
#!/bin/bash
# process_monitor.sh - 特定プロセスの監視

PROCESS_NAME="nginx"
CHECK_INTERVAL=5
LOG_DIR="$HOME/logs"
LOG_FILE="$LOG_DIR/process_monitor.log"

mkdir -p "$LOG_DIR"

while true; do
    if ! pgrep -x "$PROCESS_NAME" > /dev/null; then
        echo "$(date): $PROCESS_NAME is not running. Starting..."
        sudo systemctl start "$PROCESS_NAME"
        
        # アラート（実際はメール送信等）
        echo "$(date): $PROCESS_NAME was restarted" >> "$LOG_FILE"
    fi
    sleep $CHECK_INTERVAL
done
```

### 演習2: リソース使用状況レポート

```bash
#!/bin/bash
# resource_report.sh - システムリソースレポート生成

echo "=== System Resource Report ==="
echo "Date: $(date)"
echo ""

echo "CPU Usage:"
top -bn1 | grep "Cpu(s)" | awk '{print "  User: "$2"% System: "$4"%"}'
echo ""

echo "Memory Usage:"
free -h | grep "^Mem:" | awk '{print "  Total: "$2" Used: "$3" Free: "$4}'
echo ""

echo "Top 5 CPU Consumers:"
ps aux --sort=-%cpu | head -6 | tail -5 | awk '{printf "  %-20s %5s%%\n", $11, $3}'
echo ""

echo "Top 5 Memory Consumers:"
ps aux --sort=-%mem | head -6 | tail -5 | awk '{printf "  %-20s %5s%%\n", $11, $4}'
```

### 演習3: サービス自動復旧設定

```bash
# systemdの自動再起動設定
sudo nano /etc/systemd/system/myapp.service

# Unitセクションに追加（[Unit] で設定）：
StartLimitIntervalSec=60
StartLimitBurst=5

# Serviceセクションに追加（[Service] で設定）：
Restart=always
RestartSec=10

# 設定反映
sudo systemctl daemon-reload
sudo systemctl restart myapp

# テスト（疑似クラッシュ）
sudo systemctl kill -s SIGKILL myapp
# 10秒後に自動再起動される
```

## 3.7 トラブルシューティング

### よくある問題と対処

| 症状 | 原因 | 対処法 |
|------|------|--------|
| `System has not been booted with systemd` | systemd未有効 | `/etc/wsl.conf`でsystemd有効化 |
| `Failed to connect to bus` | D-Bus未起動 | `sudo service dbus start` |
| サービスが起動しない | 設定エラー | `journalctl -xe`でエラー確認 |
| CPU 使用率100% | 暴走プロセス | `top`で特定し`kill -9` |
| メモリ不足 | WSL2 メモリ制限 | `.wslconfig`で調整 |

### WSL2 特有の問題

```bash
# WSL2 メモリ制限設定
# Windows 側で %USERPROFILE%\.wslconfig 作成
[wsl2]
memory=4GB
processors=2
swap=2GB

# localhost接続できない問題
# /etc/hosts確認
cat /etc/hosts
# 127.0.0.1 localhost が存在することを確認

# ネットワーク接続リセット
wsl --shutdown  # PowerShell で実行
netsh winsock reset  # 管理者権限 PowerShell
```

### デバッグ手順

```bash
# 1. プロセス状態確認
ps aux | grep [p]rocess_name
pgrep -a process_name

# 2. ポート使用状況確認
sudo ss -tlnp
sudo lsof -i :80

# 3. ログ確認優先順位
journalctl -xe          # systemdログ
sudo tail -f /var/log/syslog # システムログ（Ubuntu系。環境によりパスは異なる）
dmesg                   # カーネルメッセージ

# 4. strace でシステムコール追跡
strace -p PID
strace command 2>&1 | grep -i error
```

## まとめ

プロセスとサービス管理の要点は次のとおりです。

1. **systemd 有効化**: `systemctl` を利用する場合に必要（環境により有効／無効が異なる）
2. **基本コマンド**: ps、top、systemctl の使い分け
3. **監視と自動化**: サービスの自動復旧設定により運用負荷を低減できる

次章では、これらの知識を基にネットワーク設定と管理を扱います。

**次章へ**: [第4章 ネットワークの基礎](../chapter4/)
