---
title: "第5章: シェルスクリプト入門"
chapter: chapter5
layout: book
---

# 第5章: シェルスクリプト入門

## 🎯 この章の目標
- シェルスクリプトの基本構造を理解する
- 変数と条件分岐を使える
- 簡単な自動化スクリプトを作れる

## 🚀 できるようになること
- 繰り返し作業を自動化できる
- バックアップスクリプトを作れる
- システム管理が効率化できる

## はじめに：シェルスクリプトで作業を自動化する

毎日同じコマンドを打つのは面倒ですよね？
シェルスクリプトを使えば、複数のコマンドを「レシピ」として保存し、1回の実行で全部終わらせることができます。

### 🤖 シェルスクリプトでできること
- **定期バックアップ**: 毎日自動でファイルを保存
- **ログ監視**: エラーを見つけたらメール通知
- **環境構築**: 新しいPCでも1コマンドで環境完成
- **データ処理**: 大量のファイルを一括処理

## 5.1 シェルスクリプトとは

### プログラミング未経験でも大丈夫！

シェルスクリプトは「コマンドの順番を書いたメモ」です。
料理のレシピと同じように、上から順番に実行されます。

### 最初のスクリプト（Hello World）

```bash
# 1. スクリプトファイルを作る（.shは慣例）
vi hello.sh

# 2. 以下を書く（コピペOK）
#!/bin/bash
# ↑これは「おまじない」（bashで実行する宣言）

echo "Hello, WSL2!"
echo "今日は $(date) です"
echo "あなたは $USER さんですね"

# 3. 実行権限を付ける（重要！）
chmod +x hello.sh

# 4. 実行する
./hello.sh
```

💡 **なぜ `./` が必要？**
- セキュリティのため、現在のフォルダは実行対象外
- `./` で「このフォルダの」という意味になる

### シェバン（Shebang）って何？

```bash
#!/bin/bash     # bashで実行（一番よく使う）
#!/bin/sh       # 古いシェルでも動く（互換性重視）
#!/usr/bin/env python3  # Pythonスクリプトの場合
```

最初の `#!` は「このファイルを何で実行するか」を指定する記号です。

## 5.2 変数と基本構文

### 変数の定義と使用

```bash
#!/bin/bash

# 変数定義（=の前後にスペース不可）
NAME="Linux"
VERSION=24.04
COUNT=0

# 変数参照
echo "OS: $NAME"
echo "Version: ${VERSION}"  # 推奨形式

# 変数の連結
FULL_NAME="${NAME}_${VERSION}"
echo "Full: $FULL_NAME"

# 算術演算
COUNT=$((COUNT + 1))
RESULT=$((10 * 5))
echo "Result: $RESULT"

# コマンド実行結果を変数に格納
CURRENT_DATE=$(date +%Y%m%d)
USER_COUNT=$(who | wc -l)
```

### 特殊変数

```bash
#!/bin/bash
# special_vars.sh - 特殊変数の確認

echo "Script name: $0"
echo "First argument: $1"
echo "Second argument: $2"
echo "All arguments: $@"
echo "Number of arguments: $#"
echo "Process ID: $$"
echo "Last command exit status: $?"

# 実行例：
# ./special_vars.sh arg1 arg2 arg3
```

### 配列

```bash
#!/bin/bash

# 配列定義
SERVERS=("web01" "web02" "db01" "db02")

# 要素アクセス
echo "First server: ${SERVERS[0]}"
echo "All servers: ${SERVERS[@]}"
echo "Number of servers: ${#SERVERS[@]}"

# 要素追加
SERVERS+=("cache01")

# ループ処理
for server in "${SERVERS[@]}"; do
    echo "Checking: $server"
done
```

## 5.3 条件分岐

### if文

```bash
#!/bin/bash

# 基本形
if [ condition ]; then
    commands
elif [ another_condition ]; then
    other_commands
else
    default_commands
fi

# 数値比較
NUMBER=10
if [ $NUMBER -eq 10 ]; then
    echo "Number is 10"
elif [ $NUMBER -gt 10 ]; then
    echo "Number is greater than 10"
else
    echo "Number is less than 10"
fi

# 文字列比較
NAME="admin"
if [ "$NAME" = "admin" ]; then
    echo "Admin user"
fi

if [ -z "$NAME" ]; then
    echo "Name is empty"
fi

if [ -n "$NAME" ]; then
    echo "Name is not empty"
fi
```

