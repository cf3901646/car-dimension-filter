# -*- coding: utf-8 -*-
"""
Upgrade right-hand board and mobile drawer from dark slate to
commercial-grade light/clean aesthetic (Autohome & Dongchedi style).
"""

import sys
import re

def main():
    path = "car_dimension_filter/template.html"
    with open(path, "r", encoding="utf-8") as f:
        content = f.read()

    # 1. 替换 desktopBoardSection HTML
    old_board_sec_pattern = r'(<!-- 右侧栏：底盘透视与性能工程看板.*?-->\s*<section id="desktopBoardSection"[^>]*>)(.*?)(</section>)'
    
    new_board_inner = '''
        <div class="bg-white text-slate-800 rounded-2xl p-5 shadow-sm border border-slate-200/90 space-y-4">
          
          <!-- 看板头部：当前选中的车辆与操作 (汽车之家/懂车帝高对比度排版) -->
          <div class="flex items-start justify-between gap-3 border-b border-slate-100 pb-3">
            <div>
              <div class="flex items-center gap-2">
                <span id="boardBrand" class="text-xs font-semibold px-2 py-0.5 rounded bg-slate-100 text-slate-700 border border-slate-200">品牌</span>
                <h2 id="boardSeriesName" class="text-lg font-bold text-slate-900 tracking-tight">车系名称</h2>
                <span id="boardLevel" class="text-[11px] text-slate-400">中大型车</span>
              </div>
              <div class="flex items-center gap-3 mt-1.5 text-xs">
                <span id="boardPrice" class="font-mono font-bold text-[#FF6600] text-sm">20.99～29.99万</span>
                <span class="text-slate-300">|</span>
                <div class="flex items-center gap-1">
                  <i class="fa-solid fa-star text-amber-400 text-xs"></i>
                  <span id="boardScore" class="font-bold text-slate-800">4.65</span>
                  <span class="text-slate-400 text-[10px]">车主口碑</span>
                </div>
                <span id="boardEvRangeBadge" class="hidden px-2 py-0.5 rounded text-[10px] font-semibold bg-emerald-50 text-emerald-700 border border-emerald-200">纯电 620km</span>
              </div>
            </div>

            <!-- 操作按钮 -->
            <div class="flex items-center gap-2">
              <button id="boardCompareBtn" class="px-2.5 py-1 text-xs font-medium text-slate-700 hover:text-slate-900 bg-slate-100 hover:bg-slate-200 border border-slate-200 rounded-lg transition-colors flex items-center gap-1.5 shadow-2xs">
                <i class="fa-solid fa-plus text-sky-600"></i> 加入对比
              </button>
            </div>
          </div>

          <!-- 2D 底盘俯视透视蓝图容器 (SVG，清爽浅冰灰画板) -->
          <div class="relative bg-[#F8FAFC] rounded-xl p-3 border border-slate-200/80 overflow-hidden flex items-center justify-center min-h-[260px]">
            <div id="boardChassisSvgContainer" class="w-full flex items-center justify-center">
              <!-- 动态注入底盘 SVG -->
            </div>
          </div>

          <!-- 商业级动力总成与推重比遥测控制台 (Precision Powertrain Telemetry Deck) -->
          <div class="telemetry-deck bg-[#F8FAFC] rounded-xl border border-slate-200/90 p-3.5 space-y-3">
            
            <!-- 顶栏：推重比精密刻度标尺 -->
            <div class="space-y-1.5">
              <div class="flex items-baseline justify-between">
                <div class="flex items-center gap-2">
                  <span class="text-[10px] tracking-wider font-mono font-bold text-slate-400 uppercase">POWERTRAIN TELEMETRY</span>
                  <span class="text-slate-300">/</span>
                  <span class="text-xs font-semibold text-slate-700">推重比指标</span>
                </div>
                <div class="flex items-baseline gap-2">
                  <span id="boardPwrLevel" class="text-[10px] font-mono px-2 py-0.5 rounded font-bold bg-amber-50 text-amber-700 border border-amber-200">超跑性能级</span>
                  <div class="flex items-baseline gap-1">
                    <span id="boardPwrRatioVal" class="text-2xl sm:text-3xl font-bold font-mono text-amber-600 tracking-tight">--</span>
                    <span class="text-[11px] font-mono font-semibold text-slate-500">Ps/t</span>
                  </div>
                </div>
              </div>

              <!-- 机械激光标尺轨道 -->
              <div class="pwr-rail-track relative pt-1 pb-2">
                <div class="h-2 w-full bg-slate-200 rounded-full overflow-hidden border border-slate-300/80 relative">
                  <!-- 色彩渐变刻度底带 -->
                  <div class="absolute inset-y-0 left-0 w-full bg-gradient-to-r from-emerald-500 via-sky-500 via-amber-500 to-rose-500 opacity-80"></div>
                  <!-- 动态高光激光游标 -->
                  <div id="boardPwrBar" class="pwr-cursor laser-cursor absolute top-0 bottom-0 left-0 bg-white shadow-[0_0_6px_rgba(0,0,0,0.3)] transition-all duration-300 w-1/2"></div>
                </div>
                <!-- 刻度分度值标注 -->
                <div class="flex justify-between text-[9px] font-mono text-slate-400 pt-1 select-none">
                  <span>0 Ps/t</span>
                  <span>100 (家用)</span>
                  <span>150 (充沛)</span>
                  <span>220 (推背)</span>
                  <span>300+ Ps/t (超跑)</span>
                </div>
              </div>
            </div>

            <!-- 底栏：动力三联精密数据视窗 (等宽机加工数据带) -->
            <div class="telemetry-metrics-bar grid grid-cols-3 divide-x divide-slate-200 border-t border-slate-200 pt-2.5">
              
              <!-- 1. 综合马力 -->
              <div class="px-2 first:pl-0">
                <div class="text-[10px] text-slate-500 font-medium">综合马力输出</div>
                <div class="flex items-baseline gap-1 mt-0.5">
                  <span id="boardHpVal" class="text-lg font-bold font-mono text-slate-900">--</span>
                  <span class="text-[10px] text-slate-500 font-mono">Ps</span>
                </div>
                <div class="text-[9px] text-slate-400 mt-0.5 font-mono">额定峰值输出</div>
              </div>

              <!-- 2. 驱动总成 -->
              <div class="px-2">
                <div class="text-[10px] text-slate-500 font-medium">驱动总成架构</div>
                <div id="boardDriveType" class="text-sm font-bold text-sky-600 mt-0.5 truncate">智能四驱</div>
                <div id="boardDriveDesc" class="text-[9px] text-slate-400 mt-0.5 truncate font-mono">双电机动力协同</div>
              </div>

              <!-- 3. 整备质量 -->
              <div class="px-2 last:pr-0">
                <div class="text-[10px] text-slate-500 font-medium">整备质量规格</div>
                <div class="flex items-baseline gap-1 mt-0.5">
                  <span id="boardWeightVal" class="text-lg font-bold font-mono text-slate-900">--</span>
                  <span class="text-[10px] text-slate-500 font-mono">kg</span>
                </div>
                <div class="text-[9px] text-slate-400 mt-0.5 font-mono">空载整备自重</div>
              </div>

            </div>

          </div>

          <!-- 年款与具体配置规格切换列表 -->
          <div class="space-y-1.5 pt-1">
            <div class="flex items-center justify-between text-xs text-slate-500">
              <span class="font-semibold text-slate-700">具体配置与驱动联动切换</span>
              <span id="boardVersionCount" class="text-[11px]">共 0 款在售配置</span>
            </div>
            <div id="boardVersionList" class="max-h-48 overflow-y-auto space-y-1 custom-scrollbar pr-1">
              <!-- 动态配置单选 -->
            </div>
          </div>

        </div>
'''

    content = re.sub(old_board_sec_pattern, r'\1' + new_board_inner + r'\3', content, flags=re.DOTALL)

    # 2. 替换手机端抽屉 mobileDrawer HTML
    old_drawer_pattern = r'(<!-- 手机移动端：底部弹性抽屉.*?-->\s*<div id="mobileDrawerBackdrop"[^>]*></div>\s*<div id="mobileDrawer"[^>]*>)(.*?)(</div>\s*<!-- 移动端常驻底部控制栏)'
    
    new_drawer_inner = '''
    <!-- 抽屉顶部手柄与标题 -->
    <div class="p-3 border-b border-slate-100 flex items-center justify-between shrink-0">
      <div class="w-8"></div>
      <div class="w-12 h-1 bg-slate-300 rounded-full mx-auto"></div>
      <button id="closeMobileDrawerBtn" class="w-8 h-8 flex items-center justify-center text-slate-400 hover:text-slate-700">
        <i class="fa-solid fa-xmark text-base"></i>
      </button>
    </div>

    <!-- 抽屉内容区 (可滚动) -->
    <div class="p-4 overflow-y-auto space-y-4 custom-scrollbar text-slate-800">
      <div>
        <div class="flex items-center gap-2">
          <span id="mDrawerBrand" class="text-xs px-2 py-0.5 rounded bg-slate-100 text-slate-700 border border-slate-200">品牌</span>
          <h3 id="mDrawerSeriesName" class="text-base font-bold text-slate-900">车系名称</h3>
        </div>
        <div class="flex items-center gap-2 mt-1.5 text-xs">
          <span id="mDrawerPrice" class="font-mono font-bold text-[#FF6600]">价格</span>
          <span class="text-slate-300">|</span>
          <span class="text-amber-500 font-bold flex items-center gap-1">
            <i class="fa-solid fa-star text-xs"></i>
            <span id="mDrawerScore" class="text-slate-800">4.6</span>
          </span>
          <span id="mDrawerRangeBadge" class="hidden px-1.5 py-0.2 rounded text-[10px] bg-emerald-50 text-emerald-700 border border-emerald-200">续航</span>
        </div>
      </div>

      <!-- 手机底盘透视 SVG 容器 (清爽浅灰底座) -->
      <div class="bg-[#F8FAFC] rounded-xl p-2 border border-slate-200/80 flex items-center justify-center min-h-[220px]">
        <div id="mDrawerChassisSvgContainer" class="w-full flex items-center justify-center"></div>
      </div>

      <!-- 手机端工程动力遥测仪表 -->
      <div class="bg-[#F8FAFC] p-3 rounded-xl border border-slate-200/90 space-y-2">
        <div class="flex items-baseline justify-between">
          <span class="text-[10px] font-mono text-slate-400 uppercase tracking-wider">POWER-TO-WEIGHT</span>
          <div class="flex items-baseline gap-1.5">
            <span id="mDrawerPwrLevel" class="text-[10px] font-mono px-1.5 py-0.2 rounded bg-amber-50 text-amber-700 border border-amber-200 font-bold">性能级</span>
            <span id="mDrawerPwrVal" class="text-2xl font-bold font-mono text-amber-600">--</span>
            <span class="text-[10px] font-mono text-slate-500">Ps/t</span>
          </div>
        </div>
        <!-- 刻度条 -->
        <div class="h-1.5 w-full bg-slate-200 rounded-full overflow-hidden border border-slate-300 relative">
          <div class="absolute inset-y-0 left-0 w-full bg-gradient-to-r from-emerald-500 via-sky-500 via-amber-500 to-rose-500 opacity-80"></div>
          <div id="mDrawerPwrBar" class="absolute top-0 bottom-0 left-0 bg-white shadow-[0_0_4px_rgba(0,0,0,0.3)] w-1/2"></div>
        </div>
        <div class="grid grid-cols-2 divide-x divide-slate-200 pt-1 text-[11px]">
          <div class="pr-2">
            <span class="text-slate-500 text-[10px]">驱动总成: </span>
            <span id="mDrawerDriveType" class="font-bold text-sky-600">四驱</span>
          </div>
          <div class="pl-2">
            <span class="text-slate-500 text-[10px]">马力输出: </span>
            <span id="mDrawerHpVal" class="font-bold font-mono text-slate-900">-- Ps</span>
          </div>
        </div>
      </div>

      <!-- 年款配置列表 -->
      <div class="space-y-1.5">
        <div class="text-xs font-semibold text-slate-700">切换配置观察驱动轮变化:</div>
        <div id="mDrawerVersionList" class="space-y-1 max-h-40 overflow-y-auto custom-scrollbar"></div>
      </div>
    </div>
  '''

    # 更新 mobileDrawer 容器样式 (从 bg-slate-900 改为 bg-white)
    content = content.replace(
        'class="fixed inset-x-0 bottom-0 z-50 bg-slate-900 text-white rounded-t-3xl max-h-[85vh] flex flex-col drawer-closed drawer-transition lg:hidden border-t border-slate-800 shadow-2xl"',
        'class="fixed inset-x-0 bottom-0 z-50 bg-white text-slate-800 rounded-t-3xl max-h-[85vh] flex flex-col drawer-closed drawer-transition lg:hidden border-t border-slate-200 shadow-2xl"'
    )

    content = re.sub(old_drawer_pattern, r'\1' + new_drawer_inner + r'\3', content, flags=re.DOTALL)

    # 3. 替换 renderChassisSvg 为清爽白底/工程浅灰版本
    old_chassis_start = "    // 辅助函数：绘制高精 2D 底盘俯视透视 SVG"
    old_chassis_end = "    // 初始化应用程序\n    function initApp() {"
    
    start_pos = content.find(old_chassis_start)
    end_pos = content.find(old_chassis_end)

    if start_pos != -1 and end_pos != -1:
        new_chassis_svg_func = '''    // 辅助函数：绘制高精 2D 底盘俯视透视 SVG (汽车之家/懂车帝同款现代商业级白底工程线框图)
    function renderChassisSvg(length_mm, width_mm, wheelbase_mm, drive_type, pwr_ratio, max_hp, weight_kg) {
      const l = length_mm || 4800;
      const w = width_mm || 1900;
      const wb = wheelbase_mm || 2900;
      const drv = drive_type || "四驱";
      
      const svg_w = 460;
      const svg_h = 240;
      
      const scale = 0.058; // 1mm = 0.058px
      const body_l = l * scale; // 约 250～310px
      const body_w = w * scale; // 约 95～125px
      const wb_l = wb * scale;   // 约 160～200px
      
      const center_x = svg_w / 2 - 10;
      const center_y = svg_h / 2;
      
      const box_x = center_x - body_l / 2;
      const box_y = center_y - body_w / 2;
      
      const front_overhang = (body_l - wb_l) * 0.45;
      const front_axle_x = box_x + front_overhang;
      const rear_axle_x = front_axle_x + wb_l;
      
      const wheel_l = 28;
      const wheel_w = 12;
      
      const fl_x = front_axle_x - wheel_l / 2;
      const fl_y = box_y - wheel_w / 2;
      const fr_x = front_axle_x - wheel_l / 2;
      const fr_y = box_y + body_w - wheel_w / 2;
      
      const rl_x = rear_axle_x - wheel_l / 2;
      const rl_y = box_y - wheel_w / 2;
      const rr_x = rear_axle_x - wheel_l / 2;
      const rr_y = box_y + body_w - wheel_w / 2;
      
      const is_fwd = drv.includes("前驱");
      const is_rwd = drv.includes("后驱");
      const is_awd = drv.includes("四驱") || (!is_fwd && !is_rwd);
      
      const front_glow = is_fwd || is_awd;
      const rear_glow = is_rwd || is_awd;
      
      // 白底高对比车轮样式：高亮轮为电能蓝/琥珀橙，未驱动轮为清爽铝合金灰
      const fw_style = front_glow 
        ? 'fill="#0284c7" stroke="#0369a1" stroke-width="2" class="wheel-glow-awd"' 
        : 'fill="#cbd5e1" stroke="#94a3b8" stroke-width="1.5"';
      const rw_style = rear_glow 
        ? 'fill="#f59e0b" stroke="#d97706" stroke-width="2" class="wheel-glow-amber"' 
        : 'fill="#cbd5e1" stroke="#94a3b8" stroke-width="1.5"';
      
      return `
        <svg viewBox="0 0 ${svg_w} ${svg_h}" xmlns="http://www.w3.org/2000/svg" class="w-full h-auto max-h-[220px] select-none">
          <defs>
            <!-- 极淡工程微网格 -->
            <pattern id="svg-grid-light" width="20" height="20" patternUnits="userSpaceOnUse">
              <path d="M 20 0 L 0 0 0 20" fill="none" stroke="rgba(0,0,0,0.035)" stroke-width="1"/>
            </pattern>
            <!-- 浅色动力单元渐变 -->
            <linearGradient id="frontPowerLight" x1="0%" y1="0%" x2="100%" y2="0%">
              <stop offset="0%" stop-color="#0284c7"/>
              <stop offset="100%" stop-color="#38bdf8"/>
            </linearGradient>
            <linearGradient id="rearPowerLight" x1="0%" y1="0%" x2="100%" y2="0%">
              <stop offset="0%" stop-color="#d97706"/>
              <stop offset="100%" stop-color="#fbbf24"/>
            </linearGradient>
          </defs>

          <!-- 背景工程网格 -->
          <rect width="${svg_w}" height="${svg_h}" fill="transparent" />
          <rect width="${svg_w}" height="${svg_h}" fill="url(#svg-grid-light)" />

          <!-- 中轴线 -->
          <line x1="${box_x - 20}" y1="${center_y}" x2="${box_x + body_l + 20}" y2="${center_y}" stroke="rgba(100,116,139,0.3)" stroke-dasharray="4 4" stroke-width="1" />

          <!-- 前后车轴 -->
          <line x1="${front_axle_x}" y1="${box_y - 8}" x2="${front_axle_x}" y2="${box_y + body_w + 8}" stroke="${front_glow ? 'rgba(2,132,199,0.6)' : 'rgba(148,163,184,0.4)'}" stroke-width="${front_glow ? '2' : '1.5'}" />
          <line x1="${rear_axle_x}" y1="${box_y - 8}" x2="${rear_axle_x}" y2="${box_y + body_w + 8}" stroke="${rear_glow ? 'rgba(217,119,6,0.6)' : 'rgba(148,163,184,0.4)'}" stroke-width="${rear_glow ? '2' : '1.5'}" />

          <!-- 中央传动/动力连接轴 (四驱全贯通) -->
          ${is_awd ? `
            <line x1="${front_axle_x}" y1="${center_y}" x2="${rear_axle_x}" y2="${center_y}" stroke="#0284c7" stroke-width="3" stroke-dasharray="6 3" opacity="0.9" />
          ` : ''}

          <!-- 车身外壳工程透视投影 (白底深灰工程线框，明朗通透) -->
          <rect x="${box_x}" y="${box_y}" width="${body_l}" height="${body_w}" rx="14" fill="#FFFFFF" stroke="#475569" stroke-width="1.8" />
          
          <!-- 座舱透明投影 (乘员舱浅灰微底) -->
          <rect x="${box_x + body_l * 0.22}" y="${box_y + 10}" width="${body_l * 0.52}" height="${body_w - 20}" rx="8" fill="rgba(241, 245, 249, 0.75)" stroke="#cbd5e1" stroke-width="1.2" />

          <!-- 前动力总成图标 (前驱或四驱发光) -->
          ${front_glow ? `
            <rect x="${front_axle_x - 14}" y="${center_y - 10}" width="28" height="20" rx="4" fill="url(#frontPowerLight)" stroke="#0284c7" stroke-width="1.5" />
            <text x="${front_axle_x}" y="${center_y + 3}" fill="#ffffff" font-size="8" font-family="monospace" font-weight="bold" text-anchor="middle">⚡ 前驱</text>
          ` : `
            <rect x="${front_axle_x - 10}" y="${center_y - 8}" width="20" height="16" rx="3" fill="#f1f5f9" stroke="#cbd5e1" stroke-width="1" />
          `}

          <!-- 后动力总成图标 (后驱或四驱发光) -->
          ${rear_glow ? `
            <rect x="${rear_axle_x - 14}" y="${center_y - 10}" width="28" height="20" rx="4" fill="url(#rearPowerLight)" stroke="#d97706" stroke-width="1.5" />
            <text x="${rear_axle_x}" y="${center_y + 3}" fill="#ffffff" font-size="8" font-family="monospace" font-weight="bold" text-anchor="middle">⚡ 后驱</text>
          ` : `
            <rect x="${rear_axle_x - 10}" y="${center_y - 8}" width="20" height="16" rx="3" fill="#f1f5f9" stroke="#cbd5e1" stroke-width="1" />
          `}

          <!-- 四个车轮渲染 -->
          <rect x="${fl_x}" y="${fl_y}" width="${wheel_l}" height="${wheel_w}" rx="3" ${fw_style} />
          <rect x="${fr_x}" y="${fr_y}" width="${wheel_l}" height="${wheel_w}" rx="3" ${fw_style} />
          <rect x="${rl_x}" y="${rl_y}" width="${wheel_l}" height="${wheel_w}" rx="3" ${rw_style} />
          <rect x="${rr_x}" y="${rr_y}" width="${wheel_l}" height="${wheel_w}" rx="3" ${rw_style} />

          <!-- 汽车之家/懂车帝同款尺寸标尺直接标注 -->
          
          <!-- 1. 轴距标尺 (上方，科技蓝标尺 + 纯白药丸气泡) -->
          <g transform="translate(0, ${box_y - 18})">
            <line x1="${front_axle_x}" y1="0" x2="${rear_axle_x}" y2="0" stroke="#0284c7" stroke-width="1.5" />
            <line x1="${front_axle_x}" y1="-4" x2="${front_axle_x}" y2="8" stroke="#0284c7" stroke-width="1.2" />
            <line x1="${rear_axle_x}" y1="-4" x2="${rear_axle_x}" y2="8" stroke="#0284c7" stroke-width="1.2" />
            <!-- 轴距数字胶囊 -->
            <rect x="${(front_axle_x + rear_axle_x)/2 - 42}" y="-11" width="84" height="18" rx="4" fill="#ffffff" stroke="#0284c7" stroke-width="1" />
            <text x="${(front_axle_x + rear_axle_x)/2}" y="2" fill="#0284c7" font-size="10" font-family="monospace" font-weight="bold" text-anchor="middle">轴距 ${wb}mm</text>
          </g>

          <!-- 2. 车长标尺 (下方，冷灰中性标尺 + 纯白药丸气泡) -->
          <g transform="translate(0, ${box_y + body_w + 20})">
            <line x1="${box_x}" y1="0" x2="${box_x + body_l}" y2="0" stroke="#64748b" stroke-width="1.2" />
            <line x1="${box_x}" y1="-4" x2="${box_x}" y2="4" stroke="#64748b" stroke-width="1" />
            <line x1="${box_x + body_l}" y1="-4" x2="${box_x + body_l}" y2="4" stroke="#64748b" stroke-width="1" />
            <rect x="${box_x + body_l/2 - 38}" y="-8" width="76" height="16" rx="3" fill="#ffffff" stroke="#94a3b8" stroke-width="1" />
            <text x="${box_x + body_l/2}" y="3" fill="#334155" font-size="9" font-family="monospace" font-weight="semibold" text-anchor="middle">长 ${l}mm</text>
          </g>

          <!-- 3. 车宽标尺 (左侧，垂直标尺) -->
          <g transform="translate(${box_x - 22}, 0)">
            <line x1="0" y1="${box_y}" x2="0" y2="${box_y + body_w}" stroke="#64748b" stroke-width="1.2" />
            <line x1="-4" y1="${box_y}" x2="4" y2="${box_y}" stroke="#64748b" stroke-width="1" />
            <line x1="-4" y1="${box_y + body_w}" x2="4" y2="${box_y + body_w}" stroke="#64748b" stroke-width="1" />
            <text x="-6" y="${center_y + 3}" fill="#334155" font-size="9" font-family="monospace" font-weight="semibold" text-anchor="end">宽 ${w}mm</text>
          </g>

        </svg>
      `;
    }'''
        content = content[:start_pos] + new_chassis_svg_func + "\n\n" + content[end_pos:]

    # 4. 替换 renderBoardVersions 中的深色列表项为白底现代卡片
    old_version_block = """        return `
          <div class="flex items-center justify-between p-2 rounded-lg bg-slate-800/60 hover:bg-slate-800 border border-slate-700/60 cursor-pointer text-xs transition-colors"
               onclick="switchSpecificVersion(${s.series_id}, ${idx})">
            <div class="truncate mr-2">
              <span class="text-white font-medium truncate">${v.model_name || `配置款 ${idx+1}`}</span>
              <div class="text-[10px] text-slate-400 mt-0.5 font-mono">
                ${v.horsepower ? `${v.horsepower}Ps` : ''} ${v.weight ? `· ${v.weight}kg` : ''} ${v.ev_range ? `· 纯电${v.ev_range}km` : ''}
              </div>
            </div>
            <div class="flex items-center gap-1.5 shrink-0">
              <span class="text-[10px] px-1.5 py-0.2 rounded border font-semibold ${badgeColor}">${vDrv}</span>
              <span class="font-mono text-amber-400 text-[11px] font-bold">${vPwr} <span class="text-[9px] text-slate-500">Ps/t</span></span>
            </div>
          </div>
        `;"""

    new_version_block = """        return `
          <div class="flex items-center justify-between p-2.5 rounded-lg bg-white hover:bg-slate-50 border border-slate-200/90 cursor-pointer text-xs transition-all shadow-2xs hover:border-sky-300"
               onclick="switchSpecificVersion(${s.series_id}, ${idx})">
            <div class="truncate mr-2">
              <span class="text-slate-900 font-semibold truncate block">${v.model_name || `配置款 ${idx+1}`}</span>
              <div class="text-[10px] text-slate-500 mt-0.5 font-mono">
                ${v.horsepower ? `${v.horsepower}Ps` : ''} ${v.weight ? `· ${v.weight}kg` : ''} ${v.ev_range ? `· 纯电${v.ev_range}km` : ''}
              </div>
            </div>
            <div class="flex items-center gap-1.5 shrink-0">
              <span class="text-[10px] px-1.5 py-0.2 rounded border font-semibold ${badgeColor}">${vDrv}</span>
              <span class="font-mono text-amber-600 text-[11px] font-bold">${vPwr} <span class="text-[9px] text-slate-400">Ps/t</span></span>
            </div>
          </div>
        `;"""

    content = content.replace(old_version_block, new_version_block)

    # 替换 badgeColor 中的深色类名
    content = content.replace(
        "const badgeColor = isAwd ? 'bg-sky-950 text-sky-400 border-sky-800' : (isRwd ? 'bg-amber-950 text-amber-400 border-amber-800' : 'bg-slate-800 text-slate-400 border-slate-700');",
        "const badgeColor = isAwd ? 'bg-sky-50 text-sky-700 border-sky-200' : (isRwd ? 'bg-amber-50 text-amber-700 border-amber-200' : 'bg-slate-100 text-slate-600 border-slate-200');"
    )

    # 5. 替换 openMobileDrawerWithData 中的手机配置列表项
    old_m_list = """      mList.innerHTML = (s.versions || []).slice(0, 6).map((v, i) => `
        <div class="flex items-center justify-between p-2 rounded bg-slate-800 text-[11px] border border-slate-700/60"
             onclick="switchSpecificVersion(${s.series_id}, ${i})">
          <span class="truncate text-white">${v.model_name}</span>
          <span class="text-amber-400 font-mono font-bold shrink-0 ml-2">${v.pwr_ratio || '--'} Ps/t</span>
        </div>
      `).join('');"""

    new_m_list = """      mList.innerHTML = (s.versions || []).slice(0, 6).map((v, i) => `
        <div class="flex items-center justify-between p-2 rounded-lg bg-slate-50 hover:bg-slate-100 text-[11px] border border-slate-200/90 text-slate-800"
             onclick="switchSpecificVersion(${s.series_id}, ${i})">
          <span class="truncate font-medium text-slate-900">${v.model_name}</span>
          <span class="text-amber-600 font-mono font-bold shrink-0 ml-2">${v.pwr_ratio || '--'} Ps/t</span>
        </div>
      `).join('');"""

    content = content.replace(old_m_list, new_m_list)

    # 6. 统一把对比表格中底盘透视的单元格底色从 bg-slate-950 改为 bg-slate-50
    content = content.replace(
        '<td class="p-2 bg-slate-950 rounded-lg">',
        '<td class="p-2 bg-slate-50 rounded-lg border border-slate-100">'
    )

    with open(path, "w", encoding="utf-8") as f:
        f.write(content)

    print("Successfully upgraded to light/clean commercial UI!")

if __name__ == "__main__":
    main()
