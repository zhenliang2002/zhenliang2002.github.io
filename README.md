# zhenliang2002.github.io

个人博客。纯静态，无运行时依赖，由 `build.py` 从 `content/` 生成。

## 结构

```
content/
  site.json          站点信息：名字、邮箱、标题、导语、导航
  pages/about.md     关于页
  posts/*.md         文章，文件名 YYYY-MM-DD-slug.md
assets/style.css     唯一一份样式表
build.py             生成器（Python 3.8+，只用标准库）
index.html           生成物：首页
about.html           生成物：关于页
posts/*.html         生成物：文章页
feed.xml sitemap.xml 生成物
```

## 写一篇文章

在 `content/posts/` 新建 `2026-12-01-my-post.md`：

```markdown
---
title: 标题
date: 2026-12-01
tags: 标签一, 标签二
summary: 一句话摘要，会出现在首页列表和 RSS 里。
---

正文，支持标题、列表、引用、代码块、链接和图片。
```

然后重新生成：

```bash
python build.py
```

## 发布

`main` 分支根目录即站点（GitHub Pages 直接托管），`.nojekyll` 关闭 Jekyll 处理。提交并推送后一分钟内生效。

## 设计

单色：纯黑底、白色四档透明度、1px 发丝线，不用任何彩色。字体走系统栈（MiSans / 苹方 / 思源黑体 / Segoe UI）。标题与正文的排版参数集中在 `assets/style.css` 顶部的变量里。
