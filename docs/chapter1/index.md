---
title: "第1章: Linuxの世界への第一歩"
chapter: chapter1
layout: book
---

# 第1章: Linuxの世界への第一歩

## 前提（検証環境）
- WSL2 上の Ubuntu（例: 22.04/24.04）
- 本章のコマンドは Ubuntu 側のターミナルで実行する
- Windows 側のファイルは `/mnt/c` などにマウントされる（性能特性の差に留意）

## この章の目標
- Linux の基本概念を把握する
- 基本コマンド 10 個の用途を説明できる
- ファイルとディレクトリを操作できる

## できるようになること
- ターミナルで基本的なファイル操作ができる
- コマンドラインで作業を進められる
- Linux のディレクトリ階層の概要を説明できる

## 1.1 Linux ファイルシステムの構造理解

### なぜファイルシステムを理解する必要があるのか？

Windows では、エクスプローラーを使って視覚的にファイルを操作します。
Linux では主にコマンドでファイルを操作するため、「現在地（作業ディレクトリ）」と「配置」を把握することが重要です。

### Linux のディレクトリ階層の考え方

Linux は Windows と異なる設計思想を持ちます。本書では差分を整理しながら説明します。

![Linuxファイルシステム構造図]({{ site.baseurl }}/assets/images/linux-filesystem-tree.svg)

例えとして、次のように捉えると理解しやすくなります。
- Windows は「複数の建物（C:、D: ドライブ）」がある
- Linux は「1 つの大きな建物（/）」の中にすべての部屋がある

上の図は、Linux ファイルシステムの階層構造の概要を示しています。ルートディレクトリ（/）を起点として、役割ごとにディレクトリが配置されます。

```bash
# 現在位置の確認
pwd
# 出力例: /home/username

# ルートディレクトリへ移動
cd /

# 主要ディレクトリの確認
ls -la
```

主要ディレクトリの役割は次のとおりです。
- `/home`: ユーザーのホームディレクトリ
- `/etc`: システム設定ファイル
- `/var`: 可変データ（ログ、キャッシュ）
- `/usr`: ユーザープログラム
- `/tmp`: 一時ファイル（再起動で削除）

### WSL2 環境での特性

WSL2 では、Windows ファイルシステムが `/mnt` 以下にマウントされます。

```bash
# Windowsのドライブ確認
ls /mnt/
# 出力: c  d  （ドライブに応じて）

# WindowsのCドライブアクセス
cd /mnt/c/Users/
ls
```

## 1.2 必須コマンド10個の習得

### 学習の進め方（目安）
- **基礎**: `ls`（一覧）、`cd`（移動）、`pwd`（現在地）
- **次に**: `mkdir`（作成）、`cp`（コピー）、`rm`（削除）
- **必要に応じて**: その他のコマンド

### 1. pwd - 現在のディレクトリ確認（Print Working Directory）

```bash
pwd
# 実行結果例：
# /home/username

# これは「現在、/home/username にいる」という意味
```

**利用場面**
- 作業ディレクトリを見失った場合
- スクリプトで現在位置を確認する場合

### 2. ls - ファイル・ディレクトリ一覧（List）

```bash
# 基本形（シンプル表示）
ls
# 実行結果例：
# Desktop  Documents  Downloads  Pictures

# 詳細表示（頻用）
ls -la
# 実行結果例：
# total 32
# drwxr-xr-x 5 user user 4096 Jan 15 10:30 .
# drwxr-xr-x 3 root root 4096 Jan 10 09:00 ..
# drwxr-xr-x 2 user user 4096 Jan 15 10:00 Desktop
# -rw-r--r-- 1 user user  220 Jan 10 09:00 .bashrc

# 人間が読みやすいサイズ表示
ls -lh
# 実行結果例：
# -rw-r--r-- 1 user user 1.5K Jan 15 10:25 file.txt
#                        ↑ キロバイト表示（例: 1.5K）
```

#### ls の出力の読み方（要点）
```text
drwxr-xr-x 2 user group 4096 Jan 15 10:30 directory
│└─┴─┴─┘  │  │    │     │    │             │
│権限     │  │    │     │    │             └─名前
│         │  │    │     │    └─更新日時
│         │  │    │     └─サイズ（バイト）
│         │  │    └─グループ（チーム名）
│         │  └─所有者（持ち主）
│         └─リンク数（通常は参照程度）
└─種類（d:フォルダ、-:ファイル）
```

### 3. cd - ディレクトリ移動

