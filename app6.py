import streamlit as st
import os
from PIL import Image
import pandas as pd
import random
import io

def main():
    # 初始化设置
    reference_folder = 'InputCD4'  # 参考图文件夹
    rating_folders = ['RealCD4', 'OutputCD4']  # 待评分图文件夹
    random_seed = 666  # 固定随机种子确保可重复性

    # 获取图片列表（确保所有文件夹中都有相同的图片）
    image_names = set(os.listdir(reference_folder))
    for folder in rating_folders:
        image_names &= set(os.listdir(folder))
    image_names = sorted(list(image_names))

    # 生成所有待评分图像路径（打乱顺序）
    random.seed(random_seed)
    all_rating_images = []
    for name in image_names:
        for folder in rating_folders:
            all_rating_images.append((name, folder))
    random.shuffle(all_rating_images)

    # 初始化session状态
    if 'index' not in st.session_state:
        st.session_state.index = 0
    if 'scores' not in st.session_state:
        st.session_state.scores = {}
    if 'all_rating_images' not in st.session_state:
        st.session_state.all_rating_images = all_rating_images

    def save_score():
        name, folder = st.session_state.all_rating_images[st.session_state.index]
        if name not in st.session_state.scores:
            st.session_state.scores[name] = {}
        
        st.session_state.scores[name][folder] = {
            "score1": int(st.session_state.get(f"{name}_{folder}_score1", 5)),
            "score2": int(st.session_state.get(f"{name}_{folder}_score2", 5)),
            "score3": int(st.session_state.get(f"{name}_{folder}_score3", 5))
        }

    # 页面标题和样式
    st.title("IF染色CD4盲评系统")
    
    # 自定义CSS样式
    st.markdown("""
    <style>
        .score-button {
            width: 30px !important;
            height: 30px !important;
            min-width: 30px !important;
            padding: 0 !important;
            margin: 0 2px !important;
        }
        .score-label {
            text-align: center;
            font-weight: bold;
            margin: 5px 0;
            font-size: 14px;
        }
        img {
            border-radius: 0px !important;
            max-height: 400px;
            object-fit: contain;
        }
    </style>
    """, unsafe_allow_html=True)

    # 当前评分进度
    total_ratings = len(st.session_state.all_rating_images)
    current_rating = st.session_state.index + 1
    st.write(f"### 评分进度: {current_rating}/{total_ratings}")

    # 获取当前评分的图像
    current_image_name, current_folder = st.session_state.all_rating_images[st.session_state.index]

    # 使用st.columns创建三列布局
    col1, col2, col3 = st.columns([1, 1, 1])  # 三列等宽

    # 第一列：参考图
    with col1:
        ref_img_path = os.path.join(reference_folder, current_image_name)
        if os.path.exists(ref_img_path):
            ref_img = Image.open(ref_img_path)
            st.image(ref_img, caption="参考图", use_container_width=True, clamp=True)
        else:
            st.warning(f"参考图 {current_image_name} 不存在")

    # 第二列：待评分图
    with col2:
        rating_img_path = os.path.join(current_folder, current_image_name)
        if os.path.exists(rating_img_path):
            rating_img = Image.open(rating_img_path)
            st.image(rating_img, caption="待评分图像", use_container_width=True, clamp=True)
        else:
            st.error(f"待评分图 {current_image_name} 不存在")

    # 第三列：评分项
    with col3:
        # st.write("### 评分项")
        
        # 从session_state获取已保存的评分或初始化
        saved_scores = st.session_state.scores.get(current_image_name, {}).get(current_folder, {})
        
        # 三个评分维度
        dimensions = [
            ("细胞核细节", f"{current_image_name}_{current_folder}_score1", saved_scores.get("score1", 5)),
            ("染色模式一致性", f"{current_image_name}_{current_folder}_score2", saved_scores.get("score2", 5)),
            ("无非特异性染色", f"{current_image_name}_{current_folder}_score3", saved_scores.get("score3", 5))
        ]

        for label, key, default_value in dimensions:
            current_value = st.session_state.get(key, default_value)
            
            st.markdown(f'<div class="score-label">{label}</div>', unsafe_allow_html=True)
            
            # 评分按钮
            cols = st.columns(5)
            for i in range(1, 6):
                with cols[i-1]:
                    if st.button(str(i), 
                               key=f"{key}_{i}", 
                               type="primary" if current_value == i else "secondary",
                               help=f"{i}分: {'不可接受' if i == 1 else '可接受' if i == 2 else '好' if i == 3 else '很好' if i == 4 else '优'}"):
                        st.session_state[key] = i
                        st.rerun()

    # 导航按钮
    nav_col2, nav_col3 = st.columns([1, 3])  # nav_col1, 
    # with nav_col1:
    #     if st.button("上一张") and st.session_state.index > 0:
    #         save_score()
    #         st.session_state.index -= 1
    #         st.rerun()
    with nav_col2:
        if st.button("下一张") and st.session_state.index < total_ratings - 1:
            save_score()
            st.session_state.index += 1
            st.rerun()
    with nav_col3:
        if st.button("保存评分并生成下载链接"):
            save_score()
            # 准备数据
            rows = []
            for img_name, folders in st.session_state.scores.items():
                for folder, scores in folders.items():
                    rows.append({
                        "image_name": img_name,
                        "folder": folder,  # 这里会显示是Real还是Output
                        "score1": scores["score1"],
                        "score2": scores["score2"],
                        "score3": scores["score3"],
                    })
            
            df = pd.DataFrame(rows)
            
            # 生成Excel文件
            output = io.BytesIO()
            with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                df.to_excel(writer, index=False)
            output.seek(0)

            st.success("评分结果已生成！请点击下面按钮下载：")
            st.download_button(
                label="📥 下载评分结果 (Excel)",
                data=output,
                file_name="盲评结果.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )

    # 页脚信息
    st.markdown("请确认已完成当前图像的评分")
    st.markdown("---")
    st.markdown("**评分标准说明**")
    st.markdown("- **5分**: 优")
    st.markdown("- **4分**: 很好") 
    st.markdown("- **3分**: 好")
    st.markdown("- **2分**: 可接受")
    st.markdown("- **1分**: 不可接受")
    st.markdown("**评分维度说明**")
    st.markdown("- **细胞核细节**: 细胞核轮廓完整可辨")
    st.markdown("- **染色模式一致性**: 主要表现为细胞膜染色，有时伴随轻微胞质染色") 
    st.markdown("- **无非特异性染色**: 背景干净、无染色伪影")

if __name__ == "__main__":
    main()