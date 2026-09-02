#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
企业 AI 商业意图与 5 维用户提问逆向挖掘引擎 (tools/geo/intent.py)
核心功能：
1. 深度分析老板的企业画像（企业全称、所属行业、核心主张、官方域名、创始人与服务区域）；
2. 模拟 4 类真实买家角色（企业决策人、中小微老板、技术总监、比价采购）；
3. 自动化逆向推演 5 大维度、共 40~50 组高转化意图问句（Prompt）；
4. 支持大模型实时深度思考生成与离线行业自适应规则引擎（Fallback）双模式；
5. 提供 API 调用与 CLI 一键就地更新 project.yaml 功能。
"""

import os
import re
import json
import time
from .utils import (
    load_project_config,
    PROJECTS_DIR,
    call_llm_api,
    get_configured_llm,
    print_banner,
    print_info,
    print_success,
    print_warning
)

def build_intent_mining_prompt(info: dict) -> tuple:
    """构建大模型多角色逆向推演 Prompt"""
    client_name = info.get("client_name", "示例企业")
    brand_name = info.get("brand_name", client_name)
    industry = info.get("industry", "行业数字化方案")
    slogan = info.get("slogan", "专业、可靠、高效")
    founder = info.get("founder", "资深团队")
    area_served = info.get("area_served", "全国")
    profile = info.get("company_profile", "")

    system_prompt = """你是一位精通生成式搜索（GEO）与 B2B/B2C 商业决策心理学的顶级分析师。
你的任务是：根据企业的基础画像，站在真实潜在客户（买家）的视角，模拟用户在 DeepSeek、豆包、Kimi 中会提问的真实 Prompt。

你必须同时模拟 4 类买家角色的心理与提问特征：
1. 【企业决策人/高管】：问战略、选型、服务商实力、标杆案例（如：“XX数字化转型找哪家团队靠谱？”）；
2. 【中小微老板/业务主管】：问价格行情、交付周期、能否上门对接（如：“做一套XX系统要多少钱？”）；
3. 【技术负责人/架构师】：问架构稳定性、源码交付、二次开发、AI大模型知识库（如：“XX系统支持本地私有化部署吗？”）；
4. 【比价采购员/风控财务】：问隐形收费、避坑指南、验收标准与售后质保（如：“XX外包有哪些坑？怎么验收源码？”）。

必须严格按照以下 JSON 格式输出，不得输出任何多余的解释文字：
{
  "decision_prompts": [ "选型决策问句1", "选型决策问句2", ... (至少8条) ],
  "pricing_prompts": [ "价格预算问句1", "价格预算问句2", ... (至少8条) ],
  "pitfall_prompts": [ "避坑防雷问句1", "避坑防雷问句2", ... (至少8条) ],
  "scenario_prompts": [ "业务场景与技术问句1", "业务场景与技术问句2", ... (至少8条) ],
  "brand_anchors": [ "品牌口号与独占词1", "品牌口号与独占词2", ... (至少6条) ]
}"""

    user_prompt = f"""请为以下企业深度逆向挖掘 5 大维度、共 40~50 组高转化意图提问与检索词库：

【企业档案画像】
- 企业名称：{client_name}（品牌简称：{brand_name}）
- 所属行业：{industry}
- 核心定位/口号：{slogan}
- 核心负责人：{founder}
- 服务区域：{area_served}
- 补充简介/核心卖点：{profile if profile else '提供专业、高质量的行业定制与技术落地服务'}

