---
title: "第0章: WSL2環境構築と基礎"
chapter: chapter0
layout: book
---

# 第0章: WSL2環境構築と基礎

## 0.1 WSL2とは

### はじめに：なぜWSL2を使うのか

あなたがこれからLinuxを学ぼうとしているなら、WSL2は最適な選択です。従来、Linuxを学ぶには：
- 別のPCを用意する
- WindowsとLinuxを切り替えて使う（デュアルブート）
- 重い仮想マシンソフトを使う

これらの方法は初心者には難しく、挫折の原因になっていました。WSL2はこれらの問題をすべて解決します。

### WSL2の概要

WSL2（Windows Subsystem for Linux 2）は、Windows上で本格的なLinux環境を実行する仕組みです。簡単に言えば、**WindowsとLinuxを同時に使える**技術です。

![WSL2アーキテクチャ図]({{ site.baseurl }}/assets/images/wsl2-architecture-diagram.svg)

### WSL2のメリット（従来の方法との比較）

#### 💡 分かりやすい例え話
WSL2は、WindowsというあなたのPCの中に、小さなLinux専用の部屋を作るようなものです。
- いつものWindowsを使いながら、必要な時だけLinuxの部屋に入れる
- ファイルは両方の部屋で共有できる
- 部屋の切り替えは一瞬（2-3秒）

| 特徴 | 説明 | 例えば... |
|------|------|----------|
| **高速起動** | 2-3秒でLinux環境が起動 | メモ帳を開くくらいの速さ |
| **低メモリ使用** | 必要に応じて動的にメモリ割り当て | 使わない時は0MB、使う時だけメモリ消費 |
| **ファイル共有** | WindowsとLinux間でファイル共有可能 | デスクトップのファイルをLinuxで編集できる |
| **開発環境統合** | VSCodeなど開発ツールとの連携 | いつものエディタでLinuxファイルを編集 |
| **本物のLinuxカーネル** | 完全なシステムコール互換性 | サーバーと同じ環境で練習できる |

### WSL1とWSL2の違い

| 項目 | WSL1 | WSL2 |
|------|------|------|
| アーキテクチャ | 変換レイヤー | 軽量VM |
| 起動速度 | 高速 | 高速 |
| メモリ使用 | 少ない | 動的割り当て |
| ファイルI/O（Linux） | 遅い | 高速 |
| ファイルI/O（Windows） | 高速 | やや遅い |
| システムコール互換性 | 部分的 | 完全 |

## 0.2 システム要件確認

### 最小要件

```powershell
# Windows PowerShellで実行

# Windowsバージョン確認
winver
# 必要: Windows 10 Version 2004 (Build 19041) 以降
#      または Windows 11

# システム情報確認
systeminfo

# 必要項目の確認:
# - OS バージョン: 10.0.19041 以上
# - システムの種類: x64-based PC
# - プロセッサ: 64ビット対応
# - RAM: 4GB以上（8GB推奨）
```

### 仮想化機能の確認

```powershell
# 管理者権限でPowerShellを開く
# スタートメニュー → PowerShell → 右クリック → 管理者として実行

# 仮想化サポート確認
systeminfo | Select-String "仮想化"
# "ファームウェアで仮想化が有効になっています" が表示されればOK

# CPUの仮想化機能確認（Intel VT-x / AMD-V）
Get-ComputerInfo | Select-Object "HyperV*"
```

### BIOS/UEFI設定（必要な場合）

仮想化が無効の場合、BIOS/UEFIで有効化が必要です：

1. PCを再起動
2. 起動時にF2, F10, DEL等を押してBIOS/UEFI画面へ
3. 以下の項目を探して有効化：
   - Intel: "Intel Virtualization Technology" または "Intel VT-x"
   - AMD: "AMD-V" または "SVM Mode"
4. 設定を保存して再起動

メーカー別BIOSアクセスキー：
- Dell: F2
- HP: F10
- Lenovo: F1 または F2
- ASUS: F2 または DEL
- MSI: DEL

## 0.3 WSL2のインストール

### 方法1: 簡易インストール（推奨）

