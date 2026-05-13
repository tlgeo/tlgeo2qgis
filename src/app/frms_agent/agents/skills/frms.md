# FRMS System - Hướng dẫn khai thác

## Giới thiệu

FRMS (Forest Resource Management System) là hệ thống quản lý tài nguyên rừng với 4 trụ cột chính:

1. **Quản lý Lô rừng** (Forest Plots Management)
2. **Quản lý Chủ rừng** (Forest Owners Management)
3. **Quản lý Diễn biến rừng** (Forest Changes Tracking)
4. **Báo cáo & Thống kê** (Reports & Statistics)

## Database Connection

### Kết nối PostgreSQL

```python
FRMS_DB_CONFIG = {
    "host": os.getenv("FRMS_DB_HOST", "localhost"),
    "port": int(os.getenv("FRMS_DB_PORT", "8088")),
    "dbname": os.getenv("FRMS_DB_NAME", "data_forest"),
    "user": os.getenv("FRMS_DB_USER", "postgres"),
    "password": os.getenv("FRMS_DB_PASSWORD", ""),
}
```

**Lỗi kết nối:**
- `connection refused` → Database server không chạy hoặc sai port
- `timeout` → Firewall block hoặc server quá tải
- `password authentication failed` → Sai username/password

**Xử lý khi không kết nối được:**
1. Kiểm tra server PostgreSQL đang chạy
2. Kiểm tra port trong cấu hình
3. Kiểm tra tường lửa cho phép kết nối

---

## 1. Lô rừng (Forest Plots)

### Mô tả
Lô rừng là đơn vị quản lý cơ bản trong hệ thống FRMS, được xác định bởi ranh giới địa lý và thông tin thuộc tính.

### Thuộc tính chính
| Trường | Mô tả |
|--------|-------|
| plot_id | Mã định danh duy nhất |
| area | Diện tích (hecta) |
| forest_type | Loại rừng (tự nhiên, trồng,...) |
| district | Quận/Huyện |
| commune | Xã/Phường |
| owner_id | Mã chủ rừng (liên kết) |
| status | Trạng thái (active, inactive) |

### Câu hỏi mẫu
- "Lô rừng nào có diện tích trên 100 hecta?"
- "Cho tôi xem danh sách lô rừng ở huyện X"
- "Tìm lô rừng theo mã chủ rừng"

---

## 2. Chủ rừng (Forest Owners)

### Mô tả
Chủ rừng là cá nhân/tổ chức sở hữu hoặc quản lý đất rừng.

### Thuộc tính chính
| Trường | Mô tả |
|--------|-------|
| owner_id | Mã định danh |
| name | Tên chủ rừng |
| id_card | Số CCCD/CMND |
| phone | Số điện thoại |
| address | Địa chỉ |
| ownership_type | Loại sở hữu (cá nhân, tổ chức, nhà nước) |

### Câu hỏi mẫu
- "Chủ rừng có tên X ở đâu?"
- "Cho tôi xem danh sách chủ rừng ở tỉnh Y"
- "Tìm chủ rừng theo số điện thoại"

---

## 3. Diễn biến rừng (Forest Changes)

### Mô tả
Theo dõi các thay đổi trong lô rừng theo thời gian.

### Loại thay đổi
| Loại | Mô tả |
|------|-------|
| CREATE | Lô rừng mới được tạo |
| UPDATE | Thông tin lô rừng thay đổi |
| SPLIT | Lô rừng bị tách |
| MERGE | Nhiều lô được gộp |
| DELETE | Lô rừng bị xóa |

### Thuộc tính
| Trường | Mô tả |
|--------|-------|
| change_id | Mã diễn biến |
| plot_id | Mã lô rừng |
| change_type | Loại thay đổi |
| change_date | Ngày thay đổi |
| description | Mô tả chi tiết |
| user_id | Người thực hiện |

### Câu hỏi mẫu
- "Có bao nhiêu lô rừng được tạo trong tháng này?"
- "Lịch sử thay đổi của lô X"
- "Những lô rừng nào bị tách trong quý vừa qua?"

---

## 4. Báo cáo & Thống kê

### Loại báo cáo
- **Báo cáo diện tích**: Tổng diện tích rừng theo khu vực
- **Báo cáo chủ rừng**: Phân bố chủ rừng theo loại hình
- **Báo cáo diễn biến**: Tình hình biến động tài nguyên rừng
- **Báo cáo tổng hợp**: Báo cáo định kỳ theo yêu cầu

### Câu hỏi mẫu
- "Tổng diện tích rừng trên toàn quốc?"
- "Báo cáo diễn biến rừng quý I năm nay"
- "So sánh diện tích rừng giữa các tỉnh"

---

## Khi không có kết nối Database

Nếu không thể kết nối database, hãy trả lời:

1. **Xin lỗi và giải thích** ngắn gọn về vấn đề kết nối
2. **Gợi ý các bước xử lý**:
   - Kiểm tra database server đang chạy
   - Kiểm tra cấu hình kết nối trong .env
   - Liên hệ quản trị hệ thống
3. **Cung cấp câu hỏi mẫu** mà người dùng có thể hỏi khi hệ thống hoạt động
4. **Hỏi người dùng** có muốn thử lại sau không

---

## Ví dụ Response khi DB offline

```
Xin lỗi, hiện tại tôi không thể kết nối đến cơ sở dữ liệu FRMS.

Nguyên nhân có thể là:
• Database server chưa được khởi động
• Sai cấu hình kết nối trong .env
• Tường lửa chặn kết nối

Bạn có thể:
1. Kiểm tra database PostgreSQL đang chạy trên port 8088
2. Xem lại FRMS_DB_HOST, FRMS_DB_PORT trong file .env
3. Liên hệ quản trị viên để được hỗ trợ

Khi hệ thống hoạt động, bạn có thể hỏi tôi về:
• Lô rừng và thông tin chi tiết
• Chủ rừng và thông tin liên hệ
• Diễn biến rừng theo thời gian
• Báo cáo và thống kê
```

---

## Best Practices

1. **Luôn kiểm tra kết nối** trước khi truy vấn
2. **Dùng parameterized queries** để tránh SQL injection
3. **Giới hạn kết quả** với LIMIT để tránh quá tải
4. **Xử lý lỗi gracefully** và thông báo rõ ràng cho user
5. **Ghi log** mọi truy vấn để debug