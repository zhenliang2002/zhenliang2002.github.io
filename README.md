# zhenliang2002.github.io

静态博客。无运行时依赖，`build.py` 从 `content/` 生成 HTML。

## 结构

```
content/
  site.json       标题、域名、导航
  posts/*.md      文章，文件名 YYYY-MM-DD-slug.md
assets/style.css  唯一一份样式表
build.py          生成器（Python 3.8+，仅标准库）
index.html        生成物：首页
posts/*.html      生成物：文章页
feed.xml          生成物
sitemap.xml       生成物
```

## 写文章

`content/posts/2026-12-01-slug.md`：

```markdown
---
title: 标题
date: 2026-12-01
tags: 标签一, 标签二
summary: 一句话摘要，出现在首页列表和 RSS。
---

正文，支持标题、列表、引用、代码块、链接、图片。
```

然后：

```bash
python build.py
```

`main` 分支根目录即站点，`.nojekyll` 关闭 Jekyll，推送后自动发布。

## 设计

单色：纯黑底、白色四档透明度、1px 发丝线。字体走系统栈（MiSans / 苹方 / 思源黑体 / Segoe UI）。排版参数集中在 `assets/style.css` 顶部。

提交身份固定为 `zhenliang2002`（`.git/config` 已配置免回复邮箱），换机器克隆后需重新设置。
