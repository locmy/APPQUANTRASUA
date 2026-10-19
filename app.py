import streamlit as st
import random
from datetime import datetime
from pathlib import Path
st.image("Screenshot_20261017_170859_Hypic.jpg")

# =========================================================
# CẤU HÌNH TRANG
# =========================================================
st.set_page_config(
    page_title="Hệ Thống Tính Tiền Trà Sữa",
    page_icon="🧋",
    layout="wide"
)

# =========================================================

# =========================================================
IMAGE_URLS = {
    "Trà Sữa Truyền Thống": "IMG_be364db8-ba92-4de2-94b3-e19fabc24223~2.jpg",
    "Trà Sữa Trân Châu Đường Đen": "Screenshot_20261019_173653_Hypic.jpg",
    "Trà Sữa Thái Xanh": "retouch_2026101917475806.jpg",
    "Trà Sữa Ô Long": "IMG_188e1380-3bc7-465b-bd10-5705d2e84719.jpg",
    "Matcha Latte": "IMG_9ea76e06-da48-4efb-8b28-972ef95d5262.jpg",
    "Trà Đào Cam Sả": "IMG_7bd03c4e-527a-48b3-8a47-703262a6a50b.jpg",
    "Trà Atiso Hạt Chia": "retouch_2026101918013212.jpg",
    "Lục Trà Lựu Nha Đam": "Screenshot_20261019_180339_Google.jpg",
    "Trà Dâu Tằm": "IMG_90800819-5085-4b40-b37b-4c4a278068d7.jpg",
}

