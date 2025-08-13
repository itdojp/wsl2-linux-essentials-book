---
title: "第2章 WSL2のインストール"
chapter: chapter02
layout: default
---

# 第2章 WSL2のインストール

## システム要件確認

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

## WSL2のインストール

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

## 初期設定

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

## Windows Terminalの設定

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

## ファイルシステムアクセス

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

## VSCode統合

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

## メモリとCPU設定

### WSL2リソース設定

`.wslconfig`ファイルを作成（Windows側）：

```powershell
# %USERPROFILE%\.wslconfig を作成
notepad.exe $env:USERPROFILE\.wslconfig
```

設定例：
```ini
[wsl2]
memory=4GB        # メモリ上限
processors=2      # CPU数
swap=8GB         # スワップサイズ
localhostForwarding=true  # localhost転送
```

### 設定適用

```powershell
# WSL2完全シャットダウン
wsl --shutdown

# 再起動（設定が適用される）
wsl
```

## トラブルシューティング

### よくある問題と解決方法

**1. WSL2が起動しない**
```powershell
# 仮想化機能の確認
bcdedit /enum | findstr hypervisorlaunchtype
# "hypervisorlaunchtype Auto" であることを確認

# 無効になっている場合
bcdedit /set hypervisorlaunchtype auto
```

**2. メモリ使用量が多い**
```powershell
# メモリキャッシュクリア（WSL2内）
echo 1 | sudo tee /proc/sys/vm/drop_caches
```

**3. ネットワーク接続できない**
```powershell
# DNSリセット（WSL2内）
echo "nameserver 8.8.8.8" | sudo tee /etc/resolv.conf
```

## まとめ

この章では、WSL2のインストールから初期設定まで、実践的なセットアップ方法を学びました：

- システム要件の確認方法
- WSL2のインストール手順
- Ubuntu初期設定
- Windows Terminalのカスタマイズ
- ファイルシステムの相互アクセス
- VSCodeとの統合
- リソース管理とトラブルシューティング

次の章では、目的に応じたLinuxディストリビューションの選び方について詳しく説明します。

---