# 一车之地 · Footprint

> 一辆车要占多大地方：按尺寸选车，看商场车位停不停得下、开门够不够，比座舱的轴距与车长之比，再找同级的替代车型。收录国内 **1693 款车系、12550 款具体配置** 的官方参配与车主口碑评分。界面沿用 [3901646.xyz](https://3901646.xyz) 的日间纸风格。

## 重新构建

```bash
npm install          # 只用于构建期编译 Tailwind CSS
npm run build        # 编译 CSS，再由 build_html.py 内嵌数据和样式，生成 index.html
```

页面不再依赖 Tailwind Play CDN 和 FontAwesome CDN：样式在构建时编译并内嵌，图标是内嵌 SVG。筛选条件、选中车型和对比列表会写进网址，可以直接分享。

## 主要功能

- **我的车位**：填入自家车位的长、宽和限高（或选常见预设），每张卡片标出“停得下 / 偏紧 / 超长 / 超宽 / 超高 / 开门难”，可以只看停得下的车。车位尺寸保存在本机。
- **尺寸对比**：最多 4 款车按同一比例叠在一起（俯视看长和宽，侧视看高），直接标出车长差、车宽差、车高差；下方差距表以基准车为零点，每项给出差值和差距条，可切换基准、只看有差别的项、复制对比链接。
- **场景预设**：每个场景只改自己负责的条件，你拖好的尺寸范围不会被清掉；再点一次取消。
- **已生效条件**：列表上方列出所有生效的条件，可单独去掉。

[![Official Domain](https://img.shields.io/badge/Live-car.3901646.xyz-0284c7?style=flat-square)](https://car.3901646.xyz)
[![GitHub Pages](https://img.shields.io/badge/Mirror-GitHub%20Pages-2563eb?style=flat-square&logo=github)](https://cf3901646.github.io/car-dimension-filter/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg?style=flat-square)](LICENSE)
[![Zero Dependency](https://img.shields.io/badge/Architecture-Single%20HTML%20SPA-10b981?style=flat-square)](#)
[![Data Count](https://img.shields.io/badge/Database-1693%20Series%20%2F%2012550%20Specs-6366f1?style=flat-square)](#)

---

## 🌟 核心特色与创新功能

### 1. 🅿️ 商场地下标准车位体检 & 机械立体车位兼容度
- **国家标准尺寸真实比例映射**：依据国家住建部《车库建筑设计规范》（JGJ 100-2015）及主流商业综合体（万象城、大悦城、山姆、龙湖天街等）实测标准，以 **长 5300mm × 宽 2500mm** 为标准基准，在 2D 俯视底盘工程透视蓝图（SVG）中绘制真实比例车位地坪、反光框线与防撞橡胶限位器；
- **两侧开门余量（Door Clearance）双向引线**：实时根据选定车型车宽计算单侧开门空间 $\frac{2500 - \text{车宽}}{2}$：
  - **绿色（$\ge 320\text{mm}$）**：开门充裕，上下车从容自如；
  - **深灰（$280\sim 320\text{mm}$）**：标准余量，正常开门；
  - **橙红高亮（$< 280\text{mm}$）**：车身过宽（$> 1940\text{mm}$），提示“开门狭窄易碰门”；
- **机械立体车位通行雷达**：自动校核限长 5000mm、限宽 1850mm（宽体 1900mm）硬性警戒线，智能给出“🟢 通行无阻”、“🟡 需1.9m宽体车位”或“🔴 超标慎选”。

### 2. 📐 空间“得房率”指标（轴长比测算）
- **汽车人机工程学公式**：
  $$\text{空间得房率} = \frac{\text{轴距 (Wheelbase)}}{\text{车长 (Length)}} \times 100\%$$
- **行业级换算与公摊透视**：
  - 乘用车前后必须预留防撞吸能盒、发动机/电驱总成与后备厢（约 1.8 至 2.1 米硬性公摊）；
  - **每 1% 得房率差异 $\approx$ 约 50mm $\approx$ 整整 1 拳后排腿部空间**！
  - **👑 超高得房率（$\ge 61.5\%$）**：短前后悬、大座舱设计，车内公摊极少，后排宽绰；
  - **💎 黄金均衡座舱（$59.0\%$ 至 $61.4\%$）**：家用黄金平衡比例，兼顾碰撞吸能与实用座舱；
  - **🏎️ 运动操控取向（$< 59.0\%$）**：长车头设计或纵置动力总成，追求 50:50 前后配重与驾驶质感。

### 3. 🎯 同级相近价位核心竞品雷达（找替代横评）
- 依据当前选定车型的类别（轿车 / SUV / MPV）、指导价格区间（$\pm 35\%$ 浮动）以及轴距（$\pm 150\text{mm}$）智能交集运算；
- 优先推荐口碑评分高、级别极度接近的前 3 款热门直接竞品；
- 配备 **【一键并排对比】** 快捷指令，一键唤起 Benchmark PK 模态框，横向并排对比长宽高、轴距、空间得房率、开门余量、机械车位适应度、动力形式与推重比。

### 4. ⚡ 一体化动力总成遥测控制台 & 激光游标刻度
- 汽车之家/懂车帝同款现代商业清爽白灰工程美学，彻底摒弃生硬的塑料方块与刺眼的暗黑模式；
- 0 至 300+ Ps/吨 动态激光游标刻度尺，直观显示推重比与马力阶梯；
- 前驱 / 后驱 / 四驱动态能量流与底盘车轮差异化高亮。

---

## 🚀 快速上手与运行

### 方式一：在线免安装体验（推荐）
直接访问托管于 GitHub Pages 的在线静态网页：
👉 **[在线直达体验（官网）](https://car.3901646.xyz)** · [备用镜像（GitHub Pages）](https://cf3901646.github.io/car-dimension-filter/)

### 方式二：本地离线运行
整个应用打包为自包含的单文件 HTML，**零后端、零 node_modules、零网络依赖**：
1. 克隆本仓库：
   ```bash
   git clone https://github.com/cf3901646/car-dimension-filter.git
   cd car-dimension-filter
   ```
2. 直接双击打开 `index.html`，或用任意静态服务器运行：
   ```bash
   python -m http.server 8000
   ```
   打开浏览器访问 `http://localhost:8000` 即可。

---

## 🛠️ 项目工程结构与二次编译

```
car-dimension-filter/
├── index.html                       # 编译构建后的全量单文件 Web 页面 (内嵌全部数据与引擎)
├── README.md                        # 项目官方说明文档
├── LICENSE                          # MIT 开源协议
├── scripts/                         # 自动化测试与算法验证套件
│   ├── verify_features_124.py       # 车位体检、得房率与竞品雷达全量验证
│   └── test_competitor_algo.py      # 竞品匹配算法回归测试
└── car_dimension_filter/            # 核心工程源码目录
    ├── template.html                # 主界面模板与交互逻辑
    ├── build_html.py                # 单文件构建编译器 (合并数据并压缩输出 index.html)
    ├── verify_all_requirements.py   # 全量回归验证测试
    └── data/                        # 结构化车辆数据库
        ├── series.json              # 1693 款全量车系与 12550 款配置数据
        ├── series_covers.json       # 高清官方实车图片映射
        └── series_enriched_cache.json # 口碑评分、动力马力、驱动与推重比增强缓存
```

### 重新构建打包
若修改了 `template.html` 或补充了 `series.json` 数据，只需执行：
```bash
python car_dimension_filter/build_html.py
```
构建脚本将自动刷新并同步更新根目录 `index.html`。

---

## 📄 开源许可证 (License)

本项目基于 [MIT 许可证](LICENSE) 开源，欢迎自由学习、分享与二次开发。
