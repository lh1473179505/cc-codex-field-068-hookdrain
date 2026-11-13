# 事件与水位

`python -m hookdrain site` 起一个本地接收端。`replay` 应按 `fixtures/events.jsonl` 的 **文件顺序**（这是到达顺序）把每条事件 POST 到 `/hook`（Content-Type: application/json），同时由你的服务进程处理这些 POST，并把当前镜像写到 `--out`。

也可以把接收逻辑做成库函数，让 `replay` 在同一进程里调用，不必真的开 HTTP；但 `/hook` 的处理规则必须与文档一致，且站点要能独立启动。

## 事件

每条事件：

- `event_id` 唯一。重复投递（相同 event_id）必须忽略，不能把状态打回去。
- `type`：`order.created`、`order.updated`、`order.cancelled`
- `order_id`
- `event_time`：事件在业务上发生的时间（ISO-8601 UTC）
- `payload`：created/updated 带 `status`、`total_cents`、`items`；cancelled 带 `reason`

## 乱序与迟到

状态版本以 `event_time` 为准，不以到达顺序为准。先到的 `order.updated` 不能盖掉后来才到达、但 `event_time` 更早的 `order.created` 里不该被覆盖的字段；具体规则：

- 每个订单保留已应用事件里最大的 `event_time` 为 `applied_upto`。
- 若新事件的 `event_time` 晚于 `applied_upto`，则应用它（created 建单，updated 覆盖 payload 字段，cancelled 将 `status` 设为 `cancelled` 并保留最后一份 payload 快照）。
- 若新事件的 `event_time` 早于或等于 `applied_upto`，不要回滚已经应用的更新；把它追加到 `--out/late_arrivals.jsonl`（字段 `event_id,order_id,event_time,reason=stale`）。但有一个例外：`order.cancelled` **无论早晚** 都要把该订单标为 cancelled（补偿事件优先），并在 late_arrivals 里写 `reason=cancel_applied`（若它其实晚于 applied_upto 则不必进 late_arrivals，直接作为正常应用）。

## 水位

`--out/watermark.json` 记录：

- `arrival_count`：已接收条数（含重复）
- `unique_applied`：实际改变状态的事件数
- `event_time_watermark`：已应用事件的最大 event_time
- `arrival_index`：已经处理到 events.jsonl 的第几行（从 1 开始），用于续跑

checkpoint 应能在中断后从下一行继续，且重复 POST 同一 event_id 不二次计数 unique_applied。

夹具里 ORD-9 会先收到 updated，后收到 created（created 的 event_time 更早），created 应进 late_arrivals，最终状态以 updated 为准。ORD-4 会在已经有更新之后收到一个更早的 cancelled，仍应变成 cancelled。ORD-2 的同一 event_id 会出现两次，只能生效一次。
