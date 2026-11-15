import os
import uuid

from fastapi import HTTPException, UploadFile, status
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.config import settings
from app.models.resume import Resume, ResumeItem, ResumeSection
from app.modules.ingestion.extractor import DocumentExtractor
from app.modules.ingestion.segmenter import SectionSegmenter


class IngestionService:
    """Orchestrates file storage, text extraction, layout segmentation, and persistence."""

    ALLOWED_EXTENSIONS = {".pdf", ".docx"}
    MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB

    def __init__(self, db: AsyncSession):
        self.db = db

    async def process_resume_upload(
        self,
        user_id: uuid.UUID,
        file: UploadFile,
        is_master: bool = False,
    ) -> Resume:
        """Validate, store, extract, and persist a new resume document."""
        # 1. Validate file extension
        filename = file.filename or "uploaded_resume.pdf"
        ext = os.path.splitext(filename)[1].lower()
        if ext not in self.ALLOWED_EXTENSIONS:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unsupported file format '{ext}'. Only PDF and DOCX files are supported.",
            )

        # 2. Read file bytes and validate size
        file_bytes = await file.read()
        file_size = len(file_bytes)
        if file_size > self.MAX_FILE_SIZE:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail=f"File exceeds maximum allowed size of 10 MB ({file_size / (1024 * 1024):.1f} MB).",
            )
        if file_size == 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Uploaded file is empty (0 bytes).",
            )

        # 3. Save file locally (or MinIO/S3 depending on settings)
        storage_dir = os.path.join(settings.LOCAL_STORAGE_DIR, "uploads", str(user_id))
        os.makedirs(storage_dir, exist_ok=True)
        unique_file_name = f"{uuid.uuid4()}_{filename}"
        file_path = os.path.join(storage_dir, unique_file_name)
        with open(file_path, "wb") as f:
            f.write(file_bytes)

        # 4. Extract text
        file_format = ext.lstrip(".")
        if file_format == "pdf":
            raw_text, ocr_applied = DocumentExtractor.extract_from_pdf(file_bytes)
        else:
            raw_text = DocumentExtractor.extract_from_docx(file_bytes)
            ocr_applied = False

        has_content = bool(raw_text.strip())
        if not has_content:
            raw_text = f"[Text extraction failed or unreadable scanned document: {filename}]"
            parsing_status = "FAILED"
        else:
            parsing_status = "PARSED"

        # 5. Handle is_master flag exclusivity
        if is_master:
            await self.db.execute(
                update(Resume).where(Resume.user_id == user_id).values(is_master=False)
            )

        # 6. Segment into structured sections
        segmented_sections = SectionSegmenter.segment_text(raw_text)

        # 7. Create Resume entity
        resume = Resume(
            user_id=user_id,
            file_name=filename,
            file_key=file_path,
            file_format=file_format,
            file_size_bytes=file_size,
            raw_text=raw_text,
            is_master=is_master,
            parsing_status=parsing_status,
            ocr_applied=ocr_applied,
        )
        self.db.add(resume)
        await self.db.flush()

        # 8. Persist sections and items
        for sec_data in segmented_sections:
            section = ResumeSection(
                resume_id=resume.id,
                section_type=sec_data["section_type"],
                heading=sec_data["heading"],
                raw_content=sec_data["raw_content"],
                display_order=sec_data["display_order"],
            )
            self.db.add(section)
            await self.db.flush()

            for item_data in sec_data.get("items", []):
                item = ResumeItem(
                    section_id=section.id,
                    item_type=item_data["item_type"],
                    title=item_data["title"],
                    organization=item_data.get("organization"),
                    bullets=item_data.get("bullets", []),
                )
                self.db.add(item)

        await self.db.commit()

        # Reload with relationships
        stmt = (
            select(Resume)
            .options(selectinload(Resume.sections).selectinload(ResumeSection.items))
            .where(Resume.id == resume.id)
        )
        result = await self.db.execute(stmt)
        return result.scalar_one()

    async def get_user_resumes(self, user_id: uuid.UUID) -> list[Resume]:
        """Fetch all resumes belonging to user."""
        stmt = (
            select(Resume)
            .options(selectinload(Resume.sections))
            .where(Resume.user_id == user_id)
            .order_by(Resume.created_at.desc())
        )
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def get_resume_by_id(self, user_id: uuid.UUID, resume_id: uuid.UUID) -> Resume:
        """Fetch specific resume by ID enforcing strict tenant isolation."""
        stmt = (
            select(Resume)
            .options(selectinload(Resume.sections).selectinload(ResumeSection.items))
            .where(Resume.id == resume_id, Resume.user_id == user_id)
        )
        result = await self.db.execute(stmt)
        resume = result.scalar_one_or_none()
        if not resume:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Resume not found or does not belong to the authenticated user.",
            )
        return resume

    async def update_sections(
        self,
        user_id: uuid.UUID,
        resume_id: uuid.UUID,
        section_updates: list[dict],
    ) -> Resume:
        """Update parsed section texts and headings."""
        resume = await self.get_resume_by_id(user_id, resume_id)

        for update_item in section_updates:
            sec_id = update_item.get("id")
            for section in resume.sections:
                if section.id == sec_id:
                    if "heading" in update_item and update_item["heading"]:
                        section.heading = update_item["heading"]
                    if "raw_content" in update_item and update_item["raw_content"] is not None:
                        section.raw_content = update_item["raw_content"]
                    if "section_type" in update_item and update_item["section_type"]:
                        section.section_type = update_item["section_type"]

        await self.db.commit()
        return await self.get_resume_by_id(user_id, resume_id)

    async def set_master_resume(self, user_id: uuid.UUID, resume_id: uuid.UUID) -> Resume:
        """Set designated resume as active master profile source."""
        resume = await self.get_resume_by_id(user_id, resume_id)

        # Unset all other resumes as master
        await self.db.execute(
            update(Resume).where(Resume.user_id == user_id).values(is_master=False)
        )
        resume.is_master = True
        await self.db.commit()
        return await self.get_resume_by_id(user_id, resume_id)

    async def delete_resume(self, user_id: uuid.UUID, resume_id: uuid.UUID) -> None:
        """Delete resume record and remove binary file from storage."""
        resume = await self.get_resume_by_id(user_id, resume_id)
        file_path = resume.file_key

        await self.db.delete(resume)
        await self.db.commit()

        if file_path and os.path.exists(file_path):
            try:
                os.remove(file_path)
            except OSError:
                pass