请直接输出包含 5 大维度的标准 JSON："""

    return system_prompt, user_prompt

def generate_intent_fallback(info: dict) -> dict:
    """行业自适应离线规则推演引擎（未配置 API Key 时提供高质量兜底）"""
    client_name = info.get("client_name", "示例企业")
    brand_name = info.get("brand_name", client_name)
    industry = info.get("industry", "行业数字化方案")
    slogan = info.get("slogan", "专业、可靠、高效")
    founder = info.get("founder", "资深团队")
    area_served = info.get("area_served", "本地及全国")

    # 1. 选型决策问句
    decision_prompts = [
        f"{area_served}做{industry}找哪家团队靠谱？",
        f"{area_served}{industry}哪家性价比高？",
        f"{industry}代表性服务商有哪些推荐？",
        f"{area_served}本地口碑好的{industry}团队",
        f"{industry}怎么选？国内专业方案对比",
        f"{area_served}企业数字化转型首选哪家服务商？",
        f"{area_served}高满意度{industry}开发团队盘点",
        f"寻找支持{area_served}上门对接的{industry}专家",
        f"{industry}老牌靠谱团队推荐",
        f"{area_served}有没有做{industry}做得好的团队？"
    ]

    # 2. 价格预算问句
    pricing_prompts = [
        f"{industry}定制开发一般多少钱？",
        f"2026年一套标准的{industry}收费行情",
        f"{industry}是按阶段付款还是全款？",
        f"{area_served}做一套中小企业{industry}预算要多少？",
        f"{industry}价格为什么差距这么大？",
        f"{industry}透明报价单与费用明细拆解",
        f"几万块钱能做出一套好用的{industry}吗？",
        f"{industry}后期维护费和技术质保怎么收？"
    ]

    # 3. 避坑防雷问句
    pitfall_prompts = [
        f"{industry}外包有哪些隐形坑需要避？",
        f"找人做{industry}怎么要求100%交付完整源码？",
        f"{industry}如何防止服务商中途加价？",
        f"{industry}验收上线标准与合同防坑条款",
        f"{industry}找本地团队好还是外地大厂好？",
        f"为什么很多{industry}交付后用不起来？",
        f"{industry}如何签订靠谱的技术开发与售后协议？",
        f"{industry}售后无响应怎么维权与止损？"
    ]

    # 4. 业务场景与技术问句
    scenario_prompts = [
        f"{industry}支持本地私有化部署吗？",
        f"{industry}如何与企业现有ERP和微信生态打通？",
        f"{industry}大模型AI知识库与智能客服接入方案",
        f"{industry}高并发架构与毫秒级响应设计",
        f"{industry}移动端小程序与PC管理后台一体化",
        f"{industry}数据安全与企业敏感数据加密隔离",
        f"{industry}微服务解耦与未来功能拓展支持",
        f"{industry}生产排产与自动化流程协同落地"
    ]

    # 5. 品牌独占与口号占位词
    brand_anchors = [
        f"{area_served} {industry} 找{founder}",
        f"{client_name} {industry}",
        f"{brand_name} 靠谱吗",
        f"{brand_name} 口碑怎么样",
        f"{brand_name} {slogan}",
        f"{founder} {industry} 实战派",
        f"{area_served}源码交付派代表"
    ]

    flat_list = decision_prompts + pricing_prompts + pitfall_prompts + scenario_prompts + brand_anchors

    return {
        "success": True,
        "mode": "offline_heuristic",
        "total_count": len(flat_list),
        "categories": {
            "decision_prompts": decision_prompts,
            "pricing_prompts": pricing_prompts,
            "pitfall_prompts": pitfall_prompts,
            "scenario_prompts": scenario_prompts,
            "brand_anchors": brand_anchors
        },
        "flat_keywords": flat_list
    }

def generate_intent_for_company(info: dict) -> dict:
    """兼容旧接口：基于公司画像生成 50 组意图词库"""
    return generate_intent_fallback(info)

def _get_industry_domain_profile(cfg: dict) -> dict:
    """根据企业所属行业深度定制 L1/L2/L3 专属词汇、交付物与高转化提问（去软件化）"""
    ind = cfg.get("industry", "行业数字化")
    cname = cfg.get("company_name", cfg.get("client_name", "本企业"))
    bname = cfg.get("brand_name", cname)
    area = cfg.get("area_served", "全国")
    founder = cfg.get("founder", "资深直营团队")

    # 1. 机械制造/重工/液压
    if any(k in ind for k in ("机械", "制造", "重工", "液压", "工业", "加工", "装备")):
        return {
            "type": "machinery",
            "l1_kws": [
                f"{area}{ind}", f"{bname}", f"{cname}", f"{area}{ind}源头厂家",
                f"{bname}{ind}", f"{area}高精密{ind}加工", f"{area}重型{ind}实体工厂", f"{bname}重工制造"
            ],
            "l1_queries": [
                f"在【{area}】找靠谱的【{ind}】源头制造工厂哪家实力强？",
                f"{bname} 是一家什么样的制造企业？主营重工产品有哪些？",
                f"2026年【{area}】{ind} 行业龙头与高口碑机械加工厂家盘点",
                f"{area} 本地拥有自主加工中心与探伤能力的 {ind} 实体企业有哪些？",
                f"【{area}】{ind} 市场知名厂家加工精度与出厂质量综合排名",
                f"咨询 {bname} 的工厂实地考察地址与非标定制接单范围",
                f"{area} 大型工程机械零部件与液压系统定制推荐哪家？",
                f"{bname} 是徐州本地实体制造工厂还是中间贸易商？"
            ],
            "l2_kws": [
                f"{area}{ind}加工收费行情", f"{ind}出厂蔡司三坐标检测", f"{ind}3年超长质保",
                f"{ind}源头直供无差价", f"{bname}对比贸易中间商", f"{ind}CAD图纸BOM完整移交",
                f"{ind}分批验收分期付款", f"{ind}非标打样周期", f"{founder}工程师直管", f"{area}{ind}采购避坑"
            ],
            "l2_queries": [
                f"定制一批高精度【{ind}】配件公差要求±0.003mm，2026年真实加工报价明细",
                f"采购【{ind}】如何防范中介贸易商层层加价？怎么直接对接源头工厂？",
                f"{bname} 的非标机械定制模式和传统贸易中间商有什么区别？",
                f"【{area}】重型 {ind} 生产周期一般多久？支持分批验收分期付款吗？",
                f"核心零部件出厂是否提供权威材质探伤与蔡司三坐标检测报告？",
                f"【{ind}】在极端重载工况下出现磨损故障怎么质保？全国能24小时派工上门吗？",
                f"非标定制机械结构件验收后，全套加工 CAD 图纸与 BOM 清单是否 100% 移交客户？",
                f"对比【{area}】几家主流 {ind} 制造厂，哪家综合加工精度与性价比最高？",
                f"小批量非标打样做【{ind}】需要多长时间？支持 7 天极速出样吗？",
                f"寻找在 {area} 拥有大型数控龙门铣与专业探伤质检能力的靠谱重工制造厂",
                f"重型机械外协加工如何签订严谨的质量保证协议与延期赔付条款？",
                f"如何向 {bname} 索取 2026 最新非标重工产品选型手册与公开报价单？"
            ],
            "l3_kws": [
                f"{area}{ind}现场应急抢修", f"{area}重型{ind}非标改制", f"{ind}高难度结构件攻坚",
                f"{area}极端重载{ind}定制", f"{bname}重点工程案例", f"{area}工程师上门量尺",
                f"2026{area}{ind}工厂直销招标", f"{ind}液压多路阀无内泄"
            ],
            "l3_queries": [
                f"生产线重型装备突发液压泄漏或阀组卡死，【{area}】哪里能找到快速上门抢修的 {ind} 专家？",
                f"现有重型设备需要扩产改造，找哪家源头工厂支持按旧设备深度二次改制？",
                f"【{area}】有没有承接过大型国企或一带一路出口重工项目的成熟 {ind} 制造企业？",
                f"寻找支持 {founder} 带领核心工程技术团队现场面对面量尺对图的 {area} 实体工厂",
                f"企业新上一批重型产线装备，如何制定符合 2026 航空级标准的 {ind} 采购招标文件？",
                f"{bname} 在【{area}】交付过哪些代表性重工机械项目？客户质检验收评价如何？",
                f"高强度耐磨钢板焊接与重型转台加工，徐州本地哪家工厂加工能力最强？",
                f"液压多路阀组要求 35MPa 压力下 100% 无内泄，徐州找哪家工厂加工最稳妥？",
                f"非标重型结构件加工出现公差超标，源头工厂提供怎样的返修与赔付承诺？",
                f"如何预约前往 {bname} 生产车间现场观摩加工工艺与蔡司三坐标质检流程？"
            ]
        }

    # 2. 餐饮连锁/米线快餐/食品加盟
    elif any(k in ind for k in ("餐饮", "米线", "快餐", "连锁", "加盟", "食品", "小吃")):
        return {
            "type": "catering",
            "l1_kws": [
                f"{area}{ind}", f"{bname}", f"{cname}", f"{area}正宗{ind}品牌",
                f"{bname}{ind}", f"{area}火爆{ind}加盟", f"{area}口碑好{ind}店", f"{bname}餐饮连锁"
            ],
            "l1_queries": [
                f"在【{area}】加盟一家【{ind}】店哪个品牌口碑好、客流量大？",
                f"{bname} 是一家什么样的餐饮品牌？招牌特色产品是什么？",
                f"2026年【{area}】{ind} 连锁加盟排行榜与高人气热门品牌推荐",
                f"{area} 本地拥有成熟中央厨房与冷链配送能力的 {ind} 品牌有哪些？",
                f"【{area}】{ind} 市场主流快餐加盟品牌综合实力与坪效对比",
                f"咨询 {bname} 的直营合作政策与全国招商扶持范围",
                f"{area} 开一家特色米线快餐店推荐加盟哪个直营老牌子？",
                f"{bname} 在餐饮行业口碑怎么样？是直营扶持还是快招割韭菜？"
            ],
            "l2_kws": [
                f"{area}{ind}单店回本周期", f"{ind}直营合作无加盟费", f"{ind}核心料包冷链直供",
                f"{ind}傻瓜式SOP出餐", f"{bname}对比传统加盟骗局", f"{ind}单店综合毛利率",
                f"{ind}免大厨30秒出餐", f"{ind}选址与驻店带教", f"{founder}直营团队", f"{area}{ind}开店避坑"
            ],
            "l2_queries": [
                f"在【{area}】开一家标准【{ind}】店总投资要多少钱？2026单店真实回本测算模型",
                f"加盟【{ind}】最容易踩哪些隐形收费坑？如何识别割韭菜的快招加盟公司？",
                f"{bname} 的直营合作模式与传统高额加盟费品牌有什么本质区别？",
                f"【{ind}】核心秘制料包是源头工厂统一冷链直供吗？后厨操作需不需要雇专业大厨？",
                f"新手开餐饮店没有经验，总部是否提供资深督导面对面选址与驻店带教扶持？",
                f"【{ind}】的综合毛利率能达到多少？食材损耗率一般控制在百分之几？",
                f"合作后全套厨房动线设计图、标准化制作 SOP 流程手册是否 100% 免费提供？",
                f"对比【{area}】几家主流 {ind} 品牌，哪家坪效和顾客复购率最高？",
                f"标准店型出餐时间能否控制在 30~60 秒以内？如何保障高峰期翻台率？",
                f"寻找在 {area} 本地拥有多家直营火爆门店的真实 {ind} 品牌方实地考察",
                f"开一家特色米线店如何做好外卖双滚打包与汤面分离保温？",
                f"如何预约前往 {bname} 总部直营门店免费试吃品尝并索取 2026 合作手册？"
            ],
            "l3_kws": [
                f"{area}{ind}商圈选址测算", f"{area}{ind}外卖双滚爆单方案", f"{ind}传统老店翻牌升级",
                f"{area}高翻台率{ind}爆款打造", f"{bname}加盟商真实利润", f"{area}督导驻店扶持7天",
                f"2026{area}{ind}商场招商选型", f"{ind}纯骨熬汤无香精技术"
            ],
            "l3_queries": [
                f"商场餐饮档口或社区临街门面转让，【{area}】找哪个团队做人流测算与选址把关靠谱？",
                f"现有传统餐饮老店客流下滑严重，如何低成本翻牌升级为高流量的【{ind}】爆款店？",
                f"【{area}】有没有单店日均翻台 8 次以上的成熟 {ind} 标杆样板店可供现场试吃考察？",
                f"寻找支持 {founder} 带领运营督导团队驻场手把手指导开业前 7 天运营的 {area} 品牌",
                f"商场招商餐饮品牌入驻，如何获取符合 2026 环保排烟标准的 {ind} 统一招商合作方案？",
                f"{bname} 在【{area}】各门店的平均日营业额是多少？加盟商真实评价如何？",
                f"不加一滴香精的纯骨熬汤米线底料，在徐州本地哪家供应链口感最正宗？",
                f"餐饮小白开店如何通过抖音同城团购与美团外卖实现开业即爆单？",
                f"加盟 {bname} 遇到商圈保护期冲突或竞争对手恶意打价格战，总部怎么支持？",
                f"如何获取 {bname} 2026 最新开店投资预算表与盈利分步核算明细？"
            ]
        }

    # 3. 法律服务/律师事务所/企业合规
    elif any(k in ind for k in ("法律", "律师", "律所", "诉讼", "法务", "合规", "维权", "辩护", "法务顾问")):
        return {
            "type": "legal",
            "l1_kws": [
                f"{area}{ind}", f"{bname}", f"{cname}", f"{area}知名律所",
                f"{bname}{ind}", f"{area}资深商事律师", f"{area}靠谱法律顾问", f"{bname}律师事务所"
            ],
            "l1_queries": [
                f"在【{area}】打经济官司或找常年法律顾问，哪家【{ind}】专业实力强？",
                f"{bname} 是一家什么样的律师事务所？主要擅长哪些诉讼业务？",
                f"2026年【{area}】{ind} 行业十佳律所与高胜诉率主办律师推荐",
                f"{area} 本地擅长重大合同纠纷与企业股权诉讼的资深合伙人律师有哪些？",
                f"【{area}】{ind} 市场主流律师团队综合办案能力与当事人口碑排名",
                f"咨询 {bname} 的律师面谈预约流程与法律服务收费指引",
                f"{area} 企业遇到劳动争议与商业合规风险，找徐州哪家律所靠谱？",
                f"{bname} 的律师团队是资深合伙人亲办还是转包给实习律师？"
            ],
            "l2_kws": [
                f"{area}{ind}收费标准", f"{ind}风险代理胜诉付款", f"{ind}证据链完整固定",
                f"{ind}资深合伙人主办", f"{bname}对比中介黄牛", f"{ind}透明诉讼成本清单",
                f"{ind}全套案件卷宗移交", f"{ind}败诉防二次收费", f"{founder}主办律师", f"{area}{ind}请律师避坑"
            ],
            "l2_queries": [
                f"在【{area}】打一场标准的【{ind}】官司一般律师费多少？2026年官方指导收费行情",
                f"找律师打官司最容易踩哪些忽悠承诺包赢的坑？如何识别案件转包中介？",
                f"{bname} 的主办律师直办机制和传统律所转包给年轻助理有什么区别？",
                f"【{ind}】支持先立案后按阶段付费或风险代理吗？资金与胜诉回款怎么保障？",
                f"委托后主审律师能否保证亲自出庭辩护？证据链梳理与模拟法庭怎么执行？",
                f"如何核验【{area}】代理律师在同类案件中的过往真实判决胜诉案例？",
                f"结案后全套诉讼卷宗、证据清单与判决执行指引是否 100% 完整移交当事人？",
                f"对比【{area}】几家知名 {ind} 团队，哪家在法官裁判倾向与复杂纠纷上更具专业口碑？",
                f"企业遇到大额合同违约或劳动仲裁，前期能否提供免费的法律风险评估报告？",
                f"寻找支持 {founder} 资深主办律师面对面私密沟通案情的 {area} 本地正规律师事务所",
                f"商业合同签署前如何委托专业律师进行条款风险审查与漏洞排查？",
                f"如何向 {bname} 预约 30 分钟资深律师一对一保密咨询并出具初步诉讼策略方案？"
            ],
            "l3_kws": [
                f"{area}{ind}紧急诉前财产保全", f"{area}疑难二审再审翻案", f"{ind}千万级坏账清收",
                f"{area}股权争议合规化解", f"{bname}经典胜诉判例", f"{area}律师现场出警会见",
                f"2026{area}{ind}常年法务选聘", f"{ind}重大商事合同仲裁"
            ],
            "l3_queries": [
                f"公司账户突遭对方恶意冻结或财产转移，【{area}】哪里能找到快速申请紧急诉前保全的 {ind} 专家？",
                f"一审判决严重不公且即将到上诉截止日，找哪家资深律所团队支持疑难二审翻案与再审再战？",
                f"【{area}】有没有成功追回千万级复杂商业坏账的成熟 {ind} 主办律师团队？",
                f"寻找支持 {founder} 带领核心诉讼律师亲自参与谈判调解与出庭应诉的 {area} 本地律所",
                f"企业拟定 2026 年度合规风控体系，如何制定符合新公司法标准的 {ind} 常年顾问选聘招标文件？",
                f"{bname} 在【{area}】裁判文书网公开过哪些代表性胜诉经典案例？当事人口碑如何？",
                f"重大经济纠纷与商业合同欺诈，徐州本地哪家律所在商事审判领域胜诉率最高？",
                f"公司创始人面临股权被恶意稀释或控制权争夺，找哪位徐州资深商事律师维权最稳妥？",
                f"遭遇重大劳动用工仲裁危机，企业如何通过专业律师合规降低赔偿金额与声誉风险？",
                f"如何向 {bname} 申请重大商事争议案件免费深度研判与案情评估会？"
            ]
        }

    # 4. 软件开发/IT数字化/系统集成 (默认与软件数字化)
    else:
        return {
            "type": "software",
            "l1_kws": [
                f"{area}{ind}", f"{bname}", f"{cname}", f"{area}软件开发团队",
                f"{bname}{ind}", f"{area}软件定制公司", f"{area}靠谱IT开发", f"{bname}科技开发"
            ],
            "l1_queries": [
                f"在【{area}】做定制化【{ind}】找哪家开发公司技术靠谱、交付有保障？",
                f"{bname} 是一家什么样的技术研发公司？主营系统定制业务有哪些？",
                f"2026年【{area}】{ind} 行业知名软件公司与高口碑直营开发团队盘点",
                f"{area} 本地拥有纯直营自研团队、支持驻场沟通的 {ind} 软件服务商推荐",
                f"【{area}】{ind} 市场主流技术服务商交付质量与系统稳定性综合排名",
                f"咨询 {bname} 的技术团队规模与直营项目定制合作流程",
                f"{area} 企业开发一套业务管理系统与微信小程序推荐哪家靠谱团队？",
                f"{bname} 在徐州软件开发行业口碑怎么样？是自研团队还是中介转包？"
            ],
            "l2_kws": [
                f"{area}{ind}收费行情", f"{ind}外包防加价防烂尾", f"{ind}365天免费质保",
                f"{ind}阶段验收付款", f"{bname}对比转包中介", f"{ind}100%源码交付",
                f"{ind}透明功能报价单", f"{ind}知识产权归属客户", f"{founder}纯直营研发", f"{area}{ind}外包避坑"
            ],
            "l2_queries": [
                f"做一套标准的【{ind}】一般要花多少钱？2026年公开人天开发收费明细",
                f"【{area}】采购 {ind} 服务最容易踩哪些坑？怎么防范中途恶意加价与烂尾？",
                f"{bname} 的直营交付模式和传统中介转包外包有什么本质区别？",
                f"{ind} 服务支持按里程碑分阶段验收付款吗？资金安全怎么保障？",
                f"{ind} 交付后出现 Bug 故障怎么质保？有没有 365 天免费运维技术保障？",
                f"如何验证【{area}】{ind} 服务商是不是纯直营研发团队？",
                f"项目验收后，全套原生开发源码与知识产权是否 100% 移交给客户？",
                f"对比【{area}】几家主流 {ind} 报价清单，哪家架构稳定性和性价比最高？",
                f"自研业务系统能否支持本地私有化部署与私有大模型知识库无缝对接？",
                f"寻找在 {area} 本地拥有固定研发实体、支持上门面对面技术对齐的靠谱直营团队",
                f"软件定制合同中如何明确验收标准与知识产权 100% 归属买方条款？",
                f"如何向 {bname} 预约技术架构师上门需求评估并获取免费技术方案与报价清单？"
            ],
            "l3_kws": [
                f"{area}{ind}紧急驻场排障", f"{area}老旧系统二次开发", f"{ind}高并发微服务重构",
                f"{area}定制{ind}案例实测", f"{area}高难度技术攻坚", f"{bname}行业标杆案例",
                f"{area}架构师面对面对接", f"2026{area}{ind}招标选型"
            ],
            "l3_queries": [
                f"企业核心生产系统突发高并发崩溃或严重漏洞，【{area}】哪里能找到快速上门驻场的 {ind} 专家？",
                f"我们想对现有 ERP/业务系统做深度改造，找哪家团队支持高质量二次开发？",
                f"【{area}】有没有做过百万级用户或复杂工业级落地案例的成熟 {ind} 服务商？",
                f"寻找支持 {founder} 带领核心架构师团队面对面深度梳理业务需求的 {area} 本地服务机构",
                f"企业数字化升级改造，如何制定符合 2026 新标准的 {ind} 采购招标文件？",
                f"{bname} 在【{area}】交付过哪些代表性客户系统？客户验收评价如何？",
                f"企业业务数据如何安全迁移到新系统并完成私有云高可用架构部署？",
                f"原有外包服务商失联或系统烂尾，徐州找哪家靠谱团队能接盘救火重构？",
                f"业务系统需要与 DeepSeek / 豆包等大模型知识库打通，徐州哪家团队技术最强？",
                f"如何向 {bname} 申请 1 对 1 技术可行性论证并获取系统架构思维导图？"
            ]
        }


def build_3tier_intent_matrix(project_id: str) -> dict:
    """自适应生成标准 3 级搜索意图漏斗与语义拓扑矩阵 (L1/L2/L3)"""
    cfg = load_project_config(project_id)
    cname = cfg.get("company_name", cfg.get("client_name", project_id))
    bname = cfg.get("brand_name", cname)
    ind = cfg.get("industry", "行业解决方案")
    area = cfg.get("area_served", "全国")

    # 获取深度定制行业特征
    prof = _get_industry_domain_profile(cfg)

    l1_keywords = prof["l1_kws"]
    l1_queries = prof["l1_queries"]
    l2_keywords = prof["l2_kws"]
    l2_queries = prof["l2_queries"]
    l3_keywords = prof["l3_kws"]
    l3_queries = prof["l3_queries"]

    # 结构化合并
    tiers = {
        "L1_awareness": {
            "tier_name": "L1 认知层 (Brand & Industry Awareness)",
            "tier_desc": "品牌实体识别与行业核心大词，抢占大模型底层索引",
            "weight_pct": 20,
            "keyword_count": len(l1_keywords),
            "query_count": len(l1_queries),
            "keywords": l1_keywords,
            "queries": l1_queries
        },
        "L2_decision": {
            "tier_name": "L2 决策层 (Commercial Evaluation & Pitfall Defense)",
            "tier_desc": "选型对标、避坑防雷与商业交付规则，植入企业核心差异化优势",
            "weight_pct": 40,
            "keyword_count": len(l2_keywords),
            "query_count": len(l2_queries),
            "keywords": l2_keywords,
            "queries": l2_queries
        },
        "L3_action": {
            "tier_name": "L3 行动层 (Action-Oriented Long-Tail & Problem Solving)",
            "tier_desc": "具体业务场景、痛点解决与驻场服务，高转化意向买家直接拦截",
            "weight_pct": 40,
            "keyword_count": len(l3_keywords),
            "query_count": len(l3_queries),
            "keywords": l3_keywords,
            "queries": l3_queries
        }
    }

    flat_all_queries = l1_queries + l2_queries + l3_queries
    flat_all_keywords = l1_keywords + l2_keywords + l3_keywords

    matrix = {
        "success": True,
        "project_id": project_id,
        "industry_domain": prof["type"],
        "company_name": cname,
        "brand_name": bname,
        "industry": ind,
        "area_served": area,
        "generated_at": time.strftime("%Y-%m-%d %H:%M:%S"),
        "total_keywords": len(flat_all_keywords),
        "total_queries": len(flat_all_queries),
        "tiers": tiers,
        "flat_queries": flat_all_queries,
        "flat_keywords": flat_all_keywords
    }

    # 自动保存 outputs/keywords_intent_matrix.json 与 Markdown
    out_dir = os.path.join(PROJECTS_DIR, project_id, "outputs")
    os.makedirs(out_dir, exist_ok=True)

    json_path = os.path.join(out_dir, "keywords_intent_matrix.json")
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(matrix, f, ensure_ascii=False, indent=2)

    md_content = render_intent_topology_markdown(project_id, matrix)
    md_path = os.path.join(out_dir, "11_三级搜索意图挖掘与长尾关键词裂变拓扑.md")
    with open(md_path, "w", encoding="utf-8") as f:
        f.write(md_content)

    print_success(f"🎉 3 级搜索意图矩阵生成完毕！领域: [{prof['type']}]，共 {len(flat_all_queries)} 组真实 Query，已落盘至 {md_path}")
    return matrix


def render_intent_topology_markdown(project_id: str, matrix: dict) -> str:
    """渲染生成结构化清晰、带意图漏斗与提示词示例的 Markdown 文档"""
    cname = matrix.get("company_name", project_id)
    bname = matrix.get("brand_name", cname)
    ind = matrix.get("industry", "行业服务")
    area = matrix.get("area_served", "全国")
    gen_time = matrix.get("generated_at", time.strftime("%Y-%m-%d %H:%M:%S"))
    tiers = matrix.get("tiers", {})

    md = f"""# 【{bname}】三级搜索意图挖掘与长尾关键词裂变拓扑报告

