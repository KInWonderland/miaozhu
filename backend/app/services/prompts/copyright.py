from app.models.application import Application
from app.services.prompts.base import PromptBuilder


class CopyrightPromptBuilder(PromptBuilder):
    """软件著作权申请材料提示词构建器"""

    SYSTEM_PROMPT = """你是一位专业的软件著作权申请材料撰写专家，拥有丰富的软著申请经验。
你需要根据用户提供的软件信息，撰写高质量的软件著作权申请材料。

要求：
1. 内容专业、详实，符合中国版权局对软件著作权登记的要求
2. 语言规范、通顺，使用正式的技术文档风格
3. 内容充实，涵盖关键要点和必要细节
4. 根据软件的实际功能和特点来撰写，不要生搬硬套
5. 输出 Markdown 格式
6. 控制篇幅：既要内容完整，又要避免过度冗长

Markdown 格式规范（非常重要）：
1. **只有章节和小节使用标题（# 或 ##），其他所有内容不得使用标题格式**
2. **步骤、列表、配置项、FAQ 等编号内容必须使用列表格式（1. 2. 3. 或 -），绝对不要用标题（#）**
3. 示例：
   - ✅ 正确：1. 第一步操作   2. 第二步操作   63. 启动服务
   - ❌ 错误：# 1. 第一步操作   # 2. 第二步操作   # 63. 启动服务
4. 表格数据必须用表格格式（| 列1 | 列2 |），不得用标题或列表

严格禁止：
- 不要在开头添加任何寒暄、自我介绍或角色说明（如"好的，作为一名专业的..."、"我将为您撰写..."）
- 不要在结尾添加任何总结性说明（如"撰写说明：..."、"（章节结束）"、"本章节已严格按照..."）
- 不要添加分隔线后的元信息或写作说明
- 直接输出章节正文内容，不要有任何多余的前缀和后缀"""

    SECTION_TEMPLATES: dict[str, str] = {
        "manual_introduction": """请撰写操作说明书的「引言」章节。

请按以下结构组织内容（每个主题作为一级标题）：

# 编写目的
详细说明编写此操作说明书的目的和意义

# 软件概述
介绍软件的名称、用途、核心功能和应用价值

# 使用对象
说明本手册的适用读者，分角色描述

# 术语定义
列出文档中使用的所有专业术语及其详细解释（不少于 15 个术语）
每个术语用列表格式：
- API：应用程序接口，用于...
- JWT：JSON Web Token，一种...
- ORM：对象关系映射，用于...

# 参考资料
列出编写过程中参考的文档、标准和规范（使用列表格式）

# 文档约定
说明文档中使用的排版约定和符号说明

# 版本历史
列出文档的版本更新记录（使用列表或表格格式）

格式要求：
- **上述每个主题必须使用一级标题（#）**
- 子节使用二级标题（##）
- **术语定义、参考资料等列表内容使用列表格式（-），不要用标题（#）**
  - ✅ 正确：- API：应用程序接口   - JWT：JSON Web Token
  - ❌ 错误：# API：应用程序接口   # JWT
- 约 1300-1650 字。每个小节精炼，术语表中每个术语用 1 句话解释。""",

        "manual_overview": """请撰写操作说明书的「软件概述」章节。

请按以下结构组织内容（每个主题作为一级标题）：

# 软件简介
详细描述软件的功能定位、应用场景、解决的核心问题

# 软件架构

## 技术架构层次
描述软件的整体技术架构（前端、后端、数据层）

## 架构图示
用文字描述或简单符号表示层次关系

# 功能模块划分

列出所有主要功能模块及其职责（使用列表格式）：
- 用户管理模块：负责用户注册、登录、权限管理等
  - 用户注册功能
  - 用户登录功能
  - 权限分配功能
- 数据分析模块：负责数据统计和分析
  - 数据采集功能
  - 统计分析功能
  - 可视化展示功能

# 技术特点

描述软件采用的关键技术和创新点（使用列表格式，不少于 8 个）：
- 采用前后端分离架构，提高系统可维护性
- 使用 RESTful API 设计，标准化接口交互
- 引入缓存机制，提升系统响应速度

# 适用范围
说明软件的适用场景和目标用户群体

# 设计原则
描述软件的设计理念和遵循的设计原则（使用列表格式）

# 系统优势

与同类软件相比的优势和特色（使用列表格式，不少于 5 个）：
- 界面友好，操作简便，降低学习成本
- 性能优异，支持高并发访问
- 安全可靠，多层次安全防护

# 系统限制
说明系统的使用限制和约束条件（使用列表格式）

格式要求：
- **上述每个主要类别（软件简介、软件架构等）必须使用一级标题（#）**
- **子分类（技术架构层次等）使用二级标题（##）**
- **功能模块、技术特点、优势等列表内容使用列表格式（-），不要用标题（#）**
  - ✅ 正确：- 用户管理模块：负责...   - 数据分析模块：负责...
  - ❌ 错误：# 用户管理模块   # 数据分析模块
- 约 2000-2200 字。功能模块层次清晰，技术特点和优势简明。""",

        "manual_environment": """请撰写操作说明书的「运行环境」章节。

请按以下结构组织内容（每个主题作为一级标题）：

# 硬件环境

## 服务器端硬件要求
使用表格展示最低配置和推荐配置：
| 配置项 | 最低要求 | 推荐配置 |
| CPU | Intel i5 或同等性能 | Intel Xeon 或更高 |
| 内存 | 8GB | 16GB 或更高 |
（包括 CPU、内存、硬盘、网卡等）

## 客户端硬件要求
最低配置和推荐配置

## 网络设备要求
网络设备的具体要求

# 软件环境

## 操作系统
服务器端和客户端操作系统要求及版本

## 数据库系统
数据库类型及版本要求

## 中间件及应用服务器
所需的中间件和应用服务器

## 运行时环境
JDK、Node.js 等运行时环境要求

## 第三方依赖组件
列出主要的第三方依赖（使用列表格式）

# 网络环境

## 网络带宽
带宽要求说明

## 网络协议
支持的网络协议

## 防火墙和安全策略
防火墙配置要求

## 端口使用说明
系统使用的端口列表（使用表格或列表）

# 浏览器要求
支持的浏览器及最低版本（使用列表格式）

# 性能指标
- 系统支持的最大并发用户数
- 响应时间要求
- 数据存储容量要求

格式要求：
- **上述每个主要类别（硬件环境、软件环境等）必须使用一级标题（#）**
- **子分类（服务器端硬件要求、操作系统等）使用二级标题（##）**
- **配置项、端口列表、依赖列表等使用列表格式（-）或表格，不要用标题（#）**
  - ✅ 正确（列表）：- CPU: Intel i5 或以上   - 内存: 8GB
  - ✅ 正确（表格）：| 配置项 | 最低要求 | 推荐配置 |
  - ❌ 错误：# CPU: Intel i5   # 内存: 8GB
- 约 1100-1300 字。优先使用表格展示配置要求。""",

        "manual_installation": """请撰写操作说明书的「安装与配置」章节。

请按以下结构组织内容（每个主题作为一级标题）：

# 安装准备

## 环境检查清单
安装前的环境检查项目（使用列表格式）

## 软件和工具下载
必要的软件和工具列表及下载地址

## 安装包获取
安装包的获取方式和说明

## 账号和权限准备
安装所需的账号和权限要求

# 服务器端安装

## 操作系统配置
操作系统的配置要求和步骤（使用列表格式）

## 数据库安装和配置
数据库的安装和配置步骤（使用有序列表）：
1. 下载 MySQL 8.0 安装包
2. 执行安装程序
3. 配置 root 密码
4. 启动数据库服务

## 应用服务器部署
应用服务器的部署步骤

## 后端服务安装
后端服务的详细安装步骤（使用有序列表）

# 客户端安装

## 客户端软件安装
客户端软件的安装步骤（如适用）

## 浏览器插件安装
浏览器插件的安装方法（如适用）

# 环境配置

## 数据库连接配置
数据库连接的配置方法和参数说明

## 系统参数配置
系统参数的配置项和说明

## 缓存服务配置
缓存服务的配置方法

## 文件存储配置
文件存储路径和配置

## 日志配置
日志级别和路径配置

# 数据库初始化

数据库初始化的详细步骤（使用有序列表）：
1. 创建数据库：CREATE DATABASE dbname
2. 导入表结构：执行 schema.sql
3. 导入初始数据：执行 init_data.sql
4. 设置数据库权限：GRANT ALL ON dbname.* TO 'user'@'%'
5. 验证初始化结果

# 系统初始化

系统初始化的步骤（使用有序列表）：
1. 创建管理员账号
2. 配置系统基础参数
3. 初始化功能权限
4. 验证初始化完成

# 验证安装

安装验证的步骤（使用有序列表）：
1. 启动服务并验证进程
2. 测试功能连通性
3. 运行性能基准测试

# 常见问题

列出安装过程中可能遇到的问题及解决方案（不少于 10 个，使用列表格式）：
- 数据库连接失败：检查数据库服务状态和连接配置
- 端口被占用：使用 netstat 查看端口占用情况，修改配置或停止占用进程
- 权限不足：使用 sudo 或管理员权限执行安装命令

格式要求：
- **上述每个主要类别（安装准备、服务器端安装等）必须使用一级标题（#）**
- **子分类（环境检查清单、数据库安装和配置等）使用二级标题（##）**
- **安装步骤、配置项、问题列表等必须使用列表格式（1. 2. 3. 或 -），绝对不要用标题（#）**
  - ✅ 正确：1. 下载安装包   2. 执行安装   63. 启动服务
  - ❌ 错误：# 1. 下载安装包   # 63. 启动服务
- 约 1650-2000 字。关键步骤有命令示例，常见问题简明扼要。""",

        "manual_functions_1": """请撰写「功能详述（上）」章节内容。

请详细描述软件的前半部分核心功能模块，包括但不限于：
- 用户注册与登录
- 用户个人中心与信息管理
- 首页/仪表盘
- 数据录入和管理功能
- 搜索和查询功能

针对每一个功能模块，请按以下结构组织内容：

# 功能模块名称

## 功能说明
该功能的目的、作用和业务价值

## 操作入口
如何进入该功能页面

## 界面说明
操作界面的布局、各个控件的位置和作用

## 操作流程
分步骤描述用户如何使用该功能

## 输入说明
需要输入的数据字段及其格式要求

## 输出说明
功能执行后的输出结果、反馈信息

## 注意事项
使用该功能时需要注意的事项

格式要求：
- 不要添加"操作说明书"等总标题
- 不要使用"第一章"、"第二章"等中文编号
- 功能模块名称使用一级标题（#），如：# 用户注册与登录
- 功能模块内的小节使用二级标题（##），如：## 功能说明
- 不要在正文中手写编号（如 1.1、1.2），标题会自动编号
- **操作步骤使用有序列表（1. 2. 3.）或无序列表（-），绝对不要用标题（#）**
  - ✅ 正确示例：1. 打开浏览器   2. 输入网址   3. 点击登录
  - ❌ 错误示例：# 1. 打开浏览器   # 2. 输入网址   # 3. 点击登录
- **配置项、安装步骤等编号内容必须使用列表格式，不要使用标题**
  - ✅ 正确示例（列表）：1. 启动服务   2. 验证安装   63. 配置参数
  - ❌ 错误示例（标题）：# 1. 启动服务   # 63. 配置参数
- 约 4000-4500 字，覆盖 4-6 个核心功能模块
- 内容详细充分，重点突出主要功能""",

        "manual_functions_2": """请撰写「功能详述（下）」章节内容。延续上半部分，描述软件的后半部分功能模块。

请详细描述软件的后半部分功能模块，包括但不限于：
- 报表和统计分析功能
- 数据导入导出功能
- 消息通知功能
- 系统配置和参数设置
- 日志和审计功能
- 其他辅助功能

针对每一个功能模块，请按以下结构组织内容：

# 功能模块名称

## 功能说明
该功能的目的、作用和业务价值

## 操作入口
如何进入该功能页面

## 界面说明
操作界面的布局、各个控件的位置和作用

## 操作流程
分步骤描述用户如何使用该功能

## 输入说明
需要输入的数据字段及其格式要求

## 输出说明
功能执行后的输出结果、反馈信息

## 注意事项
使用该功能时需要注意的事项

格式要求：
- 不要添加"操作说明书"等总标题
- 不要使用"第一章"、"第二章"等中文编号
- 功能模块名称使用一级标题（#），如：# 报表统计
- 功能模块内的小节使用二级标题（##），如：## 功能说明
- 不要在正文中手写编号（如 1.1、1.2），标题会自动编号
- **操作步骤使用有序列表（1. 2. 3.）或无序列表（-），绝对不要用标题（#）**
  - ✅ 正确示例：1. 打开浏览器   2. 输入网址   3. 点击登录
  - ❌ 错误示例：# 1. 打开浏览器   # 2. 输入网址   # 3. 点击登录
- **配置项、安装步骤等编号内容必须使用列表格式，不要使用标题**
  - ✅ 正确示例（列表）：1. 启动服务   2. 验证安装   63. 配置参数
  - ❌ 错误示例（标题）：# 1. 启动服务   # 63. 配置参数
- 约 4000-4500 字，覆盖 4-6 个核心功能模块
- 内容详细充分，重点突出主要功能
- 不要与上半部分重复""",

        "manual_security": """请撰写操作说明书的「安全管理与权限控制」章节。

请按以下结构组织内容（每个主题作为一级标题）：

# 安全概述

## 系统安全设计理念
系统的安全设计思想和原则

## 安全防护体系架构
安全防护的整体架构说明

## 遵循的安全标准和规范
参考的安全标准（使用列表格式）

# 用户认证

## 登录认证机制
登录认证的实现方式和流程

## 密码策略
密码的具体要求（使用列表格式）：
- 密码长度不少于 8 位
- 必须包含大小写字母
- 必须包含数字和特殊字符
- 密码过期策略：90 天
- 历史密码检查：不允许使用最近 5 次密码

## 多因素认证
多因素认证的支持情况（如适用）

## 会话管理
会话超时策略和管理机制

## 登录失败锁定
登录失败锁定策略说明

# 权限管理

## 角色定义
系统的角色类型和层级（使用列表或表格）

## 权限分配机制
权限分配的方式和流程

## 功能权限控制
菜单级、按钮级、数据级权限控制说明

## 数据权限控制
行级、字段级数据权限控制

## 权限继承和冲突处理
权限继承规则和冲突解决策略

# 数据安全

## 数据加密策略
传输加密和存储加密的实现

## 敏感数据脱敏
敏感数据的脱敏处理方式

## 数据备份和恢复
数据备份和恢复策略

## 数据保留和销毁
数据保留期限和销毁策略

# 操作审计

## 操作日志记录
日志记录的范围和内容

## 日志查询和分析
日志查询和分析功能

## 安全告警
安全告警机制和触发条件

## 审计报告
审计报告的生成和内容

# 网络安全

## SQL 注入防护
防 SQL 注入的实现方式

## XSS 攻击防护
防 XSS 攻击的措施

## CSRF 攻击防护
防 CSRF 攻击的机制

## API 安全
API 的认证、限流、防重放机制

## HTTPS 配置
HTTPS 的配置和证书管理

格式要求：
- **上述每个主要类别（安全概述、用户认证等）必须使用一级标题（#）**
- **子分类（登录认证机制、密码策略等）使用二级标题（##）**
- **安全措施、策略要求、规则列表等使用列表格式（-），不要用标题（#）**
  - ✅ 正确：- 密码长度不少于8位   - 必须包含大小写字母   - 必须包含数字
  - ❌ 错误：# 密码长度不少于8位   # 必须包含大小写字母
- 约 2000-2200 字。体现系统的安全性，关键安全措施简述实现方式。""",

        "manual_other_notes": """请撰写操作说明书的「其他说明」章节。

请按以下结构组织内容（每个主题作为一级标题）：

# 系统维护

## 日常巡检
日常巡检项目和频率（使用列表格式）

## 性能监控
性能监控指标和调优建议

## 日志管理
日志管理和清理策略

## 健康检查
系统健康检查的方法和工具

# 数据备份与恢复

## 备份策略
全量备份、增量备份、差异备份的说明

## 备份频率
备份频率和保留策略

## 备份验证
备份数据验证方法

## 数据恢复
数据恢复操作步骤（使用有序列表）：
1. 停止相关服务
2. 定位备份文件
3. 执行恢复命令
4. 验证数据完整性
5. 重启服务

## 灾难恢复
灾难恢复方案说明

# 故障处理

## 常见故障及处理
列出不少于 10 种故障场景及处理方法（使用列表格式）：
- 数据库连接失败：检查数据库服务状态，验证连接配置
- 页面加载缓慢：清理浏览器缓存，检查网络连接
- 登录超时：检查会话配置，清除 Cookie 重新登录

## 故障诊断工具
故障诊断的工具和方法

## 故障升级流程
故障升级的流程和标准

# 性能优化

## 数据库优化
数据库优化的建议和方法

## 缓存策略
缓存策略优化建议

## 系统参数调优
系统参数调优指南

# 版本更新

## 更新流程
版本更新的详细流程

## 更新准备
更新前的准备工作清单

## 回滚方案
版本回滚的方案和步骤

## 更新日志
更新日志的管理方式

# 技术支持

## 联系方式
技术支持的联系方式

## 问题反馈
问题反馈的流程和渠道

## 常见问题 FAQ
列出不少于 15 个常见问题及解答（使用列表格式）：
- Q: 如何重置密码？
  A: 点击登录页面的"忘记密码"链接，按照提示操作
- Q: 如何修改个人信息？
  A: 登录后进入个人中心，点击编辑按钮修改

格式要求：
- **上述每个主要类别（系统维护、数据备份与恢复等）必须使用一级标题（#）**
- **子分类（日常巡检、备份策略等）使用二级标题（##）**
- **步骤、FAQ、故障场景等使用列表格式（- 或 1. 2. 3.），不要用标题（#）**
  - ✅ 正确（故障）：- 数据库连接失败：检查数据库服务状态
  - ✅ 正确（FAQ）：- Q: 如何重置密码？ A: 点击忘记密码...
  - ❌ 错误：# 数据库连接失败   # Q: 如何重置密码
- 约 1650-2000 字。故障处理包含主要场景，FAQ 包含常见问题。""",

        # 旧版 manual_functions 兼容（已有任务重新生成时使用）
        "manual_functions": """请撰写「功能详述」章节内容。

针对软件的每一个主要功能模块，请按以下结构组织内容：

# 功能模块名称

## 功能说明
该功能的目的和作用

## 操作流程
用户如何使用该功能（步骤化描述）

## 界面说明
描述相关的操作界面和控件

## 输入说明
需要输入的数据及其格式要求

## 输出说明
功能执行后的输出结果

## 注意事项
使用该功能时需要注意的事项

格式要求：
- 不要添加"操作说明书"等总标题
- 不要使用"第一章"、"第二章"等中文编号
- 功能模块名称使用一级标题（#）
- 功能模块内的小节使用二级标题（##）
- 不要在正文中手写编号（如 1.1、1.2），标题会自动编号
- **操作步骤使用有序列表（1. 2. 3.）或无序列表（-），绝对不要用标题（#）**
  - ✅ 正确示例：1. 打开页面   2. 填写表单   3. 点击提交
  - ❌ 错误示例：# 1. 打开页面   # 2. 填写表单
- 约 2000-2500 字
- 内容简明扼要""",

        "source_code_front": """请为该软件生成源程序代码的前半部分（前 30 页内容）。

软著申请要求：源代码文档每页不少于 50 行，前 30 页约需要 1500 行以上的代码。

要求：
1. 根据软件的功能描述和技术栈，生成合理、可运行的源代码
2. 代码应包含：项目入口文件、配置文件、路由定义、核心数据模型、核心服务层代码
3. 每个文件都要有文件头注释（文件名、作用说明、作者、日期）
4. 代码要有合理的行内注释
5. 代码风格规范，符合对应编程语言的最佳实践
6. 每个文件之间用明确的文件路径标记分隔
7. 格式要求（严格遵守）：

// ============ 文件路径: src/main.js ============
// 功能说明: 应用入口文件
// 作者: 开发团队
// 创建日期: 2024-01-01

代码内容...

// ============ 文件路径: src/config/index.js ============
代码内容...

8. 不要使用 markdown 代码块（```），直接输出纯代码文本
9. 代码量要充足，至少 800 行，尽量达到 1000 行
10. 代码要有完整的逻辑，不要用省略号或 TODO 占位""",

        "source_code_back": """请为该软件生成源程序代码的后半部分（后 30 页内容）。

软著申请要求：源代码文档每页不少于 50 行，后 30 页约需要 1500 行以上的代码。

要求：
1. 延续前半部分的代码风格和架构设计
2. 代码应包含：业务逻辑模块、数据处理层、工具类/帮助函数、中间件、测试代码、前端组件代码
3. 每个文件都要有文件头注释（文件名、作用说明、作者、日期）
4. 代码要有合理的行内注释
5. 每个文件之间用明确的文件路径标记分隔
6. 格式要求（严格遵守）：

// ============ 文件路径: src/services/userService.js ============
// 功能说明: 用户服务模块
// 作者: 开发团队
// 创建日期: 2024-01-01

代码内容...

// ============ 文件路径: src/utils/helpers.js ============
代码内容...

7. 不要使用 markdown 代码块（```），直接输出纯代码文本
8. 代码量要充足，至少 800 行，尽量达到 1000 行
9. 代码要有完整的逻辑，不要用省略号或 TODO 占位
10. 不要与前半部分代码重复""",

        "db_design": """请为该软件设计完整的数据库表结构。

请按以下结构组织内容：

# 数据库概述
说明数据库的整体设计思路、选型理由和设计原则

# 数据表设计

## 用户表（users）

**表说明**：存储系统用户的基本信息

**字段结构**：

| 字段名 | 类型 | 长度 | 是否为空 | 默认值 | 说明 |
|--------|------|------|----------|--------|------|
| id | BIGINT | - | NOT NULL | AUTO_INCREMENT | 主键ID |
| username | VARCHAR | 50 | NOT NULL | - | 用户名 |
| password | VARCHAR | 255 | NOT NULL | - | 密码（加密） |
| email | VARCHAR | 100 | NULL | - | 邮箱 |
| status | TINYINT | 1 | NOT NULL | 1 | 状态（1启用 0禁用） |
| created_at | DATETIME | - | NOT NULL | CURRENT_TIMESTAMP | 创建时间 |
| updated_at | DATETIME | - | NOT NULL | CURRENT_TIMESTAMP | 更新时间 |

**索引设计**：
- PRIMARY KEY (id)
- UNIQUE INDEX idx_username (username)
- INDEX idx_email (email)
- INDEX idx_created_at (created_at)

**外键关系**：
（如有外键，列出外键约束）

## 其他表名（table_name）

（按上述格式继续列出其他表，约 4-6 张核心表）

# ER 关系说明

描述各表之间的关联关系：
- users 表与 roles 表：一对多关系，一个用户可以有多个角色
- orders 表与 order_items 表：一对多关系，一个订单包含多个订单项
- users 表与 orders 表：一对多关系，一个用户可以创建多个订单

# 设计说明

解释关键的设计决策（使用列表格式）：
- 密码字段使用 VARCHAR(255) 以支持各种加密算法
- 所有表都包含 created_at 和 updated_at 字段便于追踪数据变更
- 使用逻辑删除（status 字段）而非物理删除以保留数据历史

格式要求：
- **主要章节（数据库概述、数据表设计等）使用一级标题（#）**
- **每张表使用二级标题（##）**，格式：## 表名（英文表名）
- **字段结构必须使用表格格式**，不要用标题或列表
  - ✅ 正确：| 字段名 | 类型 | 长度 | 说明 |
  - ❌ 错误：# id   # username   # password
- **索引设计、外键关系、设计说明等使用列表格式（-），不要用标题**
  - ✅ 正确：- PRIMARY KEY (id)   - UNIQUE INDEX idx_username (username)
  - ❌ 错误：# PRIMARY KEY (id)   # UNIQUE INDEX
- 表结构要符合数据库设计规范（三范式）
- 字段命名使用下划线命名法
- 每张表都要有 id、created_at、updated_at 基础字段
- 根据软件功能合理设计表结构，约 4-6 张核心表
- 总篇幅约 1000-1500 字""",

        "arch_diagram": """请根据软件信息，生成系统架构图的 D2 代码（D2 是一种现代架构图语言，支持分层容器和丰富的节点形状）。

只输出 D2 代码块，不要有任何其他文字：

```d2
direction: down

接入层: {
  style.fill: "#e0f2fe"
  style.stroke: "#0284c7"
  nginx: Nginx反向代理 {
    shape: hexagon
    style.fill: "#0ea5e9"
    style.font-color: white
  }
  gateway: API网关 {
    style.fill: "#38bdf8"
    style.font-color: white
  }
}

应用层: {
  style.fill: "#f0fdf4"
  style.stroke: "#16a34a"
  auth: 认证服务 {shape: rectangle}
  biz: 核心业务模块 {shape: rectangle}
  notify: 消息通知服务 {shape: rectangle}
}

缓存层: {
  style.fill: "#fff7ed"
  style.stroke: "#ea580c"
  redis: Redis缓存 {
    shape: cylinder
    style.fill: "#f97316"
    style.font-color: white
  }
}

存储层: {
  style.fill: "#faf5ff"
  style.stroke: "#9333ea"
  mysql: MySQL数据库 {
    shape: cylinder
    style.fill: "#a855f7"
    style.font-color: white
  }
  oss: 对象存储 {
    shape: cylinder
    style.fill: "#c084fc"
    style.font-color: white
  }
}

接入层.nginx -> 接入层.gateway
接入层.gateway -> 应用层
应用层 -> 缓存层.redis
应用层 -> 存储层
```

要求：
1. 分层和模块名称必须与本软件实际技术栈吻合（Nginx/网关/应用服务/缓存/数据库等）
2. 每层包含 2-4 个真实组件节点，数据库/缓存使用 `shape: cylinder`，网关使用 `shape: hexagon`
3. 每层用不同 fill 颜色区分（接入层蓝、应用层绿、缓存层橙、存储层紫）
4. 箭头表示真实数据流向
5. 只输出 D2 代码块，不要有任何说明文字""",

        "uml_diagram": """请根据软件信息，生成核心模块的 PlantUML 类图代码。

只输出 PlantUML 代码块，不要有任何其他文字：

```plantuml
@startuml
skinparam classBackgroundColor #FEFEFE
skinparam classBorderColor #888888
skinparam ArrowColor #444444
skinparam classFontSize 12
skinparam classAttributeFontSize 11
skinparam padding 5

class User {
  +id: Long
  +username: String
  +email: String
  +phone: String
  +status: Integer
  +createdAt: DateTime
  +login(): Boolean
  +logout(): void
  +updateProfile(): void
}

class Role {
  +id: Long
  +name: String
  +code: String
  +permissions: List
  +addPermission(): void
  +removePermission(): void
}

class Order {
  +id: Long
  +orderNo: String
  +status: String
  +totalAmount: Decimal
  +userId: Long
  +create(): void
  +cancel(): void
  +pay(): void
}

class Product {
  +id: Long
  +name: String
  +price: Decimal
  +stock: Integer
  +categoryId: Long
  +updateStock(): void
}

User "1" --> "0..*" Order : 创建
User "N" --> "N" Role : 拥有
Order "1" --> "N" Product : 包含
@enduml
```

要求：
1. 根据软件核心业务生成 **8-12 个** 关键实体类（覆盖用户/权限/核心业务/配置/日志等模块）
2. 每个类包含 4-6 个核心属性（含 id、状态、时间戳）和 2-4 个核心方法
3. 类之间用关联/组合/继承/依赖箭头连接，标注中文关系说明和数量关系（1对1/1对N/N对N）
4. 用 `package` 块按模块分组（如 用户模块、业务模块、系统模块）
5. 类名和字段名使用英文，关系说明和 package 名使用中文
6. 只输出 PlantUML 代码块，不要有任何说明文字""",

        "ui_diagrams": """请根据软件信息，生成关键功能界面的 HTML 模板。

生成 4-6 个界面，每个界面是一个完整的 HTML 页面截图区域，用单个 HTML 文件包含所有界面（用分割线隔开）。

只输出 HTML 代码块，不要有任何其他文字：

```html
<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<style>
  * { box-sizing: border-box; margin: 0; padding: 0; font-family: 'Microsoft YaHei', sans-serif; }
  .screen { width: 1200px; background: #f5f7fa; margin-bottom: 40px; border: 2px solid #e0e0e0; }
  .screen-title { background: #333; color: white; padding: 8px 16px; font-size: 14px; }
  .topbar { background: #1a1a2e; color: white; height: 50px; display: flex; align-items: center; padding: 0 20px; font-size: 15px; font-weight: bold; }
  .nav { background: #16213e; width: 200px; min-height: 500px; padding: 16px 0; float: left; }
  .nav-item { padding: 10px 20px; color: #aaa; font-size: 13px; cursor: pointer; }
  .nav-item.active { background: #0f3460; color: white; }
  .content { margin-left: 200px; padding: 20px; }
  .card-row { display: flex; gap: 16px; margin-bottom: 20px; }
  .card { flex: 1; background: white; border-radius: 8px; padding: 16px; box-shadow: 0 2px 8px rgba(0,0,0,0.08); }
  .card .num { font-size: 28px; font-weight: bold; color: #1a1a2e; }
  .card .label { font-size: 12px; color: #999; margin-top: 4px; }
  table { width: 100%; border-collapse: collapse; background: white; border-radius: 8px; overflow: hidden; }
  th { background: #f0f0f0; padding: 10px 12px; text-align: left; font-size: 13px; color: #555; }
  td { padding: 10px 12px; border-bottom: 1px solid #f0f0f0; font-size: 13px; }
  .btn { display: inline-block; padding: 5px 12px; background: #0f3460; color: white; border-radius: 4px; font-size: 12px; }
  .btn-red { background: #e74c3c; }
  .clearfix::after { content: ""; display: block; clear: both; }
  .login-box { width: 400px; margin: 80px auto; background: white; border-radius: 12px; padding: 40px; box-shadow: 0 4px 20px rgba(0,0,0,0.12); }
  .login-title { font-size: 22px; font-weight: bold; text-align: center; margin-bottom: 24px; color: #1a1a2e; }
  .form-item { margin-bottom: 16px; }
  .form-item label { display: block; font-size: 13px; color: #555; margin-bottom: 6px; }
  .form-item input, .form-item select, .form-item textarea { width: 100%; border: 1px solid #ddd; border-radius: 6px; padding: 8px 12px; font-size: 13px; }
  .submit-btn { width: 100%; background: #0f3460; color: white; border: none; border-radius: 6px; padding: 12px; font-size: 15px; cursor: pointer; }
</style>
</head>
<body style="background:#eee; padding:20px;">
<!-- 在此处根据软件实际功能生成各界面 -->
</body>
</html>
```

要求：
1. 必须包含：登录页、首页（含统计卡片）、列表页、表单页
2. 界面内容（菜单、表头、字段等）必须与该软件的实际功能模块吻合
3. 风格统一：深色导航 + 白色卡片 + 蓝色主按钮
4. 每个界面用 `<div class="screen">` 包裹，首行加 `<div class="screen-title">界面名称</div>`
5. 只输出完整 HTML 代码块，不要有任何说明文字""",

        "form_autofill": """请根据软件信息，生成软件著作权申请表需要填写的字段建议值。

请以 JSON 格式输出，包含以下字段（只输出 JSON，不要其他内容）：
{
    "software_version": "V1.0",
    "software_category": "应用软件",
    "completion_date": "YYYY-MM-DD",
    "development_method": "单独开发",
    "dev_hardware": "开发电脑配置，50字符以内",
    "runtime_hardware": "实际部署或运行设备配置，50字符以内",
    "dev_os": "开发电脑的操作系统，50字符以内",
    "dev_tools": "实际使用的开发工具，50字符以内",
    "runtime_platform": "实际运行平台或操作系统，50字符以内",
    "runtime_software": "运行依赖或支持软件，50字符以内",
    "development_language": "实际编程语言",
    "code_line_count": "纯数字，不含“行”字",
    "development_purpose": "一句话描述开发目的，50字符以内",
    "target_industry": "面向领域或行业，50字符以内",
    "technical_features": "技术特点标签及简述，100字符以内",
    "work_type": "原创",
    "rights_acquisition": "原始取得",
    "rights_scope": "全部权利",
    "publish_status": "未发表"
}

注意：
1. 结合软件名称、主要功能、模块设计及已有字段推断，不要使用占位符
2. 只输出 JSON，不要有其他文字说明
3. 所有值都是字符串类型
4. 不得编造著作权人、证件信息和首次发表日期
5. 无法从软件信息合理推断的事实字段返回空字符串""",
    }

    def _build_context(self, app: Application) -> str:
        """从 Application 模型构建软件信息上下文"""
        parts = [f"软件名称：{app.software_name or '未填写'}"]
        parts.append(f"软件简称：{app.software_short_name or '未填写'}")
        parts.append(f"主要功能：{app.main_features or '未填写'}")

        if app.software_version:
            parts.append(f"软件版本：{app.software_version}")
        if app.software_category:
            parts.append(f"软件类别：{app.software_category}")
        if app.software_description:
            parts.append(f"软件描述：{app.software_description}")
        if app.development_language:
            parts.append(f"开发语言：{app.development_language}")
        if app.runtime_platform:
            parts.append(f"运行平台：{app.runtime_platform}")
        if app.technical_features:
            parts.append(f"技术特点：{app.technical_features}")
        if app.module_design:
            parts.append(f"模块设计：{app.module_design}")
        if app.development_purpose:
            parts.append(f"开发目的：{app.development_purpose}")
        if app.target_industry:
            parts.append(f"目标行业：{app.target_industry}")
        if app.dev_hardware:
            parts.append(f"开发硬件：{app.dev_hardware}")
        if app.dev_os:
            parts.append(f"开发操作系统：{app.dev_os}")
        if app.dev_tools:
            parts.append(f"开发工具：{app.dev_tools}")
        if app.runtime_hardware:
            parts.append(f"运行硬件：{app.runtime_hardware}")
        if app.runtime_software:
            parts.append(f"运行软件：{app.runtime_software}")
        if app.code_line_count:
            parts.append(f"代码行数：{app.code_line_count}")

        return "\n".join(parts)

    # ── 图表嵌入指令（仅当 generate_diagrams=True 时追加） ──────────────────
    _DIAGRAM_INSTRUCTIONS: dict[str, str] = {
        "manual_overview": """\
## 图表嵌入要求

在「架构图示」小节正文末尾，插入一个 **D2** 系统架构图代码块，展示本软件的真实部署层次（含 Nginx/网关/应用服务/缓存/数据库）：

```d2
direction: down

接入层: {
  style.fill: "#e0f2fe"
  style.stroke: "#0284c7"
  nginx: Nginx {shape: hexagon; style.fill: "#0ea5e9"; style.font-color: white}
  gateway: API网关 {style.fill: "#38bdf8"; style.font-color: white}
}

应用层: {
  style.fill: "#f0fdf4"
  style.stroke: "#16a34a"
  模块A: 模块A名称 {shape: rectangle}
  模块B: 模块B名称 {shape: rectangle}
}

缓存层: {
  style.fill: "#fff7ed"
  style.stroke: "#ea580c"
  redis: Redis {shape: cylinder; style.fill: "#f97316"; style.font-color: white}
}

存储层: {
  style.fill: "#faf5ff"
  style.stroke: "#9333ea"
  mysql: MySQL {shape: cylinder; style.fill: "#a855f7"; style.font-color: white}
  oss: 对象存储 {shape: cylinder; style.fill: "#c084fc"; style.font-color: white}
}

接入层.nginx -> 接入层.gateway -> 应用层
应用层 -> 缓存层.redis
应用层 -> 存储层
```

在「功能模块划分」小节正文末尾，插入一个 PlantUML 类图代码块（8-12 个核心业务实体，按模块分组）：

```plantuml
@startuml
skinparam classBackgroundColor #FEFEFE
skinparam classBorderColor #888
skinparam classFontSize 12
package "用户模块" {
  class 实体名 { +字段: 类型; +方法() }
}
package "业务模块" {
  class 实体名2 { +字段: 类型; +方法() }
}
实体名 "1" --> "N" 实体名2 : 关联说明
@enduml
```

⚠️ 两个代码块内容必须完全替换为本软件的实际组件和业务实体，禁止保留任何示例占位符。""",

        "manual_functions_1": """\
## ⚠️ 界面截图强制要求（每个功能点必须执行，不得跳过）

**本节每一个功能模块，都必须在「界面说明」小节正文末尾，立即插入一个该功能界面的完整 html 代码块。**
**缺少 html 代码块 = 内容不完整。**

### 界面设计规范

每个 html 块必须：
1. 独立完整（含 `<!DOCTYPE html>`、CSS、完整 body）
2. `body` 固定 width:750px; height:560px; overflow:hidden
3. **三栏布局**：顶部导航栏(48px, #1e293b深色) + 左侧菜单(160px) + 主内容区
4. 顶栏左侧显示「软件简称 · 当前功能名」，右侧显示用户头像区（圆形头像+名字）
5. 左菜单列出**本软件所有主要功能模块**（图标+名称），当前功能高亮（#eff6ff背景+#2563eb左边框）
6. 主内容区必须有**真实感数据**：
   - 列表/管理页：面包屑 + 标题行 + 工具栏(搜索框+筛选+新增) + 数据表格(含4-5列字段，4行真实示例数据，每行有彩色状态标签+操作按钮) + 分页条
   - 表单/编辑页：面包屑 + 标题 + 分组表单(多个表单项，含输入框/下拉/日期选择器) + 底部操作按钮
   - 仪表盘/统计页：统计卡片行(4张，含数值+趋势箭头+环比数据) + 图表区(折线/柱状图，含坐标轴和数据点) + 最近记录表格
   - 卡片/广场页：搜索筛选栏 + 卡片网格(3列，每张卡片含图片占位+标题+标签+评分+操作按钮)
7. 状态标签用彩色胶囊：已通过=绿色、待审核=橙色、已拒绝=红色、正常=蓝色
8. 所有文字（菜单项、字段名、表头、示例数据、按钮）**必须与该功能完全对应**，绝对不允许出现"xxx"等占位符

### 高质量示例（列表管理页）

```html
<!DOCTYPE html><html><head><meta charset="UTF-8"><style>
*{box-sizing:border-box;margin:0;padding:0;font-family:'Microsoft YaHei',sans-serif;}
body{width:750px;height:560px;overflow:hidden;display:flex;flex-direction:column;background:#f1f5f9;}
.top{background:#1e293b;color:#fff;height:48px;display:flex;align-items:center;padding:0 16px;flex-shrink:0;}
.top-logo{font-size:14px;font-weight:700;flex:1;}
.top-user{display:flex;align-items:center;gap:8px;font-size:12px;}
.avatar{width:28px;height:28px;border-radius:50%;background:#3b82f6;display:flex;align-items:center;justify-content:center;font-size:12px;font-weight:700;}
.wrap{display:flex;flex:1;overflow:hidden;}
.nav{width:156px;background:#fff;border-right:1px solid #e2e8f0;padding:6px 0;flex-shrink:0;}
.nav-group{font-size:11px;color:#94a3b8;padding:10px 12px 4px;font-weight:600;}
.ni{padding:8px 12px;font-size:13px;color:#64748b;display:flex;align-items:center;gap:8px;cursor:pointer;border-radius:0;}
.ni.on{background:#eff6ff;color:#2563eb;font-weight:600;border-left:3px solid #2563eb;}
.main{flex:1;padding:14px;overflow:hidden;display:flex;flex-direction:column;gap:10px;}
.bc{font-size:11px;color:#94a3b8;}
.bc b{color:#475569;}
.ph{display:flex;justify-content:space-between;align-items:center;}
.pt{font-size:16px;font-weight:700;color:#0f172a;}
.bar{display:flex;gap:8px;align-items:center;}
.si{padding:6px 10px;border:1px solid #e2e8f0;border-radius:6px;font-size:12px;width:160px;background:#f8fafc;}
.sel{padding:6px 10px;border:1px solid #e2e8f0;border-radius:6px;font-size:12px;background:#f8fafc;}
.btn{padding:6px 14px;border:none;border-radius:6px;font-size:12px;cursor:pointer;display:flex;align-items:center;gap:4px;}
.b-blue{background:#2563eb;color:#fff;}
.b-out{background:#fff;color:#374151;border:1px solid #d1d5db;}
.b-green{background:#16a34a;color:#fff;}
.card{background:#fff;border-radius:10px;box-shadow:0 1px 4px rgba(0,0,0,.07);overflow:hidden;flex:1;display:flex;flex-direction:column;}
table{width:100%;border-collapse:collapse;}
thead tr{background:#f8fafc;}
th{padding:10px 12px;text-align:left;font-size:11px;color:#64748b;border-bottom:1px solid #e2e8f0;white-space:nowrap;}
td{padding:9px 12px;font-size:12px;color:#334155;border-bottom:1px solid #f1f5f9;white-space:nowrap;}
tr:last-child td{border-bottom:none;}
.tag{display:inline-flex;align-items:center;padding:2px 8px;border-radius:20px;font-size:11px;font-weight:500;}
.tg{background:#dcfce7;color:#15803d;}
.ty{background:#ffedd5;color:#c2410c;}
.tr{background:#fee2e2;color:#dc2626;}
.tb{background:#dbeafe;color:#1d4ed8;}
.lk{color:#2563eb;font-size:12px;cursor:pointer;margin-right:8px;}
.lk.d{color:#ef4444;}
.foot{display:flex;justify-content:space-between;align-items:center;padding:8px 12px;border-top:1px solid #f1f5f9;background:#fafafa;}
.fi{font-size:11px;color:#94a3b8;}
.pg{display:flex;gap:4px;}
.p{width:24px;height:24px;border-radius:4px;border:1px solid #e2e8f0;display:flex;align-items:center;justify-content:center;font-size:11px;cursor:pointer;}
.p.on{background:#2563eb;color:#fff;border-color:#2563eb;}
</style></head>
<body>
<div class="top">
  <div class="top-logo">【软件简称】管理平台</div>
  <div class="top-user"><div class="avatar">管</div>管理员</div>
</div>
<div class="wrap">
<div class="nav">
  <div class="nav-group">主要功能</div>
  <div class="ni on">📋 【当前功能】</div>
  <div class="ni">👥 【功能2】</div>
  <div class="ni">📊 【功能3】</div>
  <div class="ni">🔔 【功能4】</div>
  <div class="nav-group">系统</div>
  <div class="ni">⚙️ 系统设置</div>
  <div class="ni">📁 操作日志</div>
</div>
<div class="main">
  <div class="bc">首页 › <b>【当前功能名称】</b></div>
  <div class="ph">
    <div class="pt">【功能标题】列表</div>
    <div class="bar">
      <input class="si" placeholder="🔍 搜索【关键字段】">
      <select class="sel"><option>全部状态</option><option>正常</option><option>禁用</option></select>
      <button class="btn b-out">导出</button>
      <button class="btn b-blue">＋ 新增【对象】</button>
    </div>
  </div>
  <div class="card">
    <table>
      <thead><tr>
        <th>编号</th><th>【字段1】</th><th>【字段2】</th><th>【字段3】</th><th>创建时间</th><th>状态</th><th>操作</th>
      </tr></thead>
      <tbody>
        <tr><td>#001</td><td>【示例数据1】</td><td>【示例数据】</td><td>【示例数据】</td><td>2024-03-15</td><td><span class="tag tg">正常</span></td><td><span class="lk">详情</span><span class="lk">编辑</span><span class="lk d">删除</span></td></tr>
        <tr><td>#002</td><td>【示例数据2】</td><td>【示例数据】</td><td>【示例数据】</td><td>2024-03-14</td><td><span class="tag ty">待审核</span></td><td><span class="lk">详情</span><span class="lk">审核</span><span class="lk d">拒绝</span></td></tr>
        <tr><td>#003</td><td>【示例数据3】</td><td>【示例数据】</td><td>【示例数据】</td><td>2024-03-12</td><td><span class="tag tr">已拒绝</span></td><td><span class="lk">详情</span><span class="lk">重审</span><span class="lk d">删除</span></td></tr>
        <tr><td>#004</td><td>【示例数据4】</td><td>【示例数据】</td><td>【示例数据】</td><td>2024-03-10</td><td><span class="tag tg">正常</span></td><td><span class="lk">详情</span><span class="lk">编辑</span><span class="lk d">删除</span></td></tr>
      </tbody>
    </table>
    <div class="foot">
      <div class="fi">共 238 条 · 第 1/24 页</div>
      <div class="pg"><div class="p">‹</div><div class="p on">1</div><div class="p">2</div><div class="p">3</div><div class="p">…</div><div class="p">24</div><div class="p">›</div></div>
    </div>
  </div>
</div>
</div>
</body></html>
```

⚠️ 上面是参考样式框架。生成时必须：
- 将所有 `【xxx】` 替换为该功能的真实内容（如用户名/店铺名/申请人等真实字段）
- 左侧菜单项换成本软件实际的所有功能模块名称
- 对于仪表盘功能用统计卡片+图表布局，对于表单功能用分组表单布局，对于内容广场用卡片网格布局
- 每个界面要有 4 行以上真实示例数据，状态标签颜色要准确区分""",
    }
    # manual_functions_2 使用相同指令
    _DIAGRAM_INSTRUCTIONS["manual_functions_2"] = _DIAGRAM_INSTRUCTIONS["manual_functions_1"]

    def build(
        self,
        app: Application,
        section_key: str,
        extra_prompt: str | None = None,
    ) -> tuple[str, str]:
        template = self.SECTION_TEMPLATES.get(section_key)
        if not template:
            raise ValueError(f"Unknown section key: {section_key}")

        context = self._build_context(app)
        user_prompt = f"## 软件基本信息\n\n{context}\n\n## 撰写要求\n\n{template}"

        # 当 generate_diagrams=True 时，在相关章节追加图表嵌入指令
        if getattr(app, "generate_diagrams", False):
            diagram_instr = self._DIAGRAM_INSTRUCTIONS.get(section_key)
            if diagram_instr:
                user_prompt += f"\n\n{diagram_instr}"

        if extra_prompt:
            user_prompt += f"\n\n## 用户额外要求\n\n{extra_prompt}"

        return self.SYSTEM_PROMPT, user_prompt
