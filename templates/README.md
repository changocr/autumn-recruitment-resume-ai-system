# Python 简历模板

`resume_template.py` 以同一份 JSON 数据生成两种一页 A4 中文简历：

- `internet`：姓名与目标在左、联系方式在右，适合产品、运营和商业分析；
- `finance`：紧凑横向页眉，可选本地照片，适合研究与投研。

示例：

```powershell
python templates/resume_template.py --input templates/sample_resume.json --output output/resume.pdf --theme internet
```

示例数据仅供演示。真实内容请写入本地 `resume_master.json`。模板缺少空间时应改写内容；渲染器会对超出一页的内容报错。