```bash
# ホームディレクトリへ
cd
# または
cd ~

# 親ディレクトリへ
cd ..

# 絶対パス指定
cd /var/log

# 相対パス指定
cd ./subdirectory

# 直前のディレクトリへ戻る
cd -
```

### 4. mkdir - ディレクトリ作成

```bash
# 単一ディレクトリ作成
mkdir testdir

# 親ディレクトリも含めて作成
mkdir -p project/src/main

# 複数同時作成
mkdir dir1 dir2 dir3

# 権限指定
mkdir -m 755 public
```

### 5. touch - ファイル作成・タイムスタンプ更新

```bash
# 新規ファイル作成
touch newfile.txt

# 複数ファイル作成
touch file1.txt file2.txt file3.txt

# タイムスタンプ更新（既存ファイル）
touch existing.txt
```

### 6. cp - コピー

```bash
# ファイルコピー
cp source.txt destination.txt

# ディレクトリ再帰コピー
cp -r sourcedir/ destdir/

# 上書き前に確認
cp -i source.txt destination.txt

# 属性保持コピー
cp -p source.txt destination.txt
```

### 7. mv - 移動・名前変更

```bash
# ファイル名変更
mv oldname.txt newname.txt

# ディレクトリ移動
mkdir -p ~/documents
mv file.txt ~/documents/

# 複数ファイル移動
mkdir -p ~/logs/archive
mv *.log ~/logs/archive/

# 上書き前に確認
mv -i source.txt destination.txt
```

### 8. rm - 削除

```bash
# ファイル削除
rm file.txt

# 確認付き削除（推奨）
rm -i file.txt

# ディレクトリ削除
rm -r directory/

# 強制削除（注意）
rm -rf directory/

# 安全な使用例（$HOME 配下に限定し、対象を確認してから実行）
rm -rf -- "$HOME/tmp"/*
# 危険な例（実行禁止）
# rm -rf /  # システム全体削除
```

### 9. cat - ファイル内容表示

```bash
# ファイル表示
cat file.txt

# 複数ファイル連結
cat file1.txt file2.txt > combined.txt

# 行番号付き表示
cat -n file.txt

# 改行・タブを可視化
cat -A file.txt
```

### 10. less - ページング表示

```bash
# ファイルをページング表示
less largefile.log

# 操作方法：
# Space: 次ページ
# b: 前ページ
# /word: 検索
# n: 次の検索結果
# G: 最終行へ
# g: 先頭行へ
# q: 終了

# パイプラインでの使用
ls -la /etc | less
```

## 1.3 パーミッション（権限）の理解と操作

### 権限の基本構造

![パーミッション説明図]({{ site.baseurl }}/assets/images/permissions-explained.svg)

```bash
# 権限確認
ls -l script.sh
# 出力: -rwxr-xr-- 1 user group 245 Jan 15 10:30 script.sh

# 権限の意味
# rwx r-x r--
# │││ │││ │││
# │││ │││ └┴┴─ その他（other）: 読み取りのみ
# │││ └┴┴─ グループ（group）: 読み取り・実行
# └┴┴─ 所有者（user）: 読み取り・書き込み・実行
```

上の図は、Linuxのファイルパーミッション（権限）システムを分かりやすく説明しています。所有者、グループ、その他のユーザーごとに、読み取り（r）、書き込み（w）、実行（x）の権限がどのように設定されるかを視覚的に理解できます。

### chmod - 権限変更

```bash
# 数値指定（推奨）
chmod 755 script.sh  # rwxr-xr-x
chmod 644 data.txt   # rw-r--r--
chmod 600 secret.key # rw-------

# 記号指定
chmod +x script.sh   # 実行権限追加
chmod -w file.txt    # 書き込み権限削除
chmod u+x,g+r file   # 所有者に実行、グループに読み取り追加
```

権限の数値表現は次のとおりです。
- 4: 読み取り（r）
- 2: 書き込み（w）
- 1: 実行（x）
- 合計値: 7=rwx、6=rw-、5=r-x、4=r--

### 実践演習: スクリプト作成と実行

```bash
# 1. スクリプト作成
echo '#!/bin/bash' > hello.sh
echo 'echo "Hello, Linux!"' >> hello.sh
echo 'date' >> hello.sh

# 2. 権限確認
ls -l hello.sh
# 出力: -rw-r--r-- （実行権限なし）

# 3. 実行試行（失敗）
./hello.sh
# エラー: Permission denied

# 4. 実行権限付与
chmod +x hello.sh
# または
chmod 755 hello.sh

# 5. 実行（成功）
./hello.sh
# 出力: Hello, Linux!
#      Tue Jan 15 10:30:45 JST 2025
```