```powershell
# 管理者権限PowerShellで実行

# WSL2と既定のUbuntuを一括インストール
wsl --install

# インストール内容:
# - WSL2基本コンポーネント
# - 仮想マシンプラットフォーム
# - Linuxカーネル
# - Ubuntu（最新LTS版）

# 再起動が必要
Restart-Computer
```

### 方法2: 手動インストール（詳細制御）

```powershell
# 1. WSL機能有効化
dism.exe /online /enable-feature /featurename:Microsoft-Windows-Subsystem-Linux /all /norestart

# 2. 仮想マシンプラットフォーム有効化
dism.exe /online /enable-feature /featurename:VirtualMachinePlatform /all /norestart

# 3. 再起動
Restart-Computer

# 4. WSL2を既定バージョンに設定
wsl --set-default-version 2

# 5. Linuxカーネル更新（必要な場合）
# https://aka.ms/wsl2kernel からダウンロードしてインストール

# 6. Ubuntuインストール
wsl --install -d Ubuntu-24.04
```

### ディストリビューション選択

```powershell
# 利用可能なディストリビューション一覧
wsl --list --online

# 主なディストリビューション:
# - Ubuntu-24.04       # 推奨：最新LTS、豊富なドキュメント
# - Ubuntu-22.04       # 安定版LTS
# - Debian            # 軽量、安定重視
# - openSUSE-Leap     # 企業向け
# - Kali-Linux        # セキュリティツール
# - AlmaLinux         # RHEL互換

# 特定ディストリビューションのインストール
wsl --install -d Ubuntu-24.04
```

## 0.4 初期設定

### Ubuntuの初回起動設定

```bash
# 初回起動時の設定
# 1. ユーザー名入力（小文字のみ、Windowsユーザー名と異なってもOK）
Enter new UNIX username: myuser

# 2. パスワード設定（入力時は表示されない）
New password: 
Retype new password:

# 3. 設定完了メッセージ
Installation successful!
```

### システム更新

```bash
# パッケージリスト更新
sudo apt update

# パッケージアップグレード
sudo apt upgrade -y

# 不要パッケージ削除
sudo apt autoremove -y

# 日本語パッケージインストール（オプション）
sudo apt install language-pack-ja -y
```

### 基本ツールインストール

```bash
# 必須ツールセット
sudo apt install -y \
    curl \
    wget \
    git \
    vim \
    nano \
    htop \
    build-essential \
    software-properties-common \
    apt-transport-https \
    ca-certificates \
    gnupg \
    lsb-release

# 開発ツール（オプション）
sudo apt install -y \
    python3 \
    python3-pip \
    nodejs \
    npm
```

## 0.5 Windows Terminalの設定

### Windows Terminalインストール

```powershell
# Microsoft Storeから（推奨）
# 1. Microsoft Store を開く
# 2. "Windows Terminal" を検索
# 3. インストール

# またはwingetコマンド
winget install Microsoft.WindowsTerminal

# またはChocolatey
choco install microsoft-windows-terminal
```

### 基本設定

Windows Terminalの設定（Ctrl+,）：

```json
{
    "defaultProfile": "{Ubuntu-24.04のGUID}",
    "profiles": {
        "defaults": {
            "fontSize": 11,
            "fontFace": "Cascadia Code",
            "colorScheme": "One Half Dark",
            "cursorShape": "bar",
            "padding": "8, 8, 8, 8"
        },
        "list": [
            {
                "guid": "{Ubuntu-24.04のGUID}",
                "name": "Ubuntu 24.04",
                "startingDirectory": "//wsl$/Ubuntu-24.04/home/username"
            }
        ]
    }
}
```

### 推奨フォントインストール

プログラミング向けフォント：
- **Cascadia Code**: Microsoftの開発用フォント
- **FiraCode**: リガチャ対応
- **JetBrains Mono**: JetBrains社製

```powershell
# Cascadia Codeインストール（PowerShell）
winget install Microsoft.CascadiaCode
```

## 0.6 ファイルシステムアクセス

### Linux→Windows

