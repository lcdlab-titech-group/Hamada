# Handrail-sensor

<h2>AnalysisSystem.py</h2>
半リアルタイム半自動分析？ビジュアライズ？スクリプトです。(一応動くが見た目微妙)

<h2>getSensorData_402.py</h2>
402手すりセンサからデータを取得するスクリプトです。
config.iniはこのスクリプトの設定ファイルです。

-------------------
入力例
「python getSensorData_402.py」でデータ取得（取得値は表示されない）
「python getSensorData_402.py -v」でデバッグモードになり取得値をリアルタイム表示
  
<h2>grip_vel.py</h2>
402手すりセンサからデータを取得し、昇降速度を算出するデモ用スクリプトです。

<h2>TestOperation.py</h2>
402手すりセンサでデバッグコマンドを手軽に試す用スクリプトです。
必要に応じてコメントアウトしてください。コマンドの意味については下記の取扱説明書.pdfを参照してください。

<h2>手摺センサシステムｖｅｒ4.1(HDL-V4.1sys)取扱説明書.pdf</h2>
手すりセンサの取扱説明書です。
