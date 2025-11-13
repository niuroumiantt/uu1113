## 部署到 Ubuntu 服务器

本文记录了将仓库 `niuroumiantt/uu1113` 部署到一台全新 Ubuntu 服务器（示例 IP：`13.218.114.94`）的步骤。环境假设：已通过 SSH 登录服务器（例如 `ubuntu@ip-172-26-11-197`），拥有 sudo 权限，且使用 Nginx 作为静态站点服务器。

### 1. 更新系统并安装依赖

```bash
sudo apt update
sudo apt install -y git nginx
```

### 2. 克隆网站仓库

```bash
cd /var/www
sudo git clone https://github.com/niuroumiantt/uu1113.git
```

克隆完成后，项目会位于 `/var/www/uu1113`。

### 3. 部署静态文件

将仓库中的静态内容复制到 Nginx 默认的站点目录 `/var/www/html`（复制前先清空该目录）：

```bash
sudo rm -rf /var/www/html/*
sudo cp -R /var/www/uu1113/sites/uvation.com/public/* /var/www/html/
```

### 4. 调整文件权限

确保 Nginx 用户（`www-data`）拥有站点文件的读权限：

```bash
sudo chown -R www-data:www-data /var/www/html
```

### 5. 配置防火墙（如启用 UFW）

如果系统启用了 UFW，开放 HTTP/HTTPS：

```bash
sudo ufw allow 'Nginx Full'
```

### 6. 重启 Nginx

```bash
sudo systemctl restart nginx
```

此时即可在浏览器访问 `http://13.218.114.94/` 验证站点是否正常。

### 附加说明

- 若需要 HTTPS，可使用 Certbot 等工具申请并配置 TLS 证书。
- 若后续需更新站点，可在 `/var/www/uu1113` 目录中执行 `git pull`，再重复第 3 步和第 4 步，或者编写同步脚本自动化处理。
- 如需使用自定义 Nginx 站点配置，请在 `/etc/nginx/sites-available/` 下创建新配置，并通过 `ln -s` 链接到 `sites-enabled`，别忘了 `nginx -t` 验证语法后再重启服务。

