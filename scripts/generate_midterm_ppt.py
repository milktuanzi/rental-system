from pathlib import Path
from zipfile import ZipFile, ZIP_DEFLATED
import html


OUT = Path("智能房屋租赁系统_中期汇报.pptx")
EMU_W = 12192000
EMU_H = 6858000


def esc(text):
    return html.escape(str(text), quote=True)


def content_types(slide_count):
    overrides = [
        '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>',
        '<Default Extension="xml" ContentType="application/xml"/>',
        '<Override PartName="/ppt/presentation.xml" ContentType="application/vnd.openxmlformats-officedocument.presentationml.presentation.main+xml"/>',
        '<Override PartName="/ppt/slideMasters/slideMaster1.xml" ContentType="application/vnd.openxmlformats-officedocument.presentationml.slideMaster+xml"/>',
        '<Override PartName="/ppt/slideLayouts/slideLayout1.xml" ContentType="application/vnd.openxmlformats-officedocument.presentationml.slideLayout+xml"/>',
        '<Override PartName="/ppt/theme/theme1.xml" ContentType="application/vnd.openxmlformats-officedocument.theme+xml"/>',
    ]
    for i in range(1, slide_count + 1):
        overrides.append(
            f'<Override PartName="/ppt/slides/slide{i}.xml" ContentType="application/vnd.openxmlformats-officedocument.presentationml.slide+xml"/>'
        )
    return '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>' \
        '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">' \
        + "".join(overrides) + "</Types>"


def root_rels():
    return """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="ppt/presentation.xml"/>
</Relationships>"""


def presentation(slide_count):
    sld_ids = []
    for i in range(1, slide_count + 1):
        sld_ids.append(f'<p:sldId id="{255 + i}" r:id="rId{i}"/>')
    return f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<p:presentation xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main"
 xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"
 xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main">
  <p:sldMasterIdLst><p:sldMasterId id="2147483648" r:id="rId{slide_count + 1}"/></p:sldMasterIdLst>
  <p:sldIdLst>{''.join(sld_ids)}</p:sldIdLst>
  <p:sldSz cx="{EMU_W}" cy="{EMU_H}" type="wide"/>
  <p:notesSz cx="6858000" cy="9144000"/>
</p:presentation>"""


def presentation_rels(slide_count):
    rels = []
    for i in range(1, slide_count + 1):
        rels.append(
            f'<Relationship Id="rId{i}" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/slide" Target="slides/slide{i}.xml"/>'
        )
    rels.append(
        f'<Relationship Id="rId{slide_count + 1}" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/slideMaster" Target="slideMasters/slideMaster1.xml"/>'
    )
    rels.append(
        f'<Relationship Id="rId{slide_count + 2}" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/theme" Target="theme/theme1.xml"/>'
    )
    return '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>' \
        '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">' \
        + "".join(rels) + "</Relationships>"


def theme():
    return """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<a:theme xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" name="RentalMidterm">
  <a:themeElements>
    <a:clrScheme name="Rental">
      <a:dk1><a:srgbClr val="162033"/></a:dk1><a:lt1><a:srgbClr val="F7FAFC"/></a:lt1>
      <a:dk2><a:srgbClr val="243447"/></a:dk2><a:lt2><a:srgbClr val="EAF2F8"/></a:lt2>
      <a:accent1><a:srgbClr val="1D6E8C"/></a:accent1><a:accent2><a:srgbClr val="2D9CDB"/></a:accent2>
      <a:accent3><a:srgbClr val="F0A33A"/></a:accent3><a:accent4><a:srgbClr val="5B7C5A"/></a:accent4>
      <a:accent5><a:srgbClr val="8A5A44"/></a:accent5><a:accent6><a:srgbClr val="6F7C8C"/></a:accent6>
      <a:hlink><a:srgbClr val="2D9CDB"/></a:hlink><a:folHlink><a:srgbClr val="1D6E8C"/></a:folHlink>
    </a:clrScheme>
    <a:fontScheme name="RentalFonts">
      <a:majorFont><a:latin typeface="Aptos Display"/><a:ea typeface="Microsoft YaHei"/></a:majorFont>
      <a:minorFont><a:latin typeface="Aptos"/><a:ea typeface="Microsoft YaHei"/></a:minorFont>
    </a:fontScheme>
    <a:fmtScheme name="RentalFmt"><a:fillStyleLst><a:solidFill><a:schemeClr val="phClr"/></a:solidFill></a:fillStyleLst><a:lnStyleLst><a:ln w="6350"><a:solidFill><a:schemeClr val="phClr"/></a:solidFill></a:ln></a:lnStyleLst><a:effectStyleLst><a:effectStyle><a:effectLst/></a:effectStyle></a:effectStyleLst><a:bgFillStyleLst><a:solidFill><a:schemeClr val="phClr"/></a:solidFill></a:bgFillStyleLst></a:fmtScheme>
  </a:themeElements>
  <a:objectDefaults/><a:extraClrSchemeLst/>