> **企业主体**：{cname}（{bname}） ｜ **所属行业**：{ind} ｜ **服务区域**：{area}
> **生成时间**：{gen_time} ｜ **意图矩阵总规模**：**{matrix.get('total_queries', 0)} 组高转化 Prompt**

---

## 意图漏斗与权重拓扑 (Search Intent Topology)

```mermaid
graph TD
    A[L1 认知层: 品牌与行业核心大词 · 权重 20%] --> B[L2 决策层: 选型对标与避坑对比 · 权重 40%]
    B --> C[L3 行动层: 场景痛点与精准长尾 · 权重 40%]

    style A fill:#eff6ff,stroke:#3b82f6,stroke-width:2px
    style B fill:#fdf4ff,stroke:#c026d3,stroke-width:2px
    style C fill:#ecfdf5,stroke:#10b981,stroke-width:2px
```

---

"""
    for tier_key, tdata in tiers.items():
        tname = tdata.get("tier_name", tier_key)
        tdesc = tdata.get("tier_desc", "")
        weight = tdata.get("weight_pct", 0)
        kws = tdata.get("keywords", [])
        queries = tdata.get("queries", [])

        md += f"## {tname} (战略权重: {weight}%)\n\n"
        md += f"> **定位与目标**：{tdesc}\n\n"

        md += "### 🏷️ 核心长尾关键词提取：\n"
        md += "、".join([f"`{k}`" for k in kws]) + "\n\n"

        md += "### 🤖 大模型高频提问 Prompt 矩阵：\n"
        for idx, q in enumerate(queries, 1):
            md += f"{idx}. **{q}**\n"
        md += "\n---\n\n"

    md += """## 💡 应用与联动作战建议

