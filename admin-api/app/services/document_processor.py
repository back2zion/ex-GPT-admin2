"""
Document Processing Service
파일에서 텍스트 추출 및 청킹 처리
"""
import io
import os
import logging
from typing import List, Optional, Tuple
import hashlib
import httpx

logger = logging.getLogger(__name__)


class DocumentProcessor:
    """문서 처리 서비스 (텍스트 추출, 청킹, 임베딩)"""

    def __init__(self, embedding_endpoint: str = "http://vllm-embeddings:8000/v1"):
        """
        초기화

        Args:
            embedding_endpoint: Embedding API 엔드포인트
        """
        self.embedding_endpoint = embedding_endpoint
        self.chunk_size = 500  # 문자 단위
        self.chunk_overlap = 50

    def extract_text(self, file_content: bytes, filename: str) -> Optional[str]:
        """
        파일에서 텍스트 추출

        Args:
            file_content: 파일 바이트 데이터
            filename: 파일명

        Returns:
            Optional[str]: 추출된 텍스트 (실패 시 None)
        """
        file_ext = os.path.splitext(filename)[1].lower()

        try:
            if file_ext == '.txt':
                return self._extract_from_txt(file_content)
            elif file_ext == '.pdf':
                return self._extract_from_pdf(file_content)
            elif file_ext in ['.hwp', '.hwpx']:
                return self._extract_from_hwp(file_content)
            elif file_ext in ['.doc', '.docx']:
                return self._extract_from_docx(file_content)
            elif file_ext in ['.xlsx', '.xls']:
                return self._extract_from_excel(file_content)
            else:
                logger.warning(f"Unsupported file type: {file_ext}")
                return None
        except Exception as e:
            logger.error(f"Failed to extract text from {filename}: {e}")
            return None

    def _extract_from_txt(self, file_content: bytes) -> str:
        """TXT 파일에서 텍스트 추출"""
        # 여러 인코딩 시도
        for encoding in ['utf-8', 'cp949', 'euc-kr', 'latin-1']:
            try:
                return file_content.decode(encoding)
            except UnicodeDecodeError:
                continue

        # 모든 인코딩 실패 시 에러 무시하고 디코딩
        return file_content.decode('utf-8', errors='ignore')

    def _extract_from_pdf(self, file_content: bytes) -> Optional[str]:
        """PDF 파일에서 텍스트 추출"""
        try:
            import PyPDF2

            pdf_file = io.BytesIO(file_content)
            pdf_reader = PyPDF2.PdfReader(pdf_file)

            text_parts = []
            for page in pdf_reader.pages:
                text = page.extract_text()
                if text:
                    text_parts.append(text)

            return '\n\n'.join(text_parts)
        except ImportError:
            logger.error("PyPDF2 not installed. Install with: pip install PyPDF2")
            return None
        except Exception as e:
            logger.error(f"Failed to extract from PDF: {e}")
            return None

    def _extract_from_hwp(self, file_content: bytes) -> Optional[str]:
        """HWP/HWPX 파일에서 텍스트 추출"""
        try:
            import olefile

            # HWP 파일은 OLE 구조
            ole = olefile.OleFileIO(file_content)

            # HWP 파일의 텍스트는 BodyText 섹션에 저장
            text_parts = []

            # 섹션 찾기
            for entry in ole.listdir():
                entry_name = '/'.join(entry)
                if 'BodyText' in entry_name or 'Section' in entry_name:
                    try:
                        stream = ole.openstream(entry)
                        data = stream.read()
                        # HWP 텍스트는 UTF-16LE로 인코딩됨
                        text = data.decode('utf-16le', errors='ignore')
                        text_parts.append(text)
                    except:
                        continue

            ole.close()
            return '\n\n'.join(text_parts)
        except ImportError:
            logger.error("olefile not installed. Install with: pip install olefile")
            return None
        except Exception as e:
            logger.error(f"Failed to extract from HWP: {e}")
            # HWP 추출 실패 시 원본 파일명만 반환
            return None

    def _extract_from_docx(self, file_content: bytes) -> Optional[str]:
        """DOCX 파일에서 텍스트 추출"""
        try:
            from docx import Document

            docx_file = io.BytesIO(file_content)
            doc = Document(docx_file)

            text_parts = []
            for paragraph in doc.paragraphs:
                if paragraph.text.strip():
                    text_parts.append(paragraph.text)

            return '\n\n'.join(text_parts)
        except ImportError:
            logger.error("python-docx not installed. Install with: pip install python-docx")
            return None
        except Exception as e:
            logger.error(f"Failed to extract from DOCX: {e}")
            return None

    def _extract_from_excel(self, file_content: bytes) -> Optional[str]:
        """Excel 파일에서 텍스트 추출"""
        try:
            import openpyxl

            excel_file = io.BytesIO(file_content)
            wb = openpyxl.load_workbook(excel_file, data_only=True)

            text_parts = []
            for sheet in wb.worksheets:
                text_parts.append(f"[Sheet: {sheet.title}]")
                for row in sheet.iter_rows(values_only=True):
                    row_text = ' | '.join([str(cell) if cell is not None else '' for cell in row])
                    if row_text.strip():
                        text_parts.append(row_text)

            return '\n'.join(text_parts)
        except ImportError:
            logger.error("openpyxl not installed. Install with: pip install openpyxl")
            return None
        except Exception as e:
            logger.error(f"Failed to extract from Excel: {e}")
            return None

    def chunk_text(self, text: str) -> List[str]:
        """
        텍스트를 청크로 분할

        Args:
            text: 전체 텍스트

        Returns:
            List[str]: 청크 리스트
        """
        if not text:
            return []

        chunks = []
        start = 0
        text_length = len(text)

        while start < text_length:
            end = start + self.chunk_size

            # 청크 경계를 문장 끝으로 조정 (마침표, 줄바꿈)
            if end < text_length:
                # 다음 마침표나 줄바꿈 찾기
                for delim in ['\n\n', '\n', '. ', '。', '! ', '? ']:
                    delim_pos = text.find(delim, end - 50, end + 50)
                    if delim_pos != -1:
                        end = delim_pos + len(delim)
                        break

            chunk = text[start:end].strip()
            if chunk:
                chunks.append(chunk)

            start = end - self.chunk_overlap

        logger.info(f"Text split into {len(chunks)} chunks")
        return chunks

    async def get_embeddings(self, texts: List[str]) -> Optional[List[List[float]]]:
        """
        텍스트 리스트에 대한 임베딩 생성

        Args:
            texts: 텍스트 리스트

        Returns:
            Optional[List[List[float]]]: 임베딩 벡터 리스트 (실패 시 None)
        """
        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(
                    f"{self.embedding_endpoint}/embeddings",
                    json={
                        "input": texts,
                        "model": "Qwen3-Embedding-0.6B"
                    }
                )

                if response.status_code == 200:
                    result = response.json()
                    embeddings = [item['embedding'] for item in result['data']]
                    logger.info(f"Generated {len(embeddings)} embeddings")
                    return embeddings
                else:
                    logger.error(f"Embedding API failed: {response.status_code} - {response.text}")
                    return None
        except Exception as e:
            logger.error(f"Failed to get embeddings: {e}")
            return None

    async def process_document(
        self,
        file_content: bytes,
        filename: str,
        document_id: str,
        metadata: dict
    ) -> Tuple[Optional[str], Optional[List[dict]]]:
        """
        문서 전체 처리 (텍스트 추출 + 청킹 + 임베딩)

        Args:
            file_content: 파일 바이트 데이터
            filename: 파일명
            document_id: 문서 ID
            metadata: 메타데이터 (title, document_type 등)

        Returns:
            Tuple[Optional[str], Optional[List[dict]]]: (전체 텍스트, 청크+임베딩 리스트)
        """
        # 1. 텍스트 추출
        text = self.extract_text(file_content, filename)
        if not text:
            logger.warning(f"No text extracted from {filename}")
            return None, None

        logger.info(f"Extracted {len(text)} characters from {filename}")

        # 2. 청킹
        chunks = self.chunk_text(text)
        if not chunks:
            logger.warning(f"No chunks created from {filename}")
            return text, None

        # 3. 임베딩 생성
        embeddings = await self.get_embeddings(chunks)
        if not embeddings:
            logger.warning(f"No embeddings generated for {filename}")
            return text, None

        # 4. 청크+임베딩+메타데이터 결합
        chunk_data = []
        for i, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
            chunk_id = f"{document_id}_chunk_{i}"
            chunk_data.append({
                "id": chunk_id,
                "vector": embedding,
                "payload": {
                    "document_id": document_id,
                    "chunk_index": i,
                    "text": chunk,
                    "filename": filename,
                    **metadata
                }
            })

        logger.info(f"Processed document: {len(chunk_data)} chunks with embeddings")
        return text, chunk_data