</a:theme>"""


def slide_master():
    return """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<p:sldMaster xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main"
 xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"
 xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main">
  <p:cSld><p:bg><p:bgPr><a:solidFill><a:srgbClr val="F7FAFC"/></a:solidFill></p:bgPr></p:bg><p:spTree><p:nvGrpSpPr><p:cNvPr id="1" name=""/><p:cNvGrpSpPr/><p:nvPr/></p:nvGrpSpPr><p:grpSpPr><a:xfrm><a:off x="0" y="0"/><a:ext cx="0" cy="0"/><a:chOff x="0" y="0"/><a:chExt cx="0" cy="0"/></a:xfrm></p:grpSpPr></p:spTree></p:cSld>
  <p:clrMap accent1="accent1" accent2="accent2" accent3="accent3" accent4="accent4" accent5="accent5" accent6="accent6" bg1="lt1" bg2="lt2" folHlink="folHlink" hlink="hlink" tx1="dk1" tx2="dk2"/>
  <p:sldLayoutIdLst><p:sldLayoutId id="2147483649" r:id="rId1"/></p:sldLayoutIdLst>
  <p:txStyles><p:titleStyle/><p:bodyStyle/><p:otherStyle/></p:txStyles>
</p:sldMaster>"""


def slide_layout():
    return """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<p:sldLayout xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main"
 xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"
 xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main" type="blank" preserve="1">
  <p:cSld name="Blank"><p:spTree><p:nvGrpSpPr><p:cNvPr id="1" name=""/><p:cNvGrpSpPr/><p:nvPr/></p:nvGrpSpPr><p:grpSpPr><a:xfrm><a:off x="0" y="0"/><a:ext cx="0" cy="0"/><a:chOff x="0" y="0"/><a:chExt cx="0" cy="0"/></a:xfrm></p:grpSpPr></p:spTree></p:cSld>
  <p:clrMapOvr><a:masterClrMapping/></p:clrMapOvr>
