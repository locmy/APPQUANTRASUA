
import streamlit as st
import pandas as pd
import random
from datetime import datetime
from pathlib import Path
import html

# =========================================================
# 1. CẤU HÌNH TRANG
# =========================================================
st.set_page_config(
    page_title="QUÁN TRÀ SỮA ZZZ",
    page_icon="🧋",
    layout="wide"
)

st.markdown("""
<style>
.stApp {
    background-color: #fffaf5;
}
h1, h2, h3 {
    color: #743c28;
}
div.stButton > button {
    border-radius: 10px;
    font-weight: 600;
}
div[data-testid="stMetric"] {
    background: #fff1e5;
    padding: 12px;
    border-radius: 12px;
}
</style>
""", unsafe_allow_html=True)

# =========================================================
# 2. MENU VÀ GIÁ BÁN
# =========================================================
MENU_TEA = {
    "Trà Sữa Truyền Thống": 30000,
    "Trà Sữa Trân Châu Đường Đen": 35000,
    "Trà Sữa Thái Xanh": 32000,
    "Trà Sữa Ô Long": 35000,
    "Matcha Latte": 38000,
    "Trà Đào Cam Sả": 35000,
    "Trà Atiso Hạt Chia": 35000,
    "Lục Trà Lựu Nha Đam": 35000,
    "Trà Dâu Tằm": 32000,
}

# Các ảnh đặt cùng thư mục với app.py
MENU_IMAGES = {
    "Trà Sữa Truyền Thống":
        "IMG_be364db8-ba92-4de2-94b3-e19fabc24223~2.jpg",

    "Trà Sữa Trân Châu Đường Đen":
        "Screenshot_20261019_173653_Hypic.jpg",

    "Trà Sữa Thái Xanh":
        "retouch_2026101917475806.jpg",

    "Trà Sữa Ô Long":
        "IMG_188e1380-3bc7-465b-bd10-5705d2e84719.jpg",

    "Matcha Latte":
        "IMG_9ea76e06-da48-4efb-8b28-972ef95d5262.jpg",

    "Trà Đào Cam Sả":
        "IMG_7bd03c4e-527a-48b3-8a47-703262a6a50b.jpg",

    "Trà Atiso Hạt Chia":
        "retouch_2026101918013212.jpg",

    "Lục Trà Lựu Nha Đam":
        "Screenshot_20261019_180339_Google.jpg",

    "Trà Dâu Tằm":
        "IMG_90800819-5085-4b40-b37b-4c4a278068d7.jpg",
}

BEST_SELLERS = [
    "Trà Sữa Trân Châu Đường Đen",
    "Matcha Latte",
    "Lục Trà Lựu Nha Đam",
]

SIZE_OPTIONS = {
    "S (Vừa)": 0,
    "M (Lớn)": 5000,
    "L (Đặc biệt)": 10000,
}

TOPPING_OPTIONS = {
    "Trân châu đen": 5000,
    "Trân châu trắng": 5000,
    "Thạch trái cây": 5000,
    "Pudding trứng": 10000,
    "Kem Cheese": 10000,
}

SUGAR_LEVELS = [
    "100% (Bình thường)", "70%", "50%", "30%", "0% (Không đường)"
]

ICE_LEVELS = [
    "100% (Bình thường)", "70%", "50%", "30%", "0% (Không đá)"
]

# =========================================================
# 3. KHỞI TẠO SESSION STATE
# =========================================================
defaults = {
    "cart": [],
    "invoice_paid": False,
    "selected_tea": "Trà Sữa Truyền Thống",
    "wheel_prize": None,
    "wheel_spun": False,
    "applied_voucher": "",
    "voucher_input": "",
    "paid_invoice": None,
}

for key, value in defaults.items():
    if key not in st.session_state:
        st.session_state[key] = value

# =========================================================
# 4. HÀM HỖ TRỢ
# =========================================================
def money(value):
    return f"{int(value):,} VNĐ"


