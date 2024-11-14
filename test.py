import os

def split_file(file_path, output_dir, sizepiece):
    # Kiểm tra nếu thư mục đầu ra không tồn tại thì tạo mới
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    # Đọc toàn bộ nội dung file
    with open(file_path, 'rb') as f:
        file_data = f.read()

    # Tính kích thước mỗi phần
    total_size = len(file_data)
    num_parts = total_size // sizepiece

    # Cắt file thành num_parts phần và lưu vào thư mục
    for i in range(num_parts):
        start_index = i * sizepiece
        end_index = start_index + sizepiece if i < num_parts - 1 else total_size
        
        # Tạo tên cho các phần file trong thư mục output_dir
        part_file_name = os.path.join(output_dir, f"result_{i + 1}.txt")
        
        # Ghi phần vào file mới
        with open(part_file_name, 'wb') as part_file:
            part_file.write(file_data[start_index:end_index])

        print(f"Đã tạo phần {i + 1}: {part_file_name}")

# Sử dụng hàm
file_path = 'E:\p2p_file_sharing\port.txt'  # Đặt đường dẫn tới file cần chia
output_dir = 'E:\p2p_file_sharing\store'  # Đặt thư mục lưu các phần file
split_file(file_path, output_dir, sizepiece=1)