---
title: "第2章: テキスト処理の基本"
chapter: chapter2
layout: book
---

# 第2章: テキスト処理の基本

## 前提（検証環境）
- WSL2 上の Ubuntu（例: 22.04/24.04）
- 設定ファイル編集など一部の操作は `sudo` が必要

## この章の目標
- テキストファイルの基本的な編集操作を行える
- vi/vim の基本操作を説明できる
- パイプとリダイレクトの基本を理解する

## できるようになること
- 設定ファイルの編集と差分確認ができる
- ログファイルから必要な情報を抽出できる
- 複数のコマンドを組み合わせて処理できる

## はじめに：なぜテキスト処理が重要なのか

Linux では、設定やログの多くがテキストファイルです。
- 設定を変更する = テキストファイルを編集する
- エラーを調べる = ログファイル（テキスト）を読む
- データを分析する = テキストデータを加工する

この章では、テキスト処理の基礎を整理します。

## 2.1 テキストエディタの選択と基本操作

### エディタ選定の考え方

Linux で広く利用できるエディタは vi（vim）です。多くの Linux システムに標準搭載されますが、操作体系の理解が必要です。簡易な操作を優先する場合は、nano を利用する選択肢もあります。なお、サーバー環境では vi/vim が利用可能なケースが多いため、基本操作は把握しておくことを推奨します。

### エディタ選択の指針

| エディタ | 学習時間 | 使う場面 | 難易度（目安） |
|---------|---------|------------|--------|
| vi/vim | 30分（基本） | サーバー上での作業 | 高 |
| VSCode | 30分 | WSL2 での開発 | 中 |

補足: vi/vim は習熟に時間を要する場合がありますが、最低限の編集（保存・終了）だけでも把握しておくと運用上有効です。

### vi/vim - Linux 標準エディタ

```bash
# viの起動
vi test.txt

# 基本の3つのモード
# 1. ノーマルモード（起動時） - コマンド入力
# 2. 挿入モード - 文字入力
# 3. コマンドモード - 保存や終了
```

例: 設定ファイル編集
```bash
# システム設定のバックアップと編集
sudo cp /etc/hosts /etc/hosts.bak
sudo vi /etc/hosts

# 追加行の例
127.0.0.1    myapp.local

# vi/vim の保存と終了: Esc -> :wq
# nano を利用する場合: sudo nano /etc/hosts（保存: Ctrl+O -> Enter、終了: Ctrl+X）
```

### vim - 効率重視のエディタ

```bash
# vimの起動
vim test.txt

# モード概念（重要）
# ノーマルモード: コマンド実行（起動時）
# 挿入モード: テキスト入力（i, a, o）
# コマンドモード: ファイル操作（:）
```

最小限の操作は次のとおりです。
```bash
# 1. ファイルを開く
vim script.sh

# 2. 挿入モードへ
i

# 3. テキスト入力
#!/bin/bash
echo "Hello"

# 4. ノーマルモードへ戻る
Esc

# 5. 保存して終了
:wq
# または強制終了（保存なし）
:q!
```

vim の最低限の操作コマンド 10 個は次のとおりです。
```vim
i        # 挿入モード開始
Esc      # ノーマルモードへ
:w       # 保存
:q       # 終了
:wq      # 保存して終了
dd       # 行削除
yy       # 行コピー
p        # 貼り付け
u        # 取り消し（Undo）
/word    # 検索
```

### VSCode WSL統合

```bash
# WSL内からVSCodeを起動
code .

# ファイルを指定して開く
code script.sh

# 拡張機能推奨
# - Remote - WSL
# - Bash IDE
# - ShellCheck
```

## 2.2 基本フィルタコマンド

### grep - パターン検索

```bash
# 基本形
grep "pattern" file.txt

# よく使うオプション
grep -i "error" log.txt     # 大文字小文字無視
grep -n "TODO" script.sh     # 行番号表示
grep -r "password" /etc/    # 再帰検索
grep -v "debug" log.txt      # 除外（反転）
grep -c "WARNING" *.log      # カウント
```

