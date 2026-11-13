# hookdrain

接收合作方推送的订单事件。事件会乱序、重复、迟到，也有补偿撤销。要把当前订单状态幂等物化出来。

```
python -m hookdrain site --port 8768
python -m hookdrain replay --base http://127.0.0.1:8768 --events fixtures/events.jsonl --out <out> --checkpoint <ckpt>
python -m hookdrain verify --out <out> --expect fixtures/expected/orders.json
```
