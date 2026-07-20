---
title: "第6章: WordPress構築"
chapter: chapter6
layout: book
---

# 第6章: WordPress構築

## 前提（検証環境）
- WSL2 上の Ubuntu 24.04を推奨（22.04を使う場合は、後述の推奨versionとの差を確認する）
- systemd 有効を推奨（`systemctl` を使用。第3章の手順で有効化できる）
- 本章はパッケージ導入と `/var/www` 配下への配置を行うため `sudo` が必要
- 学習用のローカル環境（WSL2 内）を前提とし、公開サーバー用途の手順ではない

本章の取得・検証snapshotは**2026-07-21確認**です。WordPress coreは`7.0.2`、checksum localeは`en_US`へ固定します。新版へ追従するときは、URLの`latest`へ戻すのではなく、version、要件、checksum正常系・改変系を再検証して本章と[`wordpress-release.json`]({{ site.baseurl }}/assets/data/wordpress-release.json)を同じ改訂で更新します。

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

# 起動とディストリビューション起動時の自動起動設定
sudo systemctl start apache2    # 今すぐ起動
sudo systemctl enable apache2   # WSLディストリビューション起動時に自動起動

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
# PHP、必要モジュール、checksum manifest処理用のjq
sudo apt install -y php libapache2-mod-php php-mysql php-curl php-gd php-mbstring php-xml php-zip jq

# PHPとMySQL serverのversion確認
php -v
sudo mysql --batch --skip-column-names -e 'SELECT VERSION();'

# Apacheを再起動してPHPを有効化
sudo systemctl restart apache2
```

WordPress 7.0.2のVersion Check APIが示す動作下限はPHP 7.4 / MySQL 5.5.5です。一方、WordPress.orgが2026-07-21に示す安全・性能面の**推奨baseline**はPHP 8.3以上、MySQL 8.0以上またはMariaDB 10.11以上、HTTPSです。本章のローカル演習でもPHP 8.3以上とMySQL 8.0以上を推奨します。Ubuntu 22.04の標準PHP 8.1系は動作下限を満たしても推奨baseline未満なので、Ubuntu 24.04へ上げるか、保守された配布経路を別途設計してください。要件を満たさない環境で確認を省略して進めません。

### ステップ4: WordPressのインストール

次の手順は、固定archiveを一時directoryへ展開し、WordPress.orgのversion/locale別manifestと全core fileを照合してからweb rootへ配置します。Core Checksums APIはMD5を返します。この照合は、TLSで取得した公式manifestに対する破損・差分検出であり、HTTPSから独立したcode signingではありません。`curl -k`、`--insecure`、WP-CLIの`--insecure`でTLS検証を無効化しないでください。

```bash
# 固定した教材snapshot。新版追従は値だけを実行時に変えず、本章の改訂として行う
WP_VERSION='7.0.2'
WP_LOCALE='en_US'
WP_ARCHIVE="wordpress-${WP_VERSION}.tar.gz"
WP_DOWNLOAD_URL="https://downloads.wordpress.org/release/${WP_ARCHIVE}"
WP_CHECKSUM_URL="https://api.wordpress.org/core/checksums/1.0/?version=${WP_VERSION}&locale=${WP_LOCALE}"

# 途中失敗時も未検証物をweb rootに残さない
set -euo pipefail
WP_WORK_DIR="$(mktemp -d)"
cleanup_wordpress_download() {
  rm -rf -- "$WP_WORK_DIR"
}
trap cleanup_wordpress_download EXIT
trap 'exit 129' HUP
trap 'exit 130' INT
trap 'exit 143' TERM
cd "$WP_WORK_DIR"

# HTTPS/TLS検証を維持して固定versionを取得
curl --fail --location --silent --show-error \
  --proto '=https' --tlsv1.2 \
  --output "$WP_ARCHIVE" "$WP_DOWNLOAD_URL"

# 空archive、絶対path、親directory参照、wordpress/外、symbolic/hard linkを拒否
python3 - "$WP_ARCHIVE" <<'PY'
from pathlib import PurePosixPath
import sys
import tarfile

with tarfile.open(sys.argv[1], "r:gz") as archive:
    members = archive.getmembers()
    if not members:
        raise SystemExit("ERROR: archiveが空です。配置を中止します。")
    for member in members:
        path = PurePosixPath(member.name)
        unsafe_path = (
            path.is_absolute()
            or ".." in path.parts
            or not path.parts
            or path.parts[0] != "wordpress"
            or any(ord(character) < 32 or ord(character) == 127 for character in member.name)
        )
        unsafe_type = not (member.isdir() or member.isfile())
        if unsafe_path or unsafe_type:
            raise SystemExit(
                f"ERROR: 安全でないarchive memberです: {member.name!r}"
            )
PY

# preflight成功後に一時directoryへ展開
tar --extract --gzip --file "$WP_ARCHIVE"