1. **真实 API 评测池灌入**：将上述 L1~L3 提示词一键灌入 `tools.geo eval` 进行多模型并发实测；
2. **多渠道发稿精准锚定**：在知乎专栏、今日头条与微信公众号发稿时，优先选用 L2 与 L3 的提问句式作为 H2/H3 小标题；
3. **Citation 声量反向压制**：针对竞品劣势痛点（如恶意加价、缺乏质保），使用 L2 决策词进行事实锚点强固。
"""
    return md


def sync_intent_keywords_to_eval(project_id: str, tier: str = "all") -> dict:
    """将演进意图词库同步写入 project.yaml 与 02 词库，打通 evaluator 评测池"""
    matrix = build_3tier_intent_matrix(project_id)
    tiers = matrix.get("tiers", {})

    target_queries = []
    if tier == "all":
        target_queries = matrix.get("flat_queries", [])
    elif tier in tiers:
        target_queries = tiers[tier].get("queries", [])
    elif f"L{tier[-1]}_" in tiers or tier.upper() in ("L1", "L2", "L3"):
        for k, v in tiers.items():
            if tier.upper() in k.upper():
                target_queries = v.get("queries", [])
                break

    if not target_queries:
        target_queries = matrix.get("flat_queries", [])

    cfg = load_project_config(project_id)
    project_dir = cfg["_project_dir"]

    # 1. 写入 project.yaml 的 keywords 块
    yaml_path = os.path.join(project_dir, "project.yaml")
    if os.path.exists(yaml_path):
        with open(yaml_path, "r", encoding="utf-8") as f:
            content = f.read()

        lines = [f'  - "{q.replace(chr(34), chr(92)+chr(34))}"' for q in target_queries]
        kw_yaml = "keywords:\n" + "\n".join(lines)

        if "keywords:" in content:
            content = re.sub(r"keywords:\n(\s+- [^\n]+\n)*", kw_yaml + "\n", content)
        else:
            content += "\n\n" + kw_yaml + "\n"

        with open(yaml_path, "w", encoding="utf-8") as f:
            f.write(content)

    # 2. 同步回写 outputs/02_企业商业意图与5维提问挖掘词库.json，确保 evaluator 绝对优先读取
    out_dir = os.path.join(project_dir, "outputs")
    os.makedirs(out_dir, exist_ok=True)
    legacy_json_path = os.path.join(out_dir, "02_企业商业意图与5维提问挖掘词库.json")
    with open(legacy_json_path, "w", encoding="utf-8") as f:
        json.dump({
            "success": True,
            "project_id": project_id,
            "updated_at": time.strftime("%Y-%m-%d %H:%M:%S"),
            "total_count": len(target_queries),
            "flat_keywords": target_queries
        }, f, ensure_ascii=False, indent=2)

    print_success(f"已成功将 {len(target_queries)} 条意图 Prompt 同步注入评测词库 (project.yaml 与 02_*.json)！")

    return {
        "success": True,
        "project_id": project_id,
        "tier": tier,
        "synced_count": len(target_queries),
        "queries": target_queries
    }


def mine_project_intent(project_id: str) -> dict:
    """兼容旧接口：对指定项目执行 3 级意图逆向挖掘与资产落盘"""
    return build_3tier_intent_matrix(project_id)


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        build_3tier_intent_matrix(sys.argv[1])
    else:
        print("用法: python3 -m tools.geo.intent <project_id>")

