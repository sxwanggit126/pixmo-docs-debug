#!/usr/bin/env python3
"""
自动化DataDreamer数据集转换工具
从项目根目录运行: python convert.py
新增功能：同时将图片数据保存为图片文件
修正版：正确处理DataDreamer的图片数据格式
"""

import os
import json
import base64
import argparse
from io import BytesIO
from pathlib import Path
import pandas as pd
from datasets import Dataset
from PIL import Image
from loguru import logger


def get_project_root():
    """
    自动获取项目根目录
    """
    return Path(__file__).parent.absolute()


def image_to_base64(image):
    """
    将PIL Image对象转换为base64编码的字符串
    """
    if not isinstance(image, Image.Image):
        return None

    buffer = BytesIO()
    image.save(buffer, format='PNG')
    img_bytes = buffer.getvalue()
    buffer.close()

    return base64.b64encode(img_bytes).decode('utf-8')


def save_image_to_file(image, image_dir, row_idx, col_name, img_counter):
    """
    将PIL Image保存为文件

    Args:
        image: PIL Image对象
        image_dir: 图片保存目录
        row_idx: 数据行号
        col_name: 列名
        img_counter: 图片计数器（用于同一行同一列有多个图片的情况）

    Returns:
        str: 图片文件的相对路径
    """
    if not isinstance(image, Image.Image):
        return None

    # 确保图片目录存在
    image_dir.mkdir(exist_ok=True)

    # 生成图片文件名：row_{行号}_{列名}_{计数器}.png
    filename = f"row_{row_idx:06d}_{col_name}_{img_counter:03d}.png"
    filepath = image_dir / filename

    # 保存图片
    image.save(filepath, format='PNG')

    # 返回相对路径（相对于数据集目录）
    return f"images/{filename}"


def is_datadreamer_image_format(value):
    """
    检测是否是DataDreamer的图片格式：{"bytes": b'...', "path": "..."}
    """
    return (isinstance(value, dict) and
            "bytes" in value and
            isinstance(value["bytes"], bytes) and
            len(value["bytes"]) > 100)  # 图片二进制数据通常很长


def bytes_to_image(img_bytes):
    """
    将二进制数据转换为PIL Image对象
    """
    try:
        img_buffer = BytesIO(img_bytes)
        return Image.open(img_buffer)
    except Exception as e:
        logger.error(f"无法解码二进制图片数据: {e}")
        return None


def process_value(value, image_dir=None, row_idx=None, col_name=None, img_counter_dict=None):
    """
    处理不同类型的数据值，确保可以进行JSON序列化
    支持DataDreamer的图片格式和PIL Image对象

    Args:
        value: 要处理的值
        image_dir: 图片保存目录
        row_idx: 当前行号
        col_name: 当前列名
        img_counter_dict: 图片计数器字典（用于跟踪每列的图片数量）
    """
    if value is None:
        return None

    if hasattr(value, 'tolist'):
        try:
            value = value.tolist()
        except:
            pass

    # 处理DataDreamer的图片格式：{"bytes": b'...', "path": "..."}
    if is_datadreamer_image_format(value):
        img_bytes = value["bytes"]

        # 将二进制数据转换为base64用于JSON存储
        base64_data = base64.b64encode(img_bytes).decode('utf-8')

        result = {
            "type": "image",
            "format": "base64_png",
            "data": base64_data
        }

        # 如果提供了图片保存参数，则同时保存图片文件
        if image_dir is not None and row_idx is not None and col_name is not None:
            # 将二进制数据转换为PIL Image
            pil_image = bytes_to_image(img_bytes)

            if pil_image:
                # 获取当前列的图片计数器
                key = f"{row_idx}_{col_name}"
                if key not in img_counter_dict:
                    img_counter_dict[key] = 0
                img_counter_dict[key] += 1

                # 保存图片文件
                image_path = save_image_to_file(
                    pil_image, image_dir, row_idx, col_name, img_counter_dict[key]
                )

                if image_path:
                    result["file_path"] = image_path
                    logger.info(f"保存图片: {image_path} (第{row_idx + 1}行, 列'{col_name}')")

        return result

    # 处理直接的PIL Image对象
    elif isinstance(value, Image.Image):
        result = {
            "type": "image",
            "format": "base64_png",
            "data": image_to_base64(value)
        }

        # 如果提供了图片保存参数，则同时保存图片文件
        if image_dir is not None and row_idx is not None and col_name is not None:
            # 获取当前列的图片计数器
            key = f"{row_idx}_{col_name}"
            if key not in img_counter_dict:
                img_counter_dict[key] = 0
            img_counter_dict[key] += 1

            # 保存图片文件
            image_path = save_image_to_file(
                value, image_dir, row_idx, col_name, img_counter_dict[key]
            )

            if image_path:
                result["file_path"] = image_path
                logger.info(f"保存图片: {image_path} (第{row_idx + 1}行, 列'{col_name}')")

        return result

    elif isinstance(value, (list, tuple)):
        return [
            process_value(item, image_dir, row_idx, f"{col_name}_item{i}", img_counter_dict)
            for i, item in enumerate(value)
        ]
    elif isinstance(value, dict):
        return {
            k: process_value(v, image_dir, row_idx, f"{col_name}_{k}", img_counter_dict)
            for k, v in value.items()
        }
    elif isinstance(value, bytes):
        try:
            return value.decode('utf-8')
        except UnicodeDecodeError:
            return base64.b64encode(value).decode('utf-8')
    else:
        return value


