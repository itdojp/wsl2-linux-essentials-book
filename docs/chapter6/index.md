---
title: "第6章: 実践プロジェクト集"
chapter: chapter6
layout: book
---

# 第6章: 実践プロジェクト集

## はじめに：実際に動くものを作ろう！

これまで学んだ知識を使って、実際に動くシステムを作ります。
最初は難しく感じるかもしれませんが、コピペしながら動かして、少しずつ理解していきましょう。

### 📋 この章で作るもの
1. **Webサイト公開環境**（LAMP）
2. **Dockerコンテナ環境**
3. **監視システム**
4. **ログ解析システム**
5. **自動デプロイ環境**
6. **セキュリティ強化**
7. **バックアップシステム**

## 6.1 LAMP環境構築

### LAMPって何？

**LAMP**は4つのソフトウェアの頭文字です：
- **L**inux: OS（もう使ってます！）
- **A**pache: Webサーバー（ホームページを公開）
- **M**ySQL: データベース（データを保存）
- **P**HP: プログラミング言語（動的なページを作る）

これらを組み合わせると、WordPressのようなWebサイトが作れます。

### 🎯 完成イメージ
1. ブラウザで `http://localhost` にアクセス
2. WordPressの管理画面が表示される
3. ブログ記事を投稿できる

### Apache Webサーバー（ステップ1/4）

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

Apache設定の重要項目：
```apache
# サーバー名設定（警告抑制）
ServerName localhost

# ディレクトリインデックス
DirectoryIndex index.html index.php

# セキュリティヘッダー
ServerTokens Prod
ServerSignature Off
```

### MySQL データベース

```bash
# MySQLサーバーインストール
sudo apt install mysql-server -y

# セキュリティ設定
sudo mysql_secure_installation

# 質問への推奨回答：
# - VALIDATE PASSWORD component: Y
# - Password validation level: 1 (MEDIUM)
# - Remove anonymous users: Y
# - Disallow root login remotely: Y
# - Remove test database: Y
# - Reload privilege tables: Y

# MySQLログイン
sudo mysql
```

データベース作成：
```sql
-- WordPress用データベース作成
CREATE DATABASE wordpress CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci;

-- ユーザー作成と権限付与
CREATE USER 'wpuser'@'localhost' IDENTIFIED BY 'StrongPassword123!';
GRANT ALL PRIVILEGES ON wordpress.* TO 'wpuser'@'localhost';
FLUSH PRIVILEGES;

-- 確認
SHOW DATABASES;
SELECT user, host FROM mysql.user;
EXIT;
```

### PHP インストールと設定

```bash
# PHP と必要モジュール
sudo apt install php libapache2-mod-php php-mysql php-curl php-gd php-mbstring php-xml php-zip -y

# バージョン確認
php -v

# PHP設定
sudo nano /etc/php/8.3/apache2/php.ini
```

PHP推奨設定：
```ini
; メモリ制限
memory_limit = 256M

; アップロードサイズ
upload_max_filesize = 64M
post_max_size = 64M

; タイムゾーン
date.timezone = Asia/Tokyo

; エラー表示（本番環境では Off）
display_errors = Off
log_errors = On
error_log = /var/log/php_errors.log
```

### WordPress インストール

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
sudo nano wp-config.php
```

wp-config.php 設定：
```php
// データベース設定
define( 'DB_NAME', 'wordpress' );
define( 'DB_USER', 'wpuser' );
define( 'DB_PASSWORD', 'StrongPassword123!' );
define( 'DB_HOST', 'localhost' );
define( 'DB_CHARSET', 'utf8mb4' );

// セキュリティキー（https://api.wordpress.org/secret-key/1.1/salt/ から取得）
// 各キーを生成された値に置き換え
```

### Apache仮想ホスト設定

```bash
# 仮想ホスト作成
sudo nano /etc/apache2/sites-available/wordpress.conf
```

```apache
<VirtualHost *:80>
    ServerName wordpress.local
    DocumentRoot /var/www/html/wordpress
    
    <Directory /var/www/html/wordpress>
        Options FollowSymLinks
        AllowOverride All
        Require all granted
    </Directory>
    
    ErrorLog ${APACHE_LOG_DIR}/wordpress_error.log
    CustomLog ${APACHE_LOG_DIR}/wordpress_access.log combined
