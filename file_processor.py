import io
import pandas as pd

from fastapi import UploadFile


class FileProcessor:
    @staticmethod
    async def parse_file(file: UploadFile, sep: str = ",") -> str:
        """Parse the file and return its content"""
        content = await file.read()

        if file.filename.endswith(".csv"):
            df = pd.read_csv(io.BytesIO(content), sep=sep)
            print(df)
            return df.to_csv(index=False)

        if file.filename.endswith(".tsv"):
            df = pd.read_csv(io.BytesIO(content), sep="\t")
            print(df)
            return df.to_csv(index=False, sep="\t")

        if file.filename.endswith(".txt"):
            print(content.decode("utf-8"))
            return content.decode("utf-8")

        raise ValueError("Unsupported file format")
