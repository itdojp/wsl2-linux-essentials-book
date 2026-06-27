---
title: "第0章: WSL2 セットアップ"
chapter: chapter0
layout: book
---

# 第0章: WSL2 セットアップ

## 前提（検証環境）
- Windows 10 Version 2004 以降 / Windows 11
- PowerShell を管理者権限で実行できること（企業 PC などで制限される場合がある）
- 本書は WSL2 上の Ubuntu を想定（インターネット接続が必要な手順を含む）

## この章の目標
- WSL2 をインストールし、Ubuntu を起動できる
- Ubuntu 上で基本的な Linux コマンドを実行できる

## できるようになること
- Windows 上で Linux を利用できる環境を構築できる
- ターミナルからコマンドを実行できる

## 0.1 必要な環境

### Windows 要件の確認

```powershell
# PowerShell で実行
winver
```

**必要なバージョン**: 
- Windows 10 Version 2004 以降
- Windows 11（全バージョン）

※企業 PC などで管理者権限がない場合や、組織のポリシーにより WSL2 のインストールが制限されている場合があります。その場合は、システム管理者または情報システム部門に確認してください。

## 0.2 WSL2 のインストール（3 ステップ）

### ステップ1: PowerShell を管理者権限で開く

1. スタートボタンを右クリック
2. 「Windows PowerShell（管理者）」をクリック

### ステップ2: WSL2 をインストール

```powershell
# 1 行で実行
wsl --install
```

このコマンドでインストールされるものは次のとおりです。
- WSL2 本体
- Ubuntu（Linux）
- 必要な機能一式

### ステップ3: PCを再起動

インストール完了後、PCを再起動します。

## 0.3 初回セットアップ

### Ubuntuの起動

再起動後、スタートメニューから「Ubuntu」を起動します。

初回起動時の設定は次のとおりです。
```bash
# ユーザー名を入力（英小文字と数字）
Enter new UNIX username: myname

# パスワードを設定（入力時は表示されません）
New password: 
Retype new password:
```

注意: パスワードは入力しても画面に表示されません（正常な動作です）。

### 動作確認

```bash
# Ubuntuのバージョン確認
lsb_release -a

# 現在のユーザー名確認
whoami

# 現在の場所確認
pwd
```

## 0.4 Windows Terminalの設定（オプション）

必要に応じて Windows Terminal を導入します。

```powershell
# PowerShell で実行
winget install Microsoft.WindowsTerminal
```

Windows Terminalの利点は次のとおりです。
- タブで複数のターミナルを開ける
- 見やすいフォントと色
- コピー／ペーストが容易

## 0.5 トラブルシューティング

### よくある問題と解決法

#### エラー: 「WSL 2 requires an update to its kernel component」
```powershell
# カーネルアップデートをダウンロードし、手動でインストール
# 参照: https://aka.ms/wsl2kernel
```

#### エラー: 「Virtual Machine Platform」が無効
```powershell
# 管理者権限の PowerShell で実行
dism.exe /online /enable-feature /featurename:VirtualMachinePlatform /all /norestart
# その後、PC再起動
```

#### Ubuntu が起動しない
```powershell
# 初期対応
wsl --shutdown
wsl --status
wsl --update

# （必要なら）バックアップ
# wsl --export Ubuntu ubuntu-backup.tar

# 注意: --unregister は対象ディストリビューションのデータを削除します（復旧不可）
# 最終手段（データ削除を許容できる場合のみ実施）
wsl --unregister Ubuntu
wsl --install -d Ubuntu
```

## セットアップ完了

WSL2 環境の準備が完了しました。次章以降は、実際にコマンドを実行しながら進めます。

### 確認コマンド
```bash
# すべて正常に動作するか確認
echo "Hello, Linux!"
date
ls -la
```

## まとめ

- WSL2 のインストールと Ubuntu の初回セットアップが完了した
- Ubuntu ターミナルで基本コマンドが実行できる状態になった
- 以降の章は「実際にコマンドを打つ」ことを前提に進められる

---

**次章へ**: [第1章 Linux の世界への第一歩](../chapter1/)