</p:sldLayout>"""


def solid_rect(id_, x, y, w, h, color, radius=False, line=None):
    prst = "roundRect" if radius else "rect"
    ln = '<a:ln><a:noFill/></a:ln>' if line is None else f'<a:ln w="12700"><a:solidFill><a:srgbClr val="{line}"/></a:solidFill></a:ln>'
    return f"""<p:sp><p:nvSpPr><p:cNvPr id="{id_}" name="shape{id_}"/><p:cNvSpPr/><p:nvPr/></p:nvSpPr><p:spPr><a:xfrm><a:off x="{x}" y="{y}"/><a:ext cx="{w}" cy="{h}"/></a:xfrm><a:prstGeom prst="{prst}"><a:avLst/></a:prstGeom><a:solidFill><a:srgbClr val="{color}"/></a:solidFill>{ln}</p:spPr><p:txBody><a:bodyPr/><a:lstStyle/><a:p/></p:txBody></p:sp>"""


def text_box(id_, text, x, y, w, h, size=2600, color="162033", bold=False, align="l"):
    runs = []
    for idx, line in enumerate(str(text).split("\n")):
        if idx:
            runs.append("</a:p><a:p>")
        b = ' b="1"' if bold else ""
        runs.append(f'<a:r><a:rPr lang="zh-CN" sz="{size}"{b}><a:solidFill><a:srgbClr val="{color}"/></a:solidFill><a:latin typeface="Aptos"/><a:ea typeface="Microsoft YaHei"/></a:rPr><a:t>{esc(line)}</a:t></a:r>')
    return f"""<p:sp><p:nvSpPr><p:cNvPr id="{id_}" name="text{id_}"/><p:cNvSpPr txBox="1"/><p:nvPr/></p:nvSpPr><p:spPr><a:xfrm><a:off x="{x}" y="{y}"/><a:ext cx="{w}" cy="{h}"/></a:xfrm><a:prstGeom prst="rect"><a:avLst/></a:prstGeom><a:noFill/><a:ln><a:noFill/></a:ln></p:spPr><p:txBody><a:bodyPr wrap="square"/><a:lstStyle/><a:p><a:pPr algn="{align}"/>{"".join(runs)}</a:p></p:txBody></p:sp>"""


def bullet_box(id_, items, x, y, w, h, size=2200, color="243447"):
    paras = []
    for item in items:
        paras.append(f'<a:p><a:pPr marL="285750" indent="-171450"><a:buChar char="•"/></a:pPr><a:r><a:rPr lang="zh-CN" sz="{size}"><a:solidFill><a:srgbClr val="{color}"/></a:solidFill><a:latin typeface="Aptos"/><a:ea typeface="Microsoft YaHei"/></a:rPr><a:t>{esc(item)}</a:t></a:r></a:p>')
    return f"""<p:sp><p:nvSpPr><p:cNvPr id="{id_}" name="bullets{id_}"/><p:cNvSpPr txBox="1"/><p:nvPr/></p:nvSpPr><p:spPr><a:xfrm><a:off x="{x}" y="{y}"/><a:ext cx="{w}" cy="{h}"/></a:xfrm><a:prstGeom prst="rect"><a:avLst/></a:prstGeom><a:noFill/><a:ln><a:noFill/></a:ln></p:spPr><p:txBody><a:bodyPr wrap="square"/><a:lstStyle/>{"".join(paras)}</p:txBody></p:sp>"""


def title_shapes(title, section=None):
    shapes = [
        solid_rect(2, 0, 0, EMU_W, EMU_H, "F7FAFC"),
        solid_rect(3, 0, 0, 250000, EMU_H, "1D6E8C"),
        solid_rect(4, 250000, 0, 230000, EMU_H, "F0A33A"),
        text_box(5, title, 680000, 420000, 9800000, 650000, 3300, "162033", True),
    ]
    if section:
        shapes.append(text_box(6, section, 10300000, 500000, 1350000, 300000, 1250, "6F7C8C", False, "r"))
    return shapes


def card(id_, title, body, x, y, w, h, accent="1D6E8C"):
    return "".join([
        solid_rect(id_, x, y, w, h, "FFFFFF", True, "D7E3EA"),
        solid_rect(id_ + 1, x, y, 90000, h, accent),
        text_box(id_ + 2, title, x + 220000, y + 130000, w - 350000, 300000, 1800, "162033", True),
        text_box(id_ + 3, body, x + 220000, y + 520000, w - 350000, h - 600000, 1350, "243447"),
    ])


slides = [
    {
        "title": "基于 Flask 框架的智能房屋租赁系统",
        "subtitle": "软件工程基础课程项目中期汇报",
        "items": ["项目类型：Web 管理系统", "核心角色：房东 / 租客 / 系统管理员", "技术栈：Python + Flask + SQLAlchemy + Bootstrap 5", "汇报日期：2026 年 6 月"],
        "kind": "cover",
    },
    {
        "title": "项目背景与问题分析",
        "items": ["传统租赁流程依赖线下沟通和纸质材料，效率较低。", "租客筛选房源成本高，容易出现信息不对称。", "房东需要同时管理房源、预约、租约、维修和沟通事务。", "系统目标是把租赁流程统一到可追踪、可管理的在线平台。"],
    },
    {
        "title": "项目目标与系统定位",
        "items": ["构建覆盖房屋租赁主要流程的 Web 系统。", "支持三类角色按权限完成各自业务操作。", "完成房源管理、搜索筛选、预约签约、消息沟通、维修投诉和报表统计。", "中期重点：完成需求分析、系统设计和主体功能框架。"],
    },
    {
        "title": "用户角色与业务流程",
        "kind": "roles",
    },
    {
        "title": "功能需求总览",
        "kind": "modules",
    },
    {
        "title": "系统总体架构",
        "kind": "architecture",
    },
    {
        "title": "数据库与核心模型",
        "kind": "models",
    },
    {
        "title": "主要功能模块展示",
        "items": ["公共端： 首页、房源搜索、房源详情。", "房东端： 房源发布编辑、预约处理、租赁合同、维修处理、公告与报表。", "租客端： 搜索浏览、预约看房、我的租赁、维修申请、投诉和消息。", "管理端： 用户管理、房源管理、投诉处理、系统报表。"],
    },
    {
        "title": "当前开发进度",
        "kind": "progress",
    },
    {
        "title": "技术实现与安全设计",
        "items": ["采用 Flask 应用工厂模式，便于配置不同运行环境。", "使用蓝图拆分认证、公共页面、房东、租客和管理员功能。", "使用 SQLAlchemy ORM 管理数据模型和关系。", "使用 Flask-Login 管理登录会话，Flask-WTF 提供 CSRF 保护。", "通过角色权限控制限制不同用户的访问范围。"],
    },
    {
        "title": "当前问题与改进方向",
        "items": ["继续完善测试用例，覆盖登录、预约、合同、维修、投诉等关键流程。", "优化页面交互和展示细节，提升演示时的完整度。", "补充稳定的初始化数据和演示账号。", "验证部署流程，确认数据库配置、静态资源和生产环境参数。", "对智能推荐或智能代理能力进行可行范围内的补充说明或原型实现。"],
    },
    {
        "title": "后续计划与总结",
        "items": ["下一阶段重点是联调、测试、部署验证和演示材料完善。", "项目已经形成清晰的需求、架构、数据模型和主要页面结构。", "系统当前具备房屋租赁业务闭环的基础能力。", "最终目标是完成可运行、可演示、文档齐全的课程项目交付。"],
    },
]


def role_slide(title):
    shapes = title_shapes(title, "04")
    shapes.append(card(20, "房东", "发布房源\n处理预约\n管理租约\n维修与报表", 780000, 1700000, 3000000, 2100000, "1D6E8C"))
    shapes.append(card(30, "租客", "搜索房源\n预约看房\n签署合同\n维修投诉", 4200000, 1700000, 3000000, 2100000, "2D9CDB"))
    shapes.append(card(40, "管理员", "用户管理\n房源管理\n投诉处理\n系统报表", 7620000, 1700000, 3000000, 2100000, "F0A33A"))
    shapes.append(text_box(50, "业务闭环：浏览房源 -> 预约看房 -> 房东确认 -> 签订合同 -> 支付 / 维修 / 投诉", 1200000, 4700000, 9800000, 500000, 2100, "162033", True, "ctr"))
    return shapes


def modules_slide(title):
    shapes = title_shapes(title, "05")
    modules = ["用户管理", "房源管理", "智能搜索", "预约租赁", "消息公告", "维修投诉", "报表统计", "系统监控"]
    colors = ["1D6E8C", "2D9CDB", "F0A33A", "5B7C5A", "8A5A44", "6F7C8C", "1D6E8C", "F0A33A"]
    for i, name in enumerate(modules):
        col = i % 4
        row = i // 4
        x = 820000 + col * 2750000
        y = 1750000 + row * 1550000
        shapes.append(solid_rect(20 + i * 3, x, y, 2300000, 920000, "FFFFFF", True, "D7E3EA"))
        shapes.append(solid_rect(21 + i * 3, x, y, 2300000, 105000, colors[i]))
        shapes.append(text_box(22 + i * 3, name, x + 170000, y + 280000, 2000000, 300000, 2100, "162033", True, "ctr"))
    shapes.append(text_box(60, "当前阶段：核心模块已完成初步实现，后续重点为测试、联调、部署和演示优化。", 1200000, 5200000, 9800000, 380000, 1900, "243447", False, "ctr"))
    return shapes


def architecture_slide(title):
    shapes = title_shapes(title, "06")
    layers = [
        ("前端页面层", "HTML / CSS / JavaScript / Bootstrap 5"),
        ("视图路由层", "Flask Blueprints：auth / common / landlord / tenant / admin"),
        ("表单验证层", "Flask-WTF / WTForms / CSRF 保护"),
        ("模型与数据层", "SQLAlchemy Models：User / Property / Lease / Repair ..."),
        ("数据库层", "SQLite 开发环境，MySQL 生产方案"),
    ]
    for i, (name, desc) in enumerate(layers):
        y = 1450000 + i * 850000
        shapes.append(solid_rect(20 + i * 4, 1500000, y, 9000000, 570000, "FFFFFF", True, "C7D7DF"))
        shapes.append(solid_rect(21 + i * 4, 1500000, y, 1350000, 570000, "1D6E8C" if i % 2 == 0 else "2D9CDB", True))
        shapes.append(text_box(22 + i * 4, name, 1620000, y + 145000, 1150000, 230000, 1450, "FFFFFF", True, "ctr"))
        shapes.append(text_box(23 + i * 4, desc, 3050000, y + 145000, 7000000, 260000, 1700, "243447"))
    return shapes


def models_slide(title):
    shapes = title_shapes(title, "07")
    shapes.append(solid_rect(20, 5300000, 2100000, 1800000, 700000, "1D6E8C", True))
    shapes.append(text_box(21, "User", 5300000, 2320000, 1800000, 250000, 1900, "FFFFFF", True, "ctr"))
    nodes = [
        ("Property", 1700000, 1550000), ("Lease", 3300000, 3300000), ("Appointment", 7100000, 1550000),
        ("Message", 8650000, 3300000), ("Repair", 1700000, 4500000), ("Complaint", 5200000, 4500000),
        ("Payment", 8450000, 4500000), ("News", 8500000, 1550000),
    ]
    for i, (name, x, y) in enumerate(nodes):
        shapes.append(solid_rect(30 + i * 2, x, y, 1650000, 560000, "FFFFFF", True, "C7D7DF"))
        shapes.append(text_box(31 + i * 2, name, x + 100000, y + 170000, 1450000, 220000, 1550, "162033", True, "ctr"))
    shapes.append(text_box(60, "核心关系：用户发布房源、租赁房源、发送消息、提交维修和投诉；房源关联预约、合同和维修记录。", 1200000, 5800000, 9800000, 350000, 1700, "243447", False, "ctr"))
    return shapes


def progress_slide(title):
    shapes = title_shapes(title, "09")
    items = [
        ("需求分析与文档", 92, "系统需求、项目说明、结构文档"),
        ("后端架构", 88, "应用工厂、配置、蓝图、错误处理"),
        ("数据模型", 86, "用户、房源、合同、预约、维修、投诉等"),
        ("页面模板", 78, "首页、搜索页、三类后台页面"),
        ("测试与部署", 45, "后续继续补充与验证"),
    ]
    for i, (name, pct, desc) in enumerate(items):
        y = 1450000 + i * 800000
        shapes.append(text_box(20 + i * 5, name, 1100000, y, 1900000, 280000, 1550, "162033", True))
        shapes.append(solid_rect(21 + i * 5, 3150000, y + 50000, 5600000, 180000, "D7E3EA", True))
        shapes.append(solid_rect(22 + i * 5, 3150000, y + 50000, int(5600000 * pct / 100), 180000, "1D6E8C", True))
        shapes.append(text_box(23 + i * 5, f"{pct}%", 9000000, y, 700000, 240000, 1450, "243447", True))
        shapes.append(text_box(24 + i * 5, desc, 3150000, y + 280000, 6800000, 240000, 1250, "6F7C8C"))
    return shapes


def default_slide(title, items, idx):
    shapes = title_shapes(title, f"{idx:02d}")
    shapes.append(bullet_box(20, items, 900000, 1550000, 6400000, 4100000, 2050))
    shapes.append(solid_rect(30, 8050000, 1600000, 2950000, 3300000, "EAF2F8", True, "C7D7DF"))
    shapes.append(text_box(31, "展示建议", 8350000, 1840000, 2400000, 300000, 1900, "162033", True, "ctr"))
    suggestions = {
        2: "插入问题分析图\n线下流程 vs 在线系统",
        3: "插入目标矩阵\n效率 / 透明 / 管理 / 安全",
        8: "放置页面截图\n首页 / 搜索 / 后台",
        10: "插入安全设计图\n认证 / CSRF / ORM / 权限",
        11: "插入风险清单\n测试 / 部署 / 数据 / 体验",
        12: "插入阶段路线图\n中期 -> 联调 -> 验收",
    }
    shapes.append(text_box(32, suggestions.get(idx, "插入模块示意图"), 8350000, 2400000, 2400000, 1200000, 1700, "243447", False, "ctr"))
    return shapes


def cover_slide(data):
    shapes = [
        solid_rect(2, 0, 0, EMU_W, EMU_H, "162033"),
        solid_rect(3, 0, 0, EMU_W, 780000, "1D6E8C"),
        solid_rect(4, 0, 5800000, EMU_W, 520000, "F0A33A"),
        text_box(5, data["title"], 760000, 1650000, 10200000, 820000, 3800, "FFFFFF", True),
        text_box(6, data["subtitle"], 800000, 2550000, 8000000, 420000, 2100, "DDEAF0"),
        bullet_box(7, data["items"], 900000, 3450000, 6800000, 1700000, 1800, "F7FAFC"),
        solid_rect(8, 8600000, 3350000, 2300000, 1500000, "243447", True, "2D9CDB"),
        text_box(9, "CSU\n中南大学\nSoftware Engineering", 8850000, 3700000, 1800000, 650000, 1700, "FFFFFF", True, "ctr"),
    ]
    return shapes


def slide_xml(shapes):
    return f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<p:sld xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main"
 xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"
 xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main">
  <p:cSld><p:spTree>
    <p:nvGrpSpPr><p:cNvPr id="1" name=""/><p:cNvGrpSpPr/><p:nvPr/></p:nvGrpSpPr>
    <p:grpSpPr><a:xfrm><a:off x="0" y="0"/><a:ext cx="0" cy="0"/><a:chOff x="0" y="0"/><a:chExt cx="0" cy="0"/></a:xfrm></p:grpSpPr>
    {''.join(shapes)}
  </p:spTree></p:cSld>
  <p:clrMapOvr><a:masterClrMapping/></p:clrMapOvr>
</p:sld>"""


