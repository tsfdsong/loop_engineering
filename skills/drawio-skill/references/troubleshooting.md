# Troubleshooting —— 常见错误

输出不对劲（渲染、导出、布局、边）或 CLI 调用失败时读本文。多数行有一行修复。

| 错误 | 修复 |
|---------|-----|
| 缺 `id="0"` 与 `id="1"` 根 cell | `<root>` 顶部永远包含这两个 |
| 形状没连上 | 边的 `source`/`target` 必须匹配既有形状的 `id` |
| 自闭合 edge `mxCell`（`<mxCell ... edge="1" />`） | 用带 `<mxGeometry relative="1" as="geometry" />` 子元素的展开形式——自闭合边不渲染 |
| XML 注释里有 `--` | XML 规范非法——用单个连字符或改写 |
| `value` 中特殊字符 | 用 XML 实体：`&amp;` `&lt;` `&gt;` `&quot;` |
| 标签文字里的字面 `\n` | `value` 属性内换行用 `&#xa;` |
| 形状重叠 | 间距随复杂度伸缩（200–350px）；留布线走廊 |
| 边穿过形状 | 加 waypoint、分散出入点、或加大间距 |
| 箭头叠在拐弯上 | 到目标前的末段边必须 ≥20px——加大间距或加 waypoint |
| 迭代循环不停 | 5 轮后建议用户在 draw.io 桌面版打开 .drawio 细调 |
| `brew install --cask drawio` 后 `command not found: draw.io` | Homebrew 装的二进制叫 `drawio`（无点）。用 `drawio --version`，不是 `draw.io --version`。带点的名字只在 `.app` 包内（`/Applications/draw.io.app/Contents/MacOS/draw.io`）和 Windows（`draw.io.exe`）存在。 |
| macOS 找不到导出命令 | 试完整路径 `/Applications/draw.io.app/Contents/MacOS/draw.io` |
| Vision 返回 "Unable to resize image — dimensions exceed the 2576x2576px limit" | 预览 PNG 超出 Claude vision API 上限。改用 `--width 2000` 重导出，不要 `-s 2`（flag 是 `--width`，没有短形式 `-w`——传 `-w 2000` 会静默弄坏输入文件解析，drawio 报 "input file/directory not found"）。细高图仍超限就用 `--height 2000`。 |
| Linux：headless 下空白/报错输出 | 命令前加 `xvfb-run -a` |
| Linux：`--no-sandbox` 放在输入文件前（被当文件名解析） | 把 `--no-sandbox` 移到命令**最末尾**（drawio-desktop#249、#1056） |
| Linux：`Failed to get 'appData' path` / `Home directory not accessible` | 调 drawio 前 `export HOME=/tmp`（drawio-desktop#127） |
| Linux 服务器：段错误 / EGL / MESA `failed to load driver` | 加 `--disable-gpu`（无 GPU 时抑制 Chromium GL 初始化） |
| PDF 导出失败 | 确认 Chromium 可用（draw.io 桌面版自带） |
| CLI 导出背景色不对 | 已知 CLI bug；加 `--transparent` 或经 style 设背景 |
| Vision 对草稿 PNG 返回 400 "Could not process image" | 去掉 `-e` 重导预览（issue #8）。根因是 `-e` PNG 的 IEND chunk 截断，不是 `zTXt` chunk 本身——但预览跳过 `-e` 是最简修法。 |
| 最终 `-e` PNG 在看图器 / vision API 打不开 | 跑 `python3 <this-skill-dir>/scripts/repair_png.py <path>`。draw.io CLI 产出的 `-e` PNG 在 IEND 处缺 8 字节。SVG/PDF 不受影响。 |
| WSL2：找不到 `drawio` / `draw.io` | CLI 在 Windows 侧。经 `/mnt/c` 用 Windows 桌面 exe：`"/mnt/c/Program Files/draw.io/draw.io.exe"`（或用户级 `"/mnt/c/Users/<you>/AppData/Local/Programs/draw.io/draw.io.exe"`）。 |
| WSL2：打开导出文件报 `/mnt/c/...` 路径失败 | `cmd.exe` 解析不了 WSL 路径——先转换：`cmd.exe /c start "" "$(wslpath -w diagram.drawio.png)"`。`start` 后的空 `""` 是（必需的）窗口标题。 |
| 浏览器 URL 打开是空白图（Windows/WSL2） | `cmd.exe` 的 `start` 把 `&` 当分隔符、丢弃 `#` 之后的一切——`#R…`/`#create=…` fragment（整个图）就没了。绝不把 URL 直接传给 `start`。写一个 `.url` 快捷方式文件、打开它（见下方 "WSL2 / Windows"）。 |

## WSL2 / Windows 专项

**定位 CLI。** 用 `grep -qi microsoft /proc/version` 探测 WSL2。WSL2 上导出 CLI 是 Windows 桌面 exe，经 `/mnt/c` 访问（路径含空格，要加引号）：

```bash
"/mnt/c/Program Files/draw.io/draw.io.exe" --version
# per-user install fallback:
"/mnt/c/Users/$USER/AppData/Local/Programs/draw.io/draw.io.exe" --version
```

**打开文件。** 先把 WSL 路径转成 Windows 路径；`cmd.exe` 跟不了 `/mnt/c/...`：

```bash
cmd.exe /c start "" "$(wslpath -w diagram.drawio.png)"
```

**打开浏览器兜底 URL。** `cmd.exe /c start` 会剥掉 URL fragment（`&` 结束命令、`#…` 被丢）——而 fragment 承载整个图。改写 `.url` 快捷方式再打开，URL 才能完整存活：

```bash
URL=$(python3 <this-skill-dir>/scripts/encode_drawio_url.py --edit diagram.drawio)
TMP=$(mktemp --suffix=.url)
printf '[InternetShortcut]\r\nURL=%s\r\n' "$URL" > "$TMP"
cmd.exe /c start "" "$(wslpath -w "$TMP")"
```

原生 Windows 同样适用 `.url` 文件技巧（`start "" "%TEMP%\d.url"`）。
macOS/Linux 直接 `open "$URL"` / `xdg-open "$URL"`——无需 workaround。