def convert_dataset_to_jsonl(dataset_dir):
    """
    将单个数据集目录转换为JSONL格式，同时保存图片文件
    """
    dataset_path = dataset_dir / "_dataset"

    if not dataset_path.exists():
        logger.warning(f"数据集路径不存在: {dataset_path}")
        return False

    try:
        logger.info(f"加载数据集: {dataset_dir.name}")
        dataset = Dataset.load_from_disk(str(dataset_path))

        df = dataset.to_pandas()

        # 创建输出文件和图片目录
        output_file = dataset_path / f"{dataset_dir.name}.jsonl"
        image_dir = dataset_path / "images"

        # 图片计数器，用于跟踪每个位置的图片数量
        img_counter_dict = {}

        logger.info(f"开始转换 {len(df)} 行数据，{len(df.columns)} 列")
        logger.info(f"列名: {list(df.columns)}")
        logger.info(f"图片将保存到: {image_dir}")

        total_images_saved = 0

        with open(output_file, 'w', encoding='utf-8') as f:
            for idx, row in df.iterrows():
                row_dict = {}
                row_image_count = 0

                for col in df.columns:
                    value = row[col]

                    try:
                        if pd.isna(value):
                            row_dict[col] = None
                        else:
                            processed_value = process_value(
                                value, image_dir, idx, col, img_counter_dict
                            )
                            row_dict[col] = processed_value

                            # 统计这一行保存的图片数量
                            if (isinstance(processed_value, dict) and
                                    processed_value.get("type") == "image" and
                                    "file_path" in processed_value):
                                row_image_count += 1

                    except (ValueError, TypeError):
                        if value is None:
                            row_dict[col] = None
                        else:
                            processed_value = process_value(
                                value, image_dir, idx, col, img_counter_dict
                            )
                            row_dict[col] = processed_value

                # 在行数据中添加元数据
                row_dict["_metadata"] = {
                    "row_index": idx,
                    "images_in_row": row_image_count
                }

                total_images_saved += row_image_count

                json_line = json.dumps(row_dict, ensure_ascii=False, separators=(',', ':'))
                f.write(json_line + '\n')

                if (idx + 1) % 100 == 0 or (idx + 1) == len(df):
                    logger.info(f"已处理 {idx + 1}/{len(df)} 行，累计保存 {total_images_saved} 张图片")

        logger.success(f"转换完成!")
        logger.info(f"JSONL文件: {output_file}")
        logger.info(f"总共保存了 {total_images_saved} 张图片到: {image_dir}")

        # 显示图片保存统计
        if total_images_saved > 0:
            logger.info("图片保存统计:")
            for key, count in img_counter_dict.items():
                row_idx, col_name = key.split('_', 1)
                logger.info(f"  第{int(row_idx) + 1}行, 列'{col_name}': {count}张图片")
        else:
            logger.warning("没有发现图片数据或图片数据格式不匹配")

        return True

    except Exception as e:
        logger.error(f"转换失败 {dataset_dir.name}: {e}")
        import traceback
        logger.error(f"详细错误信息: {traceback.format_exc()}")
        return False


def discover_datasets(session_output_dir):
    """
    自动发现session_output目录下的所有数据集
    """
    if not session_output_dir.exists():
        logger.error(f"session_output目录不存在: {session_output_dir}")
        return []

    datasets = []

    for item in session_output_dir.iterdir():
        if item.is_dir():
            dataset_subdir = item / "_dataset"
            if dataset_subdir.exists():
                datasets.append(item)
                logger.info(f"发现数据集: {item.name}")

    return datasets


def main():
    """
    主函数，自动发现并转换所有数据集
    """
    parser = argparse.ArgumentParser(description="转换DataDreamer数据集为JSONL格式并保存图片文件")
    parser.add_argument("--dataset", type=str, help="指定要转换的数据集名称（可选）")
    parser.add_argument("--session-dir", type=str, default="session_output",
                        help="session输出目录名称（默认: session_output）")

    args = parser.parse_args()

    project_root = get_project_root()
    os.chdir(project_root)
    logger.info(f"项目根目录: {project_root}")

    session_output_dir = project_root / args.session_dir

    if args.dataset:
        target_dataset = session_output_dir / args.dataset
        if target_dataset.exists():
            logger.info(f"转换指定数据集: {args.dataset}")
            convert_dataset_to_jsonl(target_dataset)
        else:
            logger.error(f"指定的数据集不存在: {args.dataset}")
    else:
        datasets = discover_datasets(session_output_dir)

        if not datasets:
            logger.warning("未发现任何数据集")
            return

        logger.info(f"发现 {len(datasets)} 个数据集，开始批量转换")

        success_count = 0
        total_images = 0

        for dataset_dir in datasets:
            if convert_dataset_to_jsonl(dataset_dir):
                success_count += 1
                # 统计这个数据集保存的图片数量
                image_dir = dataset_dir / "_dataset" / "images"
                if image_dir.exists():
                    images_count = len(list(image_dir.glob("*.png")))
                    total_images += images_count

        logger.info(f"转换完成: {success_count}/{len(datasets)} 个数据集成功")
        logger.info(f"总共保存了 {total_images} 张图片")


if __name__ == "__main__":
    main()