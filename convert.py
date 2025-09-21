#!/usr/bin/env python3
"""
自动化DataDreamer数据集转换工具
从项目根目录运行: python convert.py
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


def process_value(value):
    """
    处理不同类型的数据值，确保可以进行JSON序列化
    """
    if value is None:
        return None

    if hasattr(value, 'tolist'):
        try:
            value = value.tolist()
        except:
            pass

    if isinstance(value, Image.Image):
        return {
            "type": "image",
            "format": "base64_png",
            "data": image_to_base64(value)
        }
    elif isinstance(value, (list, tuple)):
        return [process_value(item) for item in value]
    elif isinstance(value, dict):
        return {k: process_value(v) for k, v in value.items()}
    elif isinstance(value, bytes):
        try:
            return value.decode('utf-8')
        except UnicodeDecodeError:
            return base64.b64encode(value).decode('utf-8')
    else:
        return value


def convert_dataset_to_jsonl(dataset_dir):
    """
    将单个数据集目录转换为JSONL格式
    """
    dataset_path = dataset_dir / "_dataset"

    if not dataset_path.exists():
        logger.warning(f"数据集路径不存在: {dataset_path}")
        return False

    try:
        logger.info(f"加载数据集: {dataset_dir.name}")
        dataset = Dataset.load_from_disk(str(dataset_path))

        df = dataset.to_pandas()

        output_file = dataset_path / f"{dataset_dir.name}.jsonl"

        logger.info(f"开始转换 {len(df)} 行数据，{len(df.columns)} 列")
        logger.info(f"列名: {list(df.columns)}")

        with open(output_file, 'w', encoding='utf-8') as f:
            for idx, row in df.iterrows():
                row_dict = {}
                for col in df.columns:
                    value = row[col]

                    try:
                        if pd.isna(value):
                            row_dict[col] = None
                        else:
                            row_dict[col] = process_value(value)
                    except (ValueError, TypeError):
                        if value is None:
                            row_dict[col] = None
                        else:
                            row_dict[col] = process_value(value)

                json_line = json.dumps(row_dict, ensure_ascii=False, separators=(',', ':'))
                f.write(json_line + '\n')

                if (idx + 1) % 100 == 0:
                    logger.info(f"已处理 {idx + 1}/{len(df)} 行")

        logger.success(f"成功转换: {output_file}")
        return True

    except Exception as e:
        logger.error(f"转换失败 {dataset_dir.name}: {e}")
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
    parser = argparse.ArgumentParser(description="转换DataDreamer数据集为JSONL格式")
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
        for dataset_dir in datasets:
            if convert_dataset_to_jsonl(dataset_dir):
                success_count += 1

        logger.info(f"转换完成: {success_count}/{len(datasets)} 个数据集成功")


if __name__ == "__main__":
    main()
