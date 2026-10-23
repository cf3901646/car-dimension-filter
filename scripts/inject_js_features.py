# -*- coding: utf-8 -*-
import os
import sys

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

TEMPLATE_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "car_dimension_filter", "template.html")

with open(TEMPLATE_PATH, "r", encoding="utf-8") as f:
    text = f.read()

# 辅助函数注入点：在 getPwrRatioMeta 上方或下方加入辅助函数
helper_functions = """    // 辅助函数：解析价格均值与区间
    function parseCarPrice(s) {
      const pStr = s.price_str || '';
      const nums = pStr.match(/\\d+(?:\\.\\d+)?/g);
      if (nums && nums.length > 0) {
        const pMin = parseFloat(nums[0]);
        const pMax = nums.length > 1 ? parseFloat(nums[1]) : pMin;
        return { min: pMin, max: pMax, avg: (pMin + pMax) / 2 };
      }
      return { min: 0, max: 0, avg: 0 };
    }

    // 辅助函数：计算空间得房率 (轴长比) 与评级
    function getSpaceMeta(wheelbase, length) {
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
    }

    // 辅助函数：计算商场标准车位 (2.5m×5.3m) 开门余量与机械车位兼容度
    function getParkingFitMeta(width, length) {
      const w = width || 1900;
      const l = length || 4800;
      const doorClearance = Math.round((2500 - w) / 2);
      const lengthClearance = Math.max(0, 5300 - l);
      
      let doorTag = "开门充裕";
      let doorColor = "text-emerald-600";
      if (doorClearance < 280) {
        doorTag = "开门狭窄易碰";
        doorColor = "text-rose-600 font-bold";
      } else if (doorClearance < 320) {
        doorTag = "正常开门";
        doorColor = "text-slate-800";
      }

      let mechText = "🟢 通行无阻";
      let mechColor = "text-emerald-600";
      if (l > 5000 || w > 1900) {
        mechText = "🔴 超标慎选";
        mechColor = "text-rose-600";
      } else if (w > 1850) {
        mechText = "🟡 需1.9m宽位";
        mechColor = "text-amber-600";
      }

      return {
        doorClearance: doorClearance,
        lengthClearance: lengthClearance,
        doorTag: doorTag,
        doorColor: doorColor,
        mechText: mechText,
        mechColor: mechColor
      };
    }

    // 辅助函数：寻找同级别相近价位与尺寸的核心竞品 (找替代横评)
    function findSimilarCompetitors(targetSeries) {
      if (!targetSeries) return [];
      const tPrice = parseCarPrice(targetSeries);
      const tWb = targetSeries.wheelbase_max || targetSeries.wheelbase_min || 2800;
      const tLvl = (targetSeries.level || targetSeries.clean_level || '').toLowerCase();
      const isSuv = tLvl.includes('suv');
      const isMpv = tLvl.includes('mpv');

      const candidates = state.series.filter(s => {
        if (s.is_stopped) return false;
        if (s.series_id === targetSeries.series_id) return false;

        const sLvl = (s.level || s.clean_level || '').toLowerCase();
        if (isSuv && !sLvl.includes('suv')) return false;
        if (isMpv && !sLvl.includes('mpv')) return false;
        if (!isSuv && !isMpv && (sLvl.includes('suv') || sLvl.includes('mpv'))) return false;

        const sPrice = parseCarPrice(s);
        if (tPrice.avg > 0 && sPrice.avg > 0) {
          const diff = Math.abs(sPrice.avg - tPrice.avg);
          if (diff > Math.max(tPrice.avg * 0.35, 6)) return false;
        }

        const sWb = s.wheelbase_max || s.wheelbase_min || 0;
        if (Math.abs(sWb - tWb) > 150) return false;

        return true;
      });

      // 按口碑评分与轴距相近度综合排序
      candidates.sort((a, b) => {
        const scoreDiff = (b.score || 0) - (a.score || 0);
        if (Math.abs(scoreDiff) > 0.05) return scoreDiff;
        const diffA = Math.abs((a.wheelbase_max || 0) - tWb);
        const diffB = Math.abs((b.wheelbase_max || 0) - tWb);
        return diffA - diffB;
      });

      return candidates.slice(0, 3);
    }
"""