### ファイル・ディレクトリ判定

```bash
#!/bin/bash

FILE="/etc/passwd"
DIR="/home"

# ファイル存在確認
if [ -f "$FILE" ]; then
    echo "$FILE exists"
fi

# ディレクトリ存在確認
if [ -d "$DIR" ]; then
    echo "$DIR is a directory"
fi

# 読み取り可能確認
if [ -r "$FILE" ]; then
    echo "$FILE is readable"
fi

# 書き込み可能確認
if [ -w "$FILE" ]; then
    echo "$FILE is writable"
fi

# 実行可能確認
if [ -x "$FILE" ]; then
    echo "$FILE is executable"
fi

# ファイルサイズ確認
if [ -s "$FILE" ]; then
    echo "$FILE is not empty"
fi
```

### 条件演算子一覧

| 演算子 | 意味 | 使用例 |
|--------|------|--------|
| -eq | 等しい（数値） | [ $a -eq $b ] |
| -ne | 等しくない（数値） | [ $a -ne $b ] |
| -gt | より大きい | [ $a -gt $b ] |
| -ge | 以上 | [ $a -ge $b ] |
| -lt | より小さい | [ $a -lt $b ] |
| -le | 以下 | [ $a -le $b ] |
| = | 等しい（文字列） | [ "$a" = "$b" ] |
| != | 等しくない（文字列） | [ "$a" != "$b" ] |
| -z | 空文字列 | [ -z "$a" ] |
| -n | 空でない | [ -n "$a" ] |

### case文

```bash
#!/bin/bash

# メニュー選択
echo "Select operation:"
echo "1) Start"
echo "2) Stop"
echo "3) Restart"
echo "4) Status"
read -p "Choice: " CHOICE

case $CHOICE in
    1|start)
        echo "Starting service..."
        ;;
    2|stop)
        echo "Stopping service..."
        ;;
    3|restart)
        echo "Restarting service..."
        ;;
    4|status)
        echo "Checking status..."
        ;;
    *)
        echo "Invalid choice"
        exit 1
        ;;
esac
```

## 5.4 ループ処理

### forループ

```bash
#!/bin/bash

# 基本形
for i in 1 2 3 4 5; do
    echo "Number: $i"
done

# 範囲指定
for i in {1..10}; do
    echo "Count: $i"
done

# ステップ指定（Bash 4.0以降）
for i in {0..20..5}; do
    echo "Step: $i"  # 0, 5, 10, 15, 20
done

# ファイル処理
for file in *.txt; do
    echo "Processing: $file"
    # ファイルが存在しない場合の対処
    [ -f "$file" ] || continue
    wc -l "$file"
done

# コマンド出力を処理
for user in $(cut -d: -f1 /etc/passwd); do
    echo "User: $user"
done
```

### whileループ

```bash
#!/bin/bash

# カウンタループ
COUNT=0
while [ $COUNT -lt 5 ]; do
    echo "Count: $COUNT"
    COUNT=$((COUNT + 1))
done

# ファイル読み込み
while IFS= read -r line; do
    echo "Line: $line"
done < input.txt

# 無限ループ
while true; do
    echo "Running... (Press Ctrl+C to stop)"
    sleep 1
done

# 条件待機
while ! ping -c 1 google.com > /dev/null 2>&1; do
    echo "Waiting for network..."
    sleep 5
done
echo "Network is up!"
```

### untilループ

```bash
#!/bin/bash

# 条件が真になるまで継続
COUNT=0
until [ $COUNT -ge 5 ]; do
    echo "Count: $COUNT"
    COUNT=$((COUNT + 1))
done

# サービス起動待機
until systemctl is-active nginx > /dev/null 2>&1; do
    echo "Waiting for nginx to start..."
    sleep 2
done
echo "Nginx is running!"
```

## 5.5 関数

### 関数定義と呼び出し

```bash
#!/bin/bash

# 関数定義（方法1）
function greet() {
    echo "Hello, $1!"
}

# 関数定義（方法2）
say_goodbye() {
    local name=$1  # ローカル変数
    echo "Goodbye, $name!"
    return 0  # 戻り値（0-255）
}

# 関数呼び出し
greet "World"
say_goodbye "Linux"

# 戻り値確認
check_service() {
    local service=$1
    if systemctl is-active "$service" > /dev/null 2>&1; then
        return 0
    else
        return 1
    fi
}

if check_service nginx; then
    echo "Nginx is running"
else
    echo "Nginx is not running"
fi
```

