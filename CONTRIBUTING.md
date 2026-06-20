# 贡献指南

感谢你关注 Stock Analyst Skill！本指南将帮助你了解如何为项目贡献代码。

## 行为准则

- 使用包容性语言
- 尊重不同的观点和经验
- 优雅地接受建设性批评

## 快速开始

### 环境要求

\\\ash
Python 3.8+
git clone https://github.com/zhuang-HE/stock-analyst-skill.git
pip install -r requirements.txt
\\\

## 分支策略

| 分支类型 | 命名规范 | 示例 |
|---------|---------|------|
| 主分支 | main | 稳定版本 |
| 功能分支 | feat/ + 描述 | feat/candlestick-pattern |
| 修复分支 | fix/ + 描述 | fix/macd-calculation |

## 提交规范

\\\
<type>(<scope>): <subject>
\\\

**类型**：feat, fix, docs, refactor, perf, test, chore

**示例**：
\\\ash
git commit -m "feat(candlestick): add morning star pattern"
git commit -m "fix(macd): correct signal line calculation"
\\\

## Pull Request 流程

1. 从 main 创建功能分支
2. 开发并测试
3. Push 并创建 PR
4. 等待至少 1 人 approve
5. 点击 Merge 完成合并

## 代码规范

- 遵循 PEP 8 规范
- 函数命名：snake_case
- 类命名：PascalCase
- 常量：UPPER_SNAKE_CASE

---

**感谢你的贡献！**