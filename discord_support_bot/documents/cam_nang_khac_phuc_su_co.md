# CẨM NANG KHẮC PHỤC SỰ CỐ & SỬA LỖI MTH RECAP STUDIO (A - Z)

## 1. Lỗi Tải truyện / Không mở được trình duyệt để cào ảnh (Browser / ChromeDriver):
- **Triệu chứng:** Bấm tải truyện hoặc mở trình duyệt nhưng tool không mở được, báo lỗi driver hoặc quay tròn không tải được ảnh.
- **Nguyên nhân phổ biến nhất:**
  1. Người dùng đang mở sẵn trình duyệt **Cốc Cốc** hoặc **Google Chrome** chạy ngầm ➔ Làm xung đột cổng Debug hoặc khóa Profile khiến ChromeDriver không nhận được trình duyệt.
  2. Phần mềm diệt virus / Windows Defender chặn tool tự động hóa.
- **Cách khắc phục nhanh:**
  1. **Đóng hoàn toàn trình duyệt Cốc Cốc và Chrome** (Mở *Task Manager* (Ctrl + Shift + Esc) ➔ Tìm và tắt toàn bộ tiến trình `coccoc.exe` hoặc `chrome.exe`).
  2. Mở lại tool MTH Recap và bấm tải lại ảnh truyện.

---

## 2. Các lỗi liên quan đến Render / Xuất video:

### 🔴 Lỗi Render bị văng app (Crash) hoặc đứng yên ở 0% / 50%
- **Nguyên nhân chính:**
  1. Thư mục dự án hoặc tên file có dấu tiếng Việt, ký tự đặc biệt (@, #, $, %, dấu cách lạ).
  2. Phần mềm diệt virus (Windows Defender / Antivirus) chặn `ffmpeg.exe` hoặc `ffprobe.exe`.
  3. Tràn bộ nhớ RAM hoặc đầy ổ cứng cài đặt.
- **Cách khắc phục:**
  - Chuyển thư mục lưu dự án sang dạng tiếng Việt không dấu: `D:\Du_An_MTH\Tap_1`.
  - Mở Windows Defender / Antivirus ➔ Thêm toàn bộ thư mục cài đặt app MTH Recap vào mục **Loại trừ (Exclusions)**.
  - Vào **Cài đặt (Settings)** trong app ➔ Giảm **Số luồng xử lý (Thread count)** xuống mức 2 hoặc 4 nếu máy có ít RAM (dưới 16GB).
  - Đảm bảo ổ cứng còn trống ít nhất 10GB - 20GB.

### 🔴 Lỗi Âm thanh và hình ảnh bị lệch nhịp (Lệch Sub / Lệch tiếng)
- **Giải thích:** Khung xem trước (Preview) trong app chỉ là mô phỏng tải nhẹ.
- **Cách khắc phục:** Luôn chọn **Render thử 3 shot đầu tiên** thành video MP4 để kiểm tra độ khớp chuẩn xác 100%.

---

## 3. Các lỗi liên quan đến Giọng đọc AI & Âm thanh:

### 🔴 Lỗi Giọng đọc AI không phát ra tiếng / Báo lỗi kết nối TTS
- **Cách khắc phục:**
  - Nếu dùng Edge TTS: Kiểm tra đường truyền internet.
  - Nếu dùng Giọng cao cấp (Yupvox): Kiểm tra tài khoản xem còn Credits không (1 ký tự = 1 credit).
  - Không để một câu thoại dài quá 200 - 300 từ trong một shot, hãy ngắt kịch bản thành các câu ngắn hơn để voice đọc tự nhiên và không bị timeout.

---

## 4. Các lỗi liên quan đến Nhận diện nhân vật & Kịch bản:

### 🔴 Lỗi Quét nhân vật không ra hoặc muốn nhận diện lại từ đầu
- **Cách khắc phục:** Bật công tắc **"Rescan Characters" (Quét lại nhân vật)** ở bảng bên phải trước khi chạy. Thao tác này sẽ xóa cache cũ và quét lại chuẩn xác toàn bộ.

---

## 5. Hỗ trợ kỹ thuật từ xa:
- Nếu người dùng đã làm theo các bước trên vẫn không xử lý được, đội ngũ Kỹ thuật viên sẵn sàng hỗ trợ trực tiếp qua **UltraViewer** hoặc **AnyDesk**.
- Vui lòng gửi tin nhắn vào kênh `#🐛-báo-lỗi` trên Discord kèm: Phiên bản app (v5.4 / v6.1), ảnh chụp màn hình lỗi và mô tả bước gây lỗi để được hỗ trợ nhanh nhất.
