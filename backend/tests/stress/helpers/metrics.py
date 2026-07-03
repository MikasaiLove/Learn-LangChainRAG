"""Locust 自定义指标收集器"""

from locust import events


@events.init.add_listener
def on_locust_init(environment, **kwargs):
    """Locust startup message"""
    print(f"\n[Locust] LangChainRAG Stress Test Ready")
    print(f"   Target: {environment.host}")
    print(f"   Web UI: http://localhost:8089\n")


@events.test_start.add_listener
def on_test_start(environment, **kwargs):
    """Test start message"""
    print(f"\n>>> Test started - {environment.runner.target_user_count} users\n")


@events.test_stop.add_listener
def on_test_stop(environment, **kwargs):
    """Test end summary"""
    stats = environment.stats
    print("\n" + "=" * 50)
    print("  Stress Test Complete")
    print(f"  Total Requests: {stats.total.num_requests}")
    print(f"  Failures:       {stats.total.num_failures}")
    print(f"  Avg RPS:        {stats.total.total_rps:.1f}")
    print(f"  Avg Latency:    {stats.total.avg_response_time:.0f}ms")
    print(f"  P95 Latency:    {stats.total.get_response_time_percentile(0.95):.0f}ms")
    print(f"  P99 Latency:    {stats.total.get_response_time_percentile(0.99):.0f}ms")
    print("=" * 50 + "\n")


@events.request.add_listener
def on_request(request_type, name, response_time, response_length, exception, **kwargs):
    """Alert on slow requests"""
    if exception and response_time > 30000:
        print(f"[SLOW] {name} - {response_time:.0f}ms - {exception}")
