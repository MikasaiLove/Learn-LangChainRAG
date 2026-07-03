"""自定义 Locust SSE 客户端 — 记录首字延迟和流时长"""

import time
import httpx
from locust import events


def stream_send_message(
    client: httpx.Client,
    url: str,
    headers: dict,
    json_payload: dict,
    request_meta: dict,
) -> dict:
    """
    发送 SSE 流式请求，消费所有事件，记录指标。
    返回 {"status": "ok"|"error", "ttft_ms": float, "total_ms": float, "chunks": int, "error": str}
    """
    start_time = time.time()
    first_token_time = None
    chunk_count = 0
    full_response = ""
    error_msg = None
    status = "ok"

    try:
        with httpx.stream(
            "POST", url, headers=headers, json=json_payload, timeout=120
        ) as resp:
            request_meta["response"] = resp
            request_meta["response_length"] = 0

            if resp.status_code != 200:
                status = "error"
                error_msg = f"HTTP {resp.status_code}: {resp.text[:200]}"
                request_meta["exception"] = Exception(error_msg)
                return {
                    "status": "error",
                    "ttft_ms": 0,
                    "total_ms": (time.time() - start_time) * 1000,
                    "chunks": 0,
                    "error": error_msg,
                }

            for line in resp.iter_lines():
                if line.startswith("data: "):
                    chunk_count += 1
                    if first_token_time is None:
                        first_token_time = time.time()
                    data_str = line[6:]

                    if data_str == "[DONE]":
                        break

                    try:
                        event = __import__("json").loads(data_str)
                        if event.get("type") == "token":
                            full_response += event.get("content", "")
                    except Exception:
                        pass

    except Exception as e:
        status = "error"
        error_msg = str(e)
        request_meta["exception"] = e

    end_time = time.time()
    total_ms = (end_time - start_time) * 1000
    ttft_ms = (first_token_time - start_time) * 1000 if first_token_time else total_ms

    # 上报自定义指标到 Locust
    request_meta["response_time"] = total_ms
    request_meta["response_length"] = len(full_response)

    # 发射自定义事件用于 TTFT 统计
    events.request.fire(
        request_type="SSE",
        name="ttft_send_message",
        response_time=ttft_ms,
        response_length=len(full_response),
        exception=None if status == "ok" else request_meta.get("exception"),
    )

    return {
        "status": status,
        "ttft_ms": ttft_ms,
        "total_ms": total_ms,
        "chunks": chunk_count,
        "error": error_msg,
    }
