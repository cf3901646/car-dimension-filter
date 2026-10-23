# -*- coding: utf-8 -*-
import os
import sys

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

TEMPLATE_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "car_dimension_filter", "template.html")

with open(TEMPLATE_PATH, "r", encoding="utf-8") as f:
    text = f.read()

# 1. 在桌面端看板增加【空间得房率与泊车体检】与【同级竞品雷达】HTML
old_board_deck = """          <!-- 商业级动力总成与推重比遥测控制台 (Precision Powertrain Telemetry Deck) -->
          <div class="telemetry-deck bg-[#F8FAFC] rounded-xl border border-slate-200/90 p-3.5 space-y-3">"""

new_board_deck_addon = """          <!-- 商业级动力总成与推重比遥测控制台 (Precision Powertrain Telemetry Deck) -->
          <div class="telemetry-deck bg-[#F8FAFC] rounded-xl border border-slate-200/90 p-3.5 space-y-3">"""

old_board_versions = """          <!-- 年款与具体配置规格切换列表 -->
          <div class="space-y-1.5 pt-1">
            <div class="flex items-center justify-between text-xs text-slate-500">
              <span class="font-semibold text-slate-700">具体配置与驱动联动切换</span>
              <span id="boardVersionCount" class="text-[11px]">共 0 款在售配置</span>
            </div>
            <div id="boardVersionList" class="max-h-48 overflow-y-auto space-y-1 custom-scrollbar pr-1">
              <!-- 动态配置单选 -->
            </div>
          </div>"""

new_board_addons = """          <!-- 空间得房率与商场泊车体检工程视窗 -->
          <div class="bg-[#F8FAFC] rounded-xl border border-slate-200/90 p-3 space-y-2">
            <div class="flex items-center justify-between text-xs">
              <div class="flex items-center gap-1.5">
                <span class="w-1.5 h-1.5 rounded-full bg-indigo-500"></span>
                <span class="font-bold text-slate-800">空间得房率与商场车位体检</span>
              </div>
              <span id="boardSpaceGrade" class="text-[10px] font-mono px-2 py-0.5 rounded font-bold bg-indigo-50 text-indigo-700 border border-indigo-200">👑 高得房率座舱</span>
            </div>
            
            <div class="grid grid-cols-3 divide-x divide-slate-200 pt-1 text-xs">
              <!-- 得房率 (轴长比) -->
              <div class="px-2 first:pl-0">
                <div class="text-[10px] text-slate-500">轴长空间得房率</div>
                <div class="flex items-baseline gap-1 mt-0.5">
                  <span id="boardSpaceRatioVal" class="text-base font-bold font-mono text-indigo-600">--%</span>
                </div>
                <div class="text-[9px] text-slate-400 font-mono">轴距/车长比率</div>
              </div>

              <!-- 商场车位开门余量 -->
              <div class="px-2">
                <div class="text-[10px] text-slate-500">商场标准位开门</div>
                <div class="flex items-baseline gap-1 mt-0.5">
                  <span id="boardDoorClearanceVal" class="text-base font-bold font-mono text-slate-800">-- mm</span>
                </div>
                <div id="boardDoorDesc" class="text-[9px] text-slate-400 font-mono">2.5m标准车位</div>
              </div>

              <!-- 机械立体车位适应度 -->
              <div class="px-2 last:pr-0">
                <div class="text-[10px] text-slate-500">机械车位体检</div>
                <div class="mt-0.5">
                  <span id="boardMechTag" class="text-[11px] font-bold text-emerald-600">🟢 通行无阻</span>
                </div>
                <div class="text-[9px] text-slate-400 font-mono">限宽1850mm标准</div>
              </div>
            </div>
          </div>

          <!-- 同级相近价位核心竞品雷达 (找替代与横评) -->
          <div class="bg-[#F8FAFC] rounded-xl border border-slate-200/90 p-3 space-y-2">
            <div class="flex items-center justify-between text-xs">
              <div class="flex items-center gap-1.5">
                <i class="fa-solid fa-crosshairs text-sky-600"></i>
                <span class="font-bold text-slate-800">同级热门竞品雷达 (相似价位与尺寸)</span>
              </div>
              <button id="compareWithCompsBtn" class="text-[10px] font-semibold px-2 py-1 rounded-lg bg-sky-600 hover:bg-sky-700 text-white transition-colors flex items-center gap-1 shadow-2xs">
                <i class="fa-solid fa-code-compare"></i> 一键并排对比
              </button>
            </div>
            
            <!-- 竞品微卡片网格 -->
            <div id="boardCompetitorsList" class="grid grid-cols-1 sm:grid-cols-3 gap-2 pt-0.5">
              <!-- 动态注入 3 款同级直接竞品 -->
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
          </div>"""