## 1.4 WSL2特有のファイル操作

### Windows-Linux間のファイル共有

注意: Windows のユーザー名（`C:\Users\...`）と Ubuntu のユーザー名（`whoami`）は一致しない場合があります。`<WindowsUser>` は実環境に合わせて読み替えてください。

```bash
# LinuxからWindowsファイルへアクセス
# Windows側ユーザー名の確認
ls /mnt/c/Users

# 例: デスクトップのファイルをコピー
cp "/mnt/c/Users/<WindowsUser>/Desktop/document.txt" ~/

# WindowsからLinuxファイルへアクセス
# エクスプローラーで開く
explorer.exe .

# WSL2のネットワークパス（例。ディストリビューション名は環境により異なる）
# \\wsl$\<DistroName>\home\<linuxuser>
```

### パフォーマンス考慮事項

```bash
# 高速: Linux側ファイルシステム
time find ~ -name "*.txt" | head -100

# 低速: Windows側ファイルシステム
time find /mnt/c -name "*.txt" | head -100

# 推奨: 作業ファイルはLinux側に配置
cp -r /mnt/c/project ~/
cd ~/project
# 作業実施
```

### 改行コード問題の対処

```bash
# Windows改行（CRLF）確認
cat -A windows_file.txt
# 出力: line1^M$

# Linux改行（LF）へ変換
# dos2unix がない場合: sudo apt install -y dos2unix
dos2unix windows_file.txt
# またはsedで変換
sed -i 's/\r$//' windows_file.txt

# 確認
cat -A windows_file.txt
# 出力: line1$
```

## 1.5 演習問題

### 演習1: ディレクトリ構造作成

以下の構造を作成してください。
```text
~/project/
├── src/
│   ├── main/
│   └── test/
├── docs/
├── config/
└── README.md
```

解答例は次のとおりです。
```bash
mkdir -p ~/project/{src/{main,test},docs,config}
touch ~/project/README.md
tree ~/project  # treeコマンドで確認（未導入の場合: sudo apt install -y tree）
```

### 演習2: ファイル操作練習

```bash
# 1. testディレクトリ作成
mkdir ~/file_practice
cd ~/file_practice

# 2. 10個のファイル作成
for i in {1..10}; do touch file$i.txt; done

# 3. 偶数番号ファイルをevenディレクトリへ移動
mkdir even
mv file{2,4,6,8,10}.txt even/

# 4. 奇数番号ファイルをアーカイブ
tar -czf odd_files.tar.gz file*.txt

# 5. クリーンアップ
rm file*.txt
```

### 演習3: 権限管理

```bash
# セキュアなディレクトリ作成
mkdir ~/secure
chmod 700 ~/secure

# 共有ディレクトリ作成
mkdir ~/shared
chmod 755 ~/shared

# 実行可能スクリプト作成
cat << 'EOF' > ~/backup.sh
#!/bin/bash
mkdir -p "$HOME/documents"
tar -czf "backup_$(date +%Y%m%d).tar.gz" "$HOME/documents"
EOF
chmod 750 ~/backup.sh
```

## 1.6 トラブルシューティング

### よくある問題と対処

| 症状 | 原因 | 対処法 |
|-----|------|--------|
| `ls: cannot access` | ディレクトリが存在しない | パスを確認、`pwd`で現在位置確認 |
| `Permission denied` | 権限不足 | `ls -l`で権限確認、必要に応じて`sudo`使用 |
| `No such file or directory` | ファイルパス誤り | タブ補完使用、大文字小文字確認 |
| `Directory not empty` | 空でないディレクトリ削除 | `rm -r`使用 |
| `/mnt/c`が遅い | ファイルシステム越境 | Linux側へファイルコピー |

### デバッグのコツ

```bash
# コマンド実行前の確認
ls target_file.txt  # ファイル存在確認
pwd                 # 現在位置確認

# エラー時の情報収集
echo $?            # 直前のコマンドの終了コード（0=成功）
type command_name  # コマンドの場所確認
which command_name # 実行ファイルパス確認
```

## まとめ

本章で扱った 10 個のコマンドは、Linux の基本操作で頻出です。特に重要な観点は次の 3 点です。

1. **階層構造の把握**: `pwd` と `cd` で現在地を把握する
2. **権限の確認**: `ls -la` で権限を確認する
3. **安全な削除**: `rm -rf` は最終手段とし、対象を確認して実行する

次章では、これらのコマンドを組み合わせたテキスト処理を扱います。

**次章へ**: [第2章 テキスト処理の基本](../chapter2/)