if "function getPwrRatioMeta(pwr) {" in text:
    text = text.replace("    function getPwrRatioMeta(pwr) {", helper_functions + "\n    function getPwrRatioMeta(pwr) {")
    print("✅ 成功注入价格、空间得房率与竞品推荐核心算法！")
else:
    print("❌ 未找到 getPwrRatioMeta 锚点")

# 更新 selectSeries 函数中关于得房率、车位体检和竞品雷达的数据绑定
old_select_series_content = """      // 渲染年款配置列表
      renderBoardVersions(s);"""

new_select_series_content = """      // 更新空间得房率与泊车体检看板
      const spaceMeta = getSpaceMeta(wb, l);
      const parkMeta = getParkingFitMeta(w, l);

      const sGradeEl = document.getElementById('boardSpaceGrade');
      if (sGradeEl) {
        sGradeEl.textContent = spaceMeta.level;
        sGradeEl.className = `text-[10px] font-mono px-2 py-0.5 rounded font-bold ${spaceMeta.badgeClass}`;
      }
      const sRatioEl = document.getElementById('boardSpaceRatioVal');
      if (sRatioEl) sRatioEl.textContent = `${spaceMeta.ratio}%`;

      const dClearEl = document.getElementById('boardDoorClearanceVal');
      if (dClearEl) {
        dClearEl.textContent = `${parkMeta.doorClearance}mm`;
        dClearEl.className = `text-base font-bold font-mono ${parkMeta.doorColor}`;
      }
      const dDescEl = document.getElementById('boardDoorDesc');
      if (dDescEl) dDescEl.textContent = `${parkMeta.doorTag} · 2.5m车位`;

      const mTagEl = document.getElementById('boardMechTag');
      if (mTagEl) {
        mTagEl.textContent = parkMeta.mechText;
        mTagEl.className = `text-[11px] font-bold ${parkMeta.mechColor}`;
      }

      // 渲染同级热门竞品雷达
      renderCompetitorsRadar(s);

      // 渲染年款配置列表
      renderBoardVersions(s);"""

if old_select_series_content in text:
    text = text.replace(old_select_series_content, new_select_series_content)
    print("✅ 成功在 selectSeries 注入看板数据联动！")
else:
    print("❌ 未找到 selectSeries 锚点")

# 注入 renderCompetitorsRadar 函数定义
competitors_radar_fn = """
    // 渲染同级热门竞品雷达
    function renderCompetitorsRadar(s) {
      const comps = findSimilarCompetitors(s);
      const deskList = document.getElementById('boardCompetitorsList');
      const mobileList = document.getElementById('mDrawerCompetitorsList');

      if (!comps || comps.length === 0) {
        const emptyHtml = '<div class="text-[11px] text-slate-400 py-1 col-span-3 text-center">暂无同级极近竞品</div>';
        if (deskList) deskList.innerHTML = emptyHtml;
        if (mobileList) mobileList.innerHTML = emptyHtml;
        return;
      }

      const deskHtml = comps.map(c => {
        const cCover = c.cover_url || DEFAULT_CAR_SVG;
        const cScore = c.score ? `${c.score.toFixed(2)}★` : '暂无分';
        return `
          <div class="bg-white p-2 rounded-lg border border-slate-200/90 hover:border-sky-300 transition-all cursor-pointer shadow-2xs group"
               onclick="selectSeries(${c.series_id}, true)">
            <div class="w-full h-14 rounded-md overflow-hidden bg-slate-900 border border-slate-100 relative mb-1.5">
              <img src="${cCover}" class="w-full h-full object-cover group-hover:scale-105 transition-transform" onerror="this.onerror=null; this.src=DEFAULT_CAR_SVG;" loading="lazy">
              <span class="absolute top-0.5 right-0.5 bg-black/60 text-amber-400 font-mono text-[9px] px-1 rounded">${cScore}</span>
            </div>
            <div class="text-xs font-bold text-slate-900 truncate">${c.display_series_name || c.series_name || c.series}</div>
            <div class="flex items-center justify-between mt-1 text-[10px]">
              <span class="font-mono font-bold text-sky-700">${c.price_str || '详询'}</span>
              <span class="font-mono text-slate-500">${c.wheelbase_max || c.wheelbase_min}mm</span>
            </div>
          </div>
        `;
      }).join('');

      if (deskList) deskList.innerHTML = deskHtml;
      if (mobileList) mobileList.innerHTML = deskHtml;

      // 绑定【一键并排对比】按钮
      const compBtn = document.getElementById('compareWithCompsBtn');
      const mCompBtn = document.getElementById('mCompareWithCompsBtn');
      const doBatchCompare = () => {
        // 将当前车与推荐竞品一起加入对比
        const allIds = [s.series_id, ...comps.map(c => c.series_id)].slice(0, 4);
        state.compareList = allIds;
        updateCompareCountUI();
        renderCards(false);
        openCompareModal();
      };
      if (compBtn) compBtn.onclick = doBatchCompare;
      if (mCompBtn) mCompBtn.onclick = doBatchCompare;
    }
"""

