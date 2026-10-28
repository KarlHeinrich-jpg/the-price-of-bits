# -*- coding: utf-8 -*-
"""Lexicon for the Third-party Data Dependency Index (TDDI).

Four third-party-data categories (A-D) and two auxiliary constructs:
E = first-party data capability (FPDCI), F = generic digitalisation (placebo).
Phrases are deliberately specific: generic words such as '大数据' or '数字化'
belong to F, not to the treatment measure.
"""

CATEGORIES = {
    "A_data_acquisition": [
        "第三方数据", "外购数据", "数据采购", "购买数据", "数据购买",
        "数据供应商", "数据服务商", "数据提供方", "数据交易", "数据交换",
        "数据共享", "数据合作", "数据接入", "数据接口", "外部数据",
        "多源数据", "第三方数据源", "数据源", "数据融合", "数据整合",
        "数据清洗", "数据标签", "数据建模", "数据挖掘", "数据服务",
        "数据产品", "数据变现", "数据资产", "数据要素", "数据资源",
        "数据采购成本", "数据使用费", "数据授权",
    ],
    "B_ad_traffic": [
        "流量采购", "购买流量", "流量成本", "流量获取", "获客成本",
        "用户获取成本", "买量", "广告投放", "广告采购", "媒体采购",
        "广告代理", "精准营销", "精准投放", "程序化广告", "程序化购买",
        "信息流广告", "效果广告", "广告联盟", "联盟广告", "应用分发",
        "渠道推广", "渠道费用", "平台导流", "外部流量", "站外流量",
        "广告变现", "流量变现", "商业化变现", "广告收入", "广告业务",
        "数字营销", "移动营销", "效果营销", "营销服务", "媒介代理",
        "投放成本", "获客",
    ],
    "C_tracking_targeting": [
        "用户画像", "用户标签", "标签体系", "用户行为数据", "行为数据",
        "跨应用", "跨平台", "跨设备", "设备标识", "设备ID", "IDFA",
        "OAID", "广告标识符", "用户追踪", "定向投放", "定向广告",
        "个性化推荐", "算法推荐", "千人千面", "精准触达", "用户洞察",
        "人群包", "人群画像", "用户分层", "数据标签", "用户数据",
        "行为画像", "兴趣标签", "用户画像体系", "标签画像",
    ],
    "D_platform_ecosystem": [
        "第三方平台", "开放平台", "平台生态", "应用商店", "安卓市场",
        "苹果应用商店", "iOS", "微信小程序", "支付宝小程序", "抖音",
        "快手", "小红书", "美团", "淘宝", "京东", "拼多多", "百度",
        "腾讯", "字节跳动", "巨量引擎", "腾讯广告", "阿里妈妈",
        "百度营销", "微博", "哔哩哔哩", "知乎",
    ],
    "E_first_party": [
        "自有数据", "第一方数据", "私域流量", "私域运营", "自有平台",
        "自有APP", "自有应用", "自有网站", "自有用户", "会员体系",
        "会员数据", "用户社区", "企业微信", "CRM", "客户关系管理",
        "用户运营", "全渠道", "直营", "官方商城", "自营平台",
        "数据中台", "用户数据中心", "CDP", "DMP", "第一方",
        "自有小程序", "品牌自营", "官方旗舰店",
    ],
    "F_generic_digital": [
        "数字化转型", "数字化", "智能化", "云计算", "大数据",
        "人工智能", "物联网", "区块链", "5G", "工业互联网",
        "网络安全", "研发投入", "技术创新", "算法", "机器学习",
        "大模型", "AIGC", "数据驱动",
    ],
}

# Terms that appear in several categories are counted once in the first
# category in which they appear (order: A, B, C, D, E, F).
ALL_TERMS = []
_seen = set()
for _cat in ["A_data_acquisition", "B_ad_traffic", "C_tracking_targeting",
             "D_platform_ecosystem", "E_first_party", "F_generic_digital"]:
    for _t in CATEGORIES[_cat]:
        if _t not in _seen:
            _seen.add(_t)
            ALL_TERMS.append((_t, _cat))
