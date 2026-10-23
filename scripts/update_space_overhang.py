# -*- coding: utf-8 -*-
import os
import sys

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

TEMPLATE_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "car_dimension_filter", "template.html")

with open(TEMPLATE_PATH, "r", encoding="utf-8") as f:
    content = f.read()

# 1. 升级 getSpaceMeta
old_meta = """    function getSpaceMeta(wheelbase, length) {
      const wb = wheelbase || 2800;
      const l = length || 4800;
      const ratio = ((wb / l) * 100).toFixed(1);
      const numRatio = parseFloat(ratio);
      if (numRatio >= 61.5) {
        return {
          ratio: ratio,
          level: "👑 超高得房率",
          desc: "短前后悬大座舱",
          badgeClass: "bg-indigo-50 text-indigo-700 border-indigo-200"
        };
      } else if (numRatio >= 59.0) {
        return {
          ratio: ratio,
          level: "💎 黄金均衡座舱",
          desc: "家用黄金平衡比例",
          badgeClass: "bg-sky-50 text-sky-700 border-sky-200"
        };
      }
      return {
        ratio: ratio,
        level: "🏎️ 运动操控取向",
        desc: "长车头运动配重",
        badgeClass: "bg-amber-50 text-amber-700 border-amber-200"
      };
    }"""

new_meta = """    function getSpaceMeta(wheelbase, length) {
      const wb = wheelbase || 2800;
      const l = length || 4800;
      const overhang = Math.max(0, l - wb);
      const ratio = ((wb / l) * 100).toFixed(1);
      const numRatio = parseFloat(ratio);
      if (numRatio >= 61.5) {
        return {
          ratio: ratio,
          overhang: overhang,
          level: "👑 超高得房率",
          desc: "短前后悬大座舱",
          badgeClass: "bg-indigo-50 text-indigo-700 border-indigo-200"
        };
      } else if (numRatio >= 59.0) {
        return {
          ratio: ratio,
          overhang: overhang,
          level: "💎 黄金均衡座舱",
          desc: "家用黄金平衡比例",
          badgeClass: "bg-sky-50 text-sky-700 border-sky-200"
        };
      }
      return {
        ratio: ratio,
        overhang: overhang,
        level: "🏎️ 运动操控取向",
        desc: "长车头运动配重",
        badgeClass: "bg-amber-50 text-amber-700 border-amber-200"
      };
    }"""

# 2. 升级看板 HTML
old_board_html = """              <!-- 得房率 (轴长比) -->
              <div class="px-2 first:pl-0">
                <div class="text-[10px] text-slate-500">轴长空间得房率</div>
                <div class="flex items-baseline gap-1 mt-0.5">
                  <span id="boardSpaceRatioVal" class="text-base font-bold font-mono text-indigo-600">--%</span>
                </div>
                <div class="text-[9px] text-slate-400 font-mono">轴距/车长比率</div>
              </div>"""

new_board_html = """              <!-- 得房率 (轴长比) -->
              <div class="px-2 first:pl-0">
                <div class="flex items-center gap-1">
                  <span class="text-[10px] text-slate-500">空间得房率</span>
                  <span class="text-[9px] text-indigo-500 cursor-help" title="汽车两头需预留碰撞吸能与动力总成公摊(约1.8至2.1米)，乘用车轴长比普遍集中在57%至63%之间。车长每1%比例差距≈约50mm(整整1拳后排腿部空间)！">ⓘ</span>
                </div>
                <div class="flex items-baseline gap-1 mt-0.5">
                  <span id="boardSpaceRatioVal" class="text-base font-bold font-mono text-indigo-600">--%</span>
                </div>
                <div id="boardSpaceOverhang" class="text-[9px] text-slate-400 font-mono">公摊: --mm</div>
              </div>"""

# 3. 升级移动端抽屉 HTML
old_drawer_html = """          <div>
            <div class="text-[10px] text-slate-500">空间得房率</div>
            <div id="mDrawerSpaceRatioVal" class="font-mono font-bold text-indigo-600 mt-0.5">--%</div>
          </div>"""

new_drawer_html = """          <div>
            <div class="text-[10px] text-slate-500">空间得房率</div>
            <div id="mDrawerSpaceRatioVal" class="font-mono font-bold text-indigo-600 mt-0.5">--%</div>
            <div id="mDrawerSpaceOverhang" class="text-[9px] text-slate-400 font-mono mt-0.5">公摊 --mm</div>
          </div>"""

# 4. 数据绑定
old_select_bind = """      const sRatioEl = document.getElementById('boardSpaceRatioVal');
      if (sRatioEl) sRatioEl.textContent = `${spaceMeta.ratio}%`;"""

new_select_bind = """      const sRatioEl = document.getElementById('boardSpaceRatioVal');
      if (sRatioEl) sRatioEl.textContent = `${spaceMeta.ratio}%`;
      const sOverhangEl = document.getElementById('boardSpaceOverhang');
      if (sOverhangEl) sOverhangEl.textContent = `公摊 ${spaceMeta.overhang}mm`;"""

old_m_bind = """      const mSRatio = document.getElementById('mDrawerSpaceRatioVal');
      if (mSRatio) mSRatio.textContent = `${mSpaceMeta.ratio}%`;"""

new_m_bind = """      const mSRatio = document.getElementById('mDrawerSpaceRatioVal');
      if (mSRatio) mSRatio.textContent = `${mSpaceMeta.ratio}%`;
      const mSOverhang = document.getElementById('mDrawerSpaceOverhang');
      if (mSOverhang) mSOverhang.textContent = `公摊 ${mSpaceMeta.overhang}mm`;"""

# 5. 对比表格展示
old_compare_row = """                      <td class="p-2 font-mono font-bold text-indigo-600">
                        ${r}% <span class="text-[10px] font-normal text-slate-500">${r >= 61.5 ? '(高得房率)' : (r >= 59 ? '(均衡)' : '(运动长机舱)')}</span>
                      </td>"""

new_compare_row = """                      <td class="p-2 font-mono font-bold text-indigo-600">
                        ${r}% <span class="text-[10px] font-normal text-slate-500">${r >= 61.5 ? '(短悬大座舱)' : (r >= 59 ? '(均衡)' : '(运动长机舱)')}</span>
                        <div class="text-[10px] font-normal text-slate-400 font-mono">公摊 ${l - wb}mm · 1%≈1拳</div>
                      </td>"""

assert old_meta in content, "old_meta not found"
assert old_board_html in content, "old_board_html not found"
assert old_drawer_html in content, "old_drawer_html not found"
assert old_select_bind in content, "old_select_bind not found"
assert old_m_bind in content, "old_m_bind not found"
assert old_compare_row in content, "old_compare_row not found"

content = content.replace(old_meta, new_meta)
content = content.replace(old_board_html, new_board_html)
content = content.replace(old_drawer_html, new_drawer_html)
content = content.replace(old_select_bind, new_select_bind)
content = content.replace(old_m_bind, new_m_bind)
content = content.replace(old_compare_row, new_compare_row)

with open(TEMPLATE_PATH, "w", encoding="utf-8") as f:
    f.write(content)

print("✅ 成功更新 template.html 中的得房率公摊尺寸与人机工程换算提示！")