### 実用的な関数例

```bash
#!/bin/bash

# ログ出力関数
log_message() {
    local level=$1
    shift
    local message="$@"
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] [$level] $message" | tee -a /var/log/script.log
}

# エラーハンドリング関数
error_exit() {
    log_message "ERROR" "$1"
    exit 1
}

# 使用例
log_message "INFO" "Script started"
[ -f config.txt ] || error_exit "Config file not found"
log_message "INFO" "Script completed"

# バックアップ関数
backup_file() {
    local source=$1
    local backup="${source}.$(date +%Y%m%d_%H%M%S).bak"
    
    if [ -f "$source" ]; then
        cp "$source" "$backup"
        log_message "INFO" "Backed up $source to $backup"
        return 0
    else
        log_message "ERROR" "Source file $source not found"
        return 1
    fi
}
```

## 5.6 入出力とリダイレクト

### 標準入出力

```bash
#!/bin/bash

# ユーザー入力
read -p "Enter your name: " NAME
echo "Hello, $NAME"

# パスワード入力（非表示）
read -s -p "Enter password: " PASSWORD
echo  # 改行
echo "Password length: ${#PASSWORD}"

# タイムアウト付き入力
if read -t 5 -p "Continue? (5 sec timeout) [y/n]: " ANSWER; then
    echo "Answer: $ANSWER"
else
    echo "Timeout!"
fi

# デフォルト値
read -p "Port number [8080]: " PORT
PORT=${PORT:-8080}
echo "Using port: $PORT"
```

### リダイレクトとパイプ

```bash
#!/bin/bash

# 出力リダイレクト
echo "Log message" > output.txt   # 上書き
echo "Another log" >> output.txt  # 追記

# エラー出力リダイレクト
command 2> error.log              # エラーのみ
command > output.log 2>&1         # 両方を同じファイルへ
command &> all.log                # 簡略記法

# 入力リダイレクト
while read line; do
    echo "Processing: $line"
done < input.txt

# ヒアドキュメント
cat << EOF > config.txt
server_name=localhost
port=8080
debug=true
EOF

# コマンド置換
FILES=$(ls *.txt)
LINE_COUNT=$(wc -l < file.txt)

# パイプライン処理
cat access.log | grep ERROR | sort | uniq -c | sort -rn > error_summary.txt
```

## 5.7 エラーハンドリング

### 終了ステータス

```bash
#!/bin/bash

# コマンド実行と結果確認
cp source.txt dest.txt
if [ $? -eq 0 ]; then
    echo "Copy successful"
else
    echo "Copy failed"
    exit 1
fi

# より簡潔な書き方
if cp source.txt dest.txt; then
    echo "Copy successful"
else
    echo "Copy failed"
    exit 1
fi

# &&と||の使用
mkdir /tmp/test && echo "Directory created" || echo "Failed to create directory"
```

### set オプション

```bash
#!/bin/bash

# エラー時に即座に終了
set -e

# 未定義変数の使用でエラー
set -u

# パイプライン内のエラーも検出
set -o pipefail

# デバッグモード
set -x  # 実行コマンドを表示

# 組み合わせ
set -euo pipefail
```

### trapによるクリーンアップ

```bash
#!/bin/bash

# 一時ファイル
TEMP_FILE=$(mktemp)

# 終了時のクリーンアップ
cleanup() {
    echo "Cleaning up..."
    rm -f "$TEMP_FILE"
}

trap cleanup EXIT

# エラー時の処理
error_handler() {
    echo "Error occurred on line $1"
    exit 1
}

trap 'error_handler $LINENO' ERR

# メイン処理
echo "Processing..." > "$TEMP_FILE"
# 処理実行
```

## 5.8 実践スクリプト例

### システム監視スクリプト