if old_board_versions in text:
    text = text.replace(old_board_versions, new_board_addons)
    print("✅ 成功在桌面端看板注入【空间得房率】与【竞品雷达】HTML！")
else:
    print("❌ 未找到桌面端看板旧年款列表锚点")

# 2. 在手机端抽屉中增加相应视窗
old_drawer_end = """        <div class="grid grid-cols-2 divide-x divide-slate-200 pt-1 text-[11px]">
          <div class="pr-2">
            <span class="text-slate-500 text-[10px]">驱动总成: </span>
            <span id="mDrawerDriveType" class="font-bold text-sky-600">四驱</span>
          </div>
          <div class="pl-2">
            <span class="text-slate-500 text-[10px]">马力输出: </span>
            <span id="mDrawerHpVal" class="font-bold font-mono text-slate-900">-- Ps</span>
          </div>
        </div>
      </div>"""

new_drawer_addons = """        <div class="grid grid-cols-2 divide-x divide-slate-200 pt-1 text-[11px]">
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

      <!-- 手机端空间得房率与车位体检 -->
      <div class="bg-[#F8FAFC] p-3 rounded-xl border border-slate-200/90 space-y-2 text-xs">
        <div class="flex items-center justify-between">
          <span class="font-bold text-slate-800">空间得房率与商场车位体检</span>
          <span id="mDrawerSpaceGrade" class="text-[10px] font-mono px-1.5 py-0.2 rounded font-bold bg-indigo-50 text-indigo-700 border border-indigo-200">高得房率</span>
        </div>
        <div class="grid grid-cols-3 divide-x divide-slate-200 text-center">
          <div>
            <div class="text-[10px] text-slate-500">空间得房率</div>
            <div id="mDrawerSpaceRatioVal" class="font-mono font-bold text-indigo-600 mt-0.5">--%</div>
          </div>
          <div>
            <div class="text-[10px] text-slate-500">商场位开门</div>
            <div id="mDrawerDoorClearanceVal" class="font-mono font-bold text-slate-800 mt-0.5">-- mm</div>
          </div>
          <div>
            <div class="text-[10px] text-slate-500">机械车位</div>
            <div id="mDrawerMechTag" class="font-bold text-emerald-600 mt-0.5">🟢 可停</div>
          </div>
        </div>
      </div>

      <!-- 手机端同级热门竞品推荐 -->
      <div class="bg-[#F8FAFC] p-3 rounded-xl border border-slate-200/90 space-y-2 text-xs">
        <div class="flex items-center justify-between">
          <span class="font-bold text-slate-800">同级热门竞品雷达</span>
          <button id="mCompareWithCompsBtn" class="text-[10px] font-semibold px-2 py-0.5 rounded bg-sky-600 text-white">一键对比</button>
        </div>
        <div id="mDrawerCompetitorsList" class="space-y-1.5 pt-0.5"></div>
      </div>"""

if old_drawer_end in text:
    text = text.replace(old_drawer_end, new_drawer_addons)
    print("✅ 成功在移动端抽屉注入【空间得房率】与【竞品雷达】HTML！")
else:
    print("❌ 未找到移动端抽屉锚点")

with open(TEMPLATE_PATH, "w", encoding="utf-8") as f:
    f.write(text)
print("Updated HTML structures successfully.")
