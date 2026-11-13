from __future__ import annotations


class HookDrain:
    """Idempotent, event_time-ordered order state materializer."""

    def __init__(self):
        self.orders = {}
        self.seen_ids = set()
        self.late = []
        self.arrival_count = 0
        self.unique_applied = 0
        self.event_time_watermark = None
        self.arrival_index = 0

    def apply(self, event, arrival_index=None):
        self.arrival_count += 1
        if arrival_index is not None:
            self.arrival_index = arrival_index
        event_id = event["event_id"]
        if event_id in self.seen_ids:
            return "duplicate"
        self.seen_ids.add(event_id)

        etype = event["type"]
        order_id = event["order_id"]
        event_time = event["event_time"]
        payload = event.get("payload") or {}
        order = self.orders.get(order_id)
        applied_upto = order["applied_upto"] if order else None
        is_late = applied_upto is not None and event_time <= applied_upto

        if etype == "order.cancelled":
            if order is None:
                order = {
                    "order_id": order_id,
                    "status": "cancelled",
                    "total_cents": None,
                    "items": [],
                    "applied_upto": event_time,
                }
                self.orders[order_id] = order
            else:
                order["status"] = "cancelled"
            self.unique_applied += 1
            if is_late:
                self._late(event_id, order_id, event_time, "cancel_applied")
                return "cancel_applied"
            order["applied_upto"] = event_time
            self._mark_applied(event_time)
            return "applied"

        if is_late:
            self._late(event_id, order_id, event_time, "stale")
            return "stale"

        if order is None:
            order = {
                "order_id": order_id,
                "status": None,
                "total_cents": None,
                "items": [],
                "applied_upto": None,
            }
            self.orders[order_id] = order
        if "status" in payload:
            order["status"] = payload["status"]
        if "total_cents" in payload:
            order["total_cents"] = payload["total_cents"]
        if "items" in payload:
            order["items"] = payload["items"]
        order["applied_upto"] = event_time
        self.unique_applied += 1
        self._mark_applied(event_time)
        return "applied"

    def _late(self, event_id, order_id, event_time, reason):
        self.late.append(
            {
                "event_id": event_id,
                "order_id": order_id,
                "event_time": event_time,
                "reason": reason,
            }
        )

    def _mark_applied(self, event_time):
        if self.event_time_watermark is None or event_time > self.event_time_watermark:
            self.event_time_watermark = event_time

    def watermark(self):
        return {
            "arrival_count": self.arrival_count,
            "unique_applied": self.unique_applied,
            "event_time_watermark": self.event_time_watermark,
            "arrival_index": self.arrival_index,
        }

    def sorted_orders(self):
        return [self.orders[k] for k in sorted(self.orders)]

    def to_state(self):
        return {
            "orders": self.orders,
            "seen_ids": sorted(self.seen_ids),
            "late": self.late,
            "arrival_count": self.arrival_count,
            "unique_applied": self.unique_applied,
            "event_time_watermark": self.event_time_watermark,
            "arrival_index": self.arrival_index,
        }

    @classmethod
    def from_state(cls, state):
        core = cls()
        core.orders = dict(state.get("orders") or {})
        core.seen_ids = set(state.get("seen_ids") or [])
        core.late = list(state.get("late") or [])
        core.arrival_count = state.get("arrival_count", 0)
        core.unique_applied = state.get("unique_applied", 0)
        core.event_time_watermark = state.get("event_time_watermark")
        core.arrival_index = state.get("arrival_index", 0)
        return core
