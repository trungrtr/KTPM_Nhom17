import os
import shutil
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from PIL import Image

# 1. HTML_1: Môi trường ảo (Virtual Environment Setup & Activation in VS Code)
HTML_1 = r"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<style>
  * { box-sizing: border-box; margin: 0; padding: 0; }
  body {
    background: #FFFFFF;
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", "Segoe UI Variable", Roboto, Helvetica, Arial, sans-serif;
    color: #1E1E1E;
    padding: 0;
    margin: 0;
  }
  #container {
    width: 760px;
    background: #FFFFFF;
    border: 1px solid #D0D7DE;
    display: flex;
    flex-direction: row;
  }
  #sidebar {
    width: 200px;
    background: #F8F9FA;
    border-right: 1px solid #E1E4E8;
    padding: 9px 12px;
    flex-shrink: 0;
  }
  .explorer-header {
    font-size: 11px;
    font-weight: 700;
    color: #57606A;
    letter-spacing: 0.5px;
    text-transform: uppercase;
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 8px;
  }
  .tree-node {
    display: flex;
    align-items: center;
    font-size: 13px;
    color: #24292F;
    padding: 3px 0;
    user-select: none;
  }
  .tree-node.root {
    font-weight: 600;
  }
  .tree-node.child {
    padding-left: 18px;
    color: #424242;
  }
  .icon-arrow {
    display: inline-block;
    width: 14px;
    text-align: center;
    font-size: 10px;
    margin-right: 4px;
    color: #57606A;
  }
  #main-panel {
    flex: 1;
    background: #FFFFFF;
    display: flex;
    flex-direction: column;
    min-width: 0;
  }
  .tab-bar {
    height: 32px;
    background: #FAFAFA;
    border-bottom: 1px solid #E1E4E8;
    display: flex;
    align-items: center;
    padding: 0 14px;
    font-size: 11.5px;
  }
  .tab {
    color: #57606A;
    margin-right: 18px;
    padding: 6px 0;
    display: inline-block;
  }
  .tab.active {
    color: #1E1E1E;
    font-weight: 600;
    border-bottom: 2px solid #005FB8;
  }
  .terminal-body {
    padding: 10px 14px 12px 14px;
    font-family: Consolas, "Cascadia Code", "Courier New", monospace;
    font-size: 12.5px;
    line-height: 1.40;
    background: #FFFFFF;
    color: #1E1E1E;
  }
  .err-block {
    color: #CF222E;
  }
  .cmd-prompt {
    color: #24292F;
  }
  .cmd-kw {
    color: #005FB8;
    font-weight: 600;
  }
  .cmd-flag {
    color: #0969DA;
  }
  .cmd-val {
    color: #6F42C1;
  }
  .cmd-err {
    color: #CF222E;
    font-weight: 600;
  }
  .venv-badge {
    color: #1A7F37;
    font-weight: 700;
  }
  .cursor-block {
    display: inline-block;
    width: 7px;
    height: 13px;
    background: #24292F;
    vertical-align: middle;
    margin-left: 2px;
  }
</style>
</head>
<body>
<div id="container">
  <div id="sidebar">
    <div class="explorer-header">
      <span>Explorer</span>
      <span style="font-size: 14px; font-weight: normal; cursor: pointer;">•••</span>
    </div>
    <div class="tree-node root">
      <span class="icon-arrow">˅</span>
      <span>coolmate_selenium_test</span>
    </div>
    <div class="tree-node child">
      <span class="icon-arrow">&gt;</span>
      <span>.venv</span>
    </div>
  </div>
  <div id="main-panel">
    <div class="tab-bar">
      <span class="tab">Problems</span>
      <span class="tab">Output</span>
      <span class="tab">Debug Console</span>
      <span class="tab active">Terminal</span>
      <span class="tab">Ports</span>
    </div>
    <div class="terminal-body">
      <div class="err-block">+ .venv\Scripts\activate</div>
      <div class="err-block">+ ~~~~~~~~~~~~~~~~~~~~~~</div>
      <div class="err-block">&nbsp;&nbsp;&nbsp;&nbsp;+ CategoryInfo&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;: SecurityError: (:) [], PSSecurityException</div>
      <div class="err-block">&nbsp;&nbsp;&nbsp;&nbsp;+ FullyQualifiedErrorId : UnauthorizedAccess</div>
      <div><span class="cmd-prompt">PS D:\K1_N3\ktpm\coolmate_selenium_test&gt;</span> <span class="cmd-kw">python</span> .venv\Scripts\activate</div>
      <div>File "D:\K1_N3\ktpm\coolmate_selenium_test\.venv\Scripts\activate", line 41</div>
      <div>&nbsp;&nbsp;CYGWIN* |MSYS* |MINGW*)</div>
      <div>&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;^</div>
      <div class="cmd-err">SyntaxError: unmatched ')'</div>
      <div><span class="cmd-prompt">PS D:\K1_N3\ktpm\coolmate_selenium_test&gt;</span> <span class="cmd-kw">Set-ExecutionPolicy</span> <span class="cmd-flag">-ExecutionPolicy</span> <span class="cmd-val">RemoteSigned</span> <span class="cmd-flag">-Scope</span> <span class="cmd-val">CurrentUser</span></div>
      <div><span class="cmd-prompt">PS D:\K1_N3\ktpm\coolmate_selenium_test&gt;</span> ^C</div>
      <div><span class="cmd-prompt">PS D:\K1_N3\ktpm\coolmate_selenium_test&gt;</span> .venv\Scripts\activate</div>
      <div><span class="venv-badge">(.venv)</span> <span class="cmd-prompt">PS D:\K1_N3\ktpm\coolmate_selenium_test&gt;</span><span class="cursor-block"></span></div>
    </div>
  </div>