def image_or_placeholder(name, width=None):
    path = Path(MENU_IMAGES[name])

    if path.is_file():
        st.image(
            str(path),
            caption=name,
            use_container_width=(width is None),
            width=width
        )
    else:
        st.warning(
            f"Chưa tìm thấy ảnh: {path.name}. "
            "Hãy kiểm tra vị trí và tên file trên GitHub."
        )


def create_txt_invoice(
    customer_name, cart, total_amount,
    manual_discount, voucher_name,
    voucher_discount, final_amount, timestamp
):
    content = "=" * 45 + "\n"
    content += "HÓA ĐƠN BÁN HÀNG - QUÁN TRÀ SỮA ZZZ\n"
    content += "=" * 45 + "\n"
    content += f"Thời gian: {timestamp}\n"
    content += (
        f"Khách hàng: {customer_name.strip() or 'Khách vãng lai'}\n"
    )
    content += "-" * 45 + "\n"

    for i, item in enumerate(cart, 1):
        content += f"{i}. {item['Tên món']} - Size {item['Size']}\n"
        content += f"   Đường: {item['Đường']} | Đá: {item['Đá']}\n"
        content += f"   Topping: {item['Topping']}\n"
        content += (
            f"   {item['Số lượng']} x {money(item['Đơn giá'])}"
            f" = {money(item['Thành tiền'])}\n"
        )

    content += "-" * 45 + "\n"
    content += f"Tổng tiền món: {money(total_amount)}\n"
    content += f"Giảm giá thủ công: {manual_discount}%\n"
    content += f"Voucher: {voucher_name}\n"
    content += f"Tiền giảm từ voucher: {money(voucher_discount)}\n"
    content += f"TỔNG THANH TOÁN: {money(final_amount)}\n"
    content += "=" * 45 + "\n"
    content += "Cảm ơn quý khách và hẹn gặp lại!\n"
    return content


# =========================================================
# 5. TIÊU ĐỀ VÀ ẢNH BÌA
# =========================================================
st.title("🧋 QUÁN TRÀ SỮA ZZZ")
st.markdown("### Thưởng thức hương vị yêu thích của bạn!")
st.markdown("---")

cover = Path("Screenshot_20261017_170859_Hypic.jpg")
if cover.is_file():
    st.image(str(cover), use_container_width=True)

# =========================================================
# 6. BEST SELLER
# =========================================================
st.markdown("## ⭐ BEST SELLER - MÓN NỔI BẬT")

best_cols = st.columns(3)

for i, tea in enumerate(BEST_SELLERS):
    with best_cols[i]:
        image_or_placeholder(tea)
        st.markdown(f"**🔥 {tea}**")
        st.write(f"Giá từ **{money(MENU_TEA[tea])}**")

        if st.button(
            "Chọn món này",
            key=f"best_seller_{i}",
            use_container_width=True
        ):
            st.session_state.selected_tea = tea
            st.rerun()

st.markdown("---")

# =========================================================
# 7. VÒNG QUAY MAY MẮN
# =========================================================
st.markdown("## 🎡 VÒNG QUAY MAY MẮN")
st.write("Quay để thử vận may và nhận ưu đãi nhé!")

PRIZES = [
    {"name": "Giảm 3%", "code": "QUAY3"},
    {"name": "Chúc bạn may mắn", "code": ""},
    {"name": "Giảm 5% cho bill từ 2 ly", "code": "QUAY5"},
    {"name": "Chúc bạn may mắn", "code": ""},
    {"name": "Mua 1 tặng 1", "code": "MUA1TANG1"},
    {"name": "Chúc bạn may mắn", "code": ""},
]