```bash
#!/bin/bash
# system_monitor.sh - システムリソース監視

set -euo pipefail

# 設定
THRESHOLD_CPU=80
THRESHOLD_MEM=90
THRESHOLD_DISK=85
LOG_FILE="/var/log/system_monitor.log"

# ログ関数
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

# CPU使用率チェック
check_cpu() {
    local cpu_usage=$(top -bn1 | grep "Cpu(s)" | awk '{print int($2)}')
    if [ $cpu_usage -gt $THRESHOLD_CPU ]; then
        log "WARNING: High CPU usage: ${cpu_usage}%"
        return 1
    fi
    return 0
}

# メモリ使用率チェック
check_memory() {
    local mem_usage=$(free | grep Mem | awk '{print int($3/$2 * 100)}')
    if [ $mem_usage -gt $THRESHOLD_MEM ]; then
        log "WARNING: High memory usage: ${mem_usage}%"
        return 1
    fi
    return 0
}

# ディスク使用率チェック
check_disk() {
    local disk_usage=$(df -h / | tail -1 | awk '{print int($5)}')
    if [ $disk_usage -gt $THRESHOLD_DISK ]; then
        log "WARNING: High disk usage: ${disk_usage}%"
        return 1
    fi
    return 0
}

# メイン処理
main() {
    log "Starting system monitoring"
    
    local alert=0
    
    check_cpu || alert=1
    check_memory || alert=1
    check_disk || alert=1
    
    if [ $alert -eq 1 ]; then
        log "ALERT: System resources need attention"
        # アラート送信（メール、Slack等）
    else
        log "INFO: All systems normal"
    fi
}

# 実行
main
```

### バックアップスクリプト

```bash
#!/bin/bash
# backup.sh - 増分バックアップスクリプト

set -euo pipefail

# 設定
SOURCE_DIR="/home/user/data"
BACKUP_DIR="/backup"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_NAME="backup_${TIMESTAMP}"
RETENTION_DAYS=7

# バックアップ実行
perform_backup() {
    local full_backup_dir="${BACKUP_DIR}/${BACKUP_NAME}"
    
    # ディレクトリ作成
    mkdir -p "$full_backup_dir"
    
    # rsyncで増分バックアップ
    if [ -L "${BACKUP_DIR}/latest" ]; then
        # 前回のバックアップがある場合は増分
        rsync -av --link-dest="${BACKUP_DIR}/latest" \
              "$SOURCE_DIR/" "$full_backup_dir/"
    else
        # 初回は完全バックアップ
        rsync -av "$SOURCE_DIR/" "$full_backup_dir/"
    fi
    
    # 最新バックアップへのシンボリックリンク更新
    rm -f "${BACKUP_DIR}/latest"
    ln -s "$full_backup_dir" "${BACKUP_DIR}/latest"
    
    echo "Backup completed: $full_backup_dir"
}

# 古いバックアップ削除
cleanup_old_backups() {
    find "$BACKUP_DIR" -maxdepth 1 -type d -name "backup_*" \
         -mtime +$RETENTION_DAYS -exec rm -rf {} \;
    echo "Old backups cleaned up"
}

# メイン処理
main() {
    echo "Starting backup at $(date)"
    
    # ソースディレクトリ確認
    [ -d "$SOURCE_DIR" ] || { echo "Source directory not found"; exit 1; }
    
    # バックアップディレクトリ作成
    mkdir -p "$BACKUP_DIR"
    
    # バックアップ実行
    perform_backup
    
    # クリーンアップ
    cleanup_old_backups
    
    echo "Backup process completed at $(date)"
}

# 実行
main
```

## 5.9 cron による定期実行

### crontab 基本

```bash
# crontab編集
crontab -e

# crontab確認
crontab -l

# crontab削除
crontab -r
```

### cron記法

```text
# 分 時 日 月 曜日 コマンド
# (0-59) (0-23) (1-31) (1-12) (0-7, 0と7は日曜)

# 毎日午前2時に実行
0 2 * * * /home/user/backup.sh

# 平日の午前9時に実行
0 9 * * 1-5 /home/user/weekday_task.sh

# 5分ごとに実行
*/5 * * * * /home/user/monitor.sh

# 毎月1日の午前3時に実行
0 3 1 * * /home/user/monthly_report.sh
```

### WSL2でのcron設定

```bash
# cron起動（systemd有効時）
sudo systemctl start cron
sudo systemctl enable cron

# cron起動（systemd無効時）
sudo service cron start

# 自動起動設定（.bashrcに追加）
echo 'sudo service cron start 2>/dev/null' >> ~/.bashrc
```

## 5.10 演習問題

### 演習1: ログローテーションスクリプト

