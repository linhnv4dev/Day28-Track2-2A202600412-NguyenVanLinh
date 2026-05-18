# Hướng Dẫn Nộp Bài - Lab #28: Full Platform Integration Sprint

## Yêu Cầu Nộp Bài

**Full AI infrastructure platform demo** - từ data ingestion đến model serving với full observability.

## Các Artifacts Cần Nộp

### 1. Source Code
- Folder `lab28/` hoàn chỉnh với tất cả files
- Tất cả integration scripts hoạt động
- Prefect flows đã deploy và schedule

### 2. Screenshots Demo
Chụp màn hình các bước:
- Prefect UI: http://localhost:4200 (flow đang chạy)
- API Gateway call: `curl http://localhost:8000/health`
- Grafana dashboard: http://localhost:3000

### 3. Kết Quả Smoke Tests
Chạy và chụp màn hình kết quả:
```bash
cd lab28
pytest smoke-tests/ -v
```
Kỳ vọng: 5/5 tests passing

### 4. Production Readiness Score
```bash
python scripts/production_readiness_check.py
```
Kỳ vọng: Score >80%

### 5. Documentation
- `README.md` giải thích cách:
  - Start platform: `docker compose up -d`
  - Deploy Prefect flows
  - Run smoke tests
  - Access dashboards (Grafana:3000, Prometheus:9090, Prefect:4200)

## Định Dạng Nộp Bài

Tạo Repo GitHub chứa:
```
lab28_submission_[student_id]
├── lab28/                    # Source code hoàn chỉnh
│   ├── docker-compose.yml
│   ├── prefect/flows/
│   ├── scripts/
│   ├── api-gateway/
│   └── monitoring/
├── screenshots/              # Screenshots demo
│   ├── prefect_ui.png
│   ├── api_gateway.png
│   └── grafana_dashboard.png
├── smoke_tests_results.png   # Screenshot kết quả pytest
├── production_readiness.png  # Screenshot readiness score
└── README.md                # Hướng dẫn setup
```

## Địa Điểm Nộp
Nộp link repo GitHub qua LMS

## Tiêu Chí Chấm Điểm

| Tiêu Chí | Trọng Số | Mô Tả |
|----------|----------|-------|
| Integration Completeness | 40% | Tất cả 10 integration points hoạt động, data flow end-to-end |
| Observability | 25% | Logs, metrics, traces hiển thị; alerts configured |
| Performance | 20% | Latency trong SLO; load tested; không có memory leaks |
| Architecture Quality | 15% | Clean separation, GitOps config, documented decisions |

## Các Vấn Đề Cần Tránh

- Config drift giữa các environments
- Thiếu error handling tại integration points
- Monitoring coverage không hoàn chỉnh
- Không có rollback strategy
- Demo không test trước khi nộp

## 5 Câu Hỏi Cần Trả Lời Khi Nộp

1. **Phân tích các trade-offs trong thiết kế kiến trúc AI platform của bạn. Bạn đã cân bằng giữa performance, reliability, và maintainability như thế nào?**

2. **Trong kiến trúc hybrid (Local + Kaggle), bạn xử lý ngắt kết nối giữa local và Kaggle như thế nào? Có cơ chế fallback không?**

3. **Giải thích cách event-driven architecture với Kafka giúp decouple các components trong AI platform của bạn.**

4. **Bạn đã implement observability như thế nào? Logs, metrics, và traces được thu thập và visualized ra sao?**

5. **Nếu một service trong stack (ví dụ: Qdrant hoặc Kafka) bị crash, hệ thống của bạn sẽ xử lý như thế nào? Có graceful degradation không?**

## Trả Lời 5 Câu Hỏi Nộp Bài

### 1. Phân tích các trade-offs trong thiết kế kiến trúc AI platform

Kiến trúc được tách thành local infrastructure và GPU serving để cân bằng giữa chi phí, hiệu năng và khả năng vận hành. Local stack chạy Kafka, Prefect, Qdrant, Redis, Prometheus, Grafana và API Gateway bằng Docker Compose nên dễ demo, dễ reset và dễ quan sát. Phần GPU/vLLM được tách ra Kaggle để tận dụng tài nguyên GPU miễn phí/thấp chi phí thay vì yêu cầu máy local mạnh.

