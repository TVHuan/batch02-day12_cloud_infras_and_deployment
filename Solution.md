# Day 12 - Lab Assessment: Deploy Your AI Agent to Production
# Solution Document

## Part 1: Localhost vs Production
### Exercise 1.1: Phát hiện anti-patterns
Các anti-patterns trong code basic:
1. Hardcode API key và secrets trực tiếp trong code thay vì dùng biến môi trường.
2. Không có cơ chế Health Check / Readiness Check để hệ thống container biết trạng thái của ứng dụng.
3. Không có Graceful Shutdown, khi container bị kill sẽ làm mất các request đang xử lý dở.
4. Chạy ở chế độ Debug mode (`debug=True`), gây nguy hiểm lộ lỗi trên production.
5. Binding cứng vào localhost hoặc dùng fixed port không linh hoạt.
6. Print log bằng hàm `print()` tiêu chuẩn thay vì structured logging, khó tracking và quản lý log trên cloud.

### Exercise 1.3: So sánh với advanced version
| Feature | Basic | Advanced | Tại sao quan trọng? |
|---------|-------|----------|---------------------|
| Config | Hardcode | Env vars | Dễ thay đổi cấu hình giữa các môi trường (dev, staging, prod) mà không cần sửa code, và bảo mật thông tin (không commit secrets lên git). |
| Health check | ❌ | ✅ | Nền tảng cloud/container cần biết khi nào app sẵn sàng nhận traffic và khi nào cần phải khởi động lại (restart) nếu app bị treo. |
| Logging | print() | JSON | Structured logs dưới dạng JSON dễ dàng cho các hệ thống như ELK stack hoặc Datadog để parse, tìm kiếm và phân tích lỗi. |
| Shutdown | Đột ngột | Graceful | Đảm bảo không làm mất dữ liệu của người dùng, chờ hoàn thành xong các request đang xử lý rồi mới đóng connections và tắt app. |

## Part 2: Docker Containerization
### Exercise 2.1: Dockerfile cơ bản
1. **Base image là gì?** `python:3.11-slim`. Đây là image Linux thu gọn (Debian slim) chứa sẵn Python 3.11, giúp giảm dung lượng image.
2. **Working directory là gì?** `/app`. Đây là thư mục mặc định bên trong container nơi chứa toàn bộ mã nguồn ứng dụng.
3. **Tại sao COPY requirements.txt trước?** Để tận dụng Docker cache. Nếu file `requirements.txt` không thay đổi, Docker sẽ không cần tải và cài đặt lại thư viện ở mỗi lần build code mới, giúp tăng tốc độ build đáng kể.
4. **CMD vs ENTRYPOINT khác nhau thế nào?** `CMD` cung cấp lệnh mặc định để thực thi nhưng có thể bị override dễ dàng khi chạy `docker run`. `ENTRYPOINT` là lệnh cốt lõi của container và luôn được thực thi (khó override hơn), thường các tham số truyền vào `docker run` sẽ được nối tiếp vào ENTRYPOINT.

### Exercise 2.3: Multi-stage build
- **Stage 1 (Builder) làm gì?** Tải và cài đặt tất cả các dependencies, có thể bao gồm các thư viện build C/C++ cần thiết (như gcc, make) vào một virtual environment hoặc thư mục tạm.
- **Stage 2 (Runtime) làm gì?** Kế thừa từ một base image nhẹ nhàng (như alpine hoặc slim), chỉ copy những file thư viện đã được build sẵn từ Stage 1 sang mà không mang theo các công cụ build.
- **Tại sao image nhỏ hơn?** Vì image cuối cùng (Runtime) không chứa các build tools (compiler, header files) không cần thiết cho quá trình chạy app, giúp giảm kích thước từ hàng GB xuống chỉ còn vài chục đến vài trăm MB, đồng thời giảm diện tấn công bảo mật.

### Exercise 2.4: Docker Compose stack
Kiến trúc luồng xử lý:
`Client (Postman/Curl) → Nginx (Reverse Proxy & Load Balancer ở Port 80) → AI Agent (Port 8000) → Redis (Port 6379)`

## Part 3: Cloud Deployment
### So sánh Render vs Railway
- Railway dùng file cấu hình `railway.toml` (hoặc `railway.json`), khá đơn giản, chủ yếu định nghĩa start command và các services.
- Render dùng file `render.yaml`, theo mô hình infrastructure-as-code đầy đủ hơn, định nghĩa Blueprint của môi trường bao gồm web services, private services, databases (Redis, Postgres) và pre-build commands rất chi tiết.

## Part 4: API Security
### Exercise 4.1: API Key authentication
- **API key được check ở đâu?** Trong Dependency injection của FastAPI (hoặc middleware), hệ thống sẽ đọc header `X-API-Key` của request.
- **Điều gì xảy ra nếu sai key?** Trả về HTTP Status Code `401 Unauthorized`.
- **Làm sao rotate key?** Chỉ cần đổi giá trị của biến môi trường `AGENT_API_KEY` trên server và restart service (hoặc có cơ chế reload config). Khách hàng sẽ phải cập nhật key mới.

### Exercise 4.3: Rate limiting
- **Algorithm nào được dùng?** Thường là Sliding window hoặc Fixed window log sử dụng Redis để đếm.
- **Làm sao bypass limit cho admin?** Khi check authentication, nếu nhận dạng được token/key thuộc role Admin thì bỏ qua khâu kiểm tra và cập nhật quota trong Redis.

## Part 5: Scaling & Reliability
### Exercise 5.1 & 5.2 & 5.3
- **Liveness Probe (Health):** Trả về 200 OK ngay lập tức để báo container vẫn đang chạy.
- **Readiness Probe:** Kiểm tra kết nối tới Database/Redis, nếu thành công mới trả về 200, ngược lại trả về 503 để Load Balancer không điều hướng traffic vào instance bị lỗi.
- **Stateless Design:** Cực kỳ quan trọng để Scale ngang (Horizontal Scaling). Các biến state (ví dụ: `conversation_history`) không được lưu trong biến memory (dictionary/list) của Python, mà phải lưu tập trung vào In-memory Database như Redis để tất cả các instances của app (khi được scale ra) đều có thể đọc/ghi chung một lịch sử.

---
## Part 6: Lab Assignment - Final Project Deployment
**API URL Link:** `link prod`