if "function switchSpecificVersion(seriesId, versionIndex) {" in text:
    text = text.replace("    function switchSpecificVersion(seriesId, versionIndex) {", competitors_radar_fn + "\n    function switchSpecificVersion(seriesId, versionIndex) {")
    print("✅ 成功注入 renderCompetitorsRadar 函数！")
else:
    print("❌ 未找到 switchSpecificVersion 锚点")

# 更新 openMobileDrawerWithData 适配手机端数据同步
old_mobile_drawer_data = """      document.getElementById('mDrawerPrice').textContent = s.price_str || '暂无报价';
      document.getElementById('mDrawerScore').textContent = s.score ? s.score.toFixed(2) : '暂无口碑';"""

new_mobile_drawer_data = """      document.getElementById('mDrawerPrice').textContent = s.price_str || '暂无报价';
      document.getElementById('mDrawerScore').textContent = s.score ? s.score.toFixed(2) : '暂无口碑';

      const sL = s.length_max || s.length_min || 4800;
      const sW = s.width_max || s.width_min || 1900;
      const sWb = s.wheelbase_max || s.wheelbase_min || 2900;
      const mSpaceMeta = getSpaceMeta(sWb, sL);
      const mParkMeta = getParkingFitMeta(sW, sL);

      const mSGrade = document.getElementById('mDrawerSpaceGrade');
      if (mSGrade) {
        mSGrade.textContent = mSpaceMeta.level;
        mSGrade.className = `text-[10px] font-mono px-1.5 py-0.2 rounded font-bold ${mSpaceMeta.badgeClass}`;
      }
      const mSRatio = document.getElementById('mDrawerSpaceRatioVal');
      if (mSRatio) mSRatio.textContent = `${mSpaceMeta.ratio}%`;

      const mDClear = document.getElementById('mDrawerDoorClearanceVal');
      if (mDClear) {
        mDClear.textContent = `${mParkMeta.doorClearance}mm`;
        mDClear.className = `font-mono font-bold mt-0.5 ${mParkMeta.doorColor}`;
      }
      const mMTag = document.getElementById('mDrawerMechTag');
      if (mMTag) {
        mMTag.textContent = mParkMeta.mechText;
        mMTag.className = `font-bold mt-0.5 ${mParkMeta.mechColor}`;
      }"""

if old_mobile_drawer_data in text:
    text = text.replace(old_mobile_drawer_data, new_mobile_drawer_data)
    print("✅ 成功在移动端抽屉注入得房率与泊车体检数据绑定！")
else:
    print("❌ 未找到 openMobileDrawerWithData 锚点")