</VirtualHost>
```

```bash
# サイト有効化
sudo a2ensite wordpress.conf
sudo a2enmod rewrite
sudo systemctl reload apache2

# hosts ファイル編集（Windows側）
# C:\Windows\System32\drivers\etc\hosts に追加
# 127.0.0.1 wordpress.local
```

## 6.2 Docker環境構築

### Docker インストール

```bash
# 前提パッケージ
sudo apt update
sudo apt install apt-transport-https ca-certificates curl software-properties-common -y

# Docker GPGキー追加
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg

# Dockerリポジトリ追加
echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

# Docker インストール
sudo apt update
sudo apt install docker-ce docker-ce-cli containerd.io docker-compose-plugin -y

# ユーザーをdockerグループに追加
sudo usermod -aG docker $USER
newgrp docker

# 動作確認
docker --version
docker run hello-world
```

### Docker Compose プロジェクト

```bash
# プロジェクトディレクトリ作成
mkdir -p ~/docker-projects/webapp
cd ~/docker-projects/webapp

# docker-compose.yml 作成
nano docker-compose.yml
```

docker-compose.yml：
```yaml
version: '3.8'

services:
  web:
    image: nginx:alpine
    container_name: webapp-nginx
    ports:
      - "8080:80"
    volumes:
      - ./html:/usr/share/nginx/html
      - ./nginx.conf:/etc/nginx/conf.d/default.conf
    depends_on:
      - php
    networks:
      - webapp-network

  php:
    image: php:8.2-fpm-alpine
    container_name: webapp-php
    volumes:
      - ./html:/var/www/html
      - ./php.ini:/usr/local/etc/php/php.ini
    networks:
      - webapp-network

  db:
    image: mysql:8.0
    container_name: webapp-mysql
    environment:
      MYSQL_ROOT_PASSWORD: rootpass123
      MYSQL_DATABASE: webapp
      MYSQL_USER: webapp_user
      MYSQL_PASSWORD: userpass123
    volumes:
      - db_data:/var/lib/mysql
    ports:
      - "3306:3306"
    networks:
      - webapp-network

  phpmyadmin:
    image: phpmyadmin:latest
    container_name: webapp-phpmyadmin
    environment:
      PMA_HOST: db
      PMA_PORT: 3306
    ports:
      - "8081:80"
    depends_on:
      - db
    networks:
      - webapp-network

volumes:
  db_data:

networks:
  webapp-network:
    driver: bridge
```

Nginx設定（nginx.conf）：
```nginx
server {
    listen 80;
    server_name localhost;
    root /usr/share/nginx/html;
    index index.php index.html;

    location / {
        try_files $uri $uri/ /index.php?$query_string;
    }

    location ~ \.php$ {
        fastcgi_pass php:9000;
        fastcgi_index index.php;
        fastcgi_param SCRIPT_FILENAME /var/www/html$fastcgi_script_name;
        include fastcgi_params;
    }
}
```

テストページ作成：
```bash
# HTMLディレクトリ作成
mkdir html

# PHPテストページ
cat << 'PHP' > html/index.php
<?php
phpinfo();
?>
PHP

# 起動
docker compose up -d

# 確認
docker compose ps
curl http://localhost:8080
```

### Dockerfile によるカスタムイメージ

```bash
# Node.jsアプリケーション例
mkdir -p ~/docker-projects/nodeapp
cd ~/docker-projects/nodeapp

# Dockerfile作成
nano Dockerfile
```

Dockerfile：
```dockerfile
# ベースイメージ
FROM node:18-alpine

# 作業ディレクトリ
WORKDIR /app

# 依存関係ファイルコピー
COPY package*.json ./

# 依存関係インストール
RUN npm ci --only=production

# アプリケーションコピー
COPY . .

# ポート公開
EXPOSE 3000

# 実行ユーザー
USER node

# アプリケーション起動
CMD ["node", "index.js"]
```

アプリケーション作成：
```javascript
// index.js
const http = require('http');
const os = require('os');

