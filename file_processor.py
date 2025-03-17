from fastapi import UploadFile
from typing import List
import io
import pandas as pd


class FileProcessor:
    @staticmethod
    async def parse_file(file: UploadFile, sep: str = ",") -> List:
        """Parse the file and return its content in list of batches"""
        content = await file.read()

        if file.filename.endswith((".csv", ".tsv")):
            df = pd.read_csv(io.BytesIO(content), sep=sep, dtype=str)
            return df.apply(lambda row: " ".join(row.dropna()), axis=1).tolist()

        if file.filename.endswith(".txt"):
            return content.decode("utf-8").strip().split("\n")

        raise ValueError("Unsupported file format")