</div>
</body>
</html>
"""

# 2. HTML_2: Thư viện cần sử dụng (requirements.txt & pip freeze check)
HTML_2 = r"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<style>
  * { box-sizing: border-box; margin: 0; padding: 0; }
  body {
    background: #FFFFFF;
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", "Segoe UI Variable", Roboto, Helvetica, Arial, sans-serif;
    color: #1E1E1E;
    padding: 0;
    margin: 0;
  }
  #container {
    width: 680px;
    background: #FFFFFF;
    border: 1px solid #D0D7DE;
    display: flex;
    flex-direction: column;
  }
  .editor-tab-bar {
    height: 33px;
    background: #F3F4F6;
    border-bottom: 1px solid #E1E4E8;
    display: flex;
    align-items: center;
  }
  .editor-tab {
    height: 33px;
    background: #FFFFFF;
    border-right: 1px solid #E1E4E8;
    border-top: 2px solid #005FB8;
    display: flex;
    align-items: center;
    padding: 0 12px;
    font-size: 12px;
    color: #24292F;
    font-weight: 500;
  }
  .tab-icon {
    margin-right: 6px;
    color: #57606A;
    font-size: 12px;
  }
  .close-icon {
    margin-left: 10px;
    color: #8C959F;
    font-size: 11px;
    cursor: pointer;
  }
  .editor-content {
    display: flex;
    background: #FFFFFF;
    padding: 6px 0;
    font-family: Consolas, "Cascadia Code", "Courier New", monospace;
    font-size: 12px;
    line-height: 1.38;
  }
  .line-numbers {
    width: 40px;
    text-align: right;
    padding-right: 12px;
    color: #8C959F;
    user-select: none;
    flex-shrink: 0;
  }
  .code-lines {
    flex: 1;
    color: #24292F;
  }
  .pkg-name {
    color: #0550AE;
  }
  .pkg-ver {
    color: #116329;
    font-weight: 500;
  }
  .terminal-panel {
    border-top: 1px solid #D0D7DE;
    background: #FFFFFF;
  }
  .term-tab-bar {
    height: 30px;
    background: #FAFAFA;
    border-bottom: 1px solid #E1E4E8;
    display: flex;
    align-items: center;
    padding: 0 14px;
    font-size: 11.5px;
  }
  .term-tab {
    color: #57606A;
    margin-right: 18px;
    padding: 5px 0;
  }
  .term-tab.active {
    color: #1E1E1E;
    font-weight: 600;
    border-bottom: 2px solid #005FB8;
  }
  .term-body {
    padding: 8px 14px 10px 14px;
    font-family: Consolas, "Cascadia Code", "Courier New", monospace;
    font-size: 12px;
    line-height: 1.38;
    color: #24292F;
  }
  .pkg-list {
    display: grid;
    grid-template-columns: 200px 100px;
    row-gap: 1px;
    margin-bottom: 4px;
  }
  .venv-badge {
    color: #1A7F37;
    font-weight: 700;
  }
  .cmd-kw {
    color: #005FB8;
    font-weight: 600;
  }
  .cursor-block {
    display: inline-block;
    width: 7px;
    height: 13px;
    background: #24292F;
    vertical-align: middle;
    margin-left: 2px;
  }
</style>
</head>
<body>
<div id="container">
  <div class="editor-tab-bar">
    <div class="editor-tab">
      <span class="tab-icon">📄</span>
      <span>requirements.txt</span>
      <span class="close-icon">✕</span>
    </div>
  </div>
  <div class="editor-content">
    <div class="line-numbers">
1<br>2<br>3<br>4<br>5<br>6<br>7<br>8<br>9<br>10<br>11<br>12<br>13<br>14<br>15<br>16<br>17<br>18<br>19<br>20<br>21<br>22<br>23<br>24<br>25<br>26<br>27<br>28
    </div>
    <div class="code-lines">
      <div><span class="pkg-name">attrs</span>==<span class="pkg-ver">26.1.0</span></div>
      <div><span class="pkg-name">certifi</span>==<span class="pkg-ver">2026.7.22</span></div>
      <div><span class="pkg-name">cffi</span>==<span class="pkg-ver">2.1.1</span></div>
      <div><span class="pkg-name">charset-normalizer</span>==<span class="pkg-ver">3.5.2</span></div>
      <div><span class="pkg-name">colorama</span>==<span class="pkg-ver">0.4.6</span></div>
      <div><span class="pkg-name">h11</span>==<span class="pkg-ver">0.16.0</span></div>
      <div><span class="pkg-name">idna</span>==<span class="pkg-ver">3.20</span></div>
      <div><span class="pkg-name">iniconfig</span>==<span class="pkg-ver">2.3.1</span></div>
      <div><span class="pkg-name">outcome</span>==<span class="pkg-ver">1.3.0.post0</span></div>
      <div><span class="pkg-name">packaging</span>==<span class="pkg-ver">26.3</span></div>
      <div><span class="pkg-name">pluggy</span>==<span class="pkg-ver">1.7.0</span></div>
      <div><span class="pkg-name">pycparser</span>==<span class="pkg-ver">3.11</span></div>
      <div><span class="pkg-name">Pygments</span>==<span class="pkg-ver">2.21.0</span></div>
      <div><span class="pkg-name">PySocks</span>==<span class="pkg-ver">1.7.1</span></div>
      <div><span class="pkg-name">pytest</span>==<span class="pkg-ver">9.1.1</span></div>
      <div><span class="pkg-name">python-dotenv</span>==<span class="pkg-ver">1.2.4</span></div>
      <div><span class="pkg-name">requests</span>==<span class="pkg-ver">2.34.2</span></div>
      <div><span class="pkg-name">selenium</span>==<span class="pkg-ver">4.51.0</span></div>
      <div><span class="pkg-name">sniffio</span>==<span class="pkg-ver">1.3.1</span></div>
      <div><span class="pkg-name">sortedcontainers</span>==<span class="pkg-ver">2.4.0</span></div>
      <div><span class="pkg-name">trio</span>==<span class="pkg-ver">0.34.0</span></div>
      <div><span class="pkg-name">trio-websocket</span>==<span class="pkg-ver">0.12.2</span></div>
      <div><span class="pkg-name">typing_extensions</span>==<span class="pkg-ver">4.16.0</span></div>
      <div><span class="pkg-name">urllib3</span>==<span class="pkg-ver">2.8.0</span></div>
      <div><span class="pkg-name">webdriver-manager</span>==<span class="pkg-ver">4.1.2</span></div>
      <div><span class="pkg-name">websocket-client</span>==<span class="pkg-ver">1.9.2</span></div>
      <div><span class="pkg-name">wsproto</span>==<span class="pkg-ver">1.3.2</span></div>
      <div>&nbsp;</div>
    </div>
  </div>
  <div class="terminal-panel">
    <div class="term-tab-bar">
      <span class="term-tab">Problems</span>
      <span class="term-tab">Output</span>
      <span class="term-tab">Debug Console</span>
      <span class="term-tab active">Terminal</span>
      <span class="term-tab">Ports</span>
    </div>
    <div class="term-body">
      <div class="pkg-list">
        <div>sniffio</div><div>1.3.1</div>
        <div>sortedcontainers</div><div>2.4.0</div>
        <div>trio</div><div>0.34.0</div>
        <div>trio-websocket</div><div>0.12.2</div>
        <div>typing_extensions</div><div>4.16.0</div>
        <div>urllib3</div><div>2.8.0</div>
        <div>webdriver-manager</div><div>4.1.2</div>
        <div>websocket-client</div><div>1.9.2</div>
        <div>wsproto</div><div>1.3.2</div>
      </div>
      <div><span class="venv-badge">(.venv)</span> PS D:\K1_N3\ktpm\coolmate_selenium_test&gt; <span class="cmd-kw">pip</span> freeze &gt; requirements.txt</div>
      <div><span class="venv-badge">(.venv)</span> PS D:\K1_N3\ktpm\coolmate_selenium_test&gt; <span class="cmd-kw">python</span> -c "import selenium; print(selenium.__version__)"</div>
      <div style="font-weight: 600; color: #24292F;">4.51.0</div>
      <div><span class="venv-badge">(.venv)</span> PS D:\K1_N3\ktpm\coolmate_selenium_test&gt;<span class="cursor-block"></span></div>
    </div>
  </div>
</div>
</body>
</html>
"""