const server = http.createServer((req, res) => {
    res.writeHead(200, { 'Content-Type': 'text/plain' });
    res.end(`Hello from Docker!\nHostname: ${os.hostname()}\n`);
});

server.listen(3000, () => {
    console.log('Server running on port 3000');
});
```

```json
// package.json
{
  "name": "nodeapp",
  "version": "1.0.0",
  "description": "Simple Node.js app",
  "main": "index.js",
  "scripts": {
    "start": "node index.js"
  }
}
```

ビルドと実行：
```bash
# イメージビルド
docker build -t nodeapp:v1 .

# コンテナ実行
docker run -d -p 3000:3000 --name myapp nodeapp:v1

# ログ確認
docker logs myapp
```

## 6.3 監視システム構築

### システム監視スクリプト

```bash
#!/bin/bash
# system_monitor.sh - 総合システム監視

# 設定
MONITOR_DIR="/var/log/monitoring"
ALERT_EMAIL="admin@example.com"
SLACK_WEBHOOK="https://hooks.slack.com/services/YOUR/WEBHOOK/URL"

# しきい値
THRESHOLD_CPU=80
THRESHOLD_MEM=90
THRESHOLD_DISK=85
THRESHOLD_LOAD=4.0

# ディレクトリ作成
sudo mkdir -p $MONITOR_DIR

# ログ記録関数
log_metric() {
    local metric=$1
    local value=$2
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    echo "$timestamp,$metric,$value" >> "$MONITOR_DIR/metrics.csv"
}

# アラート送信関数
send_alert() {
    local level=$1
    local message=$2
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    
    # ログ記録
    echo "[$timestamp] [$level] $message" >> "$MONITOR_DIR/alerts.log"
    
    # Slack通知（WebhookURL設定時）
    if [ -n "$SLACK_WEBHOOK" ]; then
        curl -X POST -H 'Content-type: application/json' \
            --data "{\"text\":\"[$level] $message\"}" \
            "$SLACK_WEBHOOK"
    fi
    
    # メール通知（mail設定時）
    # echo "$message" | mail -s "[$level] System Alert" $ALERT_EMAIL
}

# CPU監視
check_cpu() {
    local cpu_usage=$(top -bn1 | grep "Cpu(s)" | awk '{print int($2)}')
    log_metric "cpu_usage" "$cpu_usage"
    
    if [ $cpu_usage -gt $THRESHOLD_CPU ]; then
        send_alert "WARNING" "High CPU usage: ${cpu_usage}%"
        return 1
    fi
    return 0
}

# メモリ監視
check_memory() {
    local mem_info=$(free | grep Mem)
    local total=$(echo $mem_info | awk '{print $2}')
    local used=$(echo $mem_info | awk '{print $3}')
    local usage=$(echo "scale=0; $used * 100 / $total" | bc)
    
    log_metric "memory_usage" "$usage"
    
    if [ $usage -gt $THRESHOLD_MEM ]; then
        send_alert "WARNING" "High memory usage: ${usage}%"
        return 1
    fi
    return 0
}

# ディスク監視
check_disk() {
    local disk_usage=$(df -h / | tail -1 | awk '{print int($5)}')
    log_metric "disk_usage" "$disk_usage"
    
    if [ $disk_usage -gt $THRESHOLD_DISK ]; then
        send_alert "WARNING" "High disk usage: ${disk_usage}%"
        return 1
    fi
    return 0
}

# ロードアベレージ監視
check_load() {
    local load_1min=$(uptime | awk -F'load average:' '{print $2}' | awk '{print $1}' | tr -d ',')
    log_metric "load_average" "$load_1min"
    
    if (( $(echo "$load_1min > $THRESHOLD_LOAD" | bc -l) )); then
        send_alert "WARNING" "High load average: $load_1min"
        return 1
    fi
    return 0
}

# サービス監視
check_services() {
    local services=("nginx" "mysql" "ssh")
    
    for service in "${services[@]}"; do
        if ! systemctl is-active --quiet $service; then
            send_alert "ERROR" "Service $service is down"
            
            # 自動再起動試行
            sudo systemctl restart $service
            sleep 5
            
            if systemctl is-active --quiet $service; then
                send_alert "INFO" "Service $service restarted successfully"
            else
                send_alert "CRITICAL" "Failed to restart $service"
            fi
        fi
    done
}

