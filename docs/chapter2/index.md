---
title: "第2章: テキスト処理入門"
chapter: chapter2
layout: book
---

# 第2章: テキスト処理の基本

## 🎯 この章の目標
- テキストファイルを自由に編集できる
- viエディタの基本操作をマスター
- パイプとリダイレクトを使いこなす

## 🚀 できるようになること
- 設定ファイルを編集できる
- ログファイルを分析できる
- 複数のコマンドを組み合わせられる

## はじめに：なぜテキスト処理が重要なのか

Linuxの世界では、ほとんどの設定やログが「テキストファイル」です。
- 設定を変更する = テキストファイルを編集する
- エラーを調べる = ログファイル（テキスト）を読む
- データを分析する = テキストデータを加工する

この章では、テキストを自在に扱えるようになります。

## 2.1 テキストエディタの選択と基本操作

### どのエディタを使うべきか？

Linuxで最も一般的なエディタは**vi**（vim）です。どのLinuxシステムにも必ず入っているため、基本操作を身につけておくと便利です。

### エディタ選択の指針

| エディタ | 学習時間 | 使うべき場面 | 難易度 |
|---------|---------|------------|--------|
| vi/vim | 30分（基本） | サーバー上での作業 | ⭐⭐⭐ |
| VSCode | 30分 | WSL2での開発 | ⭐⭐ |

💡 **アドバイス**: viは最初難しく感じますが、基本操作だけならすぐに身につきます。

### vi/vim - Linux標準エディタ

```bash
# viの起動
vi test.txt

# 基本の3つのモード
# 1. ノーマルモード（起動時） - コマンド入力
# 2. 挿入モード - 文字入力
# 3. コマンドモード - 保存や終了
```

実践例：設定ファイル編集
```bash
# システム設定のバックアップと編集
sudo cp /etc/hosts /etc/hosts.bak
sudo nano /etc/hosts

# 追加行の例
127.0.0.1    myapp.local
# Ctrl+O → Enter → Ctrl+X で保存終了
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

最小限の操作：
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

vim生存必須コマンド10個：
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

実践的なgrepパターン：
```bash
# 1. エラーログ抽出
grep -E "(ERROR|FATAL)" application.log

# 2. IPアドレス検索
grep -E "\b([0-9]{1,3}\.){3}[0-9]{1,3}\b" access.log

# 3. 空行除外
grep -v "^$" config.txt

# 4. コメント行除外
grep -v "^#" /etc/ssh/sshd_config

# 5. プロセス検索の定番
ps aux | grep nginx | grep -v grep
```

### sed - ストリーム編集

```bash
# 基本形: 置換
sed 's/old/new/' file.txt        # 各行の最初のみ
sed 's/old/new/g' file.txt       # 全置換

# ファイル直接編集
sed -i 's/localhost/127.0.0.1/g' config.txt

# 行削除
sed '/^#/d' config.txt            # コメント行削除
sed '/^$/d' file.txt              # 空行削除

# 行追加
sed '1i\#!/bin/bash' script.sh    # 先頭に追加
sed '$a\exit 0' script.sh         # 末尾に追加
```

実用例：
```bash
# 設定ファイルの値変更
sed -i 's/port=8080/port=3000/g' app.conf

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

実用的なawkパターン：
```bash
# 1. ログ集計
awk '{count[$1]++} END {for (ip in count) print ip, count[ip]}' access.log

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
cat access.log | awk '{print $1}' | sort | uniq -c | sort -rn | head -10

# 2. プロセスメモリ使用量トップ5
ps aux | sort -k4 -rn | head -5

# 3. 大きいファイル検索
find /var -type f -size +100M 2>/dev/null | xargs ls -lh

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

### 解析タスク1: ステータスコード集計

```bash
# ステータスコード別カウント
awk '{print $5}' access.log | sort | uniq -c | sort -rn

# 成功率計算
total=$(wc -l < access.log)
success=$(grep " 200 " access.log | wc -l)
echo "Success rate: $(echo "scale=2; $success * 100 / $total" | bc)%"
```

### 解析タスク2: エラー分析

```bash
# 500エラーの時刻とIP抽出
grep " 500 " access.log | awk '{print $1, $2, $3}'

# エラー多発時間帯の特定
grep " 500 " access.log | awk '{print $2}' | cut -d: -f1 | sort | uniq -c | sort -rn
```

### 解析タスク3: トラフィック分析

```bash
# 転送量合計（バイト）
awk '{sum += $6} END {print "Total:", sum, "bytes"}' access.log

# IP別アクセス数トップ10
awk '{print $3}' access.log | sort | uniq -c | sort -rn | head -10

# ページ別アクセス数
awk '{print $4}' access.log | sort | uniq -c | sort -rn
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
grep -E "[0-2][0-9]:[0-5][0-9]:[0-5][0-9]" log.txt
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

LOG_FILE="$1"

if [ ! -f "$LOG_FILE" ]; then
    echo "Usage: $0 <logfile>"
    exit 1
fi

echo "=== Log Analysis Report ==="
echo "Total lines: $(wc -l < $LOG_FILE)"
echo ""

echo "Error summary:"
grep -i "error" $LOG_FILE | head -5

echo ""
echo "Top 5 IP addresses:"
awk '{print $1}' $LOG_FILE | sort | uniq -c | sort -rn | head -5
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
grep -v "^#" app.conf | grep -v "^$" | while IFS='=' read key value; do
    echo "export APP_${key^^}=$value"
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
| 改行コード問題 | Windows/Linux混在 | `dos2unix`使用 |
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

テキスト処理は以下の3段階で習得します：

1. **エディタ操作**: nanoから始めて徐々にvimへ
2. **フィルタコマンド**: grep → sed → awkの順で学習
3. **パイプライン**: 単純な2段階から複雑な処理へ

次章では、これらの技術を活用してプロセスとサービス管理を学習します。