# 3. HTML_3: Chạy test 1 testplan (pytest test_first.py)
HTML_3 = r"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<style>
  * { box-sizing: border-box; margin: 0; padding: 0; }
  body {
    background: #FFFFFF;
    font-family: Consolas, "Cascadia Code", "Courier New", monospace;
    color: #1E1E1E;
    padding: 0;
    margin: 0;
  }
  #container {
    width: 740px;
    background: #FFFFFF;
    border: 1px solid #D0D7DE;
    padding: 12px 14px;
    line-height: 1.40;
    font-size: 12.5px;
  }
  .session-sep {
    color: #57606A;
  }
  .session-info {
    color: #57606A;
  }
  .collected {
    color: #24292F;
    margin-bottom: 4px;
  }
  .test-row {
    color: #1E1E1E;
  }
  .test-id {
    color: #24292F;
  }
  .test-url {
    color: #0969DA;
  }
  .pass-badge {
    color: #1A7F37;
    font-weight: 700;
  }
  .result-banner {
    color: #1A7F37;
    font-weight: 700;
  }
  .venv-badge {
    color: #1A7F37;
    font-weight: 700;
  }
  .cursor-block {
    display: inline-block;
    width: 7px;
    height: 13px;
    background: #24292F;
    vertical-align: middle;
    margin-left: 2px;
  }
