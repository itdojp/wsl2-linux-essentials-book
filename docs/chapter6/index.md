---
title: "第6章: WordPress構築"
chapter: chapter6
layout: book
---

# 第6章: WordPress構築

## 🎯 この章の目標
- LAMP環境を構築できる
- WordPressをインストールできる
- Webサーバーの基本を理解する

## 🚀 できるようになること
- 自分のブログサイトを立ち上げられる
- データベースを操作できる
- Webサーバーを管理できる

## はじめに：実際に動くWebサイトを作ろう！

これまで学んだ知識を使って、実際に動くWordPressサイトを作ります。
最初は難しく感じるかもしれませんが、コピペしながら動かして、少しずつ理解していきましょう。

### 📋 この章で作るもの
**WordPressブログサイト** - 世界中のWebサイトの約40%で使われている人気のシステムです！

## 6.1 LAMP環境でWordPressを動かそう

### LAMPって何？

**LAMP**は4つのソフトウェアの頭文字です：
- **L**inux: OS（この本で使っているUbuntu環境）
- **A**pache: Webサーバー（Webページを外部に公開するソフトウェア）
- **M**ySQL: データベース（記事やユーザー情報などのデータを保存する場所）
- **P**HP: プログラミング言語（動的なWebページを生成するための言語）

これらを組み合わせると、WordPressのようなWebサイトが作れます。

### 🎯 完成イメージ
1. ブラウザで `http://localhost/wordpress` にアクセス
2. WordPressの初期設定画面が表示される
3. ブログ記事を投稿できる

### ステップ1: Apache Webサーバーのインストール

```bash
# まずはシステムを最新に
sudo apt update

# Apacheをインストール（Webサーバー）
sudo apt install apache2 -y

# 起動と自動起動設定
sudo systemctl start apache2    # 今すぐ起動
sudo systemctl enable apache2   # PC起動時に自動起動

# 動作確認
sudo systemctl status apache2
# 緑色で「active (running)」と表示されればOK！
```

🎉 **確認方法**：
Windowsのブラウザで `http://localhost` を開く
→ 「Apache2 Ubuntu Default Page」が表示されれば成功！

### ステップ2: MySQLデータベースのインストール

```bash
# MySQLサーバーインストール
sudo apt install mysql-server -y

# MySQLにログイン
sudo mysql
```

MySQLプロンプトで以下を実行：
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

### ステップ3: PHPのインストール

```bash
# PHP と必要モジュール
sudo apt install php libapache2-mod-php php-mysql php-curl php-gd php-mbstring php-xml php-zip -y

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
sudo chmod -R 755 /var/www/html/wordpress

# 設定ファイル作成
cd /var/www/html/wordpress
sudo cp wp-config-sample.php wp-config.php
sudo vi wp-config.php
```

wp-config.php の編集箇所（データベース設定部分のみ変更）：
```php
// ** Database settings ** //
define( 'DB_NAME', 'wordpress' );
define( 'DB_USER', 'wpuser' );
define( 'DB_PASSWORD', 'StrongPassword123!' );
define( 'DB_HOST', 'localhost' );
define( 'DB_CHARSET', 'utf8mb4' );
define( 'DB_COLLATE', '' );
```

### ステップ5: WordPressの初期設定

1. **ブラウザでアクセス**
   - Windowsのブラウザで `http://localhost/wordpress` を開く

2. **言語選択**
   - 「日本語」を選択して「続ける」

3. **サイト情報の入力**
   - サイトのタイトル: 好きな名前（例：私のブログ）
   - ユーザー名: admin（または好きな名前）
   - パスワード: 強力なパスワードを設定
   - メールアドレス: あなたのメールアドレス

4. **インストール実行**
   - 「WordPressをインストール」をクリック

5. **完成！**
   - ログインして、記事を投稿してみましょう！

### 🎊 おめでとうございます！

これで、あなたのWordPressサイトが完成しました！

**できるようになったこと：**
- ✅ Webサーバーの構築
- ✅ データベースの作成と管理
- ✅ PHPアプリケーションの動作
- ✅ WordPressの運用

### トラブルシューティング

#### Apacheが起動しない場合
```bash
# エラーログを確認
sudo journalctl -xe | grep apache2

# 設定ファイルの文法チェック
sudo apache2ctl configtest
```

#### MySQLに接続できない場合
```bash
# MySQLサービスの状態確認
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

### さらに学びたい方へ

WordPressの基本的な構築ができました！次のステップとして：

1. **テーマのカスタマイズ** - 見た目を変更してオリジナルサイトに
2. **プラグインの追加** - 機能を拡張して便利に
3. **セキュリティ対策** - より安全なサイト運営のために
4. **バックアップ設定** - 大切なデータを守るために

これらの内容は、より高度な学習として別途深く学んでいくことをお勧めします。

## まとめ

第6章では、実際に動くWordPressサイトを構築しました。LAMP環境の構築から始まり、WordPressのインストールまで、一連の流れを体験できました。

これはLinuxを使った実践的なプロジェクトの第一歩です。ここで学んだ知識を基に、さらに複雑なシステムの構築にもチャレンジしてみてください！

---

> **注意**  
> 本書の現行バージョンでは第6章までを対象としており、第7章以降の内容は今後の拡張や関連書籍で扱う予定です。  
> より高度なトラブルシューティングや運用のコツについて学びたい場合は、linux-infra-textbook など上位レベルの書籍もあわせて参照してください。
