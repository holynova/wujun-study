# 吴军 · 专题学习

将吴军 14 门得到课程整理成 42 个专题，以精读文章、逐篇出处和 15 页中文漫画图解辅助学习。专题采用选择性编排，不表示已逐篇覆盖全部课程。

界面沿用伯恩斯坦青少年音乐会项目的双栏布局：左侧目录、分类与搜索，右侧精读正文与全屏幻灯片。米白纸色、宋体标题、深红强调色和移动端布局均延续参考项目。

截至 2026-11-17，已完成 42 篇专题文章及 17 份已校对图解（共 255 页），其中理财 6 个专题全部完成。其余 25 份图解因 NotebookLM 服务限流暂未完成，来源与逐页提纲已准备。

## 使用

```sh
npm install
npm run build
npm test
npm run dev
```

正式网站挂载在 xiaosang.cc/wujun-study/，由作品集 xiaosang-portfolio Worker 统一部署；原 Sites 私有预览保留。部署只包含 `dist/`；源码仓库中的 `src/data/topics/` 保存脱敏后的精读内容，支持干净检出重建。

## 内容与来源

原始课程仓库：[holynova/my-data](https://github.com/holynova/my-data)。来源固定到具体提交，每个专题附可追溯的课程标题和 GitHub 链接。原始课程全文及 NotebookLM 来源材料保留在本地 `work/`，不进入源码仓库或网站。网站正文是专题归纳，不声称是吴军逐字原文。历史案例保留原有时间与适用条件。

## 图解生产

- 一份结构化来源对应一份图解，显式绑定 `source_id`。
- 全部简体中文，《丁丁历险记》清线漫画风格，恰好 15 页，含封面与来源页。
- `scripts/ppt_pipeline.py` 保存独立生产状态，关闭写操作自动重试。提交前先落盘，结果不明先对账；明确失败最多每天 3 次。
- 相邻普通调用间隔至少 15 秒，提交间隔至少 60 秒。提交 20 分钟后才开始查询，其后查询间隔至少 5 分钟。读取其他生产项目的容量与冷却状态，不修改它们。
- 原始 PDF 保存在 `work/slides/`，下载后检查页数，再进行视觉及事实复核。`review_pending` 和 `page_count_mismatch` 不会自动发布。
- 审核通过后才将 PDF 复制到 `public/slides/ep-N.pdf`，运行 `scripts/build_slides.py` 提取原始图像流并编码高清 WebP。网页仅对已完成的 15 页图解提供入口。
- `state/`、`work/`、账号信息、内部错误和凭证均不发布。生产进程与构建部署顺序执行。

运行生产脚本需要安装 NotebookLM CLI 以及 Python 的 `pypdf`，通过 `NLM_PYTHON` 指定 CLI 解释器；提取图片另需 Pillow 与 cwebp。不要切换全局账号。

```sh
python scripts/ppt_pipeline.py --minutes 90
```

本地 `complete` 与线上核验状态分别记录，未完成的图解始终如实显示“图解待完成”。
