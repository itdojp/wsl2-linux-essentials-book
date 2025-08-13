---
title: "第0章: WSL2セットアップ"
chapter: chapter0
layout: book
---

# 第0章: WSL2セットアップ

## 🎯 この章の目標
- WSL2を5分でインストールできる
- Ubuntuを起動してLinuxコマンドを試せる

## 🚀 できるようになること
- WindowsでLinuxを使える環境が整う
- ターミナルでコマンドが打てるようになる

## 0.1 必要な環境

### Windows要件の確認

```powershell
# PowerShellで実行
winver
```

**必要なバージョン**: 
- Windows 10 Version 2004 以降
- Windows 11（すべてのバージョンOK）

## 0.2 WSL2のインストール（簡単3ステップ）

### ステップ1: PowerShellを管理者権限で開く

1. スタートボタンを右クリック
2. 「Windows PowerShell（管理者）」をクリック

### ステップ2: WSL2をインストール

```powershell
# これ1行でOK！
wsl --install
```

このコマンドで以下が自動的にインストールされます：
- WSL2本体
- Ubuntu（Linux）
- 必要な機能すべて

### ステップ3: PCを再起動

インストール完了後、PCを再起動します。

## 0.3 初回セットアップ

### Ubuntuの起動

再起動後、スタートメニューから「Ubuntu」を起動します。

初回起動時の設定：
```bash
# ユーザー名を入力（英数字小文字）
Enter new UNIX username: myname

# パスワードを設定（入力時は表示されません）
New password: 
Retype new password:
```

⚠️ **重要**: パスワードは入力しても画面に表示されません。これは正常な動作です。
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

より使いやすいターミナルを使いたい場合：

```powershell
# PowerShellで実行
winget install Microsoft.WindowsTerminal
```

Windows Terminalの利点：
- タブで複数のターミナルを開ける
- 見やすいフォントと色
- コピー＆ペーストが簡単

## 0.5 トラブルシューティング

### よくある問題と解決法

#### ❌ エラー: 「WSL 2 requires an update to its kernel component」
```powershell
# カーネルアップデートをダウンロード
# https://aka.ms/wsl2kernel から手動でダウンロードしてインストール
```

#### ❌ エラー: 「Virtual Machine Platform」が無効
```powershell
# 管理者権限のPowerShellで実行
dism.exe /online /enable-feature /featurename:VirtualMachinePlatform /all /norestart
# その後、PC再起動
```

#### ❌ Ubuntuが起動しない
```powershell
# WSLをリセット
wsl --unregister Ubuntu
wsl --install -d Ubuntu
```

## 🎉 セットアップ完了！

これでWSL2環境の準備が整いました。次の章から本格的にLinuxを学んでいきましょう。

### 確認コマンド
```bash
# すべて正常に動作するか確認
echo "Hello, Linux!"
date
ls -la
```

---

**次章へ**: [第1章 Linuxの世界への第一歩](../chapter1/)