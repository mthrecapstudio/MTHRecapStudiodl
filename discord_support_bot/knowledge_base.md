# MTH Recap Studio - Knowledge Base for Support Bot AI

## 1. Giới thiệu tổng quan:
MTH Recap Studio là phần mềm chuyên dụng trên hệ điều hành Windows dùng để tự động hóa toàn bộ quy trình sản xuất video tóm tắt / review truyện tranh (Manga/Manhwa/Manhua Recap) và video hoạt hình.

## 2. Các tính năng chính của phần mềm:
- **Trình chỉnh sửa kịch bản (Script Editor):** Tự động phân đoạn cảnh, nhận diện nhân vật, tối ưu thoại và cảm xúc.
- **Hệ thống Giọng đọc AI (Voice & TTS):** Hỗ trợ Piper TTS, RVC (Voice Clone - nhân bản giọng nói theo mẫu), và các engine AI tiên tiến.
- **Trích xuất khung truyện (Panel Extractor) & Nhận diện nhân vật (Character Tracking):** Tự động cắt tách khung tranh, phát hiện nhân vật chính/phụ và loại bỏ khung thoại/chữ thừa.
- **Tăng cường hình ảnh (Image Enhancer):** Sử dụng Real-ESRGAN / AI Upscale để nâng cấp độ nét tranh từ SD lên HD/2K/4K.
- **Xuất video (Video Render):** Tự động ghép nối hình ảnh, hiệu ứng chuyển cảnh, nhạc nền và giọng đọc thành video MP4 hoàn chỉnh thông qua FFmpeg.

## 3. Yêu cầu hệ thống:
- Hệ điều hành: Windows 10 hoặc Windows 11 (64-bit).
- Vi xử lý (CPU): Tối thiểu Intel Core i5 / AMD Ryzen 5 thế hệ mới.
- RAM: Tối thiểu 8GB (khuyến nghị 16GB trở lên).
- Card đồ họa (GPU): Tối ưu tốt nhất với NVIDIA (GTX 1060 trở lên, hỗ trợ CUDA) để tăng tốc trích xuất ảnh và render. Nếu dùng CPU hoặc card AMD/Intel, phần mềm vẫn hoạt động tốt nhưng tốc độ xử lý chậm hơn.
- Dung lượng ổ cứng: Tối thiểu 10GB trống (nên dùng ổ SSD).

## 4. Hướng dẫn xử lý các lỗi thường gặp:

### A. Lỗi Render / Xuất video (FFmpeg, Crash, Treo giữa chừng):
- **Nguyên nhân 1:** Đường dẫn thư mục chứa dự án hoặc tên file có dấu tiếng Việt, ký tự đặc biệt hoặc emoji. -> **Khắc phục:** Đặt tên thư mục và file dạng tiếng Việt không dấu (ví dụ: `D:\MTHRecap_Projects\Tap_1`).
- **Nguyên nhân 2:** Thiếu FFmpeg hoặc file FFmpeg bị phần mềm diệt virus (Windows Defender/Antivirus) chặn. -> **Khắc phục:** Kiểm tra thư mục `ffmpeg_bin`, thêm thư mục app vào danh sách loại trừ (Exclusion) của Antivirus.
- **Nguyên nhân 3:** Tràn bộ nhớ RAM/VRAM hoặc ổ cứng bị đầy dung lượng. -> **Khắc phục:** Tắt bớt các ứng dụng nặng khác và dọn dẹp dung lượng ổ cứng.

### B. Lỗi Âm thanh / Giọng đọc AI (Voice/TTS/RVC):
- **Nguyên nhân 1:** Chưa tải đủ Model giọng đọc hoặc file âm thanh mẫu bị lỗi. -> **Khắc phục:** Vào cài đặt Giọng đọc để kiểm tra và tải lại model.
- **Nguyên nhân 2:** Đoạn kịch bản quá dài trong 1 dòng. -> **Khắc phục:** Ngắt kịch bản thành các câu ngắn hơn (dưới 200 từ mỗi đoạn).

### C. Lỗi Đăng nhập / Bản quyền (License Key):
- **Khắc phục:** Kiểm tra lại kết nối mạng internet (tắt VPN nếu có), kiểm tra ngày giờ trên máy tính có chuẩn xác không. Nếu key không nhận, liên hệ Ban Quản Trị để cấp lại/kiểm tra trạng thái kích hoạt.

## 5. Quy trình hỗ trợ khách hàng:
- Yêu cầu người dùng cung cấp: Phiên bản app (VD: v5.4, v6.0), mô tả bước gây lỗi, ảnh chụp màn hình thông báo lỗi và file log (nếu có).
- Hướng dẫn thân thiện, lịch sự, dễ hiểu cho người không rành kỹ thuật.
