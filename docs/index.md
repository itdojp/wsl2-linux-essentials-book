---
layout: book
title: "WSL2 Linux実践ガイド"
---

# WSL2 Linux実践ガイド

このページは、`illustrated-linux-basics-book` の次のステップとして、WSL2 上で実践的な Linux スキルを習得するための公開版の入口です。

## 本書の位置づけ

- **前提書籍**: [illustrated-linux-basics-book](https://itdojp.github.io/illustrated-linux-basics-book/)（初級）
- **本書**: 実践的な Linux スキルの習得（中級）
- **次の書籍**: [linux-infra-textbook2](https://itdojp.github.io/linux-infra-textbook2/)（上級）

### この本を読み終えるとできること

- Windows 上の WSL2 環境で、Ubuntu を使った開発・検証ができる。
- 基本的なファイル操作、テキスト処理、プロセス／サービス管理、ネットワーク確認をコマンドラインで行える。
- 簡単なシェルスクリプトを書き、日常作業を自動化できる。
- 学習用の LAMP 環境を構築し、WordPress サイトを立ち上げて検証できる。

## 読み方ガイド

- illustrated-linux-basics-book を読み終えたばかりの読者は、第0章で WSL2 のセットアップを完了させたあと、第1章から順に読み進める方法がおすすめです。
- Linux の基本コマンドには慣れており、テキスト処理やプロセス管理を強化したい読者は、第1章を軽く確認したうえで、第2章・第3章を重点的に読むと効率的です。
- ネットワークや Web サーバー構築に関心が高い読者は、第4章と第6章を中心に読み、必要に応じて前半の章へ戻って基礎操作を復習できます。
- シェルスクリプトによる自動化を試したい読者は、第1〜3章でコマンドと環境に慣れてから第5章の演習へ進むと、日常作業をスクリプト化する流れをつかみやすくなります。

## 所要時間
- 通読: 約 0.5〜1 時間（本文量ベースの概算。400〜600 文字/分換算）
- 章内のコマンドを実行しながら進める場合は、環境構築や演習の進度により変動する。

## 目次

- [第0章 WSL2セットアップ]({{ site.baseurl }}/chapter0/)
- [第1章 Linuxの世界への第一歩]({{ site.baseurl }}/chapter1/)
- [第2章 テキスト処理の基本]({{ site.baseurl }}/chapter2/)
- [第3章 プロセスとサービス管理]({{ site.baseurl }}/chapter3/)
- [第4章 ネットワークの基礎]({{ site.baseurl }}/chapter4/)
- [第5章 シェルスクリプト入門]({{ site.baseurl }}/chapter5/)
- [第6章 WordPress構築]({{ site.baseurl }}/chapter6/)

## 概要

本書は、基礎を学んだ読者が WSL2 環境で手を動かしながら、実践的な Linux スキルへ段階的に進むための教材です。

### 想定読者

- illustrated-linux-basics-bookを終えた方
- Linuxの基本コマンドは知っているが、実践経験が少ない方
- WindowsでLinux開発環境を構築したい方
- Webサーバー構築に興味がある方

### 前提知識

- 基本的なLinuxコマンド（ls, cd, cp, mv等）
- ファイルとディレクトリの概念
- テキストエディタの基本操作

### 学習成果

- **段階的学習**: 各章に学習目標と到達点を明記
- **実践重視**: すべてのコマンドが実行可能
- **エラー対処**: よくあるトラブルと解決法を記載
- **プロジェクト型**: 最終章でWordPressサイトを構築

## ライセンス

本書は **Creative Commons BY-NC-SA 4.0** ライセンスで公開されています。  
教育・研究・個人学習での利用は可能ですが、商用利用には事前の許諾が必要です。

詳細なライセンス条件: [it-engineer-knowledge-architecture/LICENSE.md](https://github.com/itdojp/it-engineer-knowledge-architecture/blob/main/LICENSE.md)

お問い合わせ  
株式会社アイティードゥ（ITDO Inc.）  
Email: [knowledge@itdo.jp](mailto:knowledge@itdo.jp)

---

**著者:** 株式会社アイティードゥ  
**バージョン:** 2.0.1  
**最終更新:** 2026-03-02
{% include page-navigation.html %}
