---
name: aidancing-image
description: Sửa ảnh qua Aidancing — chỉnh tổng quát, bóc outfit, xóa vật thể, thay nền, thay trang phục và thêm phụ kiện từ ảnh nguồn.
---

# Aidancing Image

Dùng khi người dùng chọn Aidancing để sửa ảnh. Xem ảnh nguồn, xác định phần cần thay đổi và phần cần giữ trước khi chọn script. Giữ nguyên ảnh gốc và tỷ lệ nguồn.

## Chọn thao tác sửa ảnh

Các script gọi `https://image.aidancing.net` bằng `requests`, không cần cấu hình API ảnh OpenAI trong `.env`. Đọc script liên quan trước khi chạy; nếu runtime thiếu `requests`, cài bằng `python -m pip install requests` trong môi trường đang sử dụng.

| Mục tiêu thực tế | Script trong `scripts/` | Đầu vào CLI |
|---|---|---|
| Sửa tổng quát, chỉnh nhiều thành phần, bóc outfit ra ảnh riêng | `aidancing_edit.py` | `image prompt -o output` |
| Xóa vật thể cụ thể, giữ phần còn lại | `aidancing_delete_object.py` | `image prompt -o output` |
| Đổi bối cảnh theo ảnh nền mới | `aidancing_bg_swap.py` | `subject background -p prompt -o output` |
| Mặc trang phục mẫu lên nhân vật | `aidancing_outfit_swap.py` | `person outfit -p prompt -o output` |
| Thêm phụ kiện mẫu lên nhân vật | `aidancing_add_accessory.py` | `person accessory -p prompt -o output` |

Ba script swap/accessory cần **hai ảnh**, theo đúng thứ tự trong bảng. Nếu chỉ có một ảnh và yêu cầu thay đổi bằng mô tả, dùng `aidancing_edit.py`; nếu cần khớp chính xác mẫu chưa có thì yêu cầu ảnh mẫu. Không truyền cùng một ảnh giả làm hai đầu vào. Yêu cầu phối hợp nhiều chỉnh sửa ưu tiên edit với prompt đầy đủ; chỉ tách bước nếu cần và dùng kết quả bước trước làm nguồn cho bước sau.

**Ví dụ bóc outfit từ một ảnh có sẵn:** chọn `aidancing_edit.py`, không chọn `aidancing_outfit_swap.py` hoặc chỉ xóa người bằng delete_object. Prompt:

```text
xoá bối cảnh, xoá nhân vật, bóc tách outfit ra ảnh riêng nền trắng
```

```powershell
python "$SkillDir/scripts/aidancing_edit.py" "$SessionDir/input/source.png" "xoá bối cảnh, xoá nhân vật, bóc tách outfit ra ảnh riêng nền trắng" -o "$SessionDir/output/outfit.png"
python "$SkillDir/scripts/aidancing_delete_object.py" "$SessionDir/input/source.png" "xoá cái chai nước, giữ nguyên phần còn lại" -o "$SessionDir/output/clean.png"
python "$SkillDir/scripts/aidancing_bg_swap.py" "$SessionDir/input/person.png" "$SessionDir/input/background.png" -p "Giữ nguyên nhân vật, khớp ánh sáng nền mới" -o "$SessionDir/output/background.png"
python "$SkillDir/scripts/aidancing_outfit_swap.py" "$SessionDir/input/person.png" "$SessionDir/input/outfit.png" -p "Giữ nguyên khuôn mặt và chi tiết trang phục mẫu" -o "$SessionDir/output/dressed.png"
python "$SkillDir/scripts/aidancing_add_accessory.py" "$SessionDir/input/person.png" "$SessionDir/input/accessory.png" -p "Thêm phụ kiện đúng vị trí, giữ nguyên nhân vật" -o "$SessionDir/output/accessorized.png"
```

Các script hiện poll `jobs[0]` theo loại job, chưa đối chiếu job ID. Chạy tuần tự trong cùng session dịch vụ; không chạy batch song song và kiểm tra ảnh trả về đúng yêu cầu. Nếu Aidancing thất bại, báo lỗi thực tế và dừng.

## Lưu và nghiệm thu

Dùng session `.scratch/yyyy-mm-dd_aidancing-image_ten-tac-vu/` với `input/` và `output/`. Tạo thư mục output trước khi chạy, luôn truyền `-o`. Các script không có `--session-dir`, `--aspect-ratio` hoặc `--quality`.

Kiểm tra file tồn tại, mở và xem ảnh để đối chiếu yêu cầu. Trả ảnh hoặc link file, script và prompt thực tế; báo sai khác quan sát được. Không coi trạng thái COMPLETED là nghiệm thu hình ảnh.
