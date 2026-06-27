---
title: "第6章: WordPress構築"
chapter: chapter6
layout: book
---

# 第6章: WordPress構築

## 前提（検証環境）
- WSL2 上の Ubuntu（例: 22.04/24.04）
- systemd 有効を推奨（`systemctl` を使用。第3章の手順で有効化できる）
- 本章はパッケージ導入と `/var/www` 配下への配置を行うため `sudo` が必要
- 学習用のローカル環境（WSL2 内）を前提とし、公開サーバー用途の手順ではない

## この章の目標
- LAMP 環境の構成要素を把握し、構築手順を実行できる
- WordPress をインストールし、初期設定できる
- Web サーバー（Apache）とデータベース（MySQL）の基本操作を理解する

## できるようになること
- 学習用の WordPress サイトをローカル（WSL2 内）に構築できる
- データベースの基本操作（DB/ユーザー作成）を実行できる
- Web サーバーの状態確認や再起動を行える

## はじめに：実際に動作する Web サイトを構築する

これまで学んだ内容を前提に、学習用の WordPress サイトを構築します。
手順はコマンド例を示すため、環境差分がある場合は適宜読み替えてください。

### この章で作るもの
**WordPress ブログサイト**（学習用）

## 6.1 LAMP 環境で WordPress を動かす

### LAMP とは

**LAMP**は4つのソフトウェアの頭文字です。
- **L**inux: OS（この本で使っているUbuntu環境）
- **A**pache: Web サーバー（Webページを外部に公開するソフトウェア）
- **M**ySQL: データベース（記事やユーザー情報などのデータを保存する場所）
- **P**HP: プログラミング言語（動的なWebページを生成するための言語）

これらを組み合わせると、WordPressのようなWeb サイトが作れます。

### 完成イメージ
1. ブラウザで `http://localhost/wordpress` にアクセス
2. WordPressの初期設定画面が表示される
3. ブログ記事を投稿できる

### ステップ1: Apache Web サーバーのインストール

```bash
# まずはシステムを最新に
sudo apt update

# Apacheをインストール（Web サーバー）
sudo apt install -y apache2

# 起動と自動起動設定
sudo systemctl start apache2    # 今すぐ起動
sudo systemctl enable apache2   # PC起動時に自動起動

# 動作確認
sudo systemctl status apache2
# `active (running)` と表示されれば稼働中
```

確認:
- Windows 側のブラウザで `http://localhost` を開く
- 「Apache2 Ubuntu Default Page」が表示されることを確認する

### ステップ2: MySQL データベースのインストール

```bash
# MySQL サーバーインストール
sudo apt install -y mysql-server

# MySQL にログイン
sudo mysql
```

MySQL プロンプトで次を実行します。
```sql
-- WordPress用データベース作成
CREATE DATABASE wordpress CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci;

-- ユーザー作成と権限付与
CREATE USER 'wpuser'@'localhost' IDENTIFIED BY 'StrongPassword123!';
GRANT ALL PRIVILEGES ON wordpress.* TO 'wpuser'@'localhost';
FLUSH PRIVILEGES;

-- 確認
SHOW DATABASES;
EXIT;
```

※ `StrongPassword123!` はサンプルです。学習用のローカル環境（WSL2 内）でのみ使用し、本番環境や公開サーバーでは必ず強力なパスワードに変更したうえで、認証情報を安全に管理してください。

### ステップ3: PHPのインストール

```bash
# PHP と必要モジュール
sudo apt install -y php libapache2-mod-php php-mysql php-curl php-gd php-mbstring php-xml php-zip

# バージョン確認
php -v
# PHP 8.x が表示されればOK

# Apacheを再起動してPHPを有効化
sudo systemctl restart apache2
```

### ステップ4: WordPressのインストール

