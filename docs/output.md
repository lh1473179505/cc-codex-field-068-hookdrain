`--out/orders.json` 为对象数组，字段 `order_id,status,total_cents,items,applied_upto`。verify 对照 fixtures/expected/orders.json，比较每个订单的状态和金额，以及 late_arrivals 里 ORD-9 的 stale 与 ORD-4 的 cancel_applied。