# メイン処理
main() {
    check_cpu
    check_memory
    check_disk
    check_load
    check_services
}

# 実行
main
```

### Prometheus + Grafana 監視

```bash
# Prometheusインストール
cd /tmp
wget https://github.com/prometheus/prometheus/releases/download/v2.45.0/prometheus-2.45.0.linux-amd64.tar.gz
tar -xzf prometheus-2.45.0.linux-amd64.tar.gz
sudo mv prometheus-2.45.0.linux-amd64 /opt/prometheus

# 設定ファイル
sudo nano /opt/prometheus/prometheus.yml
```

prometheus.yml：
```yaml
global:
  scrape_interval: 15s
  evaluation_interval: 15s

scrape_configs:
  - job_name: 'prometheus'
    static_configs:
      - targets: ['localhost:9090']
  
  - job_name: 'node'
    static_configs:
      - targets: ['localhost:9100']
```

Node Exporterインストール：
```bash
# Node Exporter（システムメトリクス収集）
wget https://github.com/prometheus/node_exporter/releases/download/v1.6.0/node_exporter-1.6.0.linux-amd64.tar.gz
tar -xzf node_exporter-1.6.0.linux-amd64.tar.gz
sudo mv node_exporter-1.6.0.linux-amd64/node_exporter /usr/local/bin/

# systemdサービス作成
sudo nano /etc/systemd/system/node_exporter.service
```

```ini
[Unit]
Description=Node Exporter
After=network.target

[Service]
Type=simple
User=nobody
Group=nogroup
ExecStart=/usr/local/bin/node_exporter

[Install]
WantedBy=multi-user.target
```

Grafana設定：
```bash
# Grafanaインストール
sudo apt-get install -y software-properties-common
sudo add-apt-repository "deb https://packages.grafana.com/oss/deb stable main"
wget -q -O - https://packages.grafana.com/gpg.key | sudo apt-key add -
sudo apt update
sudo apt install grafana -y

# 起動
sudo systemctl start grafana-server
sudo systemctl enable grafana-server

# アクセス: http://localhost:3000
# 初期ログイン: admin/admin
```

## 6.4 ログ収集・解析システム

### ELKスタック簡易版

```bash
# Elasticsearch（シングルノード）
docker run -d \
  --name elasticsearch \
  -p 9200:9200 \
  -p 9300:9300 \
  -e "discovery.type=single-node" \
  -e "ES_JAVA_OPTS=-Xms512m -Xmx512m" \
  elasticsearch:7.17.10

# Kibana
docker run -d \
  --name kibana \
  -p 5601:5601 \
  --link elasticsearch \
  -e "ELASTICSEARCH_HOSTS=http://elasticsearch:9200" \
  kibana:7.17.10
```

### Fluentd によるログ収集

```bash
# Fluentd インストール
curl -fsSL https://toolbelt.treasuredata.com/sh/install-ubuntu-noble-fluent-package-v5-lts.sh | sh

# 設定ファイル
sudo nano /etc/fluent/fluent.conf
```

fluent.conf：
```xml
# Nginxアクセスログ
<source>
  @type tail
  path /var/log/nginx/access.log
  pos_file /var/log/td-agent/nginx-access.pos
  tag nginx.access
  <parse>
    @type nginx
  </parse>
</source>

# システムログ
<source>
  @type tail
  path /var/log/syslog
  pos_file /var/log/td-agent/syslog.pos
  tag system.syslog
  <parse>
    @type syslog
  </parse>
</source>

# Elasticsearch出力
<match **>
  @type elasticsearch
  host localhost
  port 9200
  logstash_format true
  logstash_prefix fluentd
  logstash_dateformat %Y%m%d
  include_tag_key true
  type_name access_log
  tag_key @log_name
  flush_interval 1s
</match>
```

### ログ解析スクリプト

```bash
#!/bin/bash
# log_analyzer.sh - アクセスログ解析

LOG_FILE="/var/log/nginx/access.log"
REPORT_DIR="/var/www/html/reports"
REPORT_FILE="$REPORT_DIR/report_$(date +%Y%m%d).html"

# レポートディレクトリ作成
mkdir -p $REPORT_DIR

