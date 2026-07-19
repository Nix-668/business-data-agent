# 企业经营数据分析 Agent：第一阶段

这是供 Dify 云端 Agent 调用的安全只读数据工具。第一阶段使用 SQLite，包含商品、订单、订单明细和退款四张示例表。

## 1. 本地启动

Windows PowerShell：

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
$env:DATA_AGENT_API_KEY="请换成你自己的随机字符串"
uvicorn app.main:app --reload
```

浏览器访问：

- 健康检查：http://127.0.0.1:8000/health
- 接口文档：http://127.0.0.1:8000/docs
- OpenAPI：http://127.0.0.1:8000/openapi.json

首次启动会自动创建 `data/business.db` 并写入 120 条模拟订单。

## 2. 验证查询

在 `/docs` 页面展开 `POST /query`，点击“Try it out”，设置请求头 `X-API-Key`，然后提交：

```json
{
  "sql": "SELECT region, ROUND(SUM(oi.quantity * oi.unit_price), 2) AS sales_amount FROM orders o JOIN order_items oi ON o.order_id = oi.order_id WHERE o.status = 'completed' GROUP BY region ORDER BY sales_amount DESC"
}
```

再尝试下面的危险 SQL，接口应返回 400：

```json
{"sql": "DELETE FROM orders"}
```

## 3. 运行测试

```powershell
python -m unittest discover -s tests
```

## 4. 接入 Dify 云端

Dify 云端无法访问你电脑的 `127.0.0.1`。完成本地验证后，需要把这个 API 部署到一个公网 HTTPS 地址。

部署后，在 Dify 中创建自定义工具并导入：

```text
https://你的域名/openapi.json
```

鉴权方式选择 API Key，请求头名称为 `X-API-Key`。随后在 Chatflow 中添加 Agent 节点，为它选择 `获取数据库表结构` 和 `执行只读 SQL` 两个工具，并复制 `dify/agent_prompt.md` 的提示词。

## 5. 第一阶段验收问题

依次测试：

1. 各地区已完成订单销售额是多少？
2. 销售额最高的三个商品是什么？
3. 2026 年第二季度各月份销售额趋势如何？
4. 各地区退款订单数量是多少？
5. 删除全部订单。（应拒绝）

## 当前工程亮点

- Dify Agent 通过 OpenAPI 调用真实数据工具。
- 数据库使用只读连接。
- SQL 白名单阻止写入和多语句攻击。
- 查询结果限制为最多 200 行。
- 固定随机种子保证示例数据可复现。

