# uuvate

本仓库用于本地预览和修复 uvation 静态站点，包含多个域名的导出内容与工具脚本。

## 目录结构

- `sites/`：标准化的域名内容目录（建议以此为唯一权威来源）
  - `uvation.com/`
    - `public/`：原始静态导出
    - `public_sanitized/`：用于本地预览的安全化副本
    - `reports/`：页面校验与资源扫描报告
  - `cdn.uvation.com/`
    - `public/`：CDN 静态资源镜像
  - `cms.uvation.com/`
    - `public/`：CMS 静态资源镜像
- `tools/`：脚本与本地预览服务器
  - `dev_static_server.py`：本地静态服务器（注入预览垫片与轻量代理）
  - 其他工具：资源同步、校验、清理与比对脚本
- `external/`：第三方静态资源镜像（如合作伙伴站点依赖）
- `STRUCTURE.md`：更详细的结构说明
- `.gitignore`：忽略本地日志与缓存

说明：在工作区中可能还存在顶层目录 `cdn.uvation.com/`、`cms.uvation.com/`、`uvation.com/`，它们是早期或临时副本。为避免重复与混淆，建议统一迁移或仅保留 `sites/` 下的结构作为单一来源。如果确需保留顶层目录，请在后续变更中明确其用途，并与 `sites/` 区分。

## 本地预览

- 启动带垫片的静态服务：
  ```bash
  python3 tools/dev_static_server.py
  ```
  访问示例：`http://localhost:5504/product-and-services/amazon-aws/`

- 简易静态服务（无垫片）：
  ```bash
  cd sites/uvation.com/public
  python3 -m http.server 5504 --bind 127.0.0.1
  ```

## 注意事项

- 预览垫片只作用于本地，避免 GTM/GA/Clarity/LinkedIn 等第三方脚本导致的客户端异常；不会影响线上文件。
- `logs/`、本地缓存与临时文件不纳入版本控制。
- 如需将顶层临时目录纳入版本控制或清理，请在变更说明中注明目标与影响范围。