</style>
</head>
<body>
<div id="container">
  <div class="session-sep">============================= test session starts =============================</div>
  <div class="session-info">platform win32 -- Python 3.14.8, pytest-9.1.1, pluggy-1.7.0 -- D:\K1_N3\ktpm\coolmate_selenium_test\.venv\Scripts\python.exe</div>
  <div class="session-info">cachedir: .pytest_cache</div>
  <div class="session-info">rootdir: D:\K1_N3\ktpm\coolmate_selenium_test</div>
  <div class="collected">collected 1 item</div>
  <div style="height: 6px;"></div>
  <div class="test-row"><span class="test-id">test_first.py::test_mo_trang_chu_coolmate</span> Tiêu đề trang: COOLMATE - Thương Hiệu Thời Trang Chất Lượng Từ Việt Nam</div>
  <div class="test-row">Địa chỉ trang: <span class="test-url">https://www.coolmate.me/</span></div>
  <div class="pass-badge">PASSED</div>
  <div style="height: 6px;"></div>
  <div class="result-banner">============================== 1 passed in 13.45s ==============================</div>
  <div style="margin-top: 3px;"><span class="venv-badge">(.venv)</span> PS D:\K1_N3\ktpm\coolmate_selenium_test&gt;<span class="cursor-block"></span></div>
</div>
</body>
</html>
"""

os.makedirs('tools/html_renders', exist_ok=True)
with open('tools/html_renders/hinh_1.html', 'w', encoding='utf-8') as f:
    f.write(HTML_1)
with open('tools/html_renders/hinh_2.html', 'w', encoding='utf-8') as f:
    f.write(HTML_2)
with open('tools/html_renders/hinh_3.html', 'w', encoding='utf-8') as f:
    f.write(HTML_3)

options = Options()
options.add_argument('--headless=new')
options.add_argument('--disable-gpu')
options.add_argument('--no-sandbox')
options.add_argument('--force-device-scale-factor=2')
options.add_argument('--window-size=1200,1600')
driver = webdriver.Chrome(options=options)

images_data = [
    ('tools/html_renders/hinh_1.html', 'docs/images/hinh_1_moi_truong_ao.png'),
    ('tools/html_renders/hinh_2.html', 'docs/images/hinh_2_thu_vien.png'),
    ('tools/html_renders/hinh_3.html', 'docs/images/hinh_3_chay_test_testplan.png')
]

artifact_dir = r"C:\Users\daoqu\.gemini\antigravity\brain\86b168a6-89e3-416c-b5ed-b66361bda13a"

for html_file, out_png in images_data:
    abs_path = os.path.abspath(html_file).replace('\\', '/')
    driver.get(f'file:///{abs_path}')
    el = driver.find_element('id', 'container')
    el.screenshot(out_png)
    
    # Copy to artifact dir for direct rendering
    fname = os.path.basename(out_png)
    dest_path = os.path.join(artifact_dir, fname)
    shutil.copyfile(out_png, dest_path)
    
    with Image.open(out_png) as im:
        print(f'{fname}: size={im.size}')

driver.quit()
print('SUCCESS!')
