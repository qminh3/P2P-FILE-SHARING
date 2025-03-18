# Tổng Quan Hệ Thống P2P (Peer-to-Peer)

## Hệ thống P2P là gì?
Hệ thống P2P (Peer-to-Peer) là một kiến trúc mạng phi tập trung, trong đó mỗi nút (peer) trong mạng đều có thể đồng thời đóng vai trò là máy khách (client) và máy chủ (server). Không giống như mô hình máy chủ - máy khách truyền thống, mạng P2P không phụ thuộc vào một máy chủ trung tâm mà cho phép các nút kết nối và chia sẻ tài nguyên trực tiếp với nhau.

## Đặc điểm nổi bật
- **Phi tập trung**: Không có máy chủ trung tâm điều phối hoạt động.
- **Dễ mở rộng**: Khi có thêm nút tham gia, mạng có thể mở rộng linh hoạt.
- **Khả năng chịu lỗi cao**: Mạng vẫn hoạt động ổn định ngay cả khi một số nút ngừng hoạt động.
- **Chia sẻ tài nguyên**: Sử dụng hiệu quả băng thông, dung lượng lưu trữ và khả năng xử lý giữa các nút.
- **Tiết kiệm chi phí**: Giảm thiểu chi phí hạ tầng do không cần đầu tư máy chủ trung tâm.

## Ứng dụng phổ biến
- **Chia sẻ tệp tin**: BitTorrent, eMule.
- **Blockchain và tiền mã hóa**: Bitcoin, Ethereum.
- **Nền tảng cho vay ngang hàng (P2P Lending)**: Kết nối trực tiếp người cho vay và người vay.
- **Giao tiếp thời gian thực**: Một số phần mềm gọi điện, họp trực tuyến sử dụng mô hình P2P.

## Lợi ích
- Tăng cường quyền riêng tư và quyền kiểm soát cho người dùng.
- Tăng độ ổn định và linh hoạt của mạng.
- Giảm tình trạng nghẽn mạng và độ trễ.

## Ứng dụng trong dự án
Dự án này có thể triển khai hoặc mô phỏng hệ thống P2P phục vụ các mục đích như:
- Chia sẻ dữ liệu phi tập trung.
- Phát triển ứng dụng phi tập trung (DApps).
- Phân tán và xử lý tác vụ tính toán.
## Để chạy projet

### Đầu tiên cần chạy tracker

To run tracker , run the following command

```bash
  python tracker.py
```
To run peer for upload , run the following command

```python
  python peer.py
  # Chọn chế độ (1: Upload, 2: Download): 1
  # Nhập port cho peer server:
  # Nhập đường dẫn file để upload: E:\p2p_file_sharing\port.txt
```
To run peer for download , run the following command
```python
  python peer.py
  # Chọn chế độ (1: Upload, 2: Download): 2
  # Nhập port cho peer server:
  # Nhập tên của file cần tải: port.txt
  # Nhập piece_length: 1
  # Nhập tên file để lưu: ketqua.txt
  # Chọn phương thức tải file:
  # 1. Tải file từ một peer
  # 2. Tải file từ nhiều peers
  # Nhập lựa chọn (1/2):
```