import streamlit as st
import pandas as pd
from datetime import datetime
st.image("Screenshot_20261017_170859_Hypic.jpg")
# ---------------------------------------------------------
# CẤU HÌNH TRANG & CƠ SỞ DỮ LIỆU SẢN PHẨM
# ---------------------------------------------------------
st.set_page_config(
    page_title="Hệ Thống Tính Tiền Trà Sữa",
    page_icon="🧋",
    layout="wide"
)
# ---------------------------------------------------------

# ---------------------------------------------------------
IMAGE_URLS = {
    "Trà Sữa Truyền Thống": "",
    "Trà Sữa Trân Châu Đường Đen": "",
    "Trà Sữa Thái Xanh": "",
    "Trà Sữa Ô Long": "",
    "Matcha Latte": "",
    "Trà Đào Cam Sả": "",
    "Trà Dâu Tằm": "",
    "Trà Atiso Hạt Chia": "",
    "Lục Trà Lựu Nha Đam": "",
}

# Ba món best seller
BEST_SELLERS = [
    "Trà Sữa Trân Châu Đường Đen",
    "Matcha Latte",
    "Lục Trà Lựu Nha Đam",
]

# ---------------------------------------------------------
# Danh sách menu & giá (VND)
# ---------------------------------------------------------
MENU_TEA = {
    "Trà Sữa Truyền Thống": 30000,
    "Trà Sữa Trân Châu Đường Đen": 35000,
    "Trà Sữa Thái Xanh": 32000,
    "Trà Sữa Ô Long": 35000,
    "Matcha Latte": 38000,
    "Trà Đào Cam Sả": 35000,
    "Trà Dâu Tằm": 32000,
    "Trà Atiso Hạt Chia": 35000,
    "Lục Trà Lựu Nha Đam": 35000,
}

SIZE_OPTIONS = {
    "S (Vừa)": 0,
    "M (Lớn)": 5000,
    "L (Đặc biệt)": 10000
}

TOPPING_OPTIONS = {
    "Trân châu đen": 5000,
    "Trân châu trắng": 5000,
    "Thạch trái cây": 5000,
    "Pudding trứng": 10000,
    "Kem Cheese": 10000
}

SUGAR_LEVELS = [
    "100% (Bình thường)", "70%", "50%", "30%", "0% (Không đường)"
]

ICE_LEVELS = [
    "100% (Bình thường)", "70%", "50%", "30%", "0% (Không đá)"
]

# ---------------------------------------------------------
# KHỞI TẠO SESSION STATE
# ---------------------------------------------------------
if "cart" not in st.session_state:
    st.session_state.cart = []

if "invoice_paid" not in st.session_state:
    st.session_state.invoice_paid = False

if "wheel_result" not in st.session_state:
    st.session_state.wheel_result = None

if "wheel_used" not in st.session_state:
    st.session_state.wheel_used = False

if "voucher_code" not in st.session_state:
    st.session_state.voucher_code = ""

if "applied_voucher" not in st.session_state:
    st.session_state.applied_voucher = ""

# ---------------------------------------------------------
# VOUCHER
# Các mã này là mã mẫu do bạn có thể chỉnh sửa tùy ý.
# ---------------------------------------------------------
VOUCHERS = {
    "BOBA3": {
        "type": "percent",
        "value": 3,
        "description": "Giảm 3% tổng hóa đơn"
    },
    "BOBA5": {
        "type": "percent",
        "value": 5,
        "description": "Giảm 5% cho hóa đơn từ 2 ly"
    },
    "BOGO": {
        "type": "bogo",
        "value": 0,
        "description": "Mua 1 tặng 1 - giảm giá ly thấp hơn"
    }
}

# ---------------------------------------------------------
# HÀM TÍNH TỔNG TIỀN
# ---------------------------------------------------------
def calculate_total(cart):
    return sum(item["Thành tiền"] for item in cart)


def calculate_voucher_discount(cart, total_amount, code):
    """Trả về số tiền được giảm và thông báo voucher."""
    code = code.strip().upper()

    if not code:
        return 0, ""

    if code not in VOUCHERS:
        return 0, "Mã voucher không hợp lệ."

    voucher = VOUCHERS[code]

    if voucher["type"] == "percent":
        if code == "BOBA5":
            total_qty = sum(item["Số lượng"] for item in cart)
            if total_qty < 2:
                return 0, "BOBA5 chỉ áp dụng khi hóa đơn có từ 2 ly."

        amount = int(total_amount * voucher["value"] / 100)
        return amount, "Áp dụng voucher thành công!"

    if voucher["type"] == "bogo":
        # Mỗi cặp ly cùng món được giảm giá một ly.
        # Giá giảm không vượt quá tổng tiền món.
        discount = 0

        for item in cart:
            free_cups = item["Số lượng"] // 2
            discount += free_cups * item["Đơn giá"]

        if discount == 0:
            return 0, "BOGO cần ít nhất 2 ly cùng một món."

        return min(discount, total_amount), "Áp dụng voucher thành công!"

    return 0, ""


