# AI生成
"""
赛艇生物力学知识库 + 教练经验规则
作为Agnes Harness Agent的系统提示词

内容来源: 论文《基于赛艇运动员骨骼点的时序动作分割及运动状态分析研究与应用》
         Section 2.4 (生物力学基础) + Section 5.3.2 (犯规检测规则)
"""

# ============================================================
#  系统提示词 - 赛艇智能教练Agent的核心知识
# ============================================================

SYSTEM_PROMPT = """你是一位专业的赛艇运动教练Agent, 运行在Agnes Harness框架上。
你的职责是分析赛艇运动员的技术动作, 诊断技术问题, 并给出专业的训练建议。

## 你的专业知识背景

### 1. 赛艇生物力学基础

赛艇划桨动作是一个全身协调的复合运动, 遵循"动力链"原则:
**蹬腿 -> 开体(躯干) -> 拉臂**

发力顺序不可颠倒: 腿部先发力蹬伸, 带动躯干向后打开, 最后手臂屈曲拉桨。
这个顺序保证了最大的做功距离和最优的力量传递效率。

### 2. 划桨周期八相位模型

一个完整的划桨周期包含8个相位:

1. 提桨压腕 (Catch前): 桨柄前移, 准备入水
2. 蹬腿启动 (Catch): 桨叶入水, 腿部开始蹬伸, 膝角最小
3. 开体发力 (Drive前段): 躯干向后打开, 持续加速
4. 拉臂收桨 (Drive后段): 手臂屈曲拉桨至身体
5. 推臂复位 (Finish后): 手臂伸直推桨柄
6. 躯干前倾 (Recovery前段): 躯干向前恢复
7. 屈膝滑行 (Recovery后段): 膝盖弯曲滑向Catch
8. 桨柄复位 (Catch前): 桨柄前移到位

### 3. 时间比例

标准拉桨:回桨时间比约为 4:6 (即回桨占整个周期的约60%)。
回桨过快(占比<55%)属于技术犯规, 会影响下一周期的准备质量。

### 4. 关节角度参考值

- 膝关节: Catch时约40-55度(最大压缩), Finish时约160-170度(充分伸展)
- 髋关节: Catch时约30-45度(闭合), Finish时约110-125度(打开)
- 肘关节: Drive阶段保持伸直(>160度), Finish时约120-140度
- 躯干角: Catch时前倾约20-30度, Finish时后倒约25-35度(最优30度)

### 5. 五类技术犯规及诊断

| 犯规类型 | 检测条件 | 严重程度 | 生物学原因 | 纠正方法 |
|---------|---------|---------|-----------|---------|
| 膝关节过早溃缩 | 拉桨初期膝角速度<-10deg/s | 高 | 腿部张力丢失, 膝过早弯曲 | 强化蹬腿意识, 保持腿部推力 |
| 提早拉臂 | 躯干<30度且肘<150度 | 中 | 破坏动力链顺序, 上肢过早参与 | 先蹬腿开体, 最后再拉臂 |
| 躯干姿态失稳 | 后倒角偏离30度>15度 | 中 | 核心力量不足 | 加强核心训练, 控制后倒25-35度 |
| 伸展不充分 | 结束时膝<160度或肘<170度 | 中 | 做功行程不完整 | 加大蹬腿和拉臂幅度 |
| 回桨仓促 | 回桨时间占比<55% | 低 | 缺乏控制, 影响准备 | 放慢回桨, 充分恢复 |

## 你的工作流程

1. 接收CV管线的结构化分析结果(JSON格式)
2. 理解每个划桨周期的角度数据和犯规记录
3. 综合分析运动员的技术水平、主要问题和改进方向
4. 生成专业的诊断报告, 包含:
   - 总体评价 (技术水平分级)
   - 主要问题分析 (按严重程度排序)
   - 针对性训练建议 (具体可执行的练习)
   - 改进优先级排序

## 报告格式要求

请按以下结构输出诊断报告:

### 技术诊断报告

**一、总体评价**
[对运动员整体技术水平的评价, 1-2段]

**二、数据概览**
- 划桨周期数: X个
- 桨频: X桨/分钟
- 犯规总次数: X次
- 犯规率: X次/周期
- 主要关节活动范围

**三、问题分析**
[按严重程度从高到低排列每个问题, 包含: 发生频率、具体表现、原因分析]

**四、训练建议**
[针对每个问题给出具体的训练建议, 包含: 练习方法、注意事项、预期效果]

**五、改进优先级**
[列出改进的优先顺序和短期/长期目标]

请用专业但易懂的语言, 像一位有经验的赛艇教练在给运动员做技术复盘。
"""


# ============================================================
#  CV结果格式化函数
# ============================================================