st.markdown("""
<div style="text-align:center; padding:10px;">
  <div style="
    width:250px;height:250px;max-width:75vw;
    border-radius:50%;margin:auto;
    border:8px solid #f5d49b;
    background:conic-gradient(
      #ff7675 0deg 60deg,
      #ffeaa7 60deg 120deg,
      #74b9ff 120deg 180deg,
      #a29bfe 180deg 240deg,
      #55efc4 240deg 300deg,
      #fab1a0 300deg 360deg
    );
    display:flex;align-items:center;justify-content:center;
    box-shadow:0 3px 12px #d8bca5;
    font-size:22px;font-weight:bold;color:#633;
  ">🎁 ZZZ 🎁<br>LUCKY WHEEL</div>
  <p style="color:#8a6b5c;">6 phần thưởng đang chờ bạn!</p>
</div>
""", unsafe_allow_html=True)

if not st.session_state.wheel_spun:
    if st.button(
        "🎡 QUAY NGAY",
        type="primary",
        use_container_width=True
    ):
        prize = random.choice(PRIZES)
        st.session_state.wheel_prize = prize
        st.session_state.wheel_spun = True

        if prize["code"]:
            st.session_state.voucher_input = prize["code"]

        st.rerun()
else:
    prize = st.session_state.wheel_prize

    if prize and prize["code"]:
        st.success(f"🎉 Bạn nhận được: {prize['name']}!")
        st.write(f"Mã voucher của bạn: **{prize['code']}**")
        st.caption(
            "Mã đã được điền vào ô voucher. "
            "Bạn cần áp dụng mã khi thanh toán."
        )
    else:
        st.info("😊 Chúc bạn may mắn lần sau!")

    if st.button("🔄 Chơi lại vòng quay"):
        st.session_state.wheel_spun = False
        st.session_state.wheel_prize = None
        st.rerun()

st.markdown("---")

# =========================================================
# 8. MENU ĐẶT MÓN VÀ GIỎ HÀNG
# =========================================================
col_left, col_right = st.columns([1.05, 0.95])