実践的なgrepパターンは次のとおりです。
```bash
# 1. エラーログ抽出
grep -E "(ERROR|FATAL)" application.log

# 2. IP アドレス検索
# 簡易パターン（厳密な範囲チェックは別途実施）
grep -E "([0-9]{1,3}\.){3}[0-9]{1,3}" access.log

# 3. 空行除外
grep -v "^$" config.txt

# 4. コメント行除外
grep -v "^#" /etc/ssh/sshd_config

# 5. プロセス検索の定番
# grep 自身が混ざらない形（推奨）
pgrep -fa nginx
```

### sed - ストリーム編集

```bash
# 基本形: 置換
sed 's/old/new/' file.txt        # 各行の最初のみ
sed 's/old/new/g' file.txt       # 全置換

# ファイル直接編集（WSL2/Ubuntu の GNU sed では -i.bak でバックアップ作成）
sed -i.bak 's/localhost/127.0.0.1/g' config.txt
# macOS/BSD sed の場合（バックアップなし）: sed -i '' 's/localhost/127.0.0.1/g' config.txt

# 行削除
sed '/^#/d' config.txt            # コメント行削除
sed '/^$/d' file.txt              # 空行削除

# 行追加
sed '1i\#!/bin/bash' script.sh    # 先頭に追加
sed '$a\exit 0' script.sh         # 末尾に追加
```

実用例は次のとおりです。
```bash
# 設定ファイルの値変更
sed -i.bak 's/port=8080/port=3000/g' app.conf

# ログファイルの日付形式変更
sed 's/\([0-9]\{4\}\)-\([0-9]\{2\}\)-\([0-9]\{2\}\)/\3\/\2\/\1/g' dates.log

# 複数の置換
sed -e 's/dev/development/g' -e 's/prod/production/g' env.txt
```

### awk - テキスト処理言語

```bash
# 基本形: 列抽出
awk '{print $1}' file.txt         # 第1列
awk '{print $1, $3}' file.txt     # 第1列と第3列

# 区切り文字指定
awk -F: '{print $1}' /etc/passwd  # ユーザー名一覧

# 条件付き処理
awk '$3 > 100 {print $1}' data.txt
awk '/ERROR/ {print $0}' log.txt
```

実用的なawkパターンは次のとおりです。
```bash
# 1. ログ集計（2.3 のサンプルログ形式を前提）
awk '{count[$3]++} END {for (ip in count) print ip, count[ip]}' access.log

# 2. 合計計算
awk '{sum += $2} END {print "Total:", sum}' numbers.txt

# 3. CSV処理
awk -F, '{print $2 ":" $3}' data.csv

# 4. ディスク使用率取得
df -h | awk 'NR==2 {print $5}'
```

### パイプライン - コマンド連結

パイプライン（|）は、複数のコマンドを連鎖させて強力なデータ処理を可能にします。

![パイプライン概念図]({{ site.baseurl }}/assets/images/pipeline-concept.svg)

```bash
# 基本形
command1 | command2 | command3

# 実用例
# 1. アクセスログのトップ10 IP
cat access.log | awk '{print $3}' | sort | uniq -c | sort -rn | head -10

# 2. プロセスメモリ使用量トップ5
ps aux | sort -k4 -rn | head -5

# 3. 大きいファイル検索
find /var -type f -size +100M -exec ls -lh {} + 2>/dev/null

# 4. 設定ファイルの有効行のみ表示
grep -v "^#" /etc/ssh/sshd_config | grep -v "^$"
```

上の図は、パイプライン処理がどのように動作するかを示しています。各コマンドの出力が次のコマンドの入力として渡され、データが段階的に処理されていく様子が理解できます。

## 2.3 実践演習: ログファイル解析

### サンプルログ生成