# version/locale別の公式core checksumsをHTTPSで取得
curl --fail --silent --show-error \
  --proto '=https' --tlsv1.2 \
  --output core-checksums.json "$WP_CHECKSUM_URL"
jq -e '.checksums | (type == "object" and length > 0)' core-checksums.json >/dev/null
jq -r '.checksums | to_entries[] | "\(.value)  wordpress/\(.key)"' \
  core-checksums.json > wordpress-core.md5

# manifest対象fileの過不足も拒否する（directoryは比較対象外）
find wordpress -type f -printf '%P\n' | LC_ALL=C sort > archive-files.txt
jq -r '.checksums | keys[]' core-checksums.json | LC_ALL=C sort > checksum-files.txt
if ! diff --unified=0 checksum-files.txt archive-files.txt; then
  echo 'ERROR: WordPress core file集合が公式manifestと一致しません。' >&2
  exit 1
fi

# fileの過不足・改変・checksum不一致はnon-zeroで停止する
if ! md5sum --check --strict --quiet wordpress-core.md5; then
  echo 'ERROR: WordPress core checksumが一致しません。web rootへ配置しません。' >&2
  exit 1
fi
echo "WordPress ${WP_VERSION} (${WP_LOCALE}) core checksum: OK"

# 既存siteを暗黙に上書きしない。backup/削除は利用者が内容を確認して別途行う
if sudo test -e /var/www/html/wordpress; then
  echo 'ERROR: /var/www/html/wordpress が既に存在します。配置を中止します。' >&2
  exit 1
fi

# checksum成功後にだけドキュメントルートへ配置
sudo cp --archive wordpress /var/www/html/wordpress
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
curl --fail --silent --show-error https://api.wordpress.org/secret-key/1.1/salt/
```

`wp-config.php` 内の `AUTH_KEY` などのブロックを、上記の出力で置き換えてください。

初期設定画面で日本語を選択すると、`en_US` coreへ日本語language packが追加されます。本章の`WP_LOCALE='en_US'`は、配置前に照合する**配布archiveのchecksum集合**を表します。日本語版archiveへ変更する場合は、versionだけでなくarchive URLとchecksum localeを`ja`へそろえ、同じ正常系・改変系検証を実施してください。

### ステップ5: WordPress の初期設定

1. **ブラウザでアクセス**
   - Windows 側のブラウザで `http://localhost/wordpress` を開く

2. **言語選択**
   - 「日本語」を選択して「続ける」

3. **サイト情報の入力**
   - サイトのタイトル: 任意の名称（例: 私のブログ）
   - ユーザー名: 推測されにくい管理用ユーザー名（`admin` 等の既定候補は避ける）
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
sudo find /var/www/html/wordpress -type d -exec chmod 755 {} \;
sudo find /var/www/html/wordpress -type f -exec chmod 644 {} \;
sudo chown root:www-data /var/www/html/wordpress/wp-config.php
sudo chmod 640 /var/www/html/wordpress/wp-config.php

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

### Source Notes（2026-07-21確認）

- [WordPress Version Check API](https://api.wordpress.org/core/version-check/1.7/): `en_US`の先頭stable offerが7.0.2であることと、APIが返す実行下限PHP 7.4 / MySQL 5.5.5を確認。本章では安全・性能面の推奨baselineと区別します。
- [WordPress Release Archive](https://wordpress.org/download/releases/): 7.0.2の固定release archiveが公開されていることを確認。実行時の`latest`選択には使用しません。
- [WordPress Core Checksums API](https://api.wordpress.org/core/checksums/1.0/?version=7.0.2&locale=en_US): version/locale別の3,945 core file checksumを取得する正本。本章の照合はこのmanifestと一致する全fileを配置条件にします。
- [WordPress.org Requirements](https://wordpress.org/about/requirements/): 推奨baselineのPHP 8.3+、MySQL 8.0+またはMariaDB 10.11+、HTTPSを確認。WordPress 7.0.2だけの最低動作保証とは扱いません。
- [WP-CLI: `wp core verify-checksums`](https://developer.wordpress.org/cli/commands/core/verify-checksums/): version/locale指定、checksum不一致時のfailure、`--insecure`がTLS検証を無効化することを確認。本章ではWP-CLIを必須化せず、同じ公式manifestを直接照合します。

## まとめ

第 6 章では、学習用の WordPress サイトをローカルに構築しました。LAMP 環境の構築から WordPress のインストールまでの流れを確認しました。
公開環境に適用する場合は、セキュリティ設定やバックアップ設計などを別途検討してください。

---

> **注意**  
> 本書の現行バージョンでは第6章までを対象としており、第7章以降の内容は今後の拡張や関連書籍で扱う予定です。  
> より高度なトラブルシューティングや運用のコツについて学びたい場合は、[linux-infra-textbook2](https://github.com/itdojp/linux-infra-textbook2) など上位レベルの書籍もあわせて参照してください。

**目次へ**: [WSL2 Linux実践ガイド（トップ）](../)
