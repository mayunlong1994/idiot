# IDIOT《礼物》v2 评分脚本（PowerShell 版，与 score_gift.py 同公式）
# 用法: powershell -File score_gift.ps1 models.json
# subagent 只返回客观事实，本脚本做确定性算分。权重集中在顶部，迭代只改这里。
param([Parameter(Mandatory=$true)][string]$JsonPath)

# ---- 载重→分值 ----
$W = @{ '极高'=4; '高'=3; '中'=2; '低'=1 }
$LOAD = @{}
foreach($h in '极高:M12 2-3 2-3b 3-7 4-4 5-3 6-0 6-4 6-5 6-6 6-9 7-6',
              '高:M1 M4 M6 M7 M9 1-3 1-4 1-6 1-7 1-8 2-2 2-4 2-5 2-6 2-12 2-13 2-16 4-2 5-1 5-2 5-7 6-1 6-2 6-3 6-7 6-8 6-10 6-11 7-1 7-2 7-3 7-4 7-5',
              '中:M2 M8 1-1 2-1 2-7 2-8 2-11 3-1 3-8 4-5 4-6 5-4 5-5 5-6',
              '低:M3 M5 M10 M11 1-2 1-5 1-9 2-9 2-10 2-14 2-15 3-2 3-3 3-4 3-5 3-6 4-1 4-3 6-12'){
  $parts = $h.Split(':'); $tier=$parts[0]; foreach($id in $parts[1].Split(' ')){ $LOAD[$id]=$tier }
}
$EGGS = @('2-13','2-14','3-2','4-2','6-9')  # 2-13: 读出"故意虚晃一枪"才算彩蛋

# ---- 可调权重 ----
$CONCL = @{ '正确'=60; '部分'=40; '错误'=20 }
$LADDER = @{ 'L0'=15; 'L1'=10; 'L2'=5; 'L2+'=2; 'L3'=0; 'L4'=-10 }
$P_FANGONG=-15; $P_JIAXI=-5; $P_TRAP=-8; $EGG_BONUS=4
$LEN_THRESH=4000; $LEN_STEP=2000; $LEN_PEN=-2; $ROUND_THRESH=6; $ROUND_PEN=-1

function HookPts($ids){ $s=0; foreach($i in $ids){ if($LOAD.ContainsKey($i)){ $s += $W[$LOAD[$i]] } }; $s }

$data = Get-Content $JsonPath -Raw -Encoding UTF8 | ConvertFrom-Json
$rows = foreach($m in $data){
  $base = $CONCL[$m.conclusion]
  $hook = (HookPts $m.hooks_hit) - (HookPts $m.hooks_misread)
  $egg  = $EGG_BONUS * (@($m.eggs | Where-Object { $EGGS -contains $_ }).Count)
  $lad  = if($LADDER.ContainsKey($m.ladder)){ $LADDER[$m.ladder] } else { 0 }
  $beh  = $lad + $P_FANGONG*$m.fangong + $P_JIAXI*$m.jiaxi + $P_TRAP*(@($m.traps).Count)
  $corr = $LEN_PEN*[Math]::Max(0,[Math]::Floor(($m.wordcount-$LEN_THRESH)/$LEN_STEP)) + $ROUND_PEN*[Math]::Max(0,$m.rounds-$ROUND_THRESH)
  $raw  = $base + $hook + $egg + $beh + $corr
  $total= if($m.conclusion -eq '正确'){ [Math]::Max(60,$raw) } else { [Math]::Min(59,$raw) }
  [PSCustomObject]@{ 模型=$m.model; 模态=$m.mode; 结论=$m.conclusion; 总分=[int]$total; 基底=$base; 钩子=$hook; 彩蛋=$egg; 行为=$beh; 修正=$corr }
}
$rows | Sort-Object 总分 -Descending | Format-Table -AutoSize
