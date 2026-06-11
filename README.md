# 内网浏览器自动化编排平台

一个可本地运行的 FastAPI + Playwright 自动化编排平台，用 HTML 页面配置浏览器任务、手动执行、定时执行、查看步骤日志、截图和失败原因。

## 功能列表
- Dashboard：任务总数、今日执行、成功失败统计、最近执行记录
- 任务管理：新建、编辑、删除、手动执行
- 编排编辑器：表单模式、YAML 模式、校验、格式化、双向转换
- 执行器：goto、click、fill、wait、sleep、screenshot、assert_text、assert_visible、select、upload、download、manual_confirm
- 定时计划：cron、interval、date
- 日志：Run 详情、步骤耗时、输入快照脱敏、截图链接、错误信息
- Mock 站点：登录、表单提交、下载报表
- 登录态：脚本保存 Playwright storage_state

## 目录结构
```text
browser_automation_platform/
  app/
    main.py
    database.py
    models.py
    schemas.py
    scheduler.py
    routers/
    services/
    runner/
    static/
    templates/
  flows/examples/
  data/
  logs/
  playwright/.auth/
  scripts/
  tests/
```

## 安装步骤
macOS/Linux:
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
playwright install chromium
```

Windows:
```bat
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
playwright install chromium
```

## 启动项目
```bash
uvicorn app.main:app --reload
```

访问地址：
- Dashboard: http://127.0.0.1:8000
- 任务列表: http://127.0.0.1:8000/flows
- 定时计划: http://127.0.0.1:8000/schedules
- 教程: http://127.0.0.1:8000/tutorial
- Mock 站点: http://127.0.0.1:8000/mock-site

## 创建第一个任务
进入 `/flows/new`，使用默认 Mock YAML，点击 YAML 校验，再点击保存。保存后点击手动执行，在 Run 详情页查看步骤日志和截图。

## 运行 Mock 示例
示例文件位于 `flows/examples/`。可以把 `mock_login_and_submit.yaml` 内容粘贴到 YAML 编辑器保存，也可以通过 API 创建任务。

## Google Maps 示例
`flows/examples/google_search_maps_kunming_navigation.yaml` 按完整链路编排：打开 Google、搜索 google map、进入 Google Maps、搜索昆明、点击路线。Google 搜索可能触发风控，流程中加入了 `manual_confirm`，方便人工完成验证或确认结果页后继续。

`flows/examples/google_maps_kunming_navigation_direct.yaml` 直接打开 Google Maps 搜索昆明并点击路线，已用平台 runner 实测通过，截图保存到 `logs/google-maps-kunming-direct.png`。

## 配置定时任务
进入 `/schedules`，选择任务和调度类型：
- interval：填写 `interval_seconds`
- cron：填写 5 段表达式，例如 `*/5 * * * *`
- date：选择一次性执行时间

## 保存登录态
```bash
python scripts/save_auth_state.py http://your-internal-login.example.com work.json
```
登录完成后回车，文件保存到 `playwright/.auth/work.json`。在 YAML 中配置：
```yaml
browser:
  storage_state: "work.json"
```

## 运行测试
```bash
pytest
pytest -m e2e
```

## 常见问题
- selector 超时：检查页面元素是否变化、登录态是否失效、timeout 是否偏短。
- 下载失败：检查 download 的 selector 是否能触发浏览器下载。
- 定时计划没有触发：检查任务是否启用、schedule 是否启用、cron 表达式是否为 5 段。

## 安全注意事项
- 密码、token、cookie 放入环境变量或登录态文件。
- `playwright/.auth/*.json`、`logs/`、`data/*.db` 和 `.env` 已加入 `.gitignore`。
- 删除、提交、审批、批量修改前加入 `manual_confirm`。
- 文件路径限制在项目目录内。
- 默认同一任务单进程互斥执行。
