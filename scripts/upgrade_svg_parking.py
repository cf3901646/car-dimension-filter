# -*- coding: utf-8 -*-
import os
import sys

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

TEMPLATE_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "car_dimension_filter", "template.html")

with open(TEMPLATE_PATH, "r", encoding="utf-8") as f:
    text = f.read()

# 1. 升级 renderChassisSvg：加入商场标准车位线框 (2.5m x 5.3m) 与开门余量、前后余量、机械车位标签
old_svg_fn_start = "    function renderChassisSvg(length_mm, width_mm, wheelbase_mm, drive_type, pwr_ratio, max_hp, weight_kg) {"
old_svg_fn_end = "    // 初始化应用程序\n    function initApp() {"

new_svg_fn = """    // 辅助函数：绘制高精 2D 底盘俯视透视 SVG（集成真实主流商场 2.5m×5.3m 标准车位线框与开门余量体检）
    function renderChassisSvg(length_mm, width_mm, wheelbase_mm, drive_type, pwr_ratio, max_hp, weight_kg) {
      const l = length_mm || 4800;
      const w = width_mm || 1900;
      const wb = wheelbase_mm || 2900;
      const drv = drive_type || "四驱";
      
      const svg_w = 480;
      const svg_h = 260;
      
      const scale = 0.056; // 1mm = 0.056px
      const body_l = l * scale; // 约 240～310px
      const body_w = w * scale; // 约 95～125px
      const wb_l = wb * scale;   // 约 150～200px
      
      const center_x = svg_w / 2 - 10;
      const center_y = svg_h / 2;
      
      // 主流商场标准垂直车位：长 5300mm，宽 2500mm (国标 JGJ 100-2015 商业车位规范)
      const slot_l = 5300 * scale; // ~296.8px
      const slot_w = 2500 * scale; // ~140.0px
      const slot_x = center_x - slot_l / 2;
      const slot_y = center_y - slot_w / 2;
      
      // 车身框位置（居中停入车位）
      const box_x = center_x - body_l / 2;
      const box_y = center_y - body_w / 2;
      
      // 单侧车门开启余量（mm）
      const door_clearance = Math.round((2500 - w) / 2);
      // 前后总余量（mm）
      const length_clearance = Math.max(0, 5300 - l);
      
      // 空间得房率 (轴长比)
      const space_ratio = ((wb / l) * 100).toFixed(1);
      
      // 机械车位体检结论 (国标限长5000mm, 限宽1850mm/宽体1900mm)
      let mech_badge_text = "机械车位通行";
      let mech_badge_color = "#10b981"; // 绿
      let mech_bg = "rgba(16, 185, 129, 0.1)";
      if (l > 5000 || w > 1900) {
        mech_badge_text = "机械位超长/超宽慎选";
        mech_badge_color = "#f43f5e"; // 红
        mech_bg = "rgba(244, 63, 94, 0.1)";
      } else if (w > 1850) {
        mech_badge_text = "需1.9m宽体机械位";
        mech_badge_color = "#f59e0b"; // 黄
        mech_bg = "rgba(245, 158, 11, 0.1)";
      }
      
      // 开门舒适度评级
      let door_badge_color = "#10b981";
      let door_desc = "开门充裕";
      if (door_clearance < 280) {
        door_badge_color = "#f43f5e";
        door_desc = "开门极窄易磕";
      } else if (door_clearance < 320) {
        door_badge_color = "#0284c7";
        door_desc = "正常开门";
      }

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
      
      const fw_style = front_glow 
        ? 'fill="#0284c7" stroke="#0369a1" stroke-width="2" class="wheel-glow-awd"' 
        : 'fill="#cbd5e1" stroke="#94a3b8" stroke-width="1.5"';
      const rw_style = rear_glow 
        ? 'fill="#f59e0b" stroke="#d97706" stroke-width="2" class="wheel-glow-amber"' 
        : 'fill="#cbd5e1" stroke="#94a3b8" stroke-width="1.5"';
      
      return `
        <svg viewBox="0 0 ${svg_w} ${svg_h}" xmlns="http://www.w3.org/2000/svg" class="w-full h-auto max-h-[250px] select-none">
          <defs>
            <pattern id="svg-grid-light" width="20" height="20" patternUnits="userSpaceOnUse">
              <path d="M 20 0 L 0 0 0 20" fill="none" stroke="rgba(0,0,0,0.03)" stroke-width="1"/>
            </pattern>
            <linearGradient id="frontPowerLight" x1="0%" y1="0%" x2="100%" y2="0%">
              <stop offset="0%" stop-color="#0284c7"/>
              <stop offset="100%" stop-color="#38bdf8"/>
            </linearGradient>
            <linearGradient id="rearPowerLight" x1="0%" y1="0%" x2="100%" y2="0%">
              <stop offset="0%" stop-color="#d97706"/>
              <stop offset="100%" stop-color="#fbbf24"/>
            </linearGradient>
            <pattern id="curbStripe" width="8" height="8" patternUnits="userSpaceOnUse" patternTransform="rotate(45)">
              <rect width="4" height="8" fill="#F59E0B"/>
              <rect x="4" width="4" height="8" fill="#1E293B"/>
            </pattern>
          </defs>

          <!-- 背景工程微网格 -->
          <rect width="${svg_w}" height="${svg_h}" fill="transparent" />
          <rect width="${svg_w}" height="${svg_h}" fill="url(#svg-grid-light)" />

          <!-- ========================================== -->
          <!-- 1. 主流商场标准地下车位标尺框 (2.5m × 5.3m) -->
          <!-- ========================================== -->
          <!-- 车位底坪微阴影与高亮区域 -->
          <rect x="${slot_x}" y="${slot_y}" width="${slot_l}" height="${slot_w}" rx="2" fill="rgba(241, 245, 249, 0.75)" stroke="#E2E8F0" stroke-width="1" />
          
          <!-- 车位黄色边界实线（标准商业地下车库反光线） -->
          <!-- 上侧边线 -->
          <line x1="${slot_x}" y1="${slot_y}" x2="${slot_x + slot_l}" y2="${slot_y}" stroke="#EAB308" stroke-width="2.5" stroke-linecap="round" />
          <!-- 下侧边线 -->
          <line x1="${slot_x}" y1="${slot_y + slot_w}" x2="${slot_x + slot_l}" y2="${slot_y + slot_w}" stroke="#EAB308" stroke-width="2.5" stroke-linecap="round" />
          <!-- 车位底端挡墙封口实线 -->
          <line x1="${slot_x}" y1="${slot_y}" x2="${slot_x}" y2="${slot_y + slot_w}" stroke="#EAB308" stroke-width="2.5" stroke-dasharray="8 4" opacity="0.6" />

          <!-- 车位末端防撞倒车橡胶挡车杆 (Wheel Stopper) -->
          <rect x="${slot_x + 12}" y="${center_y - 28}" width="6" height="56" rx="2" fill="url(#curbStripe)" stroke="#475569" stroke-width="0.8" />
          
          <!-- 车位标牌文字：标准商场车位与泊车体检 -->
          <text x="${slot_x + 8}" y="${slot_y + 12}" fill="#94A3B8" font-size="8" font-family="monospace" font-weight="bold">🅿️ 商场标准车位 2.5m×5.3m</text>

          <!-- ========================================== -->
          <!-- 2. 车身两侧开门富余量（Door Clearance）尺寸引线 -->
          <!-- ========================================== -->
          <!-- 上侧车门开门间距引线 -->
          <line x1="${center_x - 10}" y1="${slot_y + 2}" x2="${center_x - 10}" y2="${box_y - 2}" stroke="${door_badge_color}" stroke-width="1.2" stroke-dasharray="3 2" />
          <polygon points="${center_x - 10},${slot_y + 2} ${center_x - 12},${slot_y + 6} ${center_x - 8},${slot_y + 6}" fill="${door_badge_color}" />
          <polygon points="${center_x - 10},${box_y - 2} ${center_x - 12},${box_y - 6} ${center_x - 8},${box_y - 6}" fill="${door_badge_color}" />
          
          <!-- 开门富余量气泡标签 -->
          <g transform="translate(${center_x - 5}, ${slot_y - 12})">
            <rect x="0" y="0" width="138" height="16" rx="4" fill="#FFFFFF" stroke="${door_badge_color}" stroke-width="1" />
            <text x="69" y="11" fill="${door_badge_color}" font-size="9" font-family="monospace" font-weight="bold" text-anchor="middle">开门余量 ${door_clearance}mm (${door_desc})</text>
          </g>

          <!-- 前后进深富余量引线 (车头侧) -->
          <line x1="${box_x + body_l + 2}" y1="${center_y}" x2="${slot_x + slot_l - 2}" y2="${center_y}" stroke="#64748B" stroke-width="1" stroke-dasharray="2 2" />
          <rect x="${box_x + body_l + 4}" y="${center_y - 7}" width="48" height="14" rx="3" fill="#FFFFFF" stroke="#CBD5E1" stroke-width="0.8" />
          <text x="${box_x + body_l + 28}" y="${center_y + 3}" fill="#64748B" font-size="8" font-family="monospace" text-anchor="middle">余${length_clearance}mm</text>

          <!-- ========================================== -->
          <!-- 3. 底盘机械结构与车身投影 -->
          <!-- ========================================== -->
          <!-- 中轴线 -->
          <line x1="${box_x - 15}" y1="${center_y}" x2="${box_x + body_l + 15}" y2="${center_y}" stroke="rgba(100,116,139,0.25)" stroke-dasharray="4 4" stroke-width="1" />

          <!-- 前后车轴 -->
          <line x1="${front_axle_x}" y1="${box_y - 8}" x2="${front_axle_x}" y2="${box_y + body_w + 8}" stroke="${front_glow ? 'rgba(2,132,199,0.6)' : 'rgba(148,163,184,0.4)'}" stroke-width="${front_glow ? '2' : '1.5'}" />
          <line x1="${rear_axle_x}" y1="${box_y - 8}" x2="${rear_axle_x}" y2="${box_y + body_w + 8}" stroke="${rear_glow ? 'rgba(217,119,6,0.6)' : 'rgba(148,163,184,0.4)'}" stroke-width="${rear_glow ? '2' : '1.5'}" />

          <!-- 中央传动/动力连接轴 (四驱全贯通) -->
          ${is_awd ? `
            <line x1="${front_axle_x}" y1="${center_y}" x2="${rear_axle_x}" y2="${center_y}" stroke="#0284c7" stroke-width="3" stroke-dasharray="6 3" opacity="0.9" />
          ` : ''}

          <!-- 车身外壳工程透视投影 -->
          <rect x="${box_x}" y="${box_y}" width="${body_l}" height="${body_w}" rx="14" fill="#FFFFFF" stroke="#334155" stroke-width="1.8" />
          
          <!-- 座舱透明投影 (乘员舱) -->
          <rect x="${box_x + body_l * 0.22}" y="${box_y + 10}" width="${body_l * 0.52}" height="${body_w - 20}" rx="8" fill="rgba(241, 245, 249, 0.85)" stroke="#cbd5e1" stroke-width="1.2" />

          <!-- 前动力总成图标 -->
          ${front_glow ? `
            <rect x="${front_axle_x - 14}" y="${center_y - 10}" width="28" height="20" rx="4" fill="url(#frontPowerLight)" stroke="#0284c7" stroke-width="1.5" />
            <text x="${front_axle_x}" y="${center_y + 3}" fill="#ffffff" font-size="8" font-family="monospace" font-weight="bold" text-anchor="middle">⚡ 前驱</text>
          ` : `
            <rect x="${front_axle_x - 10}" y="${center_y - 8}" width="20" height="16" rx="3" fill="#f1f5f9" stroke="#cbd5e1" stroke-width="1" />
          `}

          <!-- 后动力总成图标 -->
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

          <!-- ========================================== -->
          <!-- 4. 尺寸与空间得房率引线 -->
          <!-- ========================================== -->
          <!-- 轴距标尺 (上方，科技蓝标尺) -->
          <g transform="translate(0, ${box_y - 10})">
            <line x1="${front_axle_x}" y1="0" x2="${rear_axle_x}" y2="0" stroke="#0284c7" stroke-width="1.5" />
            <line x1="${front_axle_x}" y1="-4" x2="${front_axle_x}" y2="4" stroke="#0284c7" stroke-width="1.2" />
            <line x1="${rear_axle_x}" y1="-4" x2="${rear_axle_x}" y2="4" stroke="#0284c7" stroke-width="1.2" />
            <!-- 轴距与得房率气泡 -->
            <rect x="${(front_axle_x + rear_axle_x)/2 - 58}" y="-9" width="116" height="18" rx="4" fill="#ffffff" stroke="#0284c7" stroke-width="1" />
            <text x="${(front_axle_x + rear_axle_x)/2}" y="3" fill="#0284c7" font-size="9" font-family="monospace" font-weight="bold" text-anchor="middle">轴距 ${wb}mm · 得房率 ${space_ratio}%</text>
          </g>

          <!-- 车长标尺 (下方) -->
          <g transform="translate(0, ${box_y + body_w + 14})">
            <line x1="${box_x}" y1="0" x2="${box_x + body_l}" y2="0" stroke="#64748b" stroke-width="1.2" />
            <line x1="${box_x}" y1="-3" x2="${box_x}" y2="3" stroke="#64748b" stroke-width="1" />
            <line x1="${box_x + body_l}" y1="-3" x2="${box_x + body_l}" y2="3" stroke="#64748b" stroke-width="1" />
            <rect x="${box_x + body_l/2 - 40}" y="-8" width="80" height="16" rx="3" fill="#ffffff" stroke="#94a3b8" stroke-width="1" />
            <text x="${box_x + body_l/2}" y="3" fill="#334155" font-size="9" font-family="monospace" font-weight="semibold" text-anchor="middle">长 ${l}mm</text>
          </g>

          <!-- 车宽标尺 (左侧) -->
          <g transform="translate(${box_x - 18}, 0)">
            <line x1="0" y1="${box_y}" x2="0" y2="${box_y + body_w}" stroke="#64748b" stroke-width="1.2" />
            <line x1="-3" y1="${box_y}" x2="3" y2="${box_y}" stroke="#64748b" stroke-width="1" />
            <line x1="-3" y1="${box_y + body_w}" x2="3" y2="${box_y + body_w}" stroke="#64748b" stroke-width="1" />
            <text x="-5" y="${center_y + 3}" fill="#334155" font-size="9" font-family="monospace" font-weight="semibold" text-anchor="end">宽 ${w}mm</text>
          </g>

          <!-- 右下角：机械立体车位体检徽章 -->
          <g transform="translate(${svg_w - 145}, ${svg_h - 24})">
            <rect x="0" y="0" width="135" height="18" rx="4" fill="${mech_bg}" stroke="${mech_badge_color}" stroke-width="1" />
            <text x="67" y="12" fill="${mech_badge_color}" font-size="9" font-family="monospace" font-weight="bold" text-anchor="middle">${mech_badge_text}</text>
          </g>

        </svg>
      `;
    }
"""

start_pos = text.find(old_svg_fn_start)
end_pos = text.find(old_svg_fn_end)
if start_pos != -1 and end_pos != -1:
    text = text[:start_pos] + new_svg_fn + "\n" + text[end_pos:]
    print("✅ 成功升级 renderChassisSvg 算法！")
else:
    print("❌ 未找到 renderChassisSvg 标记区间")

with open(TEMPLATE_PATH, "w", encoding="utf-8") as f:
    f.write(text)
print("Updated template.html with new SVG renderer.")
