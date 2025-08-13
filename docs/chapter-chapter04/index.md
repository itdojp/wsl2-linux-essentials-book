---
title: "第4章 Linux基本コマンド"
chapter: chapter04
layout: default
---

# 第4章 Linux基本コマンド

## はじめに：この章で学ぶこと

この章では、Linuxでファイルやフォルダを扱う基本的な操作を学びます。
Windowsでマウスを使って行っていた操作を、コマンドで行えるようになります。

### 📝 学習の前に知っておくべきこと
- **コマンド** = 命令文のこと（例：「ファイルを表示して」）
- **ターミナル** = コマンドを入力する黒い画面
- **大文字と小文字は区別される**（File.txt と file.txt は別物）

## Linuxファイルシステムの構造理解

### なぜファイルシステムを理解する必要があるのか？

Windowsでは、エクスプローラーを使って視覚的にファイルを操作します。
Linuxでは、主にコマンドでファイルを操作するため、「今どこにいるか」「どこに何があるか」を理解することが重要です。

### ディレクトリ階層の基本概念

Linuxのファイルシステムは単一のルート（/）から始まる階層構造です。これは木を逆さまにしたような構造です。

![ファイルシステム構造](/wsl2-linux-essentials-book/assets/images/linux-filesystem-tree.svg)

💡 **簡単な例え話**：
- Windowsは「複数の建物（C:、D:ドライブ）」がある
- Linuxは「1つの大きな建物（/）」の中に全部屋がある

```bash
# 現在位置の確認
pwd
# 出力例: /home/username

# ルートディレクトリへ移動
cd /

# 主要ディレクトリの確認
ls -la
```

主要ディレクトリの役割：
- `/home`: ユーザーのホームディレクトリ
- `/etc`: システム設定ファイル
- `/var`: 可変データ（ログ、キャッシュ）
- `/usr`: ユーザープログラム
- `/tmp`: 一時ファイル（再起動で削除）

### WSL2環境での特殊性

WSL2では、Windowsファイルシステムが`/mnt`以下にマウントされます。

```bash
# Windowsのドライブ確認
ls /mnt/
# 出力: c  d  （ドライブに応じて）

# WindowsのCドライブアクセス
cd /mnt/c/Users/
ls
```

## 必須コマンド10個の習得

### 覚え方のコツ
- **最初は3個だけ**: `ls`（見る）、`cd`（移動）、`pwd`（現在地）
- **慣れたら追加**: `mkdir`（作る）、`cp`（コピー）、`rm`（削除）
- **必要に応じて**: 残りのコマンド

### 1. pwd - 現在のディレクトリ確認（Print Working Directory）

```bash
pwd
# 実行結果例：
# /home/username

# これは「今、home フォルダの中の username フォルダにいます」という意味
```

💡 **いつ使う？**
- 迷子になった時
- スクリプトで現在位置を確認する時

### 2. ls - ファイル・ディレクトリ一覧（List）

```bash
# 基本形（シンプル表示）
ls
# 実行結果例：
# Desktop  Documents  Downloads  Pictures

# 詳細表示（よく使う！）
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
#                        ↑ キロバイト表示（1024より1.5Kの方が分かりやすい）
```

#### ls の出力の読み方（重要！）
```
drwxr-xr-x 2 user group 4096 Jan 15 10:30 directory
│└─┴─┴─┘  │  │    │     │    │             │
│権限     │  │    │     │    │             └─名前
│         │  │    │     │    └─更新日時
│         │  │    │     └─サイズ（バイト）
│         │  │    └─グループ（チーム名）
│         │  └─所有者（持ち主）
│         └─リンク数（気にしなくてOK）
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
mv file.txt /home/user/documents/

# 複数ファイル移動
mv *.log /var/log/archive/

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

# 安全な使用例
rm -rf /home/$(whoami)/tmp/*
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

## パーミッション（権限）の理解と操作

![権限の説明](/wsl2-linux-essentials-book/assets/images/permissions-explained.svg)

### 権限の基本構造

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

権限の数値表現：
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

## WSL2特有のファイル操作

### Windows-Linux間のファイル共有

```bash
# LinuxからWindowsファイルへアクセス
# デスクトップのファイルをコピー
cp /mnt/c/Users/$(whoami)/Desktop/document.txt ~/

# WindowsからLinuxファイルへアクセス
# エクスプローラーで開く
explorer.exe .

# WSL2のネットワークパス
# \\wsl$\Ubuntu-24.04\home\username
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
dos2unix windows_file.txt
# またはsedで変換
sed -i 's/\r$//' windows_file.txt

# 確認
cat -A windows_file.txt
# 出力: line1$
```

## 演習問題

### 演習1: ディレクトリ構造作成

以下の構造を作成してください：
```
~/project/
├── src/
│   ├── main/
│   └── test/
├── docs/
├── config/
└── README.md
```

解答例：
```bash
mkdir -p ~/project/{src/{main,test},docs,config}
touch ~/project/README.md
tree ~/project  # treeコマンドで確認（要インストール: sudo apt install tree）
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
tar -czf backup_$(date +%Y%m%d).tar.gz ~/documents
EOF
chmod 750 ~/backup.sh
```

## トラブルシューティング

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

本章で習得した10個のコマンドは、Linux操作の90%以上をカバーします。特に重要なのは：

1. **階層構造の理解**: pwdとcdで位置を常に把握
2. **権限の意識**: ls -laで確認を習慣化
3. **安全な削除**: rm -rfは最後の手段

次の章では、開発環境の構築について学習します。

---