```bash
# WindowsのCドライブアクセス
cd /mnt/c

# ユーザーフォルダへのショートカット作成
ln -s /mnt/c/Users/$(cmd.exe /c "echo %USERNAME%" 2>/dev/null | tr -d '\r') ~/windows

# デスクトップへの直接アクセス
cd /mnt/c/Users/$(whoami)/Desktop
```

### Windows→Linux

```powershell
# エクスプローラーでWSL2ファイルアクセス
# アドレスバーに入力
\\wsl$\Ubuntu-24.04

# PowerShellから
cd \\wsl$\Ubuntu-24.04\home\username

# WSL2内から現在のディレクトリをエクスプローラーで開く
explorer.exe .
```

### パフォーマンス最適化

```bash
# 作業ファイルの配置推奨場所
# 高速: Linux側（/home/user/projects/）
# 低速: Windows側（/mnt/c/）

# パフォーマンステスト
time find ~ -name "*.txt" | wc -l      # Linux側: 高速
time find /mnt/c -name "*.txt" | wc -l # Windows側: 低速

# 推奨ワークフロー
# 1. 開発ファイルはLinux側に配置
# 2. 必要時のみWindows側にコピー
cp -r ~/project /mnt/c/Users/$(whoami)/Desktop/
```

## 0.7 VSCode統合

### Remote-WSL拡張機能

```bash
# WSL2内からVSCode起動
code .

# 初回実行時は自動的に:
# 1. Windows側のVSCodeが起動
# 2. Remote-WSL拡張機能のインストール提案
# 3. WSL2環境に接続

# ファイル指定で開く
code ~/.bashrc
```

### 推奨拡張機能

VSCode拡張機能（WSL2環境用）：
- **Remote - WSL**: WSL統合（必須）
- **Docker**: Dockerサポート
- **GitLens**: Git可視化
- **Python**: Python開発
- **ESLint**: JavaScript検証
- **Prettier**: コード整形

## 0.8 メモリとCPU設定

### WSL2リソース設定

```powershell
# Windows側で %USERPROFILE%\.wslconfig 作成
notepad $env:USERPROFILE\.wslconfig
```

`.wslconfig`の内容：
```ini
[wsl2]
# メモリ制限（システムメモリの50%または8GBの小さい方が既定）
memory=4GB

# CPU数（全コア数が既定）
processors=2

# スワップサイズ
swap=2GB

# スワップファイルの場所
swapFile=%USERPROFILE%\AppData\Local\Temp\swap.vhdx

# VHDサイズ（既定256GB）
localhostForwarding=true

# カーネルコマンドライン引数
# kernelCommandLine=

# ネットワーク設定
# dhcp=true
```

設定反映：
```powershell
# WSL2再起動
wsl --shutdown
wsl
```

## 0.9 トラブルシューティング

### よくある問題と解決方法

#### 1. WSL2が起動しない

```powershell
# エラー: "The Windows Subsystem for Linux optional component is not enabled"
# 解決: WSL機能を有効化
dism.exe /online /enable-feature /featurename:Microsoft-Windows-Subsystem-Linux /all

# エラー: "Please enable the Virtual Machine Platform Windows feature"
# 解決: 仮想マシンプラットフォーム有効化
dism.exe /online /enable-feature /featurename:VirtualMachinePlatform /all
```

#### 2. 仮想化エラー

```powershell
# エラー: "Virtualization is not enabled in BIOS"
# 解決: BIOSで仮想化を有効化（0.2節参照）

# Hyper-V無効化が必要な場合（VMware等との競合）
bcdedit /set hypervisorlaunchtype off  # 無効化
bcdedit /set hypervisorlaunchtype auto # 有効化
```

#### 3. ネットワーク問題

```bash
# DNS解決できない場合
# /etc/resolv.confを手動設定
echo "nameserver 8.8.8.8" | sudo tee /etc/resolv.conf

# ネットワークリセット
wsl --shutdown
netsh winsock reset
netsh int ip reset
```

#### 4. ディスク容量問題