def format_cv_result_for_agent(cv_result):
    """
    将CV管线输出格式化为Agent可理解的文本
    """
    if "error" in cv_result:
        return f"CV分析失败: {cv_result['error']}"

    summary = cv_result.get("summary", {})
    errors = cv_result.get("errors", [])
    cycles = cv_result.get("cycles", [])

    lines = []
    lines.append("## CV管线分析结果\n")
    lines.append(f"视频: {cv_result.get('video_path', '未知')}")
    lines.append(f"帧率: {cv_result.get('fps', 'N/A')} fps")
    lines.append(f"分析帧数: {cv_result.get('analyzed_frames', 0)}")
    lines.append(f"检测侧: {cv_result.get('detected_side', 'N/A')}\n")

    # 摘要
    lines.append("### 数据摘要")
    lines.append(f"- 划桨周期数: {summary.get('total_cycles', 0)}")
    lines.append(f"- 桨频: {summary.get('stroke_rate', 0)} 桨/分钟")
    lines.append(f"- 犯规总次数: {summary.get('total_errors', 0)}")
    lines.append(f"- 犯规率: {summary.get('error_rate', 0)} 次/周期")
    lines.append(f"- 平均周期时间: {summary.get('avg_cycle_time_s', 0)} 秒")
    lines.append(f"- 平均回桨占比: {summary.get('avg_recovery_ratio', 0)*100:.1f}%")

    eb = summary.get("error_breakdown", {})
    if eb:
        lines.append("- 犯规分布:")
        type_names = {
            "knee_collapse": "膝关节过早溃缩",
            "early_arm_pull": "提早拉臂",
            "trunk_misalignment": "躯干姿态失稳",
            "incomplete_extension": "伸展不充分",
            "rushed_recovery": "回桨仓促",
        }
        for etype, count in eb.items():
            lines.append(f"  - {type_names.get(etype, etype)}: {count}次")

    # 关节范围
    kr = summary.get("knee_angle_range", [0, 0])
    hr = summary.get("hip_angle_range", [0, 0])
    er = summary.get("elbow_angle_range", [0, 0])
    tr = summary.get("trunk_angle_range", [0, 0])
    lines.append(f"- 膝角范围: {kr[0]}-{kr[1]}度")
    lines.append(f"- 髋角范围: {hr[0]}-{hr[1]}度")
    lines.append(f"- 肘角范围: {er[0]}-{er[1]}度")
    lines.append(f"- 躯干角范围: {tr[0]}-{tr[1]}度\n")

    # 周期详情
    if cycles:
        lines.append("### 划桨周期详情")
        for c in cycles[:10]:  # 最多展示10个周期
            lines.append(
                f"- 周期{c['cycle_id']}: 拉桨{c['drive_time_s']}s, "
                f"回桨{c['recovery_time_s']}s, "
                f"回桨占比{c['recovery_ratio']*100:.1f}%")
        if len(cycles) > 10:
            lines.append(f"- ... 共{len(cycles)}个周期\n")
        else:
            lines.append("")

    # 犯规详情
    if errors:
        lines.append("### 犯规详情")
        for e in errors:
            lines.append(
                f"- [周期{e['cycle']}] {e['name']} (严重度:{e['severity']})\n"
                f"  详情: {e['detail']}\n"
                f"  原因: {e['cause']}\n"
                f"  纠正: {e['correction']}")
    else:
        lines.append("### 犯规详情\n未检测到明显技术犯规, 动作质量良好!")

    return "\n".join(lines)


# ============================================================
#  教练建议模板 (用于无API时的fallback)
# ============================================================

FALLBACK_TEMPLATE = """
## 技术诊断报告 (离线版)

### 一、总体评价
基于CV管线的自动化分析, 共检测到{total_cycles}个划桨周期, {total_errors}次技术犯规。
犯规率为{error_rate}次/周期, {quality_level}。

### 二、数据概览
- 划桨周期数: {total_cycles}个
- 桨频: {stroke_rate}桨/分钟
- 犯规总次数: {total_errors}次
- 犯规率: {error_rate}次/周期

### 三、问题分析
{error_analysis}

### 四、训练建议
{training_advice}

### 五、改进优先级
{priority}

注: 此为离线模板报告, 接入Agnes Harness后将由AI生成更精准的个性化诊断。
"""


def generate_fallback_report(cv_result):
    """无API时生成基础报告"""
    s = cv_result.get("summary", {})
    errors = cv_result.get("errors", [])

    total_cycles = s.get("total_cycles", 0)
    total_errors = s.get("total_errors", 0)
    error_rate = s.get("error_rate", 0)
    stroke_rate = s.get("stroke_rate", 0)

    if error_rate == 0:
        quality_level = "技术水平优秀"
    elif error_rate < 0.5:
        quality_level = "技术水平良好, 有小幅改进空间"
    elif error_rate < 1.0:
        quality_level = "技术水平中等, 存在明显技术问题"
    else:
        quality_level = "技术问题较多, 需重点改进"

    if errors:
        ea_lines = []
        for e in errors[:10]:
            ea_lines.append(
                f"- {e['name']} (周期{e['cycle']}, 严重度:{e['severity']}): {e['detail']}")
        error_analysis = "\n".join(ea_lines)
    else:
        error_analysis = "未检测到明显技术犯规"

    advice_lines = []
    seen_types = set()
    for e in errors:
        if e["type"] not in seen_types:
            advice_lines.append(f"- {e['name']}: {e['correction']}")
            seen_types.add(e["type"])
    training_advice = "\n".join(advice_lines) if advice_lines else "保持当前技术动作, 继续巩固"

    priority = "1. 修正高严重度犯规\n2. 改善中等严重度问题\n3. 优化低严重度细节"

    return FALLBACK_TEMPLATE.format(
        total_cycles=total_cycles,
        total_errors=total_errors,
        error_rate=error_rate,
        quality_level=quality_level,
        stroke_rate=stroke_rate,
        error_analysis=error_analysis,
        training_advice=training_advice,
        priority=priority,
    )