Trade-off chính là độ phức tạp kết nối tăng lên vì local phụ thuộc tunnel tới Kaggle. Để giữ reliability, API Gateway có fallback local khi vLLM tunnel lỗi, giúp smoke test và demo observability vẫn chạy được. Maintainability được ưu tiên bằng cách tách component rõ ràng: ingestion qua Kafka, orchestration bằng Prefect, vector search qua Qdrant, feature store qua Redis và monitoring bằng Prometheus/Grafana.

### 2. Xử lý ngắt kết nối giữa local và Kaggle như thế nào?

Kết nối local với Kaggle đi qua public tunnel như ngrok/cloudflared. Khi tunnel hoặc vLLM không phản hồi, API Gateway không làm crash service mà dùng fallback response local để trả kết quả hợp lệ cho client. Điều này cho phép hệ thống degrade gracefully: các chức năng local như health check, metrics, Kafka ingestion, Redis feature store và Qdrant vector store vẫn hoạt động.

Trong production thực tế, fallback có thể mở rộng thành cached responses, model nhỏ local, retry có backoff, circuit breaker và cảnh báo Prometheus/Grafana khi Kaggle endpoint lỗi. Trong demo hiện tại, fallback local giúp chứng minh API Gateway vẫn ổn định dù GPU serving tạm thời unavailable.

### 3. Kafka giúp decouple components như thế nào?

Kafka đóng vai trò event bus giữa data ingestion và pipeline xử lý. Producer chỉ cần gửi records vào topic `data.raw`, không cần biết Prefect flow, Delta Lake, Redis hay Qdrant xử lý phía sau ra sao. Consumer/Pipeline có thể chạy độc lập, retry độc lập và scale độc lập.

Cách này giúp hệ thống dễ mở rộng hơn so với gọi trực tiếp giữa các service. Nếu downstream tạm lỗi, data vẫn có thể được giữ trong Kafka để xử lý lại. Kafka cũng hỗ trợ replay event, phù hợp với AI platform cần tái xử lý dữ liệu, rebuild feature store hoặc regenerate embeddings.

### 4. Observability được implement như thế nào?

Observability gồm metrics, logs và dashboard. API Gateway expose `/metrics` bằng `prometheus-fastapi-instrumentator`, Prometheus scrape metrics từ API Gateway và các service liên quan, Grafana dùng Prometheus làm datasource để hiển thị trạng thái service. Các endpoint health như `/health`, Prometheus `/-/healthy`, Qdrant `/healthz` và Grafana `/api/health` được dùng trong smoke tests và readiness check.

Logs được lấy qua Docker logs cho từng service như API Gateway, Kafka, Prefect worker và Prometheus. Prefect UI hiển thị flow run Kafka → Delta, giúp theo dõi trạng thái orchestration. Production readiness script tự động kiểm tra reliability, observability, security, vector store, feature store và Kafka topic để xác nhận hệ thống sẵn sàng demo.

### 5. Nếu Kafka hoặc Qdrant crash thì hệ thống xử lý như thế nào?

Nếu Kafka crash, data ingestion sẽ fail tạm thời nhưng các service khác như API Gateway, Grafana, Prometheus, Qdrant và Redis vẫn có thể tiếp tục chạy. Sau khi Kafka được restart bằng Docker Compose, producer có thể gửi lại dữ liệu và pipeline Prefect có thể chạy lại để tái tạo Delta/Feature data. Trong production, nên bổ sung retry, dead-letter topic và alert khi Kafka unavailable.

Nếu Qdrant crash, API Gateway vẫn giữ health endpoint và fallback response, nhưng vector search sẽ bị ảnh hưởng. Sau khi Qdrant restart, collection `documents` có thể được tạo lại và script embedding local có thể chạy lại để upsert vectors. Nhờ dữ liệu gốc đi qua Kafka/Delta, hệ thống có khả năng rebuild vector store thay vì mất hoàn toàn pipeline.

## Câu Hỏi Thêm?
Liên hệ giảng viên qua LMS hoặc office hours.