```bash
# 実践用ディレクトリ作成
mkdir ~/log_analysis
cd ~/log_analysis

# アクセスログ風データ生成
cat << 'SCRIPT' > generate_log.sh
#!/bin/bash
for i in {1..1000}; do
    ip=$((RANDOM % 256)).$((RANDOM % 256)).$((RANDOM % 256)).$((RANDOM % 256))
    status=(200 404 500 301)
    code=${status[$((RANDOM % 4))]}
    size=$((RANDOM % 10000))
    echo "$(date '+%Y-%m-%d %H:%M:%S') $ip GET /page$((RANDOM % 10)).html $code $size"
done
SCRIPT

chmod +x generate_log.sh
./generate_log.sh > access.log
```

ログ形式（スペース区切り）は次のとおりです（演習ではこの列番号を使います）。

- 1: 日付
- 2: 時刻
- 3: IP
- 4: メソッド
- 5: パス
- 6: ステータスコード
- 7: サイズ（バイト）

### 解析タスク1: ステータスコード集計

```bash
# ステータスコード別カウント
awk '{print $6}' access.log | sort | uniq -c | sort -rn

# 成功率計算
awk 'BEGIN { total=0; success=0 } { total++ } $6==200 { success++ } END { if (total>0) { printf "Success rate: %.2f%%\n", success*100/total } else { print "Success rate: 0.00%" } }' access.log
```

### 解析タスク2: エラー分析

```bash
# 500エラーの時刻と IP 抽出
grep " 500 " access.log | awk '{print $1, $2, $3}'

# エラー多発時間帯の特定
grep " 500 " access.log | awk '{print $2}' | cut -d: -f1 | sort | uniq -c | sort -rn
```

### 解析タスク3: トラフィック分析

```bash
# 転送量合計（バイト）
awk '{sum += $7} END {print "Total:", sum, "bytes"}' access.log

# IP 別アクセス数トップ10
awk '{print $3}' access.log | sort | uniq -c | sort -rn | head -10

# ページ別アクセス数
awk '{print $5}' access.log | sort | uniq -c | sort -rn
```

## 2.4 正規表現入門

### 基本メタ文字

```bash
# . : 任意の1文字
grep "s.t" file.txt  # sat, set, s1t等

# * : 直前の文字の0回以上
grep "ab*c" file.txt  # ac, abc, abbc等

# ^ : 行頭
grep "^Error" log.txt

# $ : 行末
grep "\.txt$" filelist.txt

# [] : 文字クラス
grep "[0-9]" file.txt      # 数字
grep "[a-zA-Z]" file.txt   # 英字
```

### 拡張正規表現（-E）

```bash
# + : 1回以上
grep -E "ab+c" file.txt    # abc, abbc（acは含まない）

# ? : 0回または1回
grep -E "colou?r" file.txt # color, colour

# | : OR
grep -E "(error|warning|fatal)" log.txt

# {} : 繰り返し回数
grep -E "[0-9]{3}-[0-9]{4}" phone.txt  # 123-4567形式
```

### 実用的な正規表現パターン

```bash
# メールアドレス
grep -E "[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}" contacts.txt

# URL
grep -E "https?://[a-zA-Z0-9./-]+" documents.txt

# 日付（YYYY-MM-DD）
grep -E "[0-9]{4}-[0-9]{2}-[0-9]{2}" log.txt

# 時刻（HH:MM:SS）
grep -E "([01][0-9]|2[0-3]):[0-5][0-9]:[0-5][0-9]" log.txt
```

## 2.5 ファイル内容の比較と変換

### diff - ファイル差分

```bash
# 基本比較
diff file1.txt file2.txt

# 並列表示
diff -y file1.txt file2.txt

# 統一形式（推奨）
diff -u file1.txt file2.txt

# ディレクトリ比較
diff -r dir1/ dir2/
```

### sort - ソート

```bash
# 基本ソート
sort file.txt

# 数値ソート
sort -n numbers.txt

# 逆順
sort -r file.txt

# 特定フィールドでソート
sort -k2 -n data.txt  # 第2フィールドで数値ソート

# 重複削除
sort -u file.txt
```

### uniq - 重複処理