# 在卡片列表 renderCards 中加入得房率标签
old_card_dim = """<span class="text-slate-600 text-[10px]">${s.length_min || s.length_max}×${s.width_min || s.width_max}×${s.height_min || s.height_max}</span>"""
new_card_dim = """<span class="text-slate-600 text-[10px]">${s.length_min || s.length_max}×${s.width_min || s.width_max}×${s.height_min || s.height_max}</span>
                    <span class="text-[9px] font-mono px-1 py-0.2 rounded bg-indigo-50 text-indigo-700 border border-indigo-100">得房率 ${(( (s.wheelbase_max||s.wheelbase_min)/(s.length_max||s.length_min) )*100).toFixed(1)}%</span>"""

if old_card_dim in text:
    text = text.replace(old_card_dim, new_card_dim)
    print("✅ 成功在卡片列表展示【空间得房率】标签！")
else:
    print("❌ 未找到卡片列表尺寸行锚点")

# 在对比表格 renderCompareModal 中加入空间得房率、商场车位开门余量、机械车位适应度 3 行
old_compare_rows = """                <tr>
                  <td class="p-2 font-medium text-slate-500 bg-slate-50/50">轴距 (mm)</td>
                  ${cars.map(c => `
                    <td class="p-2 font-mono font-bold text-sky-700 text-sm">
                      ${c.wheelbase_min || c.wheelbase_max} mm
                    </td>
                  `).join('')}
                </tr>"""

new_compare_rows = """                <tr>
                  <td class="p-2 font-medium text-slate-500 bg-slate-50/50">轴距 (mm)</td>
                  ${cars.map(c => `
                    <td class="p-2 font-mono font-bold text-sky-700 text-sm">
                      ${c.wheelbase_min || c.wheelbase_max} mm
                    </td>
                  `).join('')}
                </tr>
                <tr>
                  <td class="p-2 font-medium text-slate-500 bg-slate-50/50">空间得房率 (轴长比)</td>
                  ${cars.map(c => {
                    const l = c.length_max || c.length_min || 4800;
                    const wb = c.wheelbase_max || c.wheelbase_min || 2800;
                    const r = ((wb / l) * 100).toFixed(1);
                    return `
                      <td class="p-2 font-mono font-bold text-indigo-600">
                        ${r}% <span class="text-[10px] font-normal text-slate-500">${r >= 61.5 ? '(高得房率)' : (r >= 59 ? '(均衡)' : '(运动长机舱)')}</span>
                      </td>
                    `;
                  }).join('')}
                </tr>
                <tr>
                  <td class="p-2 font-medium text-slate-500 bg-slate-50/50">商场标准车位开门余量</td>
                  ${cars.map(c => {
                    const w = c.width_max || c.width_min || 1900;
                    const gap = Math.round((2500 - w) / 2);
                    const color = gap < 280 ? 'text-rose-600 font-bold' : (gap < 320 ? 'text-slate-800' : 'text-emerald-600 font-bold');
                    return `
                      <td class="p-2 font-mono ${color}">
                        ${gap} mm ${gap < 280 ? '(偏窄易磕门)' : (gap < 320 ? '(正常)' : '(充裕)')}
                      </td>
                    `;
                  }).join('')}
                </tr>
                <tr>
                  <td class="p-2 font-medium text-slate-500 bg-slate-50/50">机械立体车位兼容度</td>
                  ${cars.map(c => {
                    const l = c.length_max || c.length_min || 4800;
                    const w = c.width_max || c.width_min || 1900;
                    let tag = '🟢 机械位通行';
                    if (l > 5000 || w > 1900) tag = '🔴 超标慎选(超长/超宽)';
                    else if (w > 1850) tag = '🟡 需1.9m宽体机械位';
                    return `
                      <td class="p-2 font-bold text-xs">
                        ${tag}
                      </td>
                    `;
                  }).join('')}
                </tr>"""

if old_compare_rows in text:
    text = text.replace(old_compare_rows, new_compare_rows)
    print("✅ 成功在对比模态框表格注入空间得房率与泊车体检维度！")
else:
    print("❌ 未找到对比表格锚点")

with open(TEMPLATE_PATH, "w", encoding="utf-8") as f:
    f.write(text)

print("🎉 逻辑脚本与数据联动全部注入成功！")