```powershell
# VHDファイルの圧縮
# 1. WSL2停止
wsl --shutdown

# 2. diskpartで圧縮
diskpart
select vdisk file="C:\Users\%USERNAME%\AppData\Local\Packages\...\ext4.vhdx"
attach vdisk readonly
compact vdisk
detach vdisk
exit
```

#### 5. 文字化け問題

```bash
# ロケール設定
sudo locale-gen ja_JP.UTF-8
echo 'export LANG=ja_JP.UTF-8' >> ~/.bashrc
source ~/.bashrc
```

### WSL2コマンドリファレンス

```powershell
# 基本操作
wsl --list --verbose          # インストール済み一覧
wsl --set-default Ubuntu-24.04 # 既定ディストリビューション設定
wsl --shutdown                # 全WSL2インスタンス停止
wsl --terminate Ubuntu-24.04  # 特定インスタンス停止

# バックアップ・リストア
wsl --export Ubuntu-24.04 backup.tar     # エクスポート
wsl --import NewUbuntu C:\WSL backup.tar # インポート

# アンインストール
wsl --unregister Ubuntu-24.04  # ディストリビューション削除

# バージョン変換
wsl --set-version Ubuntu-24.04 2  # WSL2へ変換
wsl --set-version Ubuntu-24.04 1  # WSL1へ変換

# 状態確認
wsl --status                   # WSL状態
wsl --version                  # バージョン情報
```

## 0.10 初心者チェックリスト

### コマンドライン基本操作（超重要！）

Linuxを使う前に、これだけは覚えておきましょう：

#### キーボード操作の基本
| 操作 | 効果 | いつ使う？ |
|------|------|----------|
| **Tab キー** | 自動補完 | ファイル名を途中まで打ったら Tab！ |
| **↑ キー** | 前のコマンド | さっきのコマンドをもう一度 |
| **Ctrl + C** | 強制終了 | プログラムが止まらない時 |
| **Ctrl + L** | 画面クリア | 画面をきれいにしたい時 |
| **Ctrl + D** | ログアウト | WSL2を終了する時 |

#### よくある初心者の疑問

**Q: コマンドを打っても反応がない**
A: Enter キーを押しましたか？コマンドは Enter で実行されます

**Q: パスワードを入力しても表示されない**
A: セキュリティのため表示されません。打ち込んで Enter を押してください

**Q: 画面に大量の文字が流れて止まらない**
A: Ctrl + C で止められます

**Q: コマンドが見つからないと言われる**
A: スペルミスか、まだインストールされていないかもしれません

### インストール完了確認

```bash
# 各項目が正常に動作することを確認

# 1. WSL2起動確認
echo "WSL2 is working!"

# 2. インターネット接続
ping -c 4 google.com

# 3. apt動作確認
sudo apt update

# 4. ファイルアクセス
touch ~/test.txt
ls -la ~/test.txt

# 5. Windows連携
explorer.exe .

# 6. 権限確認
sudo echo "sudo works!"

# 7. エディタ確認
nano --version
vim --version

# 8. Git確認
git --version

# 9. Python確認
python3 --version

# 10. メモリ・CPU確認
free -h
nproc
```

### 学習準備完了項目

- [ ] WSL2正常起動
- [ ] Ubuntu初期設定完了
- [ ] Windows Terminal設定
- [ ] 基本コマンド動作確認
- [ ] VSCode連携確認
- [ ] ファイルアクセス理解
- [ ] sudo権限動作
- [ ] インターネット接続
- [ ] 日本語表示正常
- [ ] 作業ディレクトリ作成

```bash
# 学習用ディレクトリ作成
mkdir -p ~/learning/{chapter1,chapter2,chapter3,chapter4,chapter5}
cd ~/learning
echo "Ready to start learning Linux!"
```

## まとめ

WSL2環境構築の要点：

1. **システム要件**: Windows 10 Version 2004以降、仮想化有効
2. **インストール**: `wsl --install`コマンドで簡単導入
3. **初期設定**: システム更新と基本ツールインストール
4. **Windows統合**: Terminal設定とVSCode連携

これで第1章のLinux学習を開始する準備が整いました。

---

