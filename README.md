# 吴军 · 专题学习 / Wu Jun Study

将吴军 14 门课程按主题编排为 42 篇精读文章，附可追溯出处、课程筛选与全文搜索。沿用伯恩斯坦项目的双栏阅读布局，适配手机。

已完成 17 份中文清线漫画图解，每份 15 页，共 255 页，支持全屏阅读和 PDF 下载；理财 6 个专题全部完成。其余 25 份受 NotebookLM 限流影响暂未完成，来源与提纲已备好。专题采用选择性编排，不代表覆盖全部原课。

A thematic study guide to 14 Wu Jun courses, organized into 42 original study articles with traceable references, course filters and full-text search. Its responsive two-column layout follows the Bernstein project.

Includes 17 reviewed Chinese clear-line comic slide decks, exactly 15 pages each (255 pages), with a fullscreen reader and PDF downloads. All six personal-finance topics are complete. The remaining 25 decks await generation after NotebookLM rate limits; source packets and outlines are ready. This is a selective thematic guide, not a complete course transcription.

![网站截图 / Website screenshot](./assets/screenshot.png)

## 在线体验 / Live Demo

- [Cloudflare Demo](https://xiaosang.cc/wujun-study/)
- [GitHub Repo](https://github.com/holynova/wujun-study)
- [原课来源 / Course sources](https://github.com/holynova/my-data)

<img src="./assets/qr.png" width="180" alt="扫码访问 / Scan to visit">

## 本地运行 / Run locally

```sh
npm ci
npm run dev
npm test
npm run build
```

## 发布 / Deploy

```sh
npm run deploy:check
npm run deploy
```

Cloudflare Workers (`xiaosang-portfolio`) · `xiaosang.cc/wujun-study/` · `main`

源码使用 main，随作品集 master 手动部署到共享 Worker；部署前需同步作品集的挂载提交。原始课程、账号与生产状态不进入公开产物。网站使用统一 Umami 统计。

Source and deployment configuration share the main branch. Deploy manually with Wrangler. Raw courses, credentials and production state remain local. Includes Umami analytics.

[生产流程 / Production notes](./docs/production.md)