```bash
# 重複行削除（要事前ソート）
sort file.txt | uniq

# 重複カウント
sort file.txt | uniq -c

# 重複行のみ表示
sort file.txt | uniq -d

# ユニーク行のみ表示
sort file.txt | uniq -u
```

### tr - 文字変換

```bash
# 大文字→小文字
echo "HELLO" | tr 'A-Z' 'a-z'

# 改行をスペースに
cat file.txt | tr '\n' ' '

# 特定文字削除
echo "hello123world" | tr -d '0-9'

# 連続スペースを1つに
echo "hello    world" | tr -s ' '
```

## 2.6 演習問題

### 演習1: ログ解析スクリプト作成

```bash
#!/bin/bash
# log_analyzer.sh - ログファイル解析ツール

LOG_FILE="${1:-}"

if [ -z "$LOG_FILE" ] || [ ! -f "$LOG_FILE" ]; then
    echo "Usage: $0 <logfile>"
    echo "  第2.3 のサンプル形式の access.log を想定"
    exit 1
fi

echo "=== Log Analysis Report ==="
echo "Total lines: $(wc -l < \"$LOG_FILE\")"
echo ""

echo "Status codes:"
awk '{print $6}' "$LOG_FILE" | sort | uniq -c | sort -rn
echo ""

echo "Top 5 IP addresses:"
awk '{print $3}' "$LOG_FILE" | sort | uniq -c | sort -rn | head -5
echo ""

echo "Top 5 paths:"
awk '{print $5}' "$LOG_FILE" | sort | uniq -c | sort -rn | head -5
```

### 演習2: 設定ファイルパーサー

```bash
# サンプル設定ファイル作成
cat << 'CONFIG' > app.conf
# Application Configuration
server_port=8080
database_host=localhost
database_port=5432
# Security settings
enable_ssl=true
max_connections=100
CONFIG

# 設定値抽出
grep -v "^#" app.conf | grep -v "^$" | while IFS='=' read -r key value; do
    [ -n "$key" ] || continue
    escaped_value=$(printf '%q' "$value")
    echo "export APP_${key^^}=${escaped_value}"
done > env.sh
```

### 演習3: CSVデータ処理

```bash
# CSVデータ生成
cat << 'CSV' > sales.csv
Date,Product,Quantity,Price
2025-01-01,Apple,100,150
2025-01-01,Banana,200,80
2025-01-02,Apple,150,150
2025-01-02,Orange,50,120
CSV

# 売上集計
awk -F, 'NR>1 {sales[$2] += $3 * $4} END {for (p in sales) print p":", sales[p]}' sales.csv
```

## 2.7 トラブルシューティング

### よくある問題

| 問題 | 原因 | 解決方法 |
|------|------|----------|
| `Binary file matches` | バイナリファイル検索 | `grep -a`オプション使用 |
| 文字化け | 文字コード不一致 | `iconv -f SJIS -t UTF-8` |
| 改行コード問題 | Windows/Linux 混在 | `dos2unix`使用 |
| 正規表現が動かない | 基本/拡張の違い | `grep -E`使用 |
| パイプが機能しない | バッファリング | `stdbuf -o0`使用 |

### デバッグテクニック

```bash
# コマンド実行過程の確認
set -x  # デバッグモード開始
grep "error" log.txt | awk '{print $1}'
set +x  # デバッグモード終了

# 中間結果の確認
cat log.txt | tee debug1.txt | grep "error" | tee debug2.txt | wc -l

# エラー出力の確認
command 2>&1 | less
```

## まとめ

テキスト処理の学習は、次の 3 段階が目安です。

1. **エディタ操作**: nano などを併用しつつ、vi/vim の基本（保存・終了）を把握する
2. **フィルタコマンド**: `grep`、`sed`、`awk` の順で学ぶ
3. **パイプライン**: 2 段程度から段階的に組み合わせる

次章では、これらの技術を活用してプロセスとサービス管理を扱います。

**次章へ**: [第3章 プロセスとサービス管理](../chapter3/)