# =========================================================
# Danh sách menu & giá (VND)
# =========================================================
MENU = {
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

BEST_SELLERS = [
    "Trà Sữa Trân Châu Đường Đen",
    "Matcha Latte",
    "Lục Trà Lựu Nha Đam",
]

SIZE_PRICES = {
    "S - Vừa": 0,
    "M - Lớn": 5000,
    "L - Đặc biệt": 10000,
}

TOPPINGS = {
    "Trân châu đen": 5000,
    "Trân châu trắng": 5000,
    "Thạch trái cây": 5000,
    "Pudding trứng": 10000,
    "Kem Cheese": 10000,
}

SUGAR_LEVELS = [
    "100% (Bình thường)",
    "70%",
    "50%",
    "30%",
    "0% (Không đường)",
]

ICE_LEVELS = [
    "100% (Bình thường)",
    "70%",
    "50%",
    "30%",
    "0% (Không đá)",
]

# =========================================================
# VOUCHER
# ZZ3: giảm 3%
# ZZ5: giảm 5% khi mua từ 2 ly
# ZZ1: mua 1 tặng 1 cùng món
# ZZ0: chúc may mắn
# =========================================================
VOUCHERS = {
    "ZZ3": {
        "name": "Giảm 3%",
        "type": "percent",
        "value": 3,
        "min_quantity": 1,
    },
    "ZZ5": {
        "name": "Giảm 5% bill từ 2 ly",
        "type": "percent",
        "value": 5,
        "min_quantity": 2,
    },
    "ZZ1": {
        "name": "Mua 1 tặng 1",
        "type": "ZZ",
        "value": 0,
        "min_quantity": 2,
    },
    "ZZ0": {
        "name": "Chúc may mắn",
        "type": "ZZ",
        "value": 0,
        "min_quantity": 1,
    },
}

LUCKY_PRIZES = [
    "Giảm 3%",
    "Chúc may mắn",
    "Giảm 5% bill từ 2 ly",
    "Chúc may mắn",
    "Mua 1 tặng 1",
    "Chúc may mắn",
]

# =========================================================
# SESSION STATE
# =========================================================
if "cart" not in st.session_state:
    st.session_state.cart = []

if "invoice" not in st.session_state:
    st.session_state.invoice = None

if "lucky_prize" not in st.session_state:
    st.session_state.lucky_prize = ""

if "voucher_code" not in st.session_state:
    st.session_state.voucher_code = ""

if "customer_name" not in st.session_state:
    st.session_state.customer_name = ""

# =========================================================
# HÀM HỖ TRỢ
# =========================================================
def format_money(amount):
    return f"{int(round(amount)):,} đ".replace(",", ".")


def get_image_path(product_name):
    relative_path = IMAGE_URLS.get(product_name, "")
    path = Path(__file__).parent / relative_path
    if relative_path and path.is_file():
        return str(path)
    return None


def cart_quantity(cart):
    return sum(item["quantity"] for item in cart)


def calculate_subtotal(cart):
    return sum(item["unit_price"] * item["quantity"] for item in cart)


def calculate_bogo_discount(cart):
    """Tặng một ly cùng món cho mỗi cặp ly đủ điều kiện.
    Giá ly tặng là giá cơ bản của món, không tính size/topping.
    """
    discount = 0
    for item in cart:
        free_cups = item["quantity"] // 2
        discount += free_cups * MENU[item["name"]]
    return discount


def calculate_totals(cart, discount_percent=0, voucher_code=""):
    subtotal = calculate_subtotal(cart)
    total_quantity = cart_quantity(cart)
    bogo_discount = 0
    percent_discount = 0
    voucher_message = "Không áp dụng voucher"

    code = voucher_code.strip().upper()
    voucher = VOUCHERS.get(code)

    if voucher:
        if total_quantity < voucher["min_quantity"]:
            voucher_message = (
                f"Voucher {code} yêu cầu tối thiểu "
                f"{voucher['min_quantity']} ly."
            )
        elif voucher["type"] == "ZZ":
            bogo_discount = calculate_ZZ_discount(cart)
            voucher_message = "Đã áp dụng voucher Mua 1 tặng 1."
        elif voucher["type"] == "percent":
            percent_discount += voucher["value"]
            voucher_message = (
                f"Đã áp dụng voucher {voucher['name']}."
            )
    elif code:
        voucher_message = "Mã voucher không hợp lệ."

    # Phần trăm giảm giá nhập thủ công
    manual_discount = max(0, min(float(discount_percent), 100))
    percent_discount += manual_discount
    percent_discount = min(percent_discount, 100)

    amount_after_bogo = max(0, subtotal - bogo_discount)
    percent_amount = amount_after_bogo * percent_discount / 100
    final_total = max(0, amount_after_bogo - percent_amount)

    return {
        "subtotal": subtotal,
        "ZZ_discount": ZZ_discount,
        "percent_discount": percent_discount,
        "percent_amount": percent_amount,
        "final_total": final_total,
        "voucher_message": voucher_message,
    }


def reset_order():
    st.session_state.cart = []
    st.session_state.invoice = None
    st.session_state.lucky_prize = ""
    st.session_state.voucher_code = ""
    st.session_state.customer_name = ""
    st.session_state.discount_input = 0


# =========================================================
# GIAO DIỆN
# =========================================================
st.title("🧋 Tiệm trà ZZZ")
st.subheader("Hệ thống gọi món và tính tiền trà sữa")
st.caption("Chọn món yêu thích, tùy chỉnh theo khẩu vị và thanh toán.")

menu_tab, order_tab, payment_tab = st.tabs(
    ["📋 Menu", "🛒 Giỏ hàng", "💳 Thanh toán"]
)

# =========================================================
# TAB 1: MENU
# =========================================================
with menu_tab:
    st.header("📋 Menu trà sữa")

    st.write("Giá size S là giá cơ bản. Size M thêm 5.000 đ, size L thêm 10.000 đ.")

    columns = st.columns(3)

    for index, (name, price) in enumerate(MENU.items()):
        with columns[index % 3]:
            with st.container(border=True):
                image_path = get_image_path(name)

                if image_path:
                    st.image(image_path, use_container_width=True)
                else:
                    st.info("Chưa tìm thấy ảnh. Kiểm tra thư mục images trên GitHub.")

                if name in BEST_SELLERS:
                    st.markdown(f"**{name}**  \n<small>best seller ❤️‍🔥</small>", unsafe_allow_html=True)
                else:
                    st.markdown(f"**{name}**")

                st.write(f"Giá từ **{format_money(price)}**")

                with st.form(f"form_{index}"):
                    size = st.selectbox(
                        "Chọn size",
                        list(SIZE_PRICES.keys()),
                        key=f"size_{index}",
                    )

                    topping_choices = st.multiselect(
                        "Chọn topping",
                        list(TOPPINGS.keys()),
                        key=f"toppings_{index}",
                    )

                    sugar = st.selectbox(
                        "Đường",
                        SUGAR_LEVELS,
                        index=0,
                        key=f"sugar_{index}",
                    )

                    ice = st.selectbox(
                        "Đá",
                        ICE_LEVELS,
                        index=0,
                        key=f"ice_{index}",
                    )

                    quantity = st.number_input(
                        "Số lượng",
                        min_value=1,
                        max_value=50,
                        value=1,
                        step=1,
                        key=f"quantity_{index}",
                    )

                    unit_price = (
                        price
                        + SIZE_PRICES[size]
                        + sum(TOPPINGS[t] for t in topping_choices)
                    )

                    st.caption(
                        f"Đơn giá: {format_money(unit_price)}"
                    )

                    add_button = st.form_submit_button(
                        "➕ Thêm vào giỏ hàng",
                        use_container_width=True,
                    )

                    if add_button:
                        st.session_state.cart.append({
                            "name": name,
                            "base_price": price,
                            "size": size,
                            "toppings": topping_choices.copy(),
                            "sugar": sugar,
                            "ice": ice,
                            "quantity": int(quantity),
                            "unit_price": unit_price,
                        })
                        st.session_state.invoice = None
                        st.success(f"Đã thêm {name} vào giỏ hàng!")

# =========================================================
# TAB 2: GIỎ HÀNG
# =========================================================
with order_tab:
    st.header("🛒 Giỏ hàng")

    if not st.session_state.cart:
        st.info("Giỏ hàng đang trống. Hãy chọn món ở tab Menu.")
    else:
        for index, item in enumerate(st.session_state.cart):
            with st.container(border=True):
                col1, col2 = st.columns([4, 1])

                with col1:
                    st.markdown(f"**{item['name']}**")
                    st.write(f"Size: {item['size']}")
                    st.write(
                        "Topping: "
                        + (", ".join(item["toppings"]) if item["toppings"] else "Không")
                    )
                    st.write(f"Đường: {item['sugar']} | Đá: {item['ice']}")
                    st.write(f"Số lượng: {item['quantity']}")
                    st.write(
                        f"Thành tiền: **{format_money(item['unit_price'] * item['quantity'])}**"
                    )

                with col2:
                    if st.button("🗑️ Xóa", key=f"remove_{index}"):
                        st.session_state.cart.pop(index)
                        st.session_state.invoice = None
                        st.rerun()

        subtotal = calculate_subtotal(st.session_state.cart)
        st.divider()
        st.metric("Tạm tính", format_money(subtotal))

        col_a, col_b = st.columns(2)

        with col_a:
            if st.button("🧹 Xóa toàn bộ giỏ hàng", use_container_width=True):
                st.session_state.cart = []
                st.session_state.invoice = None
                st.rerun()

        with col_b:
            if st.button("➡️ Đi đến thanh toán", use_container_width=True):
                st.info("Mở tab Thanh toán để hoàn tất đơn hàng.")

# =========================================================
# TAB 3: THANH TOÁN
# =========================================================
with payment_tab:
    st.header("💳 Thanh toán")

    if not st.session_state.cart:
        st.info("Bạn chưa có món nào trong giỏ hàng.")
    else:
        customer_name = st.text_input(
            "Tên khách hàng",
            key="customer_name",
            placeholder="Nhập tên khách hàng",
        )

        st.subheader("🎡 Vòng quay may mắn")
        st.write("Hãy thử vận may để nhận một ưu đãi.")

        if st.button("🎲 Quay thưởng", use_container_width=True):
            prize = random.choice(LUCKY_PRIZES)
            st.session_state.lucky_prize = prize

            if prize == "Giảm 3%":
                st.session_state.voucher_code = "ZZ3"
            elif prize == "Giảm 5% bill từ 2 ly":
                st.session_state.voucher_code = "ZZ5"
            elif prize == "Mua 1 tặng 1":
                st.session_state.voucher_code = "ZZ1"
            else:
                st.session_state.voucher_code = ""

            st.rerun()

        if st.session_state.lucky_prize:
            if st.session_state.lucky_prize == "chúc may mắn":
                st.info("🍀 Chúc bạn may mắn lần sau!")
            else:
                st.success(f"🎉 Bạn nhận được: {st.session_state.lucky_prize}")
                
        voucher_code = st.text_input(
            "Mã voucher",
            key="voucher_code",
            placeholder="        ",
        )

        discount_input = st.number_input(
            "Giảm giá thêm (%)",
            min_value=0,
            max_value=100,
            value=0,
            step=1,
            key="discount_input",
        )

        totals = calculate_totals(
            st.session_state.cart,
            discount_percent=discount_input,
            voucher_code=voucher_code,
        )

        st.divider()
        st.subheader("🧾 Chi tiết hóa đơn")

        st.write(f"**Tạm tính:** {format_money(totals['subtotal'])}")
        st.write(
            f"**Giảm giá Mua 1 tặng 1:** "
            f"{format_money(totals['ZZ_discount'])}"
        )
        st.write(
            f"**Tổng tỷ lệ giảm giá:** "
            f"{totals['percent_discount']:g}%"
        )
        st.write(
            f"**Tiền giảm theo phần trăm:** "
            f"{format_money(totals['percent_amount'])}"
        )
        st.caption(totals["voucher_message"])

        st.markdown(
            f"### Tổng thanh toán: {format_money(totals['final_total'])}"
        )

        if st.button(
            "✅ Xác nhận thanh toán",
            type="primary",
            use_container_width=True,
        ):
            if not customer_name.strip():
                st.warning("Vui lòng nhập tên khách hàng.")
            else:
                st.session_state.invoice = {
                    "customer": customer_name.strip(),
                    "created_at": datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
                    "items": [item.copy() for item in st.session_state.cart],
                    "subtotal": totals["subtotal"],
                    "bogo_discount": totals["bogo_discount"],
                    "percent_discount": totals["percent_discount"],
                    "percent_amount": totals["percent_amount"],
                    "final_total": totals["final_total"],
                    "voucher_code": voucher_code.strip().upper(),
                    "voucher_message": totals["voucher_message"],
                }
                st.balloons()
                st.success("Thanh toán thành công!")

# =========================================================
# HÓA ĐƠN SAU THANH TOÁN
# =========================================================
if st.session_state.invoice:
    invoice = st.session_state.invoice

    st.divider()
    st.header("🧾 HÓA ĐƠN BOBA TEA")

    st.write(f"**Khách hàng:** {invoice['customer']}")
    st.write(f"**Thời gian:** {invoice['created_at']}")

    for index, item in enumerate(invoice["items"], start=1):
        toppings = ", ".join(item["toppings"]) if item["toppings"] else "Không"
        st.write(
            f"{index}. {item['name']} | {item['size']} | "
            f"Số lượng: {item['quantity']} | "
            f"Topping: {toppings} | "
            f"{format_money(item['unit_price'] * item['quantity'])}"
        )

    st.divider()
    st.write(f"Tạm tính: {format_money(invoice['subtotal'])}")
    st.write(f"Giảm Mua 1 tặng 1: {format_money(invoice['bogo_discount'])}")
    st.write(f"Tỷ lệ giảm giá: {invoice['percent_discount']:g}%")
    st.write(f"Tiền giảm theo phần trăm: {format_money(invoice['percent_amount'])}")
    st.write(f"Mã voucher: {invoice['voucher_code'] or 'Không sử dụng'}")
    st.caption(invoice["voucher_message"])

    st.markdown(
        f"## Tổng thanh toán: {format_money(invoice['final_total'])}"
    )
    st.success("Cảm ơn bạn đã ủng hộ BOBA TEA! 🧋")

    invoice_text = [
        "========== HÓA ĐƠN BOBA TEA ==========",
        f"Khách hàng: {invoice['customer']}",
        f"Thời gian: {invoice['created_at']}",
        "",
    ]

    for index, item in enumerate(invoice["items"], start=1):
        invoice_text.append(
            f"{index}. {item['name']} | {item['size']} | "
            f"Số lượng: {item['quantity']} | "
            f"Đơn giá: {format_money(item['unit_price'])} | "
            f"Thành tiền: {format_money(item['unit_price'] * item['quantity'])}"
        )
        invoice_text.append(f"   Topping: {', '.join(item['toppings']) or 'Không'}")
        invoice_text.append(f"   Đường: {item['sugar']} | Đá: {item['ice']}")

    invoice_text.extend([
        "",
        f"Tạm tính: {format_money(invoice['subtotal'])}",
        f"Giảm Mua 1 tặng 1: {format_money(invoice['bogo_discount'])}",
        f"Tỷ lệ giảm giá: {invoice['percent_discount']:g}%",
        f"Tiền giảm theo phần trăm: {format_money(invoice['percent_amount'])}",
        f"Mã voucher: {invoice['voucher_code'] or 'Không sử dụng'}",
        f"Tổng thanh toán: {format_money(invoice['final_total'])}",
        "",
        "Cảm ơn quý khách!",
    ])

    st.download_button(
        label="📥 Tải hóa đơn TXT",
        data="\n".join(invoice_text),
        file_name="hoa_don_boba_tea.txt",
        mime="text/plain",
        use_container_width=True,
    )

    if st.button("🆕 Tạo đơn hàng mới", use_container_width=True):
        reset_order()
        st.rerun()
