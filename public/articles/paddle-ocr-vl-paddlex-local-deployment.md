# Paddle OCR VL+PaddleX本地部署参考方案

## 环境准备

- **Docker CE**：最新release版本
- **GPUStack V0.7.1**（最后一个非容器管理的稳定版本）

安装步骤：创建python虚拟环境+`pip install gpustack==0.7.1`

- **vLLM 0.13.0**（用release版本即可，需要在GPUStack中指定）

![GPUStack模型配置](/images/img_11_N2QwYjcxNmY5MjZ.png)

- **PaddleOCR VL**：ModelScope/PaddlePaddle/PaddleOCR-VL
- **paddleocr-vl-api**：`ccr-2vdh3abv-pub.cnc.bj.baidubce.com/paddlepaddle/paddleocr-vl:latest-offline`
- **Node 22**：用来做proxy绕开gpustack的apikey鉴权，参考[--force-auth-localhost](https://docs.gpustack.ai/latest/cli-reference/start/?h=force+auth#server-options)，也可用其他等效方法实现

## 配置文件

### docker-compose.yml：device_ids配置成空闲的gpu

```yaml
services:
  paddleocr-vl-api:
    image: ccr-2vdh3abv-pub.cnc.bj.baidubce.com/paddlepaddle/paddleocr-vl:latest-offline
    container_name: paddleocr-vl-api
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              device_ids: ["7"]
              capabilities: [gpu]
    # TODO: Allow using a regular user
    user: root
    restart: unless-stopped
    environment:
      - VLM_BACKEND=${VLM_BACKEND:-vllm}
    command: /bin/bash -c "paddlex --serve --pipeline /home/paddleocr/pipeline_config_vllm.yaml"
    healthcheck:
      test: ["CMD-SHELL", "curl -f http://localhost:8080/health || exit 1"]
      # 如果需要更长的启动时间，可保留或调整
      # start_period: 300s
    volumes:
      - ./pipeline_config_vllm.yaml:/home/paddleocr/pipeline_config_vllm.yaml
    network_mode: "host"
```

### pipeline_config_vllm.yaml：server_url配置成实际代理的gpustack服务地址

```yaml
pipeline_name: PaddleOCR-VL

batch_size: 64

use_queues: True

use_doc_preprocessor: False
use_layout_detection: True
use_chart_recognition: False
format_block_content: False

SubModules:
  LayoutDetection:
    module_name: layout_detection
    model_name: PP-DocLayoutV2
    model_dir: null
    batch_size: 8
    threshold:
      0: 0.5 # abstract
      1: 0.5 # algorithm
      2: 0.5 # aside_text
      3: 0.5 # chart
      4: 0.5 # content
      5: 0.4 # formula
      6: 0.4 # doc_title
      7: 0.5 # figure_title
      8: 0.5 # footer
      9: 0.5 # footer
      10: 0.5 # footnote
      11: 0.5 # formula_number
      12: 0.5 # header
      13: 0.5 # header
      14: 0.5 # image
      15: 0.4 # formula
      16: 0.5 # number
      17: 0.4 # paragraph_title
      18: 0.5 # reference
      19: 0.5 # reference_content
      20: 0.45 # seal
      21: 0.5 # table
      22: 0.4 # text
      23: 0.4 # text
      24: 0.5 # vision_footnote
    layout_nms: True
    layout_unclip_ratio: [1.0, 1.0]
    layout_merge_bboxes_mode:
      0: "union" # abstract
      1: "union" # algorithm
      2: "union" # aside_text
      3: "large" # chart
      4: "union" # content
      5: "large" # display_formula
      6: "large" # doc_title
      7: "union" # figure_title
      8: "union" # footer
      9: "union" # footer
      10: "union" # footnote
      11: "union" # formula_number
      12: "union" # header
      13: "union" # header
      14: "union" # image
      15: "large" # inline_formula
      16: "union" # number
      17: "large" # paragraph_title
      18: "union" # reference
      19: "union" # reference_content
      20: "union" # seal
      21: "union" # table
      22: "union" # text
      23: "union" # text
      24: "union" # vision_footnote
  VLRecognition:
    module_name: vl_recognition
    model_name: PaddleOCR-VL-0.9B
    model_dir: null
    batch_size: 4096
    genai_config:
      backend: vllm-server
      server_url: http://host.docker.internal:8002/v1

SubPipelines:
  DocPreprocessor:
    pipeline_name: doc_preprocessor
    batch_size: 8
    use_doc_orientation_classify: True
    use_doc_unwarping: True
    SubModules:
      DocOrientationClassify:
        module_name: doc_text_orientation
        model_name: PP-LCNet_x1_0_doc_ori
        model_dir: null
        batch_size: 8
      DocUnwarping:
        module_name: image_unwarping
        model_name: UVDoc
        model_dir: null
```

## 开始部署

### vLLM启动参数（完美复刻官方paddleocr-vlm-server）

```bash
--trust-remote-code
--max-model-len=16384
--no-enable-prefix-caching
--mm-processor-cache-gb=0
--gpu-memory-utilization=0.4  # 视具体显存和实例数量来设置，4090可设置为0.4-0.45开启两个实例
--chat-template=/var/lib/gpustack/cache/model_scope/PaddlePaddle/PaddleOCR-VL/chat_template.jinja  # 必须配置官方的chat_template
--served-model-name=PaddleOCR-VL-0.9B  # 设置PaddleOCR-VL-0.9B，否则paddleocr-vl-api不认
```

> **注意：** GPUStack也要将模型名称设置为PaddleOCR-VL-0.9B

![GPUStack模型设置](/images/img_3_MGI4NTQwNzcwOTY.png)

### 示例代码

```python
import base64
import requests
import pathlib

API_URL = "http://localhost:8080/layout-parsing"  # 服务URL

image_path = "./demo.jpg"

# 对本地图像进行Base64编码
with open(image_path, "rb") as file:
    image_bytes = file.read()
    image_data = base64.b64encode(image_bytes).decode("ascii")

payload = {
    "file": image_data,  # Base64编码的文件内容或者文件URL
    "fileType": 1,  # 文件类型，1表示图像文件
}

# 调用API
response = requests.post(API_URL, json=payload)

# 处理接口返回数据
assert response.status_code == 200
result = response.json()["result"]
for i, res in enumerate(result["layoutParsingResults"]):
    print(res["prunedResult"])
    md_dir = pathlib.Path(f"markdown_{i}")
    md_dir.mkdir(exist_ok=True)
    (md_dir / "doc.md").write_text(res["markdown"]["text"])
    for img_path, img in res["markdown"]["images"].items():
        img_path = md_dir / img_path
        img_path.parent.mkdir(parents=True, exist_ok=True)
        img_path.write_bytes(base64.b64decode(img))
    print(f"Markdown document saved at {md_dir / 'doc.md'}")
    for img_name, img in res["outputImages"].items():
        img_path = f"{img_name}_{i}.jpg"
        pathlib.Path(img_path).parent.mkdir(exist_ok=True)
        with open(img_path, "wb") as f:
            f.write(base64.b64decode(img))
        print(f"Output image saved at {img_path}")
```

### 解析效果（简单验证）

![解析效果1](/images/img_25_YjIyMTk2YTU4ZDR.jpg)

![解析效果2](/images/img_19_OGFjNGMyODA5MWE.png)

```markdown
### 3.3 角色功能矩阵

#### 3.3.1 A3-2 角色权限视图-功能权限矩阵

功能权限矩阵主要展示系统各类角色对系统所有功能模块的权限；应将系统的全部功能列出，依照功能目录列表进行顺序填写。

<table border=1 style='margin: auto; width: max-content;'><tr><td colspan="6">功能权限矩阵</td></tr><tr><td style='text-align: center;'>编号</td><td style='text-align: center;'>角色名</td><td style='text-align: center;'>角色定义</td><td style='text-align: center;'>功能1</td><td style='text-align: center;'>功能2</td><td style='text-align: center;'>……</td></tr><tr><td style='text-align: center;'>1</td><td style='text-align: center;'>角色1</td><td style='text-align: center;'>角色对应的具体人员</td><td style='text-align: center;'>具备权限标注"√"，不具备为空</td><td style='text-align: center;'>√</td><td style='text-align: center;'></td></tr><tr><td style='text-align: center;'>2</td><td style='text-align: center;'>角色2</td><td style='text-align: center;'></td><td style='text-align: center;'></td><td style='text-align: center;'></td><td style='text-align: center;'></td></tr><tr><td style='text-align: center;'>3</td><td style='text-align: center;'>……</td><td style='text-align: center;'></td><td style='text-align: center;'></td><td style='text-align: center;'></td><td style='text-align: center;'></td></tr></table>

<div style="text-align: center;">表 3-3 功能权限矩阵（模板）</div>

#### 3.3.2 A3-2 角色权限视图-操作与数据权限矩阵

操作及数据权限矩阵主要展示各类角色在系统各功能模块中具备的操作权限（针对功能按钮，非列表操作项）及数据权限规则，应将系统所有功能按钮列出，功能按钮顺序应按照统一规则。

<table border=1 style='margin: auto; width: max-content;'><tr><td colspan="6">操作与数据权限矩阵</td></tr><tr><td style='text-align: center;'>功能</td><td style='text-align: center;'>角色</td><td style='text-align: center;'>功能按钮1</td><td style='text-align: center;'>功能按钮2</td><td style='text-align: center;'>...</td><td style='text-align: center;'>数据权限限制</td></tr><tr><td rowspan="3">功能1</td><td style='text-align: center;'>角色1</td><td style='text-align: center;'>具备权限标注"✓"，不具备为空</td><td style='text-align: center;'>✓</td><td style='text-align: center;'></td><td style='text-align: center;'>数据权限规则文字描述，例如仅能查看本级及下级数据</td></tr><tr><td style='text-align: center;'>角色2</td><td style='text-align: center;'></td><td style='text-align: center;'>✓</td><td style='text-align: center;'></td><td style='text-align: center;'></td></tr><tr><td style='text-align: center;'>……</td><td style='text-align: center;'></td><td style='text-align: center;'></td><td style='text-align: center;'></td><td style='text-align: center;'></td></tr><tr><td rowspan="2">功能2</td><td style='text-align: center;'>角色1</td><td style='text-align: center;'>✓</td><td style='text-align: center;'></td><td style='text-align: center;'></td><td style='text-align: center;'></td></tr><tr><td style='text-align: center;'>……</td><td style='text-align: center;'></td><td style='text-align: center;'></td><td style='text-align: center;'></td><td style='text-align: center;'></td></tr></table>

<div style="text-align: center;">表 3-4 操作与数据权限矩阵（模板）</div>
```

逻辑上来讲，本地部署的解析效果和官方的API结果是一致的。解析的结果为内嵌html的markdown，这点很赞。

**官方demo体验地址：**

1. https://huggingface.co/spaces/PaddlePaddle/PaddleOCR-VL_Online_Demo
2. https://aistudio.baidu.com/paddleocr

## 参考资料

1. https://docs.gpustack.ai/latest/cli-reference/start/?h=force+auth#server-options
2. https://github.com/PaddlePaddle/PaddleOCR/blob/main/deploy/paddleocr_vl_docker/
3. https://www.paddleocr.ai/latest/version3.x/pipeline_usage/PaddleOCR-VL.html
4. https://docs.vllm.ai/en/latest/

## 优势

1. 模型统一由GPUStack管理，部署和伸缩容方便，运维高效。
2. 充分利用官方paddlex的pipeline，中间复杂的文档处理过程不用管，直接享受SOTA级的文档解析效果。
3. 解析速度快。

## 后续设想

因为PaddleOCR VL的效果、速度、稳定性都很顶级，可以考虑对其兼容，上述为一些技术验证。最终希望实现兼容多种文档解析方案（本地部署和云端）+CPU MODE的文档解析。