# HTML開始
cat << 'HTML' > $REPORT_FILE
<!DOCTYPE html>
<html>
<head>
    <title>Access Log Report</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; }
        table { border-collapse: collapse; width: 100%; margin: 20px 0; }
        th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }
        th { background-color: #4CAF50; color: white; }
        h2 { color: #333; }
    </style>
</head>
<body>
    <h1>Nginx Access Log Analysis Report</h1>
    <p>Generated: $(date)</p>
HTML

# 総リクエスト数
echo "<h2>Summary</h2>" >> $REPORT_FILE
echo "<p>Total Requests: $(wc -l < $LOG_FILE)</p>" >> $REPORT_FILE

# ステータスコード分析
echo "<h2>Status Codes</h2>" >> $REPORT_FILE
echo "<table><tr><th>Status Code</th><th>Count</th></tr>" >> $REPORT_FILE

awk '{print $9}' $LOG_FILE | sort | uniq -c | sort -rn | while read count code; do
    echo "<tr><td>$code</td><td>$count</td></tr>" >> $REPORT_FILE
done
echo "</table>" >> $REPORT_FILE

# トップ10 IP
echo "<h2>Top 10 IP Addresses</h2>" >> $REPORT_FILE
echo "<table><tr><th>IP Address</th><th>Requests</th></tr>" >> $REPORT_FILE

awk '{print $1}' $LOG_FILE | sort | uniq -c | sort -rn | head -10 | while read count ip; do
    echo "<tr><td>$ip</td><td>$count</td></tr>" >> $REPORT_FILE
done
echo "</table>" >> $REPORT_FILE

# トップ10 URL
echo "<h2>Top 10 URLs</h2>" >> $REPORT_FILE
echo "<table><tr><th>URL</th><th>Requests</th></tr>" >> $REPORT_FILE

awk '{print $7}' $LOG_FILE | sort | uniq -c | sort -rn | head -10 | while read count url; do
    echo "<tr><td>$url</td><td>$count</td></tr>" >> $REPORT_FILE
done
echo "</table>" >> $REPORT_FILE

# HTML終了
echo "</body></html>" >> $REPORT_FILE

echo "Report generated: $REPORT_FILE"
```

## 6.5 CI/CDパイプライン構築

### GitLab Runner セットアップ

```bash
# GitLab Runner インストール
curl -L --output /usr/local/bin/gitlab-runner https://gitlab-runner-downloads.s3.amazonaws.com/latest/binaries/gitlab-runner-linux-amd64
chmod +x /usr/local/bin/gitlab-runner

# サービス登録
sudo gitlab-runner install --user=gitlab-runner --working-directory=/home/gitlab-runner
sudo gitlab-runner start

# Runner登録
sudo gitlab-runner register
# 対話式で設定入力
```

### .gitlab-ci.yml 例

```yaml
stages:
  - build
  - test
  - deploy

variables:
  APP_NAME: "myapp"
  DEPLOY_SERVER: "production.example.com"

# ビルドステージ
build:
  stage: build
  image: node:18
  script:
    - npm ci
    - npm run build
  artifacts:
    paths:
      - dist/
    expire_in: 1 week

# テストステージ
test:
  stage: test
  image: node:18
  script:
    - npm ci
    - npm test
    - npm run lint
  coverage: '/Coverage: \d+\.\d+%/'

# デプロイステージ
deploy:
  stage: deploy
  image: alpine:latest
  before_script:
    - apk add --no-cache openssh-client rsync
    - eval $(ssh-agent -s)
    - echo "$SSH_PRIVATE_KEY" | tr -d '\r' | ssh-add -
    - mkdir -p ~/.ssh
    - chmod 700 ~/.ssh
  script:
    - rsync -avz --delete dist/ ${DEPLOY_USER}@${DEPLOY_SERVER}:/var/www/${APP_NAME}/
    - ssh ${DEPLOY_USER}@${DEPLOY_SERVER} "sudo systemctl restart ${APP_NAME}"
  only:
    - main
```

### Jenkins パイプライン

```groovy
// Jenkinsfile
pipeline {
    agent any
    
    environment {
        DOCKER_IMAGE = 'myapp'
        DOCKER_TAG = "${env.BUILD_NUMBER}"
    }
    
    stages {
        stage('Checkout') {
            steps {
                checkout scm
            }
        }
        
        stage('Build') {
            steps {
                sh 'docker build -t ${DOCKER_IMAGE}:${DOCKER_TAG} .'
            }
        }
        
        stage('Test') {
            steps {
                sh 'docker run --rm ${DOCKER_IMAGE}:${DOCKER_TAG} npm test'
            }
        }
        
        stage('Push') {
            when {
                branch 'main'
            }
            steps {
                withCredentials([usernamePassword(
                    credentialsId: 'docker-hub',
                    usernameVariable: 'DOCKER_USER',
                    passwordVariable: 'DOCKER_PASS'
                )]) {
                    sh 'echo $DOCKER_PASS | docker login -u $DOCKER_USER --password-stdin'
                    sh 'docker push ${DOCKER_IMAGE}:${DOCKER_TAG}'
                }
            }
        }
        
        stage('Deploy') {
            when {
                branch 'main'
            }
            steps {
                sshagent(['deploy-key']) {
                    sh '''
                        ssh user@server "docker pull ${DOCKER_IMAGE}:${DOCKER_TAG}"
                        ssh user@server "docker stop myapp || true"
                        ssh user@server "docker run -d --name myapp -p 80:3000 ${DOCKER_IMAGE}:${DOCKER_TAG}"
                    '''
                }
            }
        }
    }
    
    post {
        success {
            slackSend(
                color: 'good',
                message: "Deployment successful: ${env.JOB_NAME} - ${env.BUILD_NUMBER}"
            )
        }
        failure {
            slackSend(
                color: 'danger',
                message: "Deployment failed: ${env.JOB_NAME} - ${env.BUILD_NUMBER}"
            )
        }
    }
}
```

## 6.6 セキュリティ強化

### ファイアウォール設定

```bash
#!/bin/bash
# firewall_setup.sh - セキュリティ設定

# UFW設定
sudo ufw --force reset
sudo ufw default deny incoming
sudo ufw default allow outgoing

# 必要なポートのみ開放
sudo ufw allow 22/tcp   # SSH
sudo ufw allow 80/tcp   # HTTP
sudo ufw allow 443/tcp  # HTTPS

# 特定IPからのSSHのみ許可（オプション）
# sudo ufw allow from 192.168.1.100 to any port 22

# レート制限（ブルートフォース対策）
sudo ufw limit ssh/tcp

# ログ有効化
sudo ufw logging on

# ファイアウォール有効化
sudo ufw --force enable

echo "Firewall configured successfully"
```

### Fail2ban設定

```bash
# Fail2banインストール
sudo apt install fail2ban -y

# カスタム設定
sudo nano /etc/fail2ban/jail.local
```

jail.local：
```ini
[DEFAULT]
bantime = 3600
findtime = 600
maxretry = 5

[sshd]
enabled = true
port = ssh
logpath = %(sshd_log)s
maxretry = 3

[nginx-http-auth]
enabled = true
filter = nginx-http-auth
port = http,https
logpath = /var/log/nginx/error.log

[nginx-noscript]
enabled = true
port = http,https
filter = nginx-noscript
logpath = /var/log/nginx/access.log
maxretry = 6

[nginx-badbots]
enabled = true
port = http,https
filter = nginx-badbots
logpath = /var/log/nginx/access.log
maxretry = 2

[nginx-noproxy]
enabled = true
port = http,https
filter = nginx-noproxy
logpath = /var/log/nginx/error.log
maxretry = 2
```

### SSL/TLS設定（Let's Encrypt）

```bash
# Certbotインストール
sudo apt install certbot python3-certbot-nginx -y

# SSL証明書取得（ドメイン必要）
sudo certbot --nginx -d example.com -d www.example.com

# 自動更新設定
sudo certbot renew --dry-run

# Cron設定
echo "0 0,12 * * * root python3 -c 'import random; import time; time.sleep(random.random() * 3600)' && certbot renew -q" | sudo tee -a /etc/crontab > /dev/null
```

## 6.7 バックアップとリストア

### 統合バックアップシステム

```bash
#!/bin/bash
# backup_system.sh - 統合バックアップ

set -euo pipefail

# 設定
BACKUP_ROOT="/backup"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="$BACKUP_ROOT/$TIMESTAMP"
RETENTION_DAYS=30

# S3設定（オプション）
S3_BUCKET="s3://my-backup-bucket"
AWS_PROFILE="default"

# バックアップ対象
BACKUP_ITEMS=(
    "/etc"
    "/var/www"
    "/home"
)

# データベースリスト
DATABASES=(
    "wordpress"
    "webapp"
)

# ログ関数
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$BACKUP_ROOT/backup.log"
}

# ディレクトリバックアップ
backup_directories() {
    log "Starting directory backup..."
    
    for item in "${BACKUP_ITEMS[@]}"; do
        if [ -d "$item" ]; then
            local backup_name=$(echo $item | tr '/' '_')
            tar -czf "$BACKUP_DIR/files${backup_name}.tar.gz" \
                --exclude='*.log' \
                --exclude='*.tmp' \
                "$item" 2>/dev/null || true
            log "Backed up: $item"
        fi
    done
}

# データベースバックアップ
backup_databases() {
    log "Starting database backup..."
    
    for db in "${DATABASES[@]}"; do
        mysqldump -u root \
            --single-transaction \
            --routines \
            --triggers \
            --events \
            "$db" | gzip > "$BACKUP_DIR/db_${db}.sql.gz"
        log "Backed up database: $db"
    done
}

# Dockerボリュームバックアップ
backup_docker_volumes() {
    log "Starting Docker volume backup..."
    
    docker volume ls -q | while read volume; do
        docker run --rm \
            -v "$volume":/source:ro \
            -v "$BACKUP_DIR":/backup \
            alpine tar -czf "/backup/docker_${volume}.tar.gz" -C /source .
        log "Backed up Docker volume: $volume"
    done
}

# S3アップロード
upload_to_s3() {
    if command -v aws &> /dev/null; then
        log "Uploading to S3..."
        aws s3 sync "$BACKUP_DIR" "$S3_BUCKET/$TIMESTAMP/" \
            --profile "$AWS_PROFILE" \
            --storage-class GLACIER_IR
        log "Upload to S3 completed"
    fi
}

# 古いバックアップ削除
cleanup_old_backups() {
    log "Cleaning up old backups..."
    
    find "$BACKUP_ROOT" -maxdepth 1 -type d -name "20*" \
        -mtime +$RETENTION_DAYS -exec rm -rf {} \;
    
    # S3からも削除
    if command -v aws &> /dev/null; then
        aws s3 ls "$S3_BUCKET/" --profile "$AWS_PROFILE" | \
            awk '{print $2}' | \
            while read dir; do
                dir_date=$(echo $dir | cut -d'_' -f1)
                if [ $(date -d "$dir_date" +%s 2>/dev/null || echo 0) -lt \
                     $(date -d "$RETENTION_DAYS days ago" +%s) ]; then
                    aws s3 rm "$S3_BUCKET/$dir" --recursive --profile "$AWS_PROFILE"
                fi
            done
    fi
    
    log "Cleanup completed"
}

# リストア関数
restore_backup() {
    local backup_date=$1
    local restore_dir="/restore/$backup_date"
    
    log "Starting restore from $backup_date..."
    
    # S3からダウンロード（必要な場合）
    if [ ! -d "$BACKUP_ROOT/$backup_date" ]; then
        aws s3 sync "$S3_BUCKET/$backup_date/" "$BACKUP_ROOT/$backup_date/" \
            --profile "$AWS_PROFILE"
    fi
    
    # ファイルリストア
    mkdir -p "$restore_dir"
    for file in "$BACKUP_ROOT/$backup_date"/files*.tar.gz; do
        tar -xzf "$file" -C "$restore_dir"
        log "Restored: $(basename $file)"
    done
    
    # データベースリストア
    for db_file in "$BACKUP_ROOT/$backup_date"/db_*.sql.gz; do
        local db_name=$(basename "$db_file" .sql.gz | cut -d'_' -f2)
        gunzip < "$db_file" | mysql -u root "$db_name"
        log "Restored database: $db_name"
    done
    
    log "Restore completed to $restore_dir"
}

# メイン処理
main() {
    # バックアップモード
    if [ "${1:-backup}" == "backup" ]; then
        log "=== Starting backup process ==="
        
        mkdir -p "$BACKUP_DIR"
        
        backup_directories
        backup_databases
        backup_docker_volumes
        upload_to_s3
        cleanup_old_backups
        
        log "=== Backup completed successfully ==="
        
    # リストアモード
    elif [ "$1" == "restore" ]; then
        if [ -z "${2:-}" ]; then
            echo "Usage: $0 restore YYYYMMDD_HHMMSS"
            exit 1
        fi
        restore_backup "$2"
    fi
}

# 実行
main "$@"
```

## 6.8 パフォーマンスチューニング

### システム最適化スクリプト

```bash
#!/bin/bash
# performance_tuning.sh - システム最適化

# カーネルパラメータ調整
sudo tee /etc/sysctl.d/99-performance.conf << 'EOF'
# ネットワーク最適化
net.core.somaxconn = 65535
net.ipv4.tcp_max_syn_backlog = 8192
net.ipv4.tcp_tw_reuse = 1
net.ipv4.tcp_fin_timeout = 30
net.ipv4.ip_local_port_range = 10000 65000

# ファイルディスクリプタ
fs.file-max = 2097152

# メモリ管理
vm.swappiness = 10
vm.dirty_ratio = 15
vm.dirty_background_ratio = 5
EOF

sudo sysctl -p /etc/sysctl.d/99-performance.conf

# Nginx最適化
sudo tee /etc/nginx/conf.d/performance.conf << 'EOF'
# ワーカープロセス
worker_processes auto;
worker_rlimit_nofile 65535;

events {
    worker_connections 4096;
    use epoll;
    multi_accept on;
}

http {
    # バッファサイズ
    client_body_buffer_size 128k;
    client_max_body_size 10m;
    client_header_buffer_size 1k;
    large_client_header_buffers 4 8k;
    
    # タイムアウト
    client_body_timeout 12;
    client_header_timeout 12;
    keepalive_timeout 15;
    send_timeout 10;
    
    # Gzip圧縮
    gzip on;
    gzip_vary on;
    gzip_min_length 1024;
    gzip_comp_level 6;
    gzip_types text/plain text/css text/xml text/javascript 
               application/json application/javascript application/xml+rss 
               application/rss+xml application/atom+xml image/svg+xml 
               text/x-js text/x-cross-domain-policy application/x-font-ttf 
               application/x-font-opentype application/vnd.ms-fontobject 
               image/x-icon;
    
    # キャッシュ
    open_file_cache max=2000 inactive=20s;
    open_file_cache_valid 30s;
    open_file_cache_min_uses 2;
    open_file_cache_errors on;
}
EOF

# MySQL最適化
sudo tee -a /etc/mysql/mysql.conf.d/mysqld.cnf << 'EOF'

[mysqld]
# バッファプール（RAMの70%程度）
innodb_buffer_pool_size = 1G
innodb_log_file_size = 256M
innodb_flush_log_at_trx_commit = 2
innodb_flush_method = O_DIRECT

# 接続数
max_connections = 500
max_connect_errors = 1000000

# クエリキャッシュ
query_cache_type = 1
query_cache_size = 128M
query_cache_limit = 2M

# その他
tmp_table_size = 64M
max_heap_table_size = 64M
thread_cache_size = 8
EOF

# サービス再起動
sudo systemctl restart nginx
sudo systemctl restart mysql

echo "Performance tuning completed"
```

## まとめ

第6章で実装したプロジェクト：

1. **LAMP環境**: WordPress動作環境の完全構築
2. **Docker環境**: コンテナ化アプリケーション管理
3. **監視システム**: Prometheus/Grafanaによる可視化
4. **ログ解析**: ELKスタックとFluentd
5. **CI/CD**: 自動デプロイパイプライン
6. **セキュリティ**: ファイアウォールとSSL
7. **バックアップ**: 統合バックアップシステム
8. **最適化**: パフォーマンスチューニング

これらのプロジェクトは、実際の運用環境で使用できる実践的な内容です。各プロジェクトを順次実装することで、総合的なインフラ管理スキルが身につきます。