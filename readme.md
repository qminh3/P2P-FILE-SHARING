
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