```bash
#!/bin/bash
# log_rotate.sh - ログファイルローテーション

LOG_DIR="/var/log/myapp"
MAX_SIZE=10485760  # 10MB
MAX_FILES=5

rotate_log() {
    local log_file=$1
    local base_name=$(basename "$log_file")
    
    # サイズチェック
    if [ -f "$log_file" ] && [ $(stat -c%s "$log_file") -gt $MAX_SIZE ]; then
        # 既存のローテーションファイルを移動
        for i in $(seq $((MAX_FILES-1)) -1 1); do
            [ -f "${log_file}.${i}" ] && mv "${log_file}.${i}" "${log_file}.$((i+1))"
        done
        
        # 現在のログをローテート
        mv "$log_file" "${log_file}.1"
        
        # 最古のファイルを削除
        [ -f "${log_file}.${MAX_FILES}" ] && rm "${log_file}.${MAX_FILES}"
        
        echo "Rotated: $log_file"
    fi
}

# メイン処理
for log_file in "$LOG_DIR"/*.log; do
    [ -f "$log_file" ] && rotate_log "$log_file"
done
```

### 演習2: ユーザー管理スクリプト

```bash
#!/bin/bash
# user_manager.sh - ユーザー一括管理

USER_LIST="users.txt"  # username,fullname,group

create_users() {
    while IFS=',' read -r username fullname group; do
        # ユーザー存在チェック
        if id "$username" &>/dev/null; then
            echo "User $username already exists"
        else
            # グループ作成
            groupadd "$group" 2>/dev/null
            
            # ユーザー作成
            useradd -m -g "$group" -c "$fullname" "$username"
            
            # 初期パスワード設定
            echo "${username}:password123" | chpasswd
            
            # パスワード変更強制
            passwd -e "$username"
            
            echo "Created user: $username"
        fi
    done < "$USER_LIST"
}

# 実行（要root権限）
[ $EUID -eq 0 ] || { echo "Run as root"; exit 1; }
create_users
```

### 演習3: デプロイスクリプト

```bash
#!/bin/bash
# deploy.sh - アプリケーションデプロイ

set -euo pipefail

# 設定
APP_DIR="/var/www/myapp"
GIT_REPO="https://github.com/user/myapp.git"
BRANCH="main"
BACKUP_DIR="/var/backups/myapp"

# デプロイ前フック
pre_deploy() {
    echo "Running pre-deploy tasks..."
    
    # バックアップ作成
    if [ -d "$APP_DIR" ]; then
        backup_name="backup_$(date +%Y%m%d_%H%M%S).tar.gz"
        tar -czf "${BACKUP_DIR}/${backup_name}" -C "$APP_DIR" .
        echo "Backup created: ${backup_name}"
    fi
    
    # サービス停止
    sudo systemctl stop myapp || true
}

# デプロイ実行
deploy() {
    echo "Deploying application..."
    
    # 最新コード取得
    if [ -d "$APP_DIR/.git" ]; then
        cd "$APP_DIR"
        git fetch origin
        git reset --hard "origin/${BRANCH}"
    else
        git clone -b "$BRANCH" "$GIT_REPO" "$APP_DIR"
        cd "$APP_DIR"
    fi
    
    # 依存関係インストール
    npm install --production
    
    # アセットビルド
    npm run build
    
    # 権限設定
    chown -R www-data:www-data "$APP_DIR"
}

# デプロイ後フック
post_deploy() {
    echo "Running post-deploy tasks..."
    
    # データベースマイグレーション
    npm run migrate
    
    # キャッシュクリア
    npm run cache:clear
    
    # サービス起動
    sudo systemctl start myapp
    
    # ヘルスチェック
    sleep 5
    if curl -f http://localhost:3000/health > /dev/null 2>&1; then
        echo "Deployment successful!"
    else
        echo "Health check failed!"
        exit 1
    fi
}

# メイン処理
main() {
    echo "Starting deployment at $(date)"
    
    pre_deploy
    deploy
    post_deploy
    
    echo "Deployment completed at $(date)"
}

# 実行
main
```

## まとめ

シェルスクリプトの習得ポイント：

1. **基本構文**: 変数、条件分岐、ループを確実に理解
2. **エラーハンドリング**: set -euo pipefail とtrapの活用
3. **実践的活用**: 日常業務の自動化から始める

これらの基礎を基に、インフラ運用の自動化を段階的に進めていきます。

**次章へ**: [第6章 WordPress構築](../chapter6/)