```bash
# WordPress ダウンロード
cd /tmp
wget https://wordpress.org/latest.tar.gz
tar -xzvf latest.tar.gz

# ドキュメントルートへ配置
sudo cp -R wordpress /var/www/html/
sudo chown -R www-data:www-data /var/www/html/wordpress

# パーミッション（ディレクトリ=755, ファイル=644）
sudo find /var/www/html/wordpress -type d -exec chmod 755 {} \;
sudo find /var/www/html/wordpress -type f -exec chmod 644 {} \;

# 設定ファイル作成
cd /var/www/html/wordpress
sudo cp wp-config-sample.php wp-config.php
# 認証情報を含むため、読み取り権限を絞る（Apache は www-data で動作する想定）
sudo chown root:www-data wp-config.php
sudo chmod 640 wp-config.php
sudo vi wp-config.php
```

wp-config.php の編集箇所（データベース設定部分のみ変更）は次のとおりです。
```php
// ** Database settings ** //
define( 'DB_NAME', 'wordpress' );
define( 'DB_USER', 'wpuser' );
define( 'DB_PASSWORD', 'StrongPassword123!' );
define( 'DB_HOST', 'localhost' );
define( 'DB_CHARSET', 'utf8mb4' );
define( 'DB_COLLATE', '' );
```

認証キー（ソルト）は、推測困難なランダム値に置き換えます（この手順は学習用のローカル環境でも推奨です）。

```bash
# 例: ソルト生成（貼り付け用）
curl -s https://api.wordpress.org/secret-key/1.1/salt/
```

`wp-config.php` 内の `AUTH_KEY` などのブロックを、上記の出力で置き換えてください。

### ステップ5: WordPress の初期設定

1. **ブラウザでアクセス**
   - Windows 側のブラウザで `http://localhost/wordpress` を開く

2. **言語選択**
   - 「日本語」を選択して「続ける」

3. **サイト情報の入力**
   - サイトのタイトル: 任意の名称（例: 私のブログ）
   - ユーザー名: admin（または任意の名前）
   - パスワード: 強力なパスワードを設定
   - メールアドレス: 任意のメールアドレス

4. **インストール実行**
   - 「WordPressをインストール」をクリック

5. **完了**
   - ログインし、管理画面が表示されることを確認する

### 構築完了

WordPress サイトの構築が完了しました。

本章で実施した作業は次のとおりです。
- Apache のインストールと起動確認
- MySQL の設定（DB/ユーザー作成）
- PHP の導入
- WordPress の配置と初期設定

### トラブルシューティング

#### Apacheが起動しない場合
```bash
# エラーログを確認
sudo journalctl -xe | grep apache2

# 設定ファイルの文法チェック
sudo apache2ctl configtest
```

#### MySQL に接続できない場合
```bash
# MySQL サービスの状態確認
sudo systemctl status mysql

# 再起動
sudo systemctl restart mysql
```

#### WordPressが表示されない場合
```bash
# パーミッションの再設定
sudo chown -R www-data:www-data /var/www/html/wordpress
sudo chmod -R 755 /var/www/html/wordpress

# Apacheの再起動
sudo systemctl restart apache2
```

### 追加学習の観点（任意）

WordPress の基本的な構築手順を確認できました。追加学習の観点は次のとおりです。

1. **テーマのカスタマイズ**: 外観を調整する
2. **プラグインの追加**: 機能を拡張する
3. **セキュリティ対策**: 更新運用、権限設計、公開範囲を見直す
4. **バックアップ設定**: 障害復旧を想定した取得・保管を設計する

これらは要件に応じて、公式ドキュメント等を参照しながら検討してください。

## まとめ

第 6 章では、学習用の WordPress サイトをローカルに構築しました。LAMP 環境の構築から WordPress のインストールまでの流れを確認しました。
公開環境に適用する場合は、セキュリティ設定やバックアップ設計などを別途検討してください。

---

> **注意**  
> 本書の現行バージョンでは第6章までを対象としており、第7章以降の内容は今後の拡張や関連書籍で扱う予定です。  
> より高度なトラブルシューティングや運用のコツについて学びたい場合は、[linux-infra-textbook2](https://github.com/itdojp/linux-infra-textbook2) など上位レベルの書籍もあわせて参照してください。

**目次へ**: [WSL2 Linux 実践ガイド（トップ）](../)
