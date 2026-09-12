# 世田谷区 Access Atlas（GitHub 便携版）

先完整解压项目，安装 Python 3.10 或更高版本。Windows 双击 **Start Access Atlas.cmd**；macOS / Linux 在项目目录运行 `sh start.sh`。浏览器会自动打开，默认使用 8765 端口，端口被占用时自动选择空闲端口。保持终端窗口开启，结束时按 Ctrl+C。目录可移动、改名，支持中文和空格路径。不需要 API key，也不需要重新下载城市数据。首次进入某类 POI 的自定义参数计算时，需要读取该类较大的本地距离表；之后调节通常更快。

## 你可以做什么

- 在真实世田谷区路网上查看可达性：15,752 条展示街段；路由使用包含周边缓冲区的 28,000 个节点、41,869 条边。
- 选择五类 POI：Healthcare、Education、Daily shopping、Parks & recreation、Civic services。总计 6,090 个 POI，包含周边设施；其中区内 2,134 个。
- 在 Indicator library 中直接选择 17 个指标。内置 69 张预计算图：每类 POI 13 种，以及 4 种不依赖 POI 类别的网络指标。
- 调节距离衰减、范围、步行速度、竞争、数量强调、机会门槛、难到达机会比例、街道样点聚合等参数。参数有英文物理解释；没有作用的参数会禁用。
- 符合经典指标族的参数会出现原指标名称；其他有效组合显示 Custom accessibility。
- 缩放、平移、选择街道看原始数值；收回侧边栏。POI 标记在缩放级别 14 及以上显示，避免远视图过密。
- 查看颜色图例和实际数值。默认数值越高越红、数值越低越蓝。点击顶部或图例中的 **Colors**，可选择 12 套色带、反转色带或自定义三种颜色（支持 HEX 输入），设置会保存在当前浏览器中。时间成本指标也按数值着色，高值代表时间更长。更换色带只更新地图和图例，不改变数值。颜色按当前 5%–95% 分位区间显示，跨配置比较时请看数值及单位。

## 配置说明

在网站中打开 **Indicator library → Full parameter guide**。完整英文说明在 `dist/guide.html`；数值配置可下载为 `dist/data/indicator-guide.csv` 和 `dist/data/presets.json`。CSV 中 radius=65 是界面约定的无穷范围；p=±5 是最大/最小聚合的界面约定。

## 真实数据与假设

- 路网、POI、行政边界为 OpenStreetMap，快照时间 2026-09-12 13:27 UTC。原始来源查询见 `scripts/fetch_data.py`。
- 采用公共街道骨架，保留住宅道路，去除形状点但保留几何长度。没有纳入所有小巷、服务道路、独立步道。只保留最大连通分量，并去除不影响节点间路径的闭合二度环。
- POI 通过最长 350 米的直线连接接入最近保留路口，不是精细的设施入口路由。路径没有交通灯、坡度、开放时间的修正。
- 设施权重 1–4 是公开说明的类型情景权重，不是实测容量。竞争需求假设为区内每个保留路口一个需求单位，不是人口数据。
- POI 指标默认两个端点取样，超过 200 米加中点。网络深度、接近性、调和中心性则将原生节点中心性映射为两个端点的聚合值。边介数直接输出原始边值。
- 网络指标没有冒称空间句法的 NAIN、NACH 或 DepthmapX 复现。
- GSI 淡色底图的 29 张瓦片已经内置，可以离线查看。近距离缩放会放大最高 13 级底图，街道矢量仍保持清晰；缓冲区域之外没有无限范围的离线底图。

## 核查与复现

- `dist/model.mjs`：统一的分布、分位读取与街道聚合计算，不按 POI 指标名称分派计算。
- `dist/worker.js`：后台计算；新参数真正计算数值，旧任务完成后不会覆盖更新的参数。
- `scripts/precompute_presets.py`：独立的经典公式实现，预计算 69 张表面。
- `scripts/verify.mjs`：随机数学样例、真实街道抽查、参数单调性与名称匹配检查。
- `audit/verification.json`：实际执行的核查记录。
- `scripts/prepare_data.py`：原始路网处理、全部最短距离与精确加权边介数。

网站运行只需要 Python 3 标准库；浏览器计算不需要 Python 数学库。重建数据才需要安装 `requirements-rebuild.txt` 中的 numpy、scipy、shapely、networkx、igraph；运行网页无需安装这些包。源数据与计算结果约占数百 MB，这是实际预计算距离表的体积。

## 来源

OpenStreetMap contributors（ODbL 1.0）：https://www.openstreetmap.org/copyright 。底图：国土地理院 https://maps.gsi.go.jp/development/ 。Leaflet 1.9.4 的许可随 `dist/vendor/Leaflet-LICENSE.txt` 提供。既有指标的原始方法文献与限制详见网页方法说明及参数指南。

## 上传 GitHub / 分享

- 上传本目录中的全部内容作为仓库根目录，保留 `dist/data/routes/` 和隐藏配置文件。推荐使用 GitHub Desktop 或 Git。不要把整个 ZIP 当成源代码文件上传。
- 便携版约 613 MiB，距离表分块最大 20 MiB。无需 Git LFS，别人可直接 Download ZIP 或 clone 获取完整数据。网页按清单校验并读取分块，不改变原始距离或结果。
- 不要只复制 HTML：运行需要完整目录。双击根目录 `index.html` 会看到启动说明。浏览器安全机制要求通过本地 HTTP 服务加载模块和计算数据。
- 要在线展示，可在 GitHub 仓库 Settings → Pages 中选择分支和根目录；根页面自动转到 `dist/`，支持任意仓库名及子路径。实际上传和启用 Pages 由仓库所有者操作。
- 新版本保留最新的自选配色、紧凑透明标题、Median street、等宽图例与计算说明，以及向下收起功能。
- 英文运行、验证、重建文档见 [README.md](README.md)，第三方数据与许可说明见 [DATA_SOURCES.md](DATA_SOURCES.md)。
