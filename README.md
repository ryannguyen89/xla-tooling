# xla-tooling
## Hướng dẫn sử dụng
1. Tải bản release mới nhất tại: https://github.com/ryannguyen89/xla-tooling/releases
2. Giải nén file zip vừa tải
3. Nhấn Shift + chuột phải vào folder vừa giải nén được xla-tooling-xxxxx và chọn **Open PowerShell Window here** ![image](https://github.com/ryannguyen89/xla-tooling/assets/54627199/07a74088-7798-454f-80d3-ec656825d10d)
4. Tại của sổ Terminal vừa mở gõ ```python -V```, nếu hệ thống hiện ra version của Python thì sang bước tiếp theo, nếu không thì cài đặt Python từ Windows Store
5. Cài package binance future:```pip install binance-futures-connector```
6. Vào thư mục xla-tooling-xxxx mở file **config.json** và thêm **api-key**, **secret-key** của Binance
7. Mở file **orders.txt**, xóa lệnh mẫu và copy lệnh muốn gửi lên sàn vào. Template: ![image](https://github.com/ryannguyen89/xla-tooling/assets/54627199/1a031fac-7a53-415c-bee6-a55938045d21)

8. Quay lại Power Shell chạy lệnh: `python main.py`
## Các lỗi thường gặp
1. Sai template => tool sẽ thông báo sai ở dòng nào và bạn phải tự kiểm tra để fix
2. IP chưa được whitelist=> vì tool chạy ở local và thường internet tại gia đình là IP động, nên sau một thời gian có thể bị thay đổi IP, tool sẽ có thông báo về IP không được whitelist, bạn cần thêm IP đó vào danh sách whitelist của API key mà bạn đang dùng.
3. Sai giá trigger => lệnh STM và TS cần điều kiện giá để có thể tạo order lên hệ thống của Binance, khi chuẩn bị push lệnh tool sẽ tự động cập nhật giá hiện tại của mã bạn cần trade và kiểm tra, nếu sai sẽ thông báo dòng sai và bạn cần kiểm tra lại
4. Các lỗi khác: Vui lòng liên hệ email: hoangnn3007@gmail.com hoặc Telegram: https://t.me/hoangnn3007 cùng với chụp màn hình thông tin lỗi và file orders.txt để được hỗ trợ.
## Buy me a coffee
Tool này được phát hành để bạn dùng hoàn toàn miễn phí, trong trường hợp nó có thể giúp bạn và bạn kiếm lời được từ nó, bạn có thể gửi mình ly cà phê: Binance PayID: `556063974`
## Chúc bạn trade thành công ^^