# ---------------------------------------------------------
# HÀM XUẤT HÓA ĐƠN TXT
# ---------------------------------------------------------
def create_txt_invoice(
    customer_name, cart, total_amount, discount,
    voucher_discount, final_amount, voucher_code
):
    now = datetime.now().strftime("%d/%m/%Y %H:%M:%S")

    content = "=" * 45 + "\n"
    content += f"{'HÓA ĐƠN BÁN HÀNG - ZZ TEA':^45}\n"
    content += "=" * 45 + "\n"
    content += f"Ngày: {now}\n"
    content += (
        f"Khách hàng: {customer_name if customer_name else 'Khách vãng lai'}\n"
    )
    content += "-" * 45 + "\n"

    for idx, item in enumerate(cart, 1):
        content += f"{idx}. {item['Tên món']} ({item['Size']})\n"
        content += f"   Đường: {item['Đường']} | Đá: {item['Đá']}\n"

        if item["Topping"] != "Không":
            content += f"   Topping: {item['Topping']}\n"

        content += (
            f"   SL: {item['Số lượng']} x {item['Đơn giá']:,}"
            f" = {item['Thành tiền']:,} VNĐ\n"
        )

    content += "-" * 45 + "\n"
    content += f"Tổng tiền món: {total_amount:,} VNĐ\n"
    content += f"Giảm giá thường: {discount}%\n"
    content += f"Giảm giá voucher: {voucher_discount:,} VNĐ\n"

    if voucher_code:
        content += f"Mã voucher: {voucher_code}\n"

    content += f"TỔNG THANH TOÁN: {final_amount:,} VNĐ\n"
    content += "=" * 45 + "\n"
    content += f"{'Cảm ơn quý khách và hẹn gặp lại!':^45}\n"

    return content


# ---------------------------------------------------------
# TIÊU ĐỀ
# ---------------------------------------------------------
st.title("🧋 QUÁN TRÀ SỮA ZZZ")
st.markdown("---")

# ---------------------------------------------------------
# MENU HÌNH ẢNH & BEST SELLER
# ---------------------------------------------------------
st.subheader("🍹 Menu thức uống")

st.caption(
    "Khám phá menu của chúng mình và lựa chọn thức uống yêu thích nhé!"
)

menu_cols = st.columns(3)

for index, (tea_name, tea_price) in enumerate(MENU_TEA.items()):
    with menu_cols[index % 3]:
        with st.container(border=True):
            image_url = IMAGE_URLS.get(tea_name, "")

            if image_url:
                st.image(image_url, use_container_width=True)

            if tea_name in BEST_SELLERS:
                st.markdown("**best seller ❤️‍🔥**")

            st.markdown(f"**{tea_name}**")
            st.write(f"{tea_price:,} VNĐ")

st.markdown("---")

# ---------------------------------------------------------
# VÒNG QUAY MAY MẮN
# ---------------------------------------------------------
st.subheader("🎡 Vòng quay may mắn")
st.write("Thử vận may và nhận ưu đãi cho đơn hàng của bạn!")

wheel_options = [
    "Giảm 3%",
    "Chúc may mắn",
    "Giảm 5% bill từ 2 ly",
    "Chúc may mắn",
    "Mua 1 tặng 1",
    "Chúc may mắn"
]

wheel_codes = {
    "Giảm 3%": "BOBA3",
    "Giảm 5% bill từ 2 ly": "BOBA5",
    "Mua 1 tặng 1": "BOGO"
}

wheel_col1, wheel_col2 = st.columns([1, 2])

with wheel_col1:
    if st.button(
        "🎯 QUAY NGAY",
        use_container_width=True,
        disabled=st.session_state.wheel_used
    ):
        result = random.choice(wheel_options)
        st.session_state.wheel_result = result
        st.session_state.wheel_used = True

        if result in wheel_codes:
            st.session_state.voucher_code = wheel_codes[result]

        st.rerun()

with wheel_col2:
    if st.session_state.wheel_result:
        result = st.session_state.wheel_result

        if result == "May mắn":
            st.info("🍀 Chúc bạn may mắn lần sau!")
        else:
            st.success(f"🎉 Chúc mừng! Bạn nhận được: {result}")

            if result in wheel_codes:
                st.write(
                    f"Mã ưu đãi của bạn: **{wheel_codes[result]}**"
                )
                st.caption(
                    "Hãy nhập mã này tại phần thanh toán để áp dụng."
                )

    if st.session_state.wheel_used:
        if st.button("🔄 Đặt lại vòng quay"):
            st.session_state.wheel_used = False
            st.session_state.wheel_result = None
            st.rerun()