def slide_rels():
    return """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/slideLayout" Target="../slideLayouts/slideLayout1.xml"/>
</Relationships>"""


def build():
    slide_count = len(slides)
    with ZipFile(OUT, "w", ZIP_DEFLATED) as z:
        z.writestr("[Content_Types].xml", content_types(slide_count))
        z.writestr("_rels/.rels", root_rels())
        z.writestr("ppt/presentation.xml", presentation(slide_count))
        z.writestr("ppt/_rels/presentation.xml.rels", presentation_rels(slide_count))
        z.writestr("ppt/theme/theme1.xml", theme())
        z.writestr("ppt/slideMasters/slideMaster1.xml", slide_master())
        z.writestr("ppt/slideMasters/_rels/slideMaster1.xml.rels", """<?xml version="1.0" encoding="UTF-8" standalone="yes"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/slideLayout" Target="../slideLayouts/slideLayout1.xml"/></Relationships>""")
        z.writestr("ppt/slideLayouts/slideLayout1.xml", slide_layout())
        z.writestr("ppt/slideLayouts/_rels/slideLayout1.xml.rels", """<?xml version="1.0" encoding="UTF-8" standalone="yes"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/slideMaster" Target="../slideMasters/slideMaster1.xml"/></Relationships>""")

        for i, s in enumerate(slides, start=1):
            kind = s.get("kind")
            if kind == "cover":
                shapes = cover_slide(s)
            elif kind == "roles":
                shapes = role_slide(s["title"])
            elif kind == "modules":
                shapes = modules_slide(s["title"])
            elif kind == "architecture":
                shapes = architecture_slide(s["title"])
            elif kind == "models":
                shapes = models_slide(s["title"])
            elif kind == "progress":
                shapes = progress_slide(s["title"])
            else:
                shapes = default_slide(s["title"], s["items"], i)
            z.writestr(f"ppt/slides/slide{i}.xml", slide_xml(shapes))
            z.writestr(f"ppt/slides/_rels/slide{i}.xml.rels", slide_rels())


if __name__ == "__main__":
    build()
    print(OUT)