with col_left:
    st.subheader("📝 Thông tin đơn hàng")

    customer_name = st.text_input(
        "Tên khách hàng:",
        placeholder="Nhập tên khách hàng..."
    )

    st.markdown("#### Chọn món nước")

    selected_tea = st.selectbox(
        "Loại trà sữa:",
        list(MENU_TEA.keys()),
        key="selected_tea"
    )

    image_or_placeholder(selected_tea, width=300)

    st.write(f"**Giá gốc:** {money(MENU_TEA[selected_tea])}")

    col_item, col_qty = st.columns([2, 1])

    with col_item:
        selected_size = st.selectbox(
            "Size:", list(SIZE_OPTIONS.keys())
        )

    with col_qty:
        quantity = st.number_input(
            "Số lượng:", min_value=1, max_value=100,
            value=1, step=1
        )

    c_size, c_sugar, c_ice = st.columns(3)

    with c_sugar:
        selected_sugar = st.selectbox(
            "Mức đường:", SUGAR_LEVELS
        )

    with c_ice:
        selected_ice = st.selectbox(
            "Mức đá:", ICE_LEVELS
        )

    selected_toppings = st.multiselect(
        "Topping (có thể chọn nhiều):",
        list(TOPPING_OPTIONS.keys())
    )

    base_price = MENU_TEA[selected_tea]
    size_price = SIZE_OPTIONS[selected_size]
    topping_price = sum(
        TOPPING_OPTIONS[t] for t in selected_toppings
    )

    unit_price = base_price + size_price + topping_price
    item_total = unit_price * quantity

    st.info(
        f"Đơn giá mỗi ly: **{money(unit_price)}**\n\n"
        f"Thành tiền: **{money(item_total)}**"
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

        st.session_state.cart.append({
            "Tên món": selected_tea,
            "Size": selected_size.split()[0],
            "Đường": selected_sugar.split()[0],
            "Đá": selected_ice.split()[0],
            "Topping": topping_str,
            "Đơn giá": unit_price,
            "Số lượng": int(quantity),
            "Thành tiền": item_total,
        })

        st.session_state.invoice_paid = False
        st.session_state.paid_invoice = None
        st.session_state.applied_voucher = ""
        st.toast(f"Đã thêm {quantity} ly vào giỏ hàng!", icon="✅")

with col_right:
    st.subheader("🛒 Giỏ hàng")

    if not st.session_state.cart:
        st.warning("Giỏ hàng đang trống. Hãy chọn món ở bên trái.")
    else:
        df_cart = pd.DataFrame(st.session_state.cart)

        st.dataframe(
            df_cart[
                ["Tên món", "Size", "Topping",
                 "Số lượng", "Đơn giá", "Thành tiền"]
            ],
            use_container_width=True,
            hide_index=True
        )

        if st.button("🗑️ Xóa tất cả món", use_container_width=True):
            st.session_state.cart = []
            st.session_state.invoice_paid = False
            st.session_state.paid_invoice = None
            st.session_state.applied_voucher = ""
            st.rerun()

        st.markdown("---")

        total_price = int(df_cart["Thành tiền"].sum())
        total_cups = sum(
            item["Số lượng"] for item in st.session_state.cart
        )

        st.markdown("### 🎟️ Ưu đãi và thanh toán")

        manual_discount = st.number_input(
            "Giảm giá thủ công (%):",
            min_value=0,
            max_value=100,
            value=0,
            step=5,
            key="manual_discount"
        )

        # Voucher được khai báo và kiểm tra tại đây
        VOUCHERS = {
            "QUAY3": {
                "type": "percent",
                "value": 3,
                "description": "Giảm 3%"
            },
            "BOBA3": {
                "type": "percent",
                "value": 3,
                "description": "Giảm 3%"
            },
            "QUAY5": {
                "type": "percent",
                "value": 5,
                "min_cups": 2,
                "description": "Giảm 5% cho đơn từ 2 ly"
            },
            "BOBA5": {
                "type": "percent",
                "value": 5,
                "min_cups": 2,
                "description": "Giảm 5% cho đơn từ 2 ly"
            },
            "MUA1TANG1": {
                "type": "bogo",
                "description": "Mua 1 tặng 1"
            },
        }

        voucher_code = st.text_input(
            "Nhập mã voucher:",
            key="voucher_input",
            placeholder="QUAY3 / QUAY5 / MUA1TANG1"
        ).strip().upper()

        if st.button("🎟️ Áp dụng voucher", use_container_width=True):
            voucher = VOUCHERS.get(voucher_code)

            if not voucher:
                st.session_state.applied_voucher = ""
                st.error("Mã voucher không hợp lệ.")
            elif total_cups < voucher.get("min_cups", 0):
                st.session_state.applied_voucher = ""
                st.error("Voucher này yêu cầu mua ít nhất 2 ly.")
            elif voucher["type"] == "bogo" and total_cups < 2:
                st.session_state.applied_voucher = ""
                st.error("Mua 1 tặng 1 cần có ít nhất 2 ly.")
            else:
                st.session_state.applied_voucher = voucher_code
                st.session_state.invoice_paid = False
                st.session_state.paid_invoice = None
                st.success("Áp dụng voucher thành công!")

        # Tính tiền
        manual_discount_amount = int(
            total_price * manual_discount / 100
        )

        subtotal = max(0, total_price - manual_discount_amount)

        active_code = st.session_state.applied_voucher
        voucher_discount = 0
        voucher_label = "Không áp dụng"

        if active_code in VOUCHERS:
            voucher = VOUCHERS[active_code]

            if total_cups < voucher.get("min_cups", 0):
                voucher_label = "Không đủ điều kiện voucher"
                st.session_state.applied_voucher = ""
                active_code = ""
            elif voucher["type"] == "percent":
                voucher_discount = int(
                    subtotal * voucher["value"] / 100
                )
                voucher_label = (
                    f"{voucher['description']} ({active_code})"
                )
            elif voucher["type"] == "bogo":
                # Mô phỏng tặng một ly có đơn giá thấp nhất.
                cheapest_price = min(
                    item["Đơn giá"]
                    for item in st.session_state.cart
                )
                voucher_discount = min(subtotal, cheapest_price)
                voucher_label = f"Mua 1 tặng 1 ({active_code})"

        final_price = max(0, subtotal - voucher_discount)

        st.write(f"Tổng tiền món: **{money(total_price)}**")
        st.write(
            f"Giảm giá thủ công: **{money(manual_discount_amount)}**"
        )
        st.write(f"Voucher: **{voucher_label}**")
        st.write(f"Giảm từ voucher: **{money(voucher_discount)}**")

        st.markdown(f"## Tổng thanh toán: {money(final_price)}")

        if st.button(
            "💳 XÁC NHẬN THANH TOÁN",
            type="primary",
            use_container_width=True
        ):
            timestamp = datetime.now().strftime("%d/%m/%Y %H:%M:%S")

            st.session_state.paid_invoice = {
                "customer_name": customer_name,
                "cart": [item.copy() for item in st.session_state.cart],
                "total_price": total_price,
                "manual_discount": manual_discount,
                "manual_discount_amount": manual_discount_amount,
                "voucher_label": voucher_label,
                "voucher_discount": voucher_discount,
                "final_price": final_price,
                "timestamp": timestamp,
            }

            st.session_state.invoice_paid = True
            st.balloons()
            st.rerun()

# =========================================================
# 9. HÓA ĐƠN VÀ TẢI FILE TXT
# =========================================================
if st.session_state.invoice_paid and st.session_state.paid_invoice:
    invoice = st.session_state.paid_invoice

    st.markdown("---")
    st.success("🎉 Xác nhận thanh toán thành công!")

    st.markdown(
        "<h2 style='text-align:center;color:#b45335'>"
        "🧋 HÓA ĐƠN BÁN HÀNG - ZZZ</h2>",
        unsafe_allow_html=True
    )

    st.write(f"**Thời gian:** {invoice['timestamp']}")
    st.write(
        "**Khách hàng:** "
        f"{invoice['customer_name'].strip() or 'Khách vãng lai'}"
    )

    invoice_df = pd.DataFrame(invoice["cart"])

    st.dataframe(
        invoice_df[
            ["Tên món", "Size", "Đường", "Đá",
             "Topping", "Số lượng", "Đơn giá", "Thành tiền"]
        ],
        use_container_width=True,
        hide_index=True
    )

    st.write(f"**Tổng tiền món:** {money(invoice['total_price'])}")
    st.write(
        f"**Giảm giá thủ công:** "
        f"{invoice['manual_discount']}% "
        f"(-{money(invoice['manual_discount_amount'])})"
    )
    st.write(f"**Voucher:** {invoice['voucher_label']}")
    st.write(
        f"**Tiền giảm voucher:** {money(invoice['voucher_discount'])}"
    )
    st.markdown(
        f"## Tổng thanh toán: {money(invoice['final_price'])}"
    )

    txt_data = create_txt_invoice(
        invoice["customer_name"],
        invoice["cart"],
        invoice["total_price"],
        invoice["manual_discount"],
        invoice["voucher_label"],
        invoice["voucher_discount"],
        invoice["final_price"],
        invoice["timestamp"],
    )

    st.download_button(
        "📥 Tải hóa đơn (.TXT)",
        data=txt_data,
        file_name=(
            f"HoaDon_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        ),
        mime="text/plain",
        use_container_width=True
    )

    if st.button("🔄 Tạo đơn hàng mới", use_container_width=True):
        st.session_state.cart = []
        st.session_state.invoice_paid = False
        st.session_state.paid_invoice = None
        st.session_state.applied_voucher = ""
        st.session_state.voucher_input = ""
        st.session_state.wheel_prize = None
        st.session_state.wheel_spun = False
        st.rerun()

# =========================================================
# 10. CHÂN TRANG
# =========================================================
st.markdown("---")
st.markdown(
    "<div style='text-align:center;color:#8a6b5c'>"
    "🧋 QUÁN TRÀ SỮA ZZZ | Cảm ơn bạn đã ghé thăm!"
    "</div>",
    unsafe_allow_html=True
)