st.markdown("---")

# ---------------------------------------------------------
# GIAO DIỆN ĐẶT HÀNG
# ---------------------------------------------------------
col_left, col_right = st.columns([1.1, 0.9])

with col_left:
    st.subheader("📝 Thông tin đơn hàng")

    customer_name = st.text_input(
        "Tên khách hàng:",
        placeholder="Nhập tên khách hàng..."
    )

    st.markdown("#### Chọn món nước & Tùy chọn")

    col_item, col_qty = st.columns([3, 1])

    with col_item:
        selected_tea = st.selectbox(
            "Loại trà sữa:",
            list(MENU_TEA.keys())
        )

    with col_qty:
        quantity = st.number_input(
            "Số lượng:",
            min_value=1,
            value=1,
            step=1
        )

    # Hiển thị ảnh món đang chọn
    selected_image = IMAGE_URLS.get(selected_tea, "")

    if selected_image:
        st.image(
            selected_image,
            caption=selected_tea,
            use_container_width=True
        )

    if selected_tea in BEST_SELLERS:
        st.markdown("**best seller ❤️‍🔥**")

    c_size, c_sugar, c_ice = st.columns(3)

    with c_size:
        selected_size = st.selectbox(
            "Size:",
            list(SIZE_OPTIONS.keys())
        )

    with c_sugar:
        selected_sugar = st.selectbox(
            "Mức đường:",
            SUGAR_LEVELS
        )

    with c_ice:
        selected_ice = st.selectbox(
            "Mức đá:",
            ICE_LEVELS
        )

    selected_toppings = st.multiselect(
        "Loại Topping (có thể chọn nhiều):",
        options=list(TOPPING_OPTIONS.keys())
    )

    base_price = MENU_TEA[selected_tea]
    size_price = SIZE_OPTIONS[selected_size]
    topping_price = sum(
        TOPPING_OPTIONS[t] for t in selected_toppings
    )

    unit_price = base_price + size_price + topping_price
    item_total = unit_price * quantity

    st.info(
        f"💡 Đơn giá 1 ly (đã gồm size & topping): "
        f"**{unit_price:,} VNĐ**"
    )

    if st.button(
        "➕ Thêm vào hóa đơn",
        type="primary",
        use_container_width=True
    ):
        topping_str = (
            ", ".join(selected_toppings)
            if selected_toppings else "Không"
        )

        item_data = {
            "Tên món": selected_tea,
            "Size": selected_size.split()[0],
            "Đường": selected_sugar.split()[0],
            "Đá": selected_ice.split()[0],
            "Topping": topping_str,
            "Đơn giá": unit_price,
            "Số lượng": quantity,
            "Thành tiền": item_total
        }

        st.session_state.cart.append(item_data)
        st.session_state.invoice_paid = False

        st.toast(
            f"Đã thêm {quantity}x {selected_tea} vào giỏ!",
            icon="✅"
        )

with col_right:
    st.subheader("🛒 Danh sách món đã gọi")

    if not st.session_state.cart:
        st.warning(
            "Giỏ hàng hiện đang trống. "
            "Vui lòng chọn món ở cột bên trái."
        )

    else:
        df_cart = pd.DataFrame(st.session_state.cart)

        st.dataframe(
            df_cart[
                [
                    "Tên món", "Size", "Topping",
                    "Số lượng", "Đơn giá", "Thành tiền"
                ]
            ],
            use_container_width=True,
            hide_index=True
        )

        if st.button("🗑️ Xóa tất cả món"):
            st.session_state.cart = []
            st.session_state.invoice_paid = False
            st.session_state.applied_voucher = ""
            st.session_state.voucher_code = ""
            st.rerun()

        st.markdown("---")

        total_price = calculate_total(st.session_state.cart)

        st.markdown(f"### Tổng tiền: {total_price:,} VNĐ")

        discount = st.number_input(
            "Giảm giá (%):",
            min_value=0,
            max_value=100,
            value=0,
            step=5
        )

        # -------------------------------------------------
        # NHẬP VOUCHER
        # -------------------------------------------------
        st.markdown("#### 🎟️ Áp dụng voucher")

        voucher_input = st.text_input(
            "Nhập mã giảm giá:",
            key="voucher_code",
            placeholder="           "
        )

        if st.button("🎫 Áp dụng mã", use_container_width=True):
            code = voucher_input.strip().upper()

            voucher_amount, message = calculate_voucher_discount(
                st.session_state.cart,
                total_price,
                code
            )

            if message == "Áp dụng voucher thành công!":
                st.session_state.applied_voucher = code
                st.success(message)
            else:
                st.session_state.applied_voucher = ""
                st.warning(message)

        applied_code = st.session_state.applied_voucher

        voucher_discount = 0

        if applied_code:
            voucher_discount, voucher_message = calculate_voucher_discount(
                st.session_state.cart,
                total_price,
                applied_code
            )

            if voucher_message != "Áp dụng voucher thành công!":
                voucher_discount = 0
                st.session_state.applied_voucher = ""
                applied_code = ""

        # Áp dụng giảm giá thường và voucher tuần tự
        after_discount = int(
            total_price * (1 - discount / 100)
        )

        final_price = max(
            0,
            after_discount - voucher_discount
        )

        if discount > 0:
            st.markdown(
                f"Giảm giá thường: **{discount}%**"
            )

        if applied_code:
            st.markdown(
                f"Voucher: **{applied_code}** "
                f"(-{voucher_discount:,} VNĐ)"
            )

        st.markdown(f"### Tổng thanh toán: {final_price:,} VNĐ")

        if st.button(
            "💳 XÁC NHẬN THANH TOÁN",
            type="primary",
            use_container_width=True
        ):
            st.session_state.invoice_paid = True
            st.balloons()

