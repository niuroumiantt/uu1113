# 项目目录结构说明（重组后）

本项目按照复杂网站建设的逻辑进行分层与分域管理：

## 顶层目录
- `sites/`：站点分域内容（生产静态资源与页面）。
- `tools/`：工具与脚本（抓取、同步、校验等）。
- `external/`：第三方站点镜像与参考素材。
- `logs/`：日志与操作记录。

## sites/
- `sites/uvation.com/public/`：`uvation.com` 的站点根目录（用于本地预览服务器）。
- `sites/uvation.com/reports/`：与 `uvation.com` 相关的下载报告与比对文件。
- `sites/cdn.uvation.com/public/`：`cdn.uvation.com` 的静态资源镜像。
- `sites/cms.uvation.com/public/`：`cms.uvation.com` 的 WordPress 上传资源镜像。

## tools/
- 常用脚本，例如 `sync_next_assets.py`、`fetch_missing_pages.py` 等。

## external/
- 第三方参考素材与镜像（例如 `www.verizon.com/`、`www.delltechnologies.com/`、`www.s81c.com/`）。

## 使用建议
- 本地预览服务器从 `sites/uvation.com/public/` 目录启动。
- 若新增页面或资源缺失，使用 `tools/` 下的脚本进行同步与校验。