# ---------------------------------------------------------
# XUẤT HÓA ĐƠN KHI ĐÃ THANH TOÁN
# ---------------------------------------------------------
if st.session_state.get("invoice_paid") and st.session_state.cart:
    st.markdown("---")
    st.success(
        "🎉 Thanh toán thành công! "
        "Dưới đây là hóa đơn chi tiết:"
    )

    # Tính lại số tiền để hóa đơn luôn khớp với giỏ hàng
    total_price = calculate_total(st.session_state.cart)

    discount = st.session_state.get("discount_value", 0)

    # Lấy giá trị giảm giá đang hiển thị từ widget
    # Khi thanh toán, Streamlit lưu giá trị widget theo key.
    # Dùng key riêng để tránh mất giá trị khi chạy lại ứng dụng.

    # Phần hóa đơn sử dụng lại mức giảm giá của giao diện
    try:
        discount = st.session_state.get("discount_input", discount)
    except Exception:
        pass

    # Tính toán lại với dữ liệu hiện có
    after_discount = int(total_price * (1 - discount / 100))

    applied_code = st.session_state.applied_voucher

    voucher_discount, _ = calculate_voucher_discount(
        st.session_state.cart,
        total_price,
        applied_code
    ) if applied_code else (0, "")

    final_price = max(0, after_discount - voucher_discount)

    invoice_box = st.container(border=True)

    with invoice_box:
        st.markdown(
            "<h2 style='text-align:center; color:#FF4B4B;'>"
            "🧋 HÓA ĐƠN BÁN HÀNG - ZZ TEA"
            "</h2>",
            unsafe_allow_html=True
        )

        st.write(
            f"**Thời gian:** "
            f"{datetime.now().strftime('%d/%m/%Y %H:%M:%S')}"
        )

        st.write(
            f"**Khách hàng:** "
            f"{customer_name if customer_name else 'Khách vãng lai'}"
        )

        st.table(
            pd.DataFrame(st.session_state.cart)[
                [
                    "Tên món", "Size", "Đường", "Đá",
                    "Topping", "Số lượng", "Thành tiền"
                ]
            ]
        )

        st.write(f"**Tổng tiền món:** {total_price:,} VNĐ")
        st.write(f"**Giảm giá thường:** {discount}%")
        st.write(f"**Giảm giá voucher:** {voucher_discount:,} VNĐ")

        if applied_code:
            st.write(f"**Mã voucher:** {applied_code}")

        st.markdown(
            f"### TỔNG THANH TOÁN: "
            f"<span style='color:red'>{final_price:,} VNĐ</span>",
            unsafe_allow_html=True
        )

    txt_data = create_txt_invoice(
        customer_name,
        st.session_state.cart,
        total_price,
        discount,
        voucher_discount,
        final_price,
        applied_code
    )

    col_dl1, col_dl2 = st.columns(2)

    with col_dl1:
        st.download_button(
            label="📥 Tải hóa đơn (.TXT)",
            data=txt_data,
            file_name=(
                f"HoaDon_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
            ),
            mime="text/plain",
            use_container_width=True
        )

    with col_dl2:
        if st.button(
            "🔄 Tạo đơn hàng mới",
            use_container_width=True
        ):
            st.session_state.cart = []
            st.session_state.invoice_paid = False
            st.session_state.applied_voucher = ""
            st.session_state.voucher_code = ""
            st.